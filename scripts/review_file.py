from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, cast

from jsonschema import Draft202012Validator, ValidationError

from scripts.check_translation import (
    TRANSLATION_NOTICE,
    GlossaryTerm,
    load_glossary,
    parse_markdown,
)
from scripts.markdown_chunks import MarkdownChunk, split_markdown
from scripts.model_runner import ModelName, run_model

type JsonValue = str | int | float | bool | None | dict[str, JsonValue] | list[JsonValue]


class JsonValidator(Protocol):
    def validate(self, instance: JsonValue) -> None: ...


@dataclass(frozen=True)
class ReviewIssue:
    category: str
    severity: str
    source_start_line: int
    source_end_line: int
    target_start_line: int
    target_end_line: int
    evidence: str
    proposed_replacement: str


@dataclass(frozen=True)
class ReviewedChunk:
    index: str
    source_start_line: int
    source_end_line: int
    target_start_line: int
    target_end_line: int
    source_sha256: str
    translation_sha256: str
    runtime_id: str
    issues: tuple[ReviewIssue, ...]


@dataclass(frozen=True)
class ReviewManifest:
    model_id: ModelName
    source_path: Path
    translation_path: Path
    output_path: Path
    source_sha256: str
    translation_sha256: str
    chunks: tuple[ReviewedChunk, ...]


