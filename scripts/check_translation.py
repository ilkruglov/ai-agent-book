from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

BOOK_TITLE = "AI-агенты изнутри: принципы проектирования и инженерная практика"
TRANSLATION_NOTICE = (
    "<!-- Русский перевод: community edition. Источник: "
    "https://github.com/bojieli/ai-agent-book; файл изменён относительно upstream. -->"
)
EXPECTED_FILES = (
    "introduction.md",
    "chapter1.md",
    "chapter2.md",
    "chapter3.md",
    "chapter4.md",
    "chapter5.md",
    "chapter6.md",
    "chapter7.md",
    "chapter8.md",
    "chapter9.md",
    "chapter10.md",
    "afterword.md",
)

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^\s*([`~]{3,})\s*$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
CJK_ALLOW_OPEN_RE = re.compile(r'^\s*<!-- cjk-allow: reason="([^"]*)" -->\s*$')
CJK_ALLOW_CLOSE_RE = re.compile(r"^\s*<!-- /cjk-allow -->\s*$")


@dataclass(frozen=True)
class FenceShape:
    marker: str
    length: int
    info: str


@dataclass(frozen=True)
class MarkdownShape:
    heading_levels: tuple[int, ...]
    headings: tuple[str, ...]
    fences: tuple[FenceShape, ...]
    table_count: int
    image_destinations: tuple[str, ...]


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class CjkOccurrence:
    line: int
    text: str


@dataclass(frozen=True)
class GlossaryTerm:
    id: str
    source: tuple[str, ...]
    preferred: str
    status: str
    rule: str
    forbidden: tuple[str, ...]


class MarkdownParseError(ValueError):
    """Markdown нельзя безопасно разобрать для структурного сравнения."""


def parse_markdown(text: str) -> MarkdownShape:
    heading_levels: list[int] = []
    headings: list[str] = []
    fences: list[FenceShape] = []
    image_destinations: list[str] = []
    table_count = 0
    active_marker: str | None = None
    active_length = 0
    active_line = 0

    for line_number, line in enumerate(text.splitlines(), start=1):
        if active_marker is not None:
            closing = FENCE_CLOSE_RE.match(line)
            if (
                closing is not None
                and closing.group(1)[0] == active_marker
                and len(closing.group(1)) >= active_length
            ):
                active_marker = None
                active_length = 0
                active_line = 0
            continue

        opening = FENCE_OPEN_RE.match(line)
        if opening is not None:
            marker_text = opening.group(1)
            marker = marker_text[0]
            active_marker = marker
            active_length = len(marker_text)
            active_line = line_number
            fences.append(
                FenceShape(
                    marker=marker,
                    length=active_length,
                    info=opening.group(2).strip(),
                )
            )
            continue

        heading = HEADING_RE.match(line)
        if heading is not None:
            heading_levels.append(len(heading.group(1)))
            headings.append(heading.group(2).strip())

        if TABLE_SEPARATOR_RE.match(line) is not None:
            table_count += 1

        for image in IMAGE_RE.finditer(line):
            destination = image.group(1) or image.group(2)
            image_destinations.append(destination)

    if active_marker is not None:
        raise MarkdownParseError(f"Незакрытый code fence со строки {active_line}")

    return MarkdownShape(
        heading_levels=tuple(heading_levels),
        headings=tuple(headings),
        fences=tuple(fences),
        table_count=table_count,
        image_destinations=tuple(image_destinations),
    )


def find_cjk(text: str) -> list[CjkOccurrence]:
    occurrences: list[CjkOccurrence] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if CJK_RE.search(line) is not None:
            occurrences.append(CjkOccurrence(line=line_number, text=line.strip()))
    return occurrences


def _require_string(mapping: Mapping[str, object], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}: поле {key!r} должно быть непустой строкой")
    return value


def _require_string_list(mapping: Mapping[str, object], key: str, context: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}: поле {key!r} должно быть списком строк")
    items = cast(list[object], value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{context}: поле {key!r} должно быть списком строк")
    return tuple(cast(str, item) for item in items)


def load_glossary(path: Path) -> tuple[GlossaryTerm, ...]:
    raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: корень glossary должен быть mapping")
    document = cast(dict[str, object], raw)
    if document.get("schema_version") != 1:
        raise ValueError(f"{path}: поддерживается только schema_version 1")
    raw_terms = document.get("terms")
    if not isinstance(raw_terms, list):
        raise ValueError(f"{path}: поле 'terms' должно быть списком")

    terms: list[GlossaryTerm] = []
    seen_ids: set[str] = set()
    for index, raw_term in enumerate(cast(list[object], raw_terms)):
        context = f"{path}: terms[{index}]"
        if not isinstance(raw_term, dict):
            raise ValueError(f"{context} должен быть mapping")
        term = cast(dict[str, object], raw_term)
        term_id = _require_string(term, "id", context)
        if term_id in seen_ids:
            raise ValueError(f"{context}: повторяющийся id {term_id!r}")
        seen_ids.add(term_id)
        status = _require_string(term, "status", context)
        if status not in {"accepted", "candidate"}:
            raise ValueError(f"{context}: неизвестный status {status!r}")
        terms.append(
            GlossaryTerm(
                id=term_id,
                source=_require_string_list(term, "source", context),
                preferred=_require_string(term, "preferred", context),
                status=status,
                rule=_require_string(term, "rule", context),
                forbidden=_require_string_list(term, "forbidden", context),
            )
        )
    return tuple(terms)


def _cjk_issues(path: Path, text: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    allow_active = False
    allow_start = 0

    for line_number, line in enumerate(text.splitlines(), start=1):
        opening = CJK_ALLOW_OPEN_RE.match(line)
        if opening is not None:
            if allow_active:
                issues.append(
                    ValidationIssue(
                        path=str(path),
                        line=line_number,
                        code="cjk-allow-structure",
                        message="Вложенный cjk-allow block запрещён",
                    )
                )
            allow_active = True
            allow_start = line_number
            if not opening.group(1).strip():
                issues.append(
                    ValidationIssue(
                        path=str(path),
                        line=line_number,
                        code="cjk-allow-reason",
                        message="cjk-allow требует непустой reason",
                    )
                )
            continue

        if CJK_ALLOW_CLOSE_RE.match(line) is not None:
            if not allow_active:
                issues.append(
                    ValidationIssue(
                        path=str(path),
                        line=line_number,
                        code="cjk-allow-structure",
                        message="Закрывающий cjk-allow marker не имеет открытия",
                    )
                )
            allow_active = False
            allow_start = 0
            continue

        if CJK_RE.search(line) is not None and not allow_active:
            issues.append(
                ValidationIssue(
                    path=str(path),
                    line=line_number,
                    code="cjk-unexpected",
                    message="Обнаружен CJK-текст вне документированного allowlist",
                )
            )

    if allow_active:
        issues.append(
            ValidationIssue(
                path=str(path),
                line=allow_start,
                code="cjk-allow-structure",
                message="cjk-allow block не закрыт",
            )
        )
    return issues


def _prose_lines(text: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    active_marker: str | None = None
    active_length = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        if active_marker is not None:
            closing = FENCE_CLOSE_RE.match(line)
            if (
                closing is not None
                and closing.group(1)[0] == active_marker
                and len(closing.group(1)) >= active_length
            ):
                active_marker = None
                active_length = 0
            continue
        opening = FENCE_OPEN_RE.match(line)
        if opening is not None:
            active_marker = opening.group(1)[0]
            active_length = len(opening.group(1))
            continue
        if line.lstrip().startswith("<!--"):
            continue
        result.append((line_number, line))
    return result


def _glossary_issues(
    path: Path,
    text: str,
    terms: tuple[GlossaryTerm, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    accepted = tuple(term for term in terms if term.status == "accepted")
    for line_number, line in _prose_lines(text):
        folded_line = line.casefold()
        for term in accepted:
            for forbidden in term.forbidden:
                if forbidden and forbidden.casefold() in folded_line:
                    issues.append(
                        ValidationIssue(
                            path=str(path),
                            line=line_number,
                            code="glossary-forbidden",
                            message=(
                                f"Запрещённый вариант {forbidden!r} для термина {term.id!r}; "
                                f"использовать {term.preferred!r}"
                            ),
                        )
                    )
    return issues


def validate_translation(
    source_path: Path,
    target_path: Path,
    terms: tuple[GlossaryTerm, ...],
) -> list[ValidationIssue]:
    source_text = source_path.read_text(encoding="utf-8")
    target_text = target_path.read_text(encoding="utf-8")
    issues: list[ValidationIssue] = []

    try:
        source_shape = parse_markdown(source_text)
    except MarkdownParseError as error:
        return [
            ValidationIssue(
                path=str(source_path),
                line=0,
                code="source-parse",
                message=str(error),
            )
        ]

    try:
        target_shape = parse_markdown(target_text)
    except MarkdownParseError as error:
        issues.append(
            ValidationIssue(
                path=str(target_path),
                line=0,
                code="fence-structure",
                message=str(error),
            )
        )
        target_shape = None

    if target_shape is not None:
        if source_shape.heading_levels != target_shape.heading_levels:
            issues.append(
                ValidationIssue(
                    path=str(target_path),
                    line=0,
                    code="heading-structure",
                    message="Последовательность уровней заголовков отличается от source",
                )
            )
        if source_shape.fences != target_shape.fences:
            issues.append(
                ValidationIssue(
                    path=str(target_path),
                    line=0,
                    code="fence-structure",
                    message="Code fences отличаются от source",
                )
            )
        if source_shape.image_destinations != target_shape.image_destinations:
            issues.append(
                ValidationIssue(
                    path=str(target_path),
                    line=0,
                    code="image-structure",
                    message="Последовательность image destinations отличается от source",
                )
            )
        if source_shape.table_count != target_shape.table_count:
            issues.append(
                ValidationIssue(
                    path=str(target_path),
                    line=0,
                    code="table-structure",
                    message="Количество Markdown-таблиц отличается от source",
                )
            )

    if TRANSLATION_NOTICE not in target_text:
        issues.append(
            ValidationIssue(
                path=str(target_path),
                line=1,
                code="translation-notice",
                message="Отсутствует обязательное уведомление о русском переводе",
            )
        )

    issues.extend(_cjk_issues(target_path, target_text))
    issues.extend(_glossary_issues(target_path, target_text, terms))
    return issues


def validate_pdf_text(
    pdf_text: str,
    expected_h1: tuple[str, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if BOOK_TITLE not in pdf_text:
        issues.append(
            ValidationIssue(
                path="<pdf-text>",
                line=0,
                code="pdf-title",
                message=f"PDF не содержит название {BOOK_TITLE!r}",
            )
        )
    for heading in expected_h1:
        if heading not in pdf_text:
            issues.append(
                ValidationIssue(
                    path="<pdf-text>",
                    line=0,
                    code="pdf-heading",
                    message=f"PDF не содержит заголовок {heading!r}",
                )
            )
    if "\ufffd" in pdf_text:
        issues.append(
            ValidationIssue(
                path="<pdf-text>",
                line=0,
                code="pdf-replacement-character",
                message="PDF text содержит Unicode replacement character U+FFFD",
            )
        )
    return issues


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Проверить русский перевод книги")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--glossary", required=True, type=Path)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--pdf-text", type=Path)
    return parser


def _configuration_error(message: str) -> int:
    print(f"configuration-error: {message}", file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    source_dir = cast(Path, arguments.source)
    target_dir = cast(Path, arguments.target)
    glossary_path = cast(Path, arguments.glossary)
    only = tuple(cast(list[str], arguments.only))
    pdf_text_path = cast(Path | None, arguments.pdf_text)

    if not source_dir.is_dir():
        return _configuration_error(f"source directory не существует: {source_dir}")
    if not target_dir.is_dir():
        return _configuration_error(f"target directory не существует: {target_dir}")
    if not glossary_path.is_file():
        return _configuration_error(f"glossary не существует: {glossary_path}")

    try:
        terms = load_glossary(glossary_path)
    except (OSError, ValueError, yaml.YAMLError) as error:
        return _configuration_error(str(error))

    filenames = only or EXPECTED_FILES
    issues: list[ValidationIssue] = []
    expected_h1: list[str] = []
    for filename in filenames:
        source_path = source_dir / filename
        target_path = target_dir / filename
        if not source_path.is_file():
            return _configuration_error(f"source file не существует: {source_path}")
        if not target_path.is_file():
            return _configuration_error(f"target file не существует: {target_path}")
        issues.extend(validate_translation(source_path, target_path, terms))
        try:
            target_shape = parse_markdown(target_path.read_text(encoding="utf-8"))
        except MarkdownParseError:
            continue
        if target_shape.heading_levels and target_shape.heading_levels[0] == 1:
            expected_h1.append(target_shape.headings[0])

    if pdf_text_path is not None:
        if not pdf_text_path.is_file():
            return _configuration_error(f"pdf-text file не существует: {pdf_text_path}")
        issues.extend(
            validate_pdf_text(
                pdf_text_path.read_text(encoding="utf-8"),
                tuple(expected_h1),
            )
        )

    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.code}: {issue.message}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
