from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

if __package__:
    from scripts.check_translation import (
        TRANSLATION_NOTICE,
        GlossaryTerm,
        load_glossary,
        validate_translation,
    )
    from scripts.markdown_chunks import (
        MarkdownChunk,
        restore_missing_newline_boundaries,
        split_markdown,
    )
    from scripts.model_runner import EXACT_MODEL, ModelName, ModelResult, run_model
else:
    from check_translation import (  # pyright: ignore[reportImplicitRelativeImport]
        TRANSLATION_NOTICE,
        GlossaryTerm,
        load_glossary,
        validate_translation,
    )
    from markdown_chunks import (  # pyright: ignore[reportImplicitRelativeImport]
        MarkdownChunk,
        restore_missing_newline_boundaries,
        split_markdown,
    )
    from model_runner import (  # pyright: ignore[reportImplicitRelativeImport]
        EXACT_MODEL,
        ModelName,
        ModelResult,
        run_model,
    )


@dataclass(frozen=True)
class TranslatedChunk:
    index: str
    start_line: int
    end_line: int
    source_sha256: str
    response_sha256: str
    response_path: Path
    runtime_id: str


@dataclass(frozen=True)
class TranslationManifest:
    source_path: Path
    output_path: Path
    evidence_path: Path
    model: ModelName
    source_sha256: str
    draft_sha256: str
    chunks: tuple[TranslatedChunk, ...]


