from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlsplit

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^\s*([`~]{3,})\s*$")
LINK_RE = re.compile(
    r"(?P<image>!)?\[[^\]]*\]\(\s*"
    r"(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
INLINE_LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^)]*\)")
HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class LinkIssue:
    path: Path
    line: int
    code: str
    target: str


@dataclass(frozen=True)
class MarkdownLink:
    line: int
    target: str
    is_image: bool


def _strip_heading_markup(text: str) -> str:
    without_links = INLINE_LINK_RE.sub(r"\1", text)
    without_html = HTML_TAG_RE.sub("", without_links)
    return without_html.replace("`", "").replace("*", "")


def github_anchor(text: str, occurrence: int) -> str:
    if occurrence < 0:
        raise ValueError("occurrence должен быть неотрицательным")
    cleaned = _strip_heading_markup(text).casefold()
    characters: list[str] = []
    previous_whitespace = False
    for character in cleaned:
        if character.isspace():
            if characters and not previous_whitespace:
                characters.append("-")
            previous_whitespace = True
            continue
        previous_whitespace = False
        if character.isalnum() or character in {"-", "_"}:
            characters.append(character)
    base = "".join(characters).rstrip("-")
    return base if occurrence == 0 else f"{base}-{occurrence}"


def _outside_fence_lines(markdown: str) -> Iterator[tuple[int, str]]:
    active_marker: str | None = None
    active_length = 0
    for line_number, line in enumerate(markdown.splitlines(), start=1):
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
        yield line_number, line


def collect_anchors(markdown: str) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    for _, line in _outside_fence_lines(markdown):
        heading = HEADING_RE.match(line)
        if heading is None:
            continue
        heading_text = re.sub(r"\s+#+\s*$", "", heading.group(2))
        base = github_anchor(heading_text, 0)
        occurrence = occurrences.get(base, 0)
        anchors.add(github_anchor(heading_text, occurrence))
        occurrences[base] = occurrence + 1
    return anchors


def _collect_links(markdown: str) -> tuple[MarkdownLink, ...]:
    links: list[MarkdownLink] = []
    for line_number, line in _outside_fence_lines(markdown):
        for match in LINK_RE.finditer(line):
            target = match.group("angle") or match.group("plain")
            links.append(
                MarkdownLink(
                    line=line_number,
                    target=target,
                    is_image=match.group("image") == "!",
                )
            )
    return tuple(links)


def _load_pending_markdown(path: Path | None) -> set[str]:
    if path is None:
        return set()
    if not path.is_file():
        raise ValueError(f"partial manifest не существует: {path}")
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: manifest root должен быть mapping")
    document = cast(dict[str, object], raw)
    markdown = document.get("markdown")
    if not isinstance(markdown, list):
        raise ValueError(f"{path}: поле markdown должно быть списком")
    pending: set[str] = set()
    for index, raw_item in enumerate(cast(list[object], markdown)):
        if not isinstance(raw_item, dict):
            raise ValueError(f"{path}: markdown[{index}] должен быть mapping")
        item = cast(dict[str, object], raw_item)
        source_path = item.get("path")
        if not isinstance(source_path, str) or not source_path.startswith("book/"):
            raise ValueError(f"{path}: некорректный markdown path в позиции {index}")
        pending.add(source_path.removeprefix("book/"))
    return pending


def _is_forbidden_target(raw_target: str, decoded_path: str) -> bool:
    normalized = unquote(raw_target).replace("\\", "/").casefold()
    path_parts = Path(decoded_path).parts
    return (
        ".tmp/upstream" in normalized
        or "book-zh" in {part.casefold() for part in path_parts}
        or Path(decoded_path).is_absolute()
    )


def _issue(path: Path, link: MarkdownLink, code: str) -> LinkIssue:
    return LinkIssue(path=path, line=link.line, code=code, target=link.target)


def check_book(
    root: Path,
    only: tuple[Path, ...],
    partial_manifest: Path | None,
) -> list[LinkIssue]:
    if not root.is_dir():
        raise ValueError(f"book directory не существует: {root}")
    root_resolved = root.resolve()
    pending_markdown = _load_pending_markdown(partial_manifest)
    issues: list[LinkIssue] = []
    anchor_cache: dict[Path, set[str]] = {}

    if only:
        markdown_files: list[Path] = []
        for relative in only:
            if relative.is_absolute() or ".." in relative.parts:
                issues.append(
                    LinkIssue(
                        path=root,
                        line=0,
                        code="forbidden-target",
                        target=str(relative),
                    )
                )
                continue
            selected = root / relative
            if not selected.is_file():
                issues.append(
                    LinkIssue(
                        path=selected,
                        line=0,
                        code="missing-file",
                        target=str(relative),
                    )
                )
                continue
            markdown_files.append(selected)
    else:
        markdown_files = sorted(root.rglob("*.md"))

    for markdown_path in markdown_files:
        markdown = markdown_path.read_text(encoding="utf-8")
        for link in _collect_links(markdown):
            parsed = urlsplit(link.target)
            scheme = parsed.scheme.casefold()
            if scheme in {"http", "https", "mailto"} or parsed.netloc:
                continue
            if scheme:
                issues.append(_issue(markdown_path, link, "forbidden-target"))
                continue

            decoded_path = unquote(parsed.path)
            fragment = unquote(parsed.fragment)
            if _is_forbidden_target(link.target, decoded_path):
                issues.append(_issue(markdown_path, link, "forbidden-target"))
                continue

            if decoded_path:
                target_path = (markdown_path.parent / decoded_path).resolve()
            else:
                target_path = markdown_path.resolve()
            if not target_path.is_relative_to(root_resolved):
                issues.append(_issue(markdown_path, link, "forbidden-target"))
                continue

            if not target_path.is_file():
                try:
                    relative_target = target_path.relative_to(root_resolved).as_posix()
                except ValueError:
                    relative_target = ""
                if (
                    not link.is_image
                    and target_path.suffix.casefold() == ".md"
                    and relative_target in pending_markdown
                ):
                    continue
                code = "missing-image" if link.is_image else "missing-target"
                issues.append(_issue(markdown_path, link, code))
                continue

            if link.is_image or not fragment:
                continue
            if target_path.suffix.casefold() != ".md":
                continue
            anchors = anchor_cache.get(target_path)
            if anchors is None:
                anchors = collect_anchors(target_path.read_text(encoding="utf-8"))
                anchor_cache[target_path] = anchors
            if fragment not in anchors:
                issues.append(_issue(markdown_path, link, "missing-anchor"))

    return issues


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Проверить локальные ссылки книги")
    parser.add_argument("book_dir", type=Path)
    parser.add_argument("--only", action="append", type=Path, default=[])
    parser.add_argument("--partial-manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    root = cast(Path, arguments.book_dir)
    only = tuple(cast(list[Path], arguments.only))
    partial_manifest = cast(Path | None, arguments.partial_manifest)
    try:
        issues = check_book(root, only, partial_manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"configuration-error: {error}", file=sys.stderr)
        return 2
    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.code}: {issue.target}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
