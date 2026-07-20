from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, SchemaError, ValidationError

if __package__:
    from scripts.check_translation import (
        TRANSLATION_NOTICE,
        GlossaryTerm,
        load_glossary,
        validate_translation,
    )
    from scripts.markdown_chunks import MarkdownChunk, split_markdown
    from scripts.model_runner import EXACT_MODEL, run_model
    from scripts.translate_file import runtime_record
else:
    from check_translation import (  # pyright: ignore[reportImplicitRelativeImport]
        TRANSLATION_NOTICE,
        GlossaryTerm,
        load_glossary,
        validate_translation,
    )
    from markdown_chunks import (  # pyright: ignore[reportImplicitRelativeImport]
        MarkdownChunk,
        split_markdown,
    )
    from model_runner import (  # pyright: ignore[reportImplicitRelativeImport]
        EXACT_MODEL,
        run_model,
    )
    from translate_file import (  # pyright: ignore[reportImplicitRelativeImport]
        runtime_record,
    )

type JsonObject = dict[str, object]

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
OUTER_FENCE_RE = re.compile(r"(```|~~~)(?:markdown|md)?", re.IGNORECASE)
RUNTIME_KEYS = {
    "requested_model",
    "reported_model",
    "provider",
    "thread_id",
    "turn_id",
    "ephemeral",
    "fallback_allowed",
    "sandbox_type",
    "completion_observed",
    "usage_observed",
    "command_sha256",
    "prompt_sha256",
    "response_sha256",
    "stdout_sha256",
    "stderr_sha256",
}


@dataclass(frozen=True)
class TranslationChunkEvidence:
    source: MarkdownChunk
    draft_text: str
    draft_sha256: str
    runtime: JsonObject


@dataclass(frozen=True)
class VerifiedChunk:
    index: str
    start_line: int
    end_line: int
    source_start: int
    source_end: int
    final_start: int
    final_end: int
    source_sha256: str
    draft_sha256: str
    final_sha256: str
    translation_runtime: JsonObject
    verification_runtime: JsonObject


@dataclass(frozen=True)
class VerificationManifest:
    source_path: Path
    draft_path: Path
    output_path: Path
    evidence_path: Path
    manifest_fragment_path: Path
    source_sha256: str
    draft_sha256: str
    final_sha256: str
    chunks: tuple[VerifiedChunk, ...]