class ReviewError(RuntimeError):
    """Independent review нарушил source/translation contract."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_paths(
    repo_root: Path,
    source_path: Path,
    translation_path: Path,
    output_path: Path,
) -> tuple[Path, Path, Path, Path]:
    root = repo_root.resolve()
    source = source_path.resolve()
    translation = translation_path.resolve()
    output = output_path.resolve()
    source_root = (root / ".tmp/upstream/book").resolve()
    translation_root = (root / "book").resolve()
    output_root = (root / ".tmp/reviews").resolve()
    if not source.is_file() or not source.is_relative_to(source_root):
        raise ReviewError(f"Source должен находиться внутри {source_root}")
    if not translation.is_file() or not translation.is_relative_to(translation_root):
        raise ReviewError(f"Translation должен находиться внутри {translation_root}")
    if output == output_root or not output.is_relative_to(output_root):
        raise ReviewError(f"Output должен находиться внутри {output_root}")
    return root, source, translation, output


def _translation_body(text: str) -> tuple[str, int]:
    if not text.startswith(TRANSLATION_NOTICE):
        raise ReviewError("Translation не начинается с обязательного notice")
    remainder = text[len(TRANSLATION_NOTICE) :]
    leading_newlines = len(remainder) - len(remainder.lstrip("\n"))
    if leading_newlines == 0:
        raise ReviewError("После translation notice отсутствует перевод строки")
    return remainder[leading_newlines:], leading_newlines


def _aligned_shape(source: MarkdownChunk, target: MarkdownChunk) -> bool:
    source_shape = parse_markdown(source.text)
    target_shape = parse_markdown(target.text)
    return (
        source_shape.heading_levels == target_shape.heading_levels
        and source_shape.fences == target_shape.fences
        and source_shape.table_count == target_shape.table_count
        and source_shape.image_destinations == target_shape.image_destinations
    )


def _accepted_glossary(terms: tuple[GlossaryTerm, ...]) -> str:
    lines: list[str] = []
    for term in terms:
        if term.status != "accepted":
            continue
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
    translation_relative: str,
    source_chunk: MarkdownChunk,
    target_chunk: MarkdownChunk,
    target_line_offset: int,
    glossary: str,
) -> str:
    target_start = target_chunk.start_line + target_line_offset
    target_end = target_chunk.end_line + target_line_offset
    replacements = {
        "{{SOURCE_PATH}}": source_relative,
        "{{TRANSLATION_PATH}}": translation_relative,
        "{{SOURCE_START_LINE}}": str(source_chunk.start_line),
        "{{SOURCE_END_LINE}}": str(source_chunk.end_line),
        "{{TARGET_START_LINE}}": str(target_start),
        "{{TARGET_END_LINE}}": str(target_end),
        "{{SOURCE_SHA256}}": source_chunk.sha256,
        "{{TRANSLATION_SHA256}}": target_chunk.sha256,
        "{{GLOSSARY}}": glossary,
    }
    missing = tuple(
        marker
        for marker in (*replacements, "{{SOURCE}}", "{{TRANSLATION}}")
        if marker not in template
    )
    if missing:
        raise ReviewError(f"Review prompt не содержит markers: {', '.join(missing)}")
    rendered = template
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    rendered = rendered.replace("{{SOURCE}}", source_chunk.text)
    return rendered.replace("{{TRANSLATION}}", target_chunk.text)


def _load_schema(path: Path) -> tuple[dict[str, object], Draft202012Validator]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReviewError(f"Некорректная review JSON Schema: {path}") from error
    if not isinstance(raw, dict):
        raise ReviewError("Review JSON Schema root должен быть object")
    schema = cast(dict[str, object], raw)
    Draft202012Validator.check_schema(schema)
    return schema, Draft202012Validator(schema)


def _parse_payload(response: str, validator: Draft202012Validator) -> dict[str, object]:
    try:
        raw = cast(JsonValue, json.loads(response))
    except json.JSONDecodeError as error:
        raise ReviewError("Opus review вернул некорректный JSON") from error
    try:
        cast(JsonValidator, validator).validate(raw)
    except ValidationError as error:
        raise ReviewError(
            f"Opus review нарушил JSON Schema at {error.json_path}: {error.message}"
        ) from error
    if not isinstance(raw, dict):
        raise ReviewError("Opus review JSON root должен быть object")
    return cast(dict[str, object], raw)


def _issue_from_mapping(raw: object) -> ReviewIssue:
    item = cast(Mapping[str, object], raw)
    return ReviewIssue(
        category=cast(str, item["category"]),
        severity=cast(str, item["severity"]),
        source_start_line=cast(int, item["source_start_line"]),
        source_end_line=cast(int, item["source_end_line"]),
        target_start_line=cast(int, item["target_start_line"]),
        target_end_line=cast(int, item["target_end_line"]),
        evidence=cast(str, item["evidence"]),
        proposed_replacement=cast(str, item["proposed_replacement"]),
    )


def _validate_issue_ranges(
    issue: ReviewIssue,
    source_chunk: MarkdownChunk,
    target_chunk: MarkdownChunk,
    target_line_offset: int,
) -> None:
    target_start = target_chunk.start_line + target_line_offset
    target_end = target_chunk.end_line + target_line_offset
    source_valid = (
        source_chunk.start_line
        <= issue.source_start_line
        <= issue.source_end_line
        <= source_chunk.end_line
    )
    target_valid = target_start <= issue.target_start_line <= issue.target_end_line <= target_end
    if not source_valid or not target_valid:
        raise ReviewError(f"Issue line range выходит за границы chunk {source_chunk.index}")


def _manifest_json(manifest: ReviewManifest, root: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "model_id": manifest.model_id,
        "source_path": manifest.source_path.relative_to(root).as_posix(),
        "translation_path": manifest.translation_path.relative_to(root).as_posix(),
        "source_sha256": manifest.source_sha256,
        "translation_sha256": manifest.translation_sha256,
        "chunks": [
            {
                **{key: value for key, value in asdict(chunk).items() if key != "issues"},
                "issues": [asdict(issue) for issue in chunk.issues],
            }
            for chunk in manifest.chunks
        ],
    }


def review_file(
    source_path: Path,
    translation_path: Path,
    glossary_path: Path,
    output_path: Path,
    model: ModelName,
    repo_root: Path,
    max_chars: int = 40_000,
    timeout_seconds: int = 3_600,
) -> ReviewManifest:
    if model != "claude-opus-4-8":
        raise ReviewError("Independent review разрешён только exact model claude-opus-4-8")
    root, source, translation, output = _validate_paths(
        repo_root,
        source_path,
        translation_path,
        output_path,
    )
    prompt_path = root / "prompts/review.txt"
    schema_path = root / "prompts/review.schema.json"
    if not prompt_path.is_file() or not schema_path.is_file():
        raise ReviewError("Review prompt или JSON Schema отсутствует")
    if not glossary_path.is_file():
        raise ReviewError(f"Glossary не существует: {glossary_path}")

    source_text = source.read_text(encoding="utf-8")
    translation_text = translation.read_text(encoding="utf-8")
    target_body, target_line_offset = _translation_body(translation_text)
    source_chunks = split_markdown(source_text, max_chars=max_chars)
    target_chunks = split_markdown(target_body, max_chars=max_chars)
    if len(source_chunks) != len(target_chunks) or not all(
        _aligned_shape(source_chunk, target_chunk)
        for source_chunk, target_chunk in zip(source_chunks, target_chunks, strict=True)
    ):
        raise ReviewError("Source и translation chunks структурно не выровнены")

    terms = load_glossary(glossary_path)
    glossary = _accepted_glossary(terms)
    template = prompt_path.read_text(encoding="utf-8")
    _, validator = _load_schema(schema_path)
    reviewed: list[ReviewedChunk] = []
    chunk_root = output.parent / ".chunks" / output.stem

    for source_chunk, target_chunk in zip(source_chunks, target_chunks, strict=True):
        prompt = _render_prompt(
            template,
            source.relative_to(root).as_posix(),
            translation.relative_to(root).as_posix(),
            source_chunk,
            target_chunk,
            target_line_offset,
            glossary,
        )
        chunk_output = chunk_root / f"{source_chunk.index}.json"
        result = run_model(model, prompt, root, chunk_output, timeout_seconds)
        payload = _parse_payload(result.response, validator)
        if payload["source_sha256"] != source_chunk.sha256:
            raise ReviewError(f"Chunk {source_chunk.index}: source_sha256 не совпадает")
        if payload["translation_sha256"] != target_chunk.sha256:
            raise ReviewError(f"Chunk {source_chunk.index}: translation_sha256 не совпадает")
        if payload["model_id"] != model:
            raise ReviewError(f"Chunk {source_chunk.index}: model_id не совпадает")
        raw_issues = cast(list[object], payload["issues"])
        issues = tuple(_issue_from_mapping(raw_issue) for raw_issue in raw_issues)
        for issue in issues:
            _validate_issue_ranges(issue, source_chunk, target_chunk, target_line_offset)
        reviewed.append(
            ReviewedChunk(
                index=source_chunk.index,
                source_start_line=source_chunk.start_line,
                source_end_line=source_chunk.end_line,
                target_start_line=target_chunk.start_line + target_line_offset,
                target_end_line=target_chunk.end_line + target_line_offset,
                source_sha256=source_chunk.sha256,
                translation_sha256=target_chunk.sha256,
                runtime_id=result.evidence.runtime_id,
                issues=issues,
            )
        )

    manifest = ReviewManifest(
        model_id=model,
        source_path=source,
        translation_path=translation,
        output_path=output,
        source_sha256=_sha256(source_text),
        translation_sha256=_sha256(translation_text),
        chunks=tuple(reviewed),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(_manifest_json(manifest, root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Проверить русский перевод exact Opus model")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--translation", required=True, type=Path)
    parser.add_argument("--glossary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--model",
        required=True,
        choices=("gpt-5.6-sol", "claude-opus-4-8"),
    )
    parser.add_argument("--max-chars", type=int, default=40_000)
    parser.add_argument("--timeout-seconds", type=int, default=3_600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        manifest = review_file(
            cast(Path, arguments.source),
            cast(Path, arguments.translation),
            cast(Path, arguments.glossary),
            cast(Path, arguments.output),
            cast(ModelName, arguments.model),
            root,
            cast(int, arguments.max_chars),
            cast(int, arguments.timeout_seconds),
        )
    except (OSError, ValueError, ReviewError) as error:
        print(f"review-error: {error}", file=sys.stderr)
        return 2
    issue_count = sum(len(chunk.issues) for chunk in manifest.chunks)
    print(f"reviewed {len(manifest.chunks)} chunks; issues={issue_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