class TranslationError(RuntimeError):
    """Translation orchestration нарушил закреплённый контракт."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_paths(
    repo_root: Path,
    source_path: Path,
    output_path: Path,
    evidence_path: Path,
) -> tuple[Path, Path, Path, Path]:
    root = repo_root.resolve()
    source = source_path.resolve()
    output = output_path.resolve()
    evidence = evidence_path.resolve()
    source_root = (root / ".tmp/upstream/book").resolve()
    output_root = (root / ".tmp/drafts").resolve()
    evidence_root = (root / ".tmp/evidence").resolve()
    if not source.is_file() or not source.is_relative_to(source_root):
        raise TranslationError(f"Source должен находиться внутри {source_root}")
    if output == output_root or not output.is_relative_to(output_root):
        raise TranslationError(f"Output должен находиться внутри {output_root}")
    if evidence == evidence_root or not evidence.is_relative_to(evidence_root):
        raise TranslationError(f"Evidence должен находиться внутри {evidence_root}")
    for artifact in (output, evidence):
        if artifact.exists():
            raise TranslationError(f"Partial artifact уже существует: {artifact}")
    return root, source, output, evidence


def runtime_record(result: ModelResult) -> dict[str, object]:
    evidence = result.evidence
    return {
        "requested_model": evidence.requested_model,
        "reported_model": evidence.reported_model,
        "provider": evidence.provider,
        "thread_id": evidence.thread_id,
        "turn_id": evidence.turn_id,
        "ephemeral": evidence.ephemeral,
        "fallback_allowed": evidence.fallback_allowed,
        "sandbox_type": evidence.sandbox_type,
        "completion_observed": evidence.completion_observed,
        "usage_observed": evidence.usage_observed,
        "command_sha256": evidence.command_sha256,
        "prompt_sha256": result.prompt_sha256,
        "response_sha256": result.response_sha256,
        "stdout_sha256": result.stdout_sha256,
        "stderr_sha256": result.stderr_sha256,
    }


def _render_glossary(terms: tuple[GlossaryTerm, ...]) -> str:
    accepted = tuple(term for term in terms if term.status == "accepted")
    lines: list[str] = []
    for term in accepted:
        lines.extend(
            [
                f"- id: {term.id}",
                f"  source: {', '.join(term.source)}",
                f"  preferred: {term.preferred}",
                f"  rule: {term.rule}",
                f"  forbidden: {', '.join(term.forbidden) or '(none)'}",
            ]
        )
    return "\n".join(lines) if lines else "(accepted entries отсутствуют)"


def _render_prompt(
    template: str,
    source_relative: str,
    chunk: MarkdownChunk,
    accepted_glossary: str,
) -> str:
    required = (
        "{{SOURCE_PATH}}",
        "{{START_LINE}}",
        "{{END_LINE}}",
        "{{SOURCE_SHA256}}",
        "{{GLOSSARY}}",
        "{{SOURCE}}",
    )
    missing = tuple(marker for marker in required if marker not in template)
    if missing:
        raise TranslationError(f"Translation prompt не содержит markers: {', '.join(missing)}")
    rendered = template
    replacements = {
        "{{SOURCE_PATH}}": source_relative,
        "{{START_LINE}}": str(chunk.start_line),
        "{{END_LINE}}": str(chunk.end_line),
        "{{SOURCE_SHA256}}": chunk.sha256,
        "{{GLOSSARY}}": accepted_glossary,
    }
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    return rendered.replace("{{SOURCE}}", chunk.text)


def _has_extra_outer_fence(source: str, response: str) -> bool:
    response_lines = tuple(line for line in response.strip().splitlines() if line.strip())
    if len(response_lines) < 2:
        return False
    opening = re.fullmatch(r"(```|~~~)(?:markdown|md)?", response_lines[0].strip(), re.IGNORECASE)
    if opening is None or response_lines[-1].strip() != opening.group(1):
        return False
    source_lines = tuple(line for line in source.strip().splitlines() if line.strip())
    source_starts_with_same_fence = bool(
        source_lines and source_lines[0].lstrip().startswith(opening.group(1))
    )
    return not source_starts_with_same_fence or response_lines[0].strip().casefold() in {
        "```markdown",
        "```md",
        "~~~markdown",
        "~~~md",
    }


def translate_file(
    source_path: Path,
    output_path: Path,
    glossary_path: Path,
    evidence_path: Path,
    repo_root: Path,
    max_chars: int = 40_000,
    timeout_seconds: int = 3_600,
) -> TranslationManifest:
    root, source, output, evidence = _validate_paths(
        repo_root,
        source_path,
        output_path,
        evidence_path,
    )
    if not glossary_path.is_file():
        raise TranslationError(f"Glossary не существует: {glossary_path}")
    prompt_path = root / "prompts/translate.txt"
    if not prompt_path.is_file():
        raise TranslationError(f"Translation prompt не существует: {prompt_path}")

    source_text = source.read_text(encoding="utf-8")
    chunks = split_markdown(source_text, max_chars=max_chars)
    if not chunks:
        raise TranslationError("Source Markdown пуст")
    terms = load_glossary(glossary_path)
    accepted_glossary = _render_glossary(terms)
    template = prompt_path.read_text(encoding="utf-8")
    source_relative = source.relative_to(root).as_posix()
    chunk_root = output.parent / ".chunks" / output.stem
    translated_chunks: list[TranslatedChunk] = []
    responses: list[str] = []
    runtime_records: list[dict[str, object]] = []

    for chunk in chunks:
        prompt = _render_prompt(template, source_relative, chunk, accepted_glossary)
        chunk_output = chunk_root / f"{chunk.index}.md"
        result = run_model(EXACT_MODEL, prompt, root, chunk_output, timeout_seconds)
        if _has_extra_outer_fence(chunk.text, result.response):
            raise TranslationError(f"Chunk {chunk.index}: обнаружен лишний внешний Markdown fence")
        responses.append(result.response)
        translated_chunks.append(
            TranslatedChunk(
                index=chunk.index,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                source_sha256=chunk.sha256,
                response_sha256=result.response_sha256,
                response_path=chunk_output,
                runtime_id=result.evidence.thread_id,
            )
        )
        runtime_records.append(runtime_record(result))

    restored_responses = restore_missing_newline_boundaries(chunks, responses)
    draft = f"{TRANSLATION_NOTICE}\n\n{''.join(restored_responses)}"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(draft, encoding="utf-8")
    issues = validate_translation(source, output, terms)
    if issues:
        codes = ", ".join(sorted({issue.code for issue in issues}))
        raise TranslationError(f"Draft не прошёл structural validation: {codes}")

    evidence_document: dict[str, object] = {
        "schema_version": 1,
        "pass": "translation",
        "model_id": EXACT_MODEL,
        "source_path": source.relative_to(root).as_posix(),
        "draft_path": output.relative_to(root).as_posix(),
        "source_sha256": _sha256(source_text),
        "draft_sha256": _sha256(draft),
        "max_chars": max_chars,
        "chunks": [
            {
                "index": chunk.index,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "source_sha256": chunk.source_sha256,
                "draft_sha256": chunk.response_sha256,
                "response_path": chunk.response_path.relative_to(root).as_posix(),
                "runtime": runtime,
            }
            for chunk, runtime in zip(translated_chunks, runtime_records, strict=True)
        ],
    }
    evidence.parent.mkdir(parents=True, exist_ok=True)
    with evidence.open("x", encoding="utf-8", newline="") as evidence_file:
        json.dump(evidence_document, evidence_file, ensure_ascii=False, indent=2)
        evidence_file.write("\n")

    return TranslationManifest(
        source_path=source,
        output_path=output,
        evidence_path=evidence,
        model=EXACT_MODEL,
        source_sha256=_sha256(source_text),
        draft_sha256=_sha256(draft),
        chunks=tuple(translated_chunks),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Перевести pinned Markdown file")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--glossary", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--max-chars", type=int, default=40_000)
    parser.add_argument("--timeout-seconds", type=int, default=3_600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    try:
        manifest = translate_file(
            cast(Path, arguments.source),
            cast(Path, arguments.output),
            cast(Path, arguments.glossary),
            cast(Path, arguments.evidence),
            repo_root,
            cast(int, arguments.max_chars),
            cast(int, arguments.timeout_seconds),
        )
    except (OSError, ValueError, TranslationError) as error:
        print(f"translation-error: {error}", file=sys.stderr)
        return 2
    print(
        f"translated {manifest.source_path} -> {manifest.output_path} "
        f"with {len(manifest.chunks)} chunks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
