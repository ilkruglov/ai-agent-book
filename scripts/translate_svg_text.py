from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

if __package__:
    from scripts.check_translation import load_glossary
    from scripts.model_runner import EXACT_MODEL, ModelResult, run_model
    from scripts.translate_file import runtime_record
else:
    from check_translation import (  # pyright: ignore[reportImplicitRelativeImport]
        load_glossary,
    )
    from model_runner import (  # pyright: ignore[reportImplicitRelativeImport]
        EXACT_MODEL,
        ModelResult,
        run_model,
    )
    from translate_file import (  # pyright: ignore[reportImplicitRelativeImport]
        runtime_record,
    )

type JsonObject = dict[str, object]
type RecordKind = Literal["text", "comment"]

CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
CONTENT_RE = re.compile(
    r"(?P<text><text\b[^>]*>(?P<text_body>.*?)</text>)"
    r"|(?P<comment><!--(?P<comment_body>.*?)-->)",
    re.DOTALL,
)


@dataclass(frozen=True)
class SvgTextRecord:
    id: str
    path: str
    kind: RecordKind
    source: str


class SvgTranslationError(RuntimeError):
    """Локализация SVG нарушила fail-closed контракт."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_records(
    source_dir: Path,
    file_pattern: re.Pattern[str],
) -> tuple[SvgTextRecord, ...]:
    if not source_dir.is_dir():
        raise SvgTranslationError(f"Каталог SVG не существует: {source_dir}")

    records: list[SvgTextRecord] = []
    for path in sorted(source_dir.glob("*.svg")):
        if file_pattern.fullmatch(path.name) is None:
            continue
        index = 0
        text = path.read_text(encoding="utf-8")
        for match in CONTENT_RE.finditer(text):
            body = match.group("text_body") or match.group("comment_body") or ""
            source = html.unescape(body.strip())
            if CJK_RE.search(source) is None:
                continue
            kind: RecordKind = "text" if match.group("text") is not None else "comment"
            records.append(
                SvgTextRecord(
                    id=f"{path.name}:{index:04d}",
                    path=path.name,
                    kind=kind,
                    source=source,
                )
            )
            index += 1

    if not records:
        raise SvgTranslationError("По заданному шаблону не найдено CJK-текста")
    return tuple(records)


def validate_mapping(
    records: Sequence[SvgTextRecord],
    raw_mapping: Mapping[str, object],
) -> dict[str, str]:
    expected_keys = {record.id for record in records}
    actual_keys = set(raw_mapping)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        raise SvgTranslationError(
            f"ключи mapping не совпали: missing={missing[:5]}, extra={extra[:5]}"
        )

    mapping: dict[str, str] = {}
    for record in records:
        value = raw_mapping[record.id]
        if not isinstance(value, str) or not value.strip():
            raise SvgTranslationError(f"{record.id}: перевод должен быть непустой строкой")
        if "\n" in value or "\r" in value:
            raise SvgTranslationError(f"{record.id}: перевод должен занимать одну строку")
        if CJK_RE.search(value) is not None:
            raise SvgTranslationError(f"{record.id}: перевод содержит CJK")
        mapping[record.id] = value.strip()
    return mapping


def _replace_content(
    text: str,
    path_name: str,
    mapping: Mapping[str, str],
) -> str:
    index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal index
        body = match.group("text_body") or match.group("comment_body") or ""
        if CJK_RE.search(html.unescape(body)) is None:
            return match.group(0)

        record_id = f"{path_name}:{index:04d}"
        index += 1
        translated = html.escape(mapping[record_id], quote=False)
        leading = body[: len(body) - len(body.lstrip())]
        trailing = body[len(body.rstrip()) :]
        replacement_body = f"{leading}{translated}{trailing}"
        if match.group("text") is not None:
            original = match.group(0)
            body_start = match.start("text_body") - match.start()
            body_end = match.end("text_body") - match.start()
            return f"{original[:body_start]}{replacement_body}{original[body_end:]}"
        return f"<!--{replacement_body}-->"

    return CONTENT_RE.sub(replace, text)


def apply_mapping(
    source_dir: Path,
    output_dir: Path,
    records: Sequence[SvgTextRecord],
    raw_mapping: Mapping[str, object],
) -> tuple[Path, ...]:
    mapping = validate_mapping(records, raw_mapping)
    filenames = sorted({record.path for record in records})
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    for filename in filenames:
        source = source_dir / filename
        output = output_dir / filename
        if output.exists():
            raise SvgTranslationError(f"Output уже существует: {output}")
        translated = _replace_content(source.read_text(encoding="utf-8"), filename, mapping)
        if CJK_RE.search(translated) is not None:
            raise SvgTranslationError(f"После локализации остался CJK: {filename}")
        output.write_text(translated, encoding="utf-8", newline="")
        outputs.append(output)

    return tuple(outputs)


def _load_json_mapping(path: Path) -> dict[str, object]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SvgTranslationError(f"Mapping должен быть JSON object: {path}")
    return cast(dict[str, object], raw)


def _output_schema(records: Sequence[SvgTextRecord]) -> JsonObject:
    properties = {record.id: {"type": "string", "minLength": 1} for record in records}
    return {
        "type": "object",
        "properties": properties,
        "required": [record.id for record in records],
        "additionalProperties": False,
    }


def _glossary_text(glossary_path: Path) -> str:
    terms = load_glossary(glossary_path)
    return "\n".join(f"- {' / '.join(term.source)} → {term.preferred}" for term in terms)


def _prompt(
    records: Sequence[SvgTextRecord],
    glossary_path: Path,
    draft_mapping: Mapping[str, str] | None,
) -> str:
    payload: list[dict[str, str]] = []
    for record in records:
        item = {
            "id": record.id,
            "file": record.path,
            "kind": record.kind,
            "source": record.source,
        }
        if draft_mapping is not None:
            item["draft"] = draft_mapping[record.id]
        payload.append(item)

    if draft_mapping is None:
        task = (
            "Переведи каждый source напрямую с китайского на русский. "
            "Это первый проход перевода подписей технических SVG-схем."
        )
    else:
        task = (
            "Выполни независимую сверку source с draft и верни исправленный русский перевод. "
            "Исправляй пропуски, смысловые ошибки и терминологию; корректный draft сохраняй."
        )

    return f"""{task}

