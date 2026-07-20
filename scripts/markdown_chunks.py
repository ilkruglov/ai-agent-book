from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from itertools import pairwise

FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^\s*([`~]{3,})\s*$")


@dataclass(frozen=True)
class MarkdownChunk:
    index: str
    start_line: int
    end_line: int
    text: str
    sha256: str


class ChunkingError(ValueError):
    """Markdown нельзя разбить без повреждения неделимого блока."""


def _heading_offsets(text: str, level: int) -> tuple[int, ...]:
    heading_re = re.compile(rf"^#{{{level}}}(?!#)[ \t]+")
    offsets: list[int] = []
    offset = 0
    active_marker: str | None = None
    active_length = 0
    in_comment = False

    for line in text.splitlines(keepends=True):
        if active_marker is not None:
            closing = FENCE_CLOSE_RE.match(line)
            if (
                closing is not None
                and closing.group(1)[0] == active_marker
                and len(closing.group(1)) >= active_length
            ):
                active_marker = None
                active_length = 0
            offset += len(line)
            continue

        if in_comment:
            if "-->" in line:
                in_comment = False
            offset += len(line)
            continue

        opening = FENCE_OPEN_RE.match(line)
        if opening is not None:
            active_marker = opening.group(1)[0]
            active_length = len(opening.group(1))
            offset += len(line)
            continue

        comment_start = line.find("<!--")
        if comment_start >= 0 and line.find("-->", comment_start + 4) < 0:
            in_comment = True
            offset += len(line)
            continue

        if heading_re.match(line) is not None:
            offsets.append(offset)
        offset += len(line)

    return tuple(offsets)


def _split_at_heading(text: str, level: int) -> tuple[str, ...]:
    offsets = tuple(offset for offset in _heading_offsets(text, level) if offset > 0)
    if not offsets:
        return (text,)
    boundaries = (0, *offsets, len(text))
    return tuple(text[start:end] for start, end in pairwise(boundaries) if start < end)


def _markdown_blocks(text: str) -> tuple[str, ...]:
    blocks: list[str] = []
    current: list[str] = []
    active_marker: str | None = None
    active_length = 0
    in_comment = False

    for line in text.splitlines(keepends=True):
        current.append(line)
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

        if in_comment:
            if "-->" in line:
                in_comment = False
            continue

        opening = FENCE_OPEN_RE.match(line)
        if opening is not None:
            active_marker = opening.group(1)[0]
            active_length = len(opening.group(1))
            continue

        comment_start = line.find("<!--")
        if comment_start >= 0 and line.find("-->", comment_start + 4) < 0:
            in_comment = True
            continue

        if not line.strip():
            blocks.append("".join(current))
            current = []

    if current:
        blocks.append("".join(current))
    return tuple(blocks)


def _pack_blocks(text: str, max_chars: int) -> tuple[str, ...]:
    blocks = _markdown_blocks(text)
    chunks: list[str] = []
    current = ""
    for block in blocks:
        if len(block) > max_chars:
            raise ChunkingError(
                f"неделимый Markdown-блок длиной {len(block)} превышает max_chars={max_chars}"
            )
        if current and len(current) + len(block) > max_chars:
            chunks.append(current)
            current = block
        else:
            current += block
    if current:
        chunks.append(current)
    return tuple(chunks)


def _split_oversized_h2_part(text: str, max_chars: int) -> tuple[str, ...]:
    h3_parts = _split_at_heading(text, level=3)
    if len(h3_parts) == 1:
        return _pack_blocks(text, max_chars)
    chunks: list[str] = []
    for part in h3_parts:
        if len(part) <= max_chars:
            chunks.append(part)
        else:
            chunks.extend(_pack_blocks(part, max_chars))
    return tuple(chunks)


def _line_range(text_before: str, chunk_text: str) -> tuple[int, int]:
    start_line = text_before.count("\n") + 1
    newline_count = chunk_text.count("\n")
    end_line = start_line + newline_count
    if chunk_text.endswith("\n"):
        end_line -= 1
    return start_line, max(start_line, end_line)


def split_markdown(text: str, max_chars: int) -> tuple[MarkdownChunk, ...]:
    if max_chars <= 0:
        raise ValueError("max_chars должен быть положительным")
    if not text:
        return ()

    raw_chunks: list[str] = []
    for h2_part in _split_at_heading(text, level=2):
        if len(h2_part) <= max_chars:
            raw_chunks.append(h2_part)
        else:
            raw_chunks.extend(_split_oversized_h2_part(h2_part, max_chars))

    chunks: list[MarkdownChunk] = []
    consumed = ""
    for ordinal, chunk_text in enumerate(raw_chunks):
        start_line, end_line = _line_range(consumed, chunk_text)
        chunks.append(
            MarkdownChunk(
                index=f"{ordinal:03d}",
                start_line=start_line,
                end_line=end_line,
                text=chunk_text,
                sha256=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            )
        )
        consumed += chunk_text

    if consumed != text:
        raise AssertionError("Внутренняя ошибка: chunking не сохранил исходный текст")
    return tuple(chunks)