class VerificationError(RuntimeError):
    """GPT-сверка или её provenance нарушили fail-closed контракт."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity


def _mapping(value: object, context: str) -> JsonObject:
    if not isinstance(value, dict):
        raise VerificationError(f"{context} должен быть JSON object")
    return cast(JsonObject, value)


def _string(document: Mapping[str, object], key: str, context: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{context}: поле {key} должно быть непустой строкой")
    return value


def _hash(document: Mapping[str, object], key: str, context: str) -> str:
    value = _string(document, key, context)
    if HASH_RE.fullmatch(value) is None:
        raise VerificationError(f"{context}: поле {key} не является SHA-256")
    return value


def _load_json(path: Path, context: str) -> JsonObject:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise VerificationError(f"{context}: некорректный JSON") from error
    return _mapping(raw, context)


def _inside(path: Path, root: Path, context: str) -> Path:
    resolved = path.resolve()
    expected_root = root.resolve()
    if resolved == expected_root or not resolved.is_relative_to(expected_root):
        raise VerificationError(f"{context} должен находиться внутри {expected_root}")
    return resolved


def _validate_paths(
    repo_root: Path,
    source_path: Path,
    draft_path: Path,
    translation_evidence_path: Path,
    output_path: Path,
    evidence_path: Path,
    manifest_fragment_path: Path,
) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    root = repo_root.resolve()
    source = _inside(source_path, root / ".tmp/upstream/book", "Source")
    draft = _inside(draft_path, root / ".tmp/drafts", "Draft")
    translation_evidence = _inside(
        translation_evidence_path,
        root / ".tmp/evidence",
        "Translation evidence",
    )
    output = _inside(output_path, root / ".tmp/verified", "Output")
    evidence = _inside(evidence_path, root / ".tmp/evidence", "Verification evidence")
    fragment = _inside(
        manifest_fragment_path,
        root / ".tmp/evidence",
        "Manifest fragment",
    )
    for required in (source, draft, translation_evidence):
        if not required.is_file():
            raise VerificationError(f"Обязательный input отсутствует: {required}")
    for new_artifact in (output, evidence, fragment):
        if new_artifact.exists():
            raise VerificationError(f"Partial artifact уже существует: {new_artifact}")
    return root, source, draft, translation_evidence, output, evidence, fragment


def _validate_runtime(record: object, context: str, response_sha256: str) -> JsonObject:
    runtime = _mapping(record, context)
    if set(runtime) != RUNTIME_KEYS:
        raise VerificationError(f"{context}: runtime fields не совпали с contract")
    if (
        runtime.get("requested_model") != EXACT_MODEL
        or runtime.get("reported_model") != EXACT_MODEL
    ):
        raise VerificationError(f"{context}: exact model identity не подтверждена")
    if runtime.get("provider") != "openai":
        raise VerificationError(f"{context}: provider должен быть openai")
    if runtime.get("ephemeral") is not True or runtime.get("fallback_allowed") is not False:
        raise VerificationError(f"{context}: ephemeral/fallback evidence противоречива")
    if runtime.get("sandbox_type") != "readOnly":
        raise VerificationError(f"{context}: sandbox должен быть readOnly")
    if runtime.get("completion_observed") is not True or runtime.get("usage_observed") is not True:
        raise VerificationError(f"{context}: completion/usage evidence отсутствует")
    _string(runtime, "thread_id", context)
    _string(runtime, "turn_id", context)
    for key in (
        "command_sha256",
        "prompt_sha256",
        "response_sha256",
        "stdout_sha256",
        "stderr_sha256",
    ):
        _hash(runtime, key, context)
    if runtime.get("response_sha256") != response_sha256:
        raise VerificationError(f"{context}: response_sha256 не совпал с artifact")
    return runtime


def _load_translation_chunks(
    root: Path,
    source: Path,
    draft: Path,
    evidence_path: Path,
) -> tuple[TranslationChunkEvidence, ...]:
    document = _load_json(evidence_path, "translation evidence")
    expected_keys = {
        "schema_version",
        "pass",
        "model_id",
        "source_path",
        "draft_path",
        "source_sha256",
        "draft_sha256",
        "max_chars",
        "chunks",
    }
    if set(document) != expected_keys:
        raise VerificationError("translation evidence fields не совпали с contract")
    if (
        document.get("schema_version") != 1
        or document.get("pass") != "translation"
        or document.get("model_id") != EXACT_MODEL
    ):
        raise VerificationError("translation evidence header противоречив")
    if document.get("source_path") != source.relative_to(root).as_posix():
        raise VerificationError("translation evidence source_path не совпал")
    if document.get("draft_path") != draft.relative_to(root).as_posix():
        raise VerificationError("translation evidence draft_path не совпал")

    source_text = source.read_text(encoding="utf-8")
    draft_text = draft.read_text(encoding="utf-8")
    if document.get("source_sha256") != _sha256(source_text):
        raise VerificationError("translation evidence source hash не совпал")
    if document.get("draft_sha256") != _sha256(draft_text):
        raise VerificationError("translation evidence draft hash не совпал")
    max_chars = document.get("max_chars")
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars <= 0:
        raise VerificationError("translation evidence max_chars некорректен")

    source_chunks = split_markdown(source_text, max_chars=max_chars)
    raw_chunks = document.get("chunks")
    if not isinstance(raw_chunks, list):
        raise VerificationError("translation evidence chunk count не совпал")
    raw_chunk_items = cast(list[object], raw_chunks)
    if len(raw_chunk_items) != len(source_chunks):
        raise VerificationError("translation evidence chunk count не совпал")

    result: list[TranslationChunkEvidence] = []
    draft_parts: list[str] = []
    response_root = (root / ".tmp/drafts/.chunks").resolve()
    for ordinal, (source_chunk, raw_chunk) in enumerate(
        zip(source_chunks, raw_chunk_items, strict=True)
    ):
        context = f"translation evidence chunks[{ordinal}]"
        chunk = _mapping(raw_chunk, context)
        if set(chunk) != {
            "index",
            "start_line",
            "end_line",
            "source_sha256",
            "draft_sha256",
            "response_path",
            "runtime",
        }:
            raise VerificationError(f"{context}: fields не совпали с contract")
        expected_identity = (
            source_chunk.index,
            source_chunk.start_line,
            source_chunk.end_line,
            source_chunk.sha256,
        )
        actual_identity = (
            chunk.get("index"),
            chunk.get("start_line"),
            chunk.get("end_line"),
            chunk.get("source_sha256"),
        )
        if actual_identity != expected_identity:
            raise VerificationError(f"{context}: source identity не совпала")
        response_relative = _string(chunk, "response_path", context)
        response_path = (root / response_relative).resolve()
        if not response_path.is_relative_to(response_root) or not response_path.is_file():
            raise VerificationError(f"{context}: response_path вне .tmp/drafts/.chunks")
        draft_chunk = response_path.read_text(encoding="utf-8")
        draft_sha256 = _sha256(draft_chunk)
        if chunk.get("draft_sha256") != draft_sha256:
            raise VerificationError(f"{context}: draft_sha256 не совпал")
        runtime = _validate_runtime(chunk.get("runtime"), f"{context} runtime", draft_sha256)
        result.append(
            TranslationChunkEvidence(
                source=source_chunk,
                draft_text=draft_chunk,
                draft_sha256=draft_sha256,
                runtime=runtime,
            )
        )
        draft_parts.append(draft_chunk)

    assembled_draft = f"{TRANSLATION_NOTICE}\n\n{''.join(draft_parts)}"
    if assembled_draft != draft_text:
        raise VerificationError("translation evidence draft chunks не собирают exact draft")
    return tuple(result)


def _render_glossary(terms: tuple[GlossaryTerm, ...]) -> str:
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
    chunk: TranslationChunkEvidence,
    glossary: str,
) -> str:
    replacements = {
        "{{SOURCE_PATH}}": source_relative,
        "{{START_LINE}}": str(chunk.source.start_line),
        "{{END_LINE}}": str(chunk.source.end_line),
        "{{SOURCE_SHA256}}": chunk.source.sha256,
        "{{DRAFT_SHA256}}": chunk.draft_sha256,
        "{{GLOSSARY}}": glossary,
        "{{SOURCE}}": chunk.source.text,
        "{{DRAFT}}": chunk.draft_text,
    }
    missing = tuple(marker for marker in replacements if marker not in template)
    if missing:
        raise VerificationError(f"Verification prompt не содержит markers: {', '.join(missing)}")
    rendered = template
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    return rendered


def _load_schema(path: Path) -> JsonObject:
    schema = _load_json(path, "verification schema")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise VerificationError(f"Verification JSON Schema некорректна: {error.message}") from error
    return schema


def _parse_response(
    response: str,
    schema: JsonObject,
    chunk: TranslationChunkEvidence,
) -> str:
    try:
        raw: object = json.loads(response)
    except json.JSONDecodeError as error:
        raise VerificationError("GPT-сверка вернула некорректный JSON") from error
    try:
        Draft202012Validator(schema).validate(raw)  # pyright: ignore[reportUnknownMemberType]
    except ValidationError as error:
        raise VerificationError(
            f"GPT-сверка нарушила JSON Schema at {error.json_path}: {error.message}"
        ) from error
    document = _mapping(raw, "GPT-сверка result")
    if document.get("source_sha256") != chunk.source.sha256:
        raise VerificationError("GPT-сверка source_sha256 не совпал")
    if document.get("draft_sha256") != chunk.draft_sha256:
        raise VerificationError("GPT-сверка draft_sha256 не совпал")
    if document.get("model_id") != EXACT_MODEL:
        raise VerificationError("GPT-сверка model_id не совпал")
    corrected = _string(document, "corrected_translation", "GPT-сверка result")
    issues = document.get("issues")
    if corrected != chunk.draft_text and isinstance(issues, list) and not issues:
        raise VerificationError("GPT-сверка изменила draft без связанной issue")
    lines = tuple(line for line in corrected.strip().splitlines() if line.strip())
    if (
        len(lines) >= 2
        and OUTER_FENCE_RE.fullmatch(lines[0].strip()) is not None
        and lines[-1].strip() == lines[0].strip()[:3]
    ):
        raise VerificationError("GPT-сверка добавила лишний внешний Markdown fence")
    draft_boundaries = (
        len(chunk.draft_text) - len(chunk.draft_text.lstrip("\n")),
        len(chunk.draft_text) - len(chunk.draft_text.rstrip("\n")),
    )
    corrected_boundaries = (
        len(corrected) - len(corrected.lstrip("\n")),
        len(corrected) - len(corrected.rstrip("\n")),
    )
    if draft_boundaries != corrected_boundaries:
        raise VerificationError("GPT-сверка изменила newline boundary chunk")
    return corrected


def _source_identity(root: Path, source: Path) -> tuple[str, str]:
    source_relative = source.relative_to(root / ".tmp/upstream").as_posix()
    data = source.read_bytes()
    blob_sha1 = _git_blob_sha1(data)
    upstream = _load_json(root / "upstream.json", "upstream manifest")
    raw_markdown = upstream.get("markdown")
    if not isinstance(raw_markdown, list):
        raise VerificationError("upstream manifest markdown должен быть list")
    expected_blob = ""
    for raw_entry in cast(list[object], raw_markdown):
        entry = _mapping(raw_entry, "upstream markdown entry")
        if entry.get("path") == source_relative:
            expected_blob = _string(entry, "blob_sha1", "upstream markdown entry")
            break
    if not expected_blob or expected_blob != blob_sha1:
        raise VerificationError("Pinned source blob не совпал с upstream manifest")
    return source_relative, blob_sha1


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="") as output_file:
            json.dump(dict(document), output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")
    except FileExistsError as error:
        raise VerificationError(f"Partial artifact уже существует: {path}") from error


def verify_file(
    source_path: Path,
    draft_path: Path,
    translation_evidence_path: Path,
    output_path: Path,
    evidence_path: Path,
    manifest_fragment_path: Path,
    glossary_path: Path,
    repo_root: Path,
    timeout_seconds: int = 3_600,
) -> VerificationManifest:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds должен быть положительным")
    (
        root,
        source,
        draft,
        translation_evidence,
        output,
        evidence,
        fragment,
    ) = _validate_paths(
        repo_root,
        source_path,
        draft_path,
        translation_evidence_path,
        output_path,
        evidence_path,
        manifest_fragment_path,
    )
    if not glossary_path.is_file():
        raise VerificationError(f"Glossary не существует: {glossary_path}")
    prompt_path = root / "prompts/verify_translation.txt"
    schema_path = root / "prompts/verify_translation.schema.json"
    if not prompt_path.is_file() or not schema_path.is_file():
        raise VerificationError("Verification prompt/schema отсутствуют")

    chunks = _load_translation_chunks(root, source, draft, translation_evidence)
    terms = load_glossary(glossary_path)
    glossary = _render_glossary(terms)
    template = prompt_path.read_text(encoding="utf-8")
    schema = _load_schema(schema_path)
    corrected_parts: list[str] = []
    verified_chunks: list[VerifiedChunk] = []
    source_offset = 0
    final_offset = 0

    response_root = output.parent / ".responses" / output.stem
    for ordinal, chunk in enumerate(chunks):
        prompt = _render_prompt(
            template,
            source.relative_to(root).as_posix(),
            chunk,
            glossary,
        )
        response_path = response_root / f"{chunk.source.index}.json"
        result = run_model(EXACT_MODEL, prompt, root, response_path, timeout_seconds)
        corrected = _parse_response(result.response, schema, chunk)
        corrected_sha256 = _sha256(corrected)
        verification_runtime = runtime_record(result)
        source_end = source_offset + len(chunk.source.text)
        final_end = final_offset + len(corrected)
        verified_chunks.append(
            VerifiedChunk(
                index=chunk.source.index,
                start_line=chunk.source.start_line,
                end_line=chunk.source.end_line,
                source_start=source_offset,
                source_end=source_end,
                final_start=final_offset,
                final_end=final_end,
                source_sha256=chunk.source.sha256,
                draft_sha256=chunk.draft_sha256,
                final_sha256=corrected_sha256,
                translation_runtime=chunk.runtime,
                verification_runtime=verification_runtime,
            )
        )
        corrected_parts.append(corrected)
        source_offset = source_end
        final_offset = final_end
        if ordinal + 1 != len(chunks) and not corrected:
            raise AssertionError("Пустой corrected chunk прошёл schema")

    final_text = f"{TRANSLATION_NOTICE}\n\n{''.join(corrected_parts)}"
    candidate = output.parent / ".candidates" / output.name
    if candidate.exists():
        raise VerificationError(f"Partial candidate уже существует: {candidate}")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    with candidate.open("x", encoding="utf-8", newline="") as candidate_file:
        candidate_file.write(final_text)
    issues = validate_translation(source, candidate, terms)
    if issues:
        codes = ", ".join(sorted({issue.code for issue in issues}))
        raise VerificationError(f"Corrected translation не прошёл validation: {codes}")
    try:
        with output.open("x", encoding="utf-8", newline="") as output_file:
            output_file.write(final_text)
    except FileExistsError as error:
        raise VerificationError(f"Partial artifact уже существует: {output}") from error
    candidate.unlink()

    source_text = source.read_text(encoding="utf-8")
    draft_text = draft.read_text(encoding="utf-8")
    source_sha256 = _sha256(source_text)
    draft_sha256 = _sha256(draft_text)
    final_sha256 = _sha256(final_text)
    source_relative, blob_sha1 = _source_identity(root, source)

    evidence_document: dict[str, object] = {
        "schema_version": 1,
        "pass": "source_verification",
        "model_id": EXACT_MODEL,
        "source_path": source.relative_to(root).as_posix(),
        "draft_path": draft.relative_to(root).as_posix(),
        "output_path": output.relative_to(root).as_posix(),
        "source_sha256": source_sha256,
        "draft_sha256": draft_sha256,
        "final_sha256": final_sha256,
        "chunks": [
            {
                "index": chunk.index,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "source_start": chunk.source_start,
                "source_end": chunk.source_end,
                "final_start": chunk.final_start,
                "final_end": chunk.final_end,
                "source_sha256": chunk.source_sha256,
                "draft_sha256": chunk.draft_sha256,
                "final_sha256": chunk.final_sha256,
                "runtime": chunk.verification_runtime,
            }
            for chunk in verified_chunks
        ],
    }
    fragment_document: dict[str, object] = {
        "path": output.name,
        "source": {
            "path": source_relative,
            "blob_sha1": blob_sha1,
            "sha256": source_sha256,
        },
        "final_sha256": final_sha256,
        "chunks": [
            {
                "index": chunk.index,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "source_start": chunk.source_start,
                "source_end": chunk.source_end,
                "final_start": chunk.final_start,
                "final_end": chunk.final_end,
                "source_sha256": chunk.source_sha256,
                "draft_sha256": chunk.draft_sha256,
                "final_sha256": chunk.final_sha256,
                "passes": {
                    "translation": chunk.translation_runtime,
                    "source_verification": chunk.verification_runtime,
                },
            }
            for chunk in verified_chunks
        ],
    }
    _write_json(evidence, evidence_document)
    _write_json(fragment, fragment_document)
    return VerificationManifest(
        source_path=source,
        draft_path=draft,
        output_path=output,
        evidence_path=evidence,
        manifest_fragment_path=fragment,
        source_sha256=source_sha256,
        draft_sha256=draft_sha256,
        final_sha256=final_sha256,
        chunks=tuple(verified_chunks),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Сверить русский draft с pinned source")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--translation-evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--manifest-fragment", required=True, type=Path)
    parser.add_argument("--glossary", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=3_600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    try:
        manifest = verify_file(
            cast(Path, arguments.source),
            cast(Path, arguments.draft),
            cast(Path, arguments.translation_evidence),
            cast(Path, arguments.output),
            cast(Path, arguments.evidence),
            cast(Path, arguments.manifest_fragment),
            cast(Path, arguments.glossary),
            repo_root,
            cast(int, arguments.timeout_seconds),
        )
    except (OSError, ValueError, VerificationError) as error:
        print(f"verification-error: {error}", file=sys.stderr)
        return 2
    print(
        f"verified {manifest.source_path} -> {manifest.output_path} "
        f"with {len(manifest.chunks)} chunks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