Верни только JSON object: ключом должен быть каждый id, значением — итоговая строка.
Обязательные правила:
- верни все и только переданные id;
- в значениях не должно остаться китайских иероглифов;
- сохраняй формулы, числа, переменные, API/code identifiers, имена моделей и продуктов;
- перевод должен быть точным, естественным и максимально кратким;
- формулировки должны помещаться в исходную геометрию SVG;
- не добавляй пояснений, Markdown и переносов строк внутри значений;
- для kind=comment переводи только смысл комментария, сохраняя identifiers.

Терминология проекта:
{_glossary_text(glossary_path)}

Данные:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}
"""


def _write_json_exclusive(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="") as output:
            json.dump(document, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except FileExistsError as error:
        raise SvgTranslationError(f"Output уже существует: {path}") from error


def _model_pass(
    *,
    repo_root: Path,
    source_dir: Path,
    file_pattern: re.Pattern[str],
    glossary_path: Path,
    mapping_path: Path,
    evidence_path: Path,
    timeout_seconds: int,
    draft_mapping_path: Path | None,
) -> None:
    records = extract_records(source_dir, file_pattern)
    draft_mapping: dict[str, str] | None = None
    if draft_mapping_path is not None:
        draft_mapping = validate_mapping(records, _load_json_mapping(draft_mapping_path))

    prompt = _prompt(records, glossary_path, draft_mapping)
    response_path = mapping_path.parent / f"{mapping_path.stem}.response.json"
    result: ModelResult = run_model(
        EXACT_MODEL,
        prompt,
        repo_root,
        response_path,
        timeout_seconds,
        output_schema=_output_schema(records),
    )
    try:
        raw_response: object = json.loads(result.response)
    except json.JSONDecodeError as error:
        raise SvgTranslationError("Exact model вернул некорректный JSON") from error
    if not isinstance(raw_response, dict):
        raise SvgTranslationError("Exact model должен вернуть JSON object")
    mapping = validate_mapping(records, cast(dict[str, object], raw_response))
    _write_json_exclusive(mapping_path, mapping)

    record_payload = [
        {"id": record.id, "path": record.path, "kind": record.kind, "source": record.source}
        for record in records
    ]
    evidence: JsonObject = {
        "schema_version": 1,
        "pass": "translation" if draft_mapping_path is None else "source-verification",
        "model_id": EXACT_MODEL,
        "source_directory": source_dir.relative_to(repo_root).as_posix(),
        "file_pattern": file_pattern.pattern,
        "record_count": len(records),
        "source_records_sha256": _sha256(
            json.dumps(record_payload, ensure_ascii=False, separators=(",", ":"))
        ),
        "mapping_sha256": _sha256(
            json.dumps(mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        ),
        "runtime": runtime_record(result),
    }
    if draft_mapping_path is not None and draft_mapping is not None:
        evidence["draft_mapping_sha256"] = _sha256(
            json.dumps(draft_mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    _write_json_exclusive(evidence_path, evidence)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Локализовать CJK-текст в SVG exact GPT-моделью")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("translate", "review"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--source-dir", required=True, type=Path)
        subparser.add_argument("--file-pattern", required=True)
        subparser.add_argument("--glossary", required=True, type=Path)
        subparser.add_argument("--mapping", required=True, type=Path)
        subparser.add_argument("--evidence", required=True, type=Path)
        subparser.add_argument("--timeout-seconds", type=int, default=3600)
        if name == "review":
            subparser.add_argument("--draft-mapping", required=True, type=Path)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--source-dir", required=True, type=Path)
    apply_parser.add_argument("--file-pattern", required=True)
    apply_parser.add_argument("--mapping", required=True, type=Path)
    apply_parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    source_dir = cast(Path, arguments.source_dir).resolve()
    file_pattern = re.compile(cast(str, arguments.file_pattern))

    try:
        if arguments.command == "apply":
            records = extract_records(source_dir, file_pattern)
            apply_mapping(
                source_dir,
                cast(Path, arguments.output_dir).resolve(),
                records,
                _load_json_mapping(cast(Path, arguments.mapping).resolve()),
            )
        else:
            draft_mapping = (
                cast(Path, arguments.draft_mapping).resolve()
                if arguments.command == "review"
                else None
            )
            _model_pass(
                repo_root=repo_root,
                source_dir=source_dir,
                file_pattern=file_pattern,
                glossary_path=cast(Path, arguments.glossary).resolve(),
                mapping_path=cast(Path, arguments.mapping).resolve(),
                evidence_path=cast(Path, arguments.evidence).resolve(),
                timeout_seconds=cast(int, arguments.timeout_seconds),
                draft_mapping_path=draft_mapping,
            )
    except (OSError, ValueError, json.JSONDecodeError, SvgTranslationError) as error:
        print(f"svg-translation-error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
