from __future__ import annotations

import hashlib

import pytest

from scripts.markdown_chunks import ChunkingError, split_markdown


def test_chunks_rejoin_byte_for_byte_and_prefer_h2_boundaries() -> None:
    text = "Вступление\n\n## Раздел A\nТекст A\n\n## Раздел B\nТекст B\n"

    chunks = split_markdown(text, max_chars=1_000)

    assert "".join(chunk.text for chunk in chunks) == text
    assert [chunk.text for chunk in chunks] == [
        "Вступление\n\n",
        "## Раздел A\nТекст A\n\n",
        "## Раздел B\nТекст B\n",
    ]


def test_oversized_h2_section_falls_back_to_h3_boundaries() -> None:
    text = "## Большой\n" + "а" * 30 + "\n\n### Подраздел\n" + "б" * 20 + "\n"

    chunks = split_markdown(text, max_chars=50)

    assert "".join(chunk.text for chunk in chunks) == text
    assert len(chunks) == 2
    assert chunks[0].text.startswith("## Большой")
    assert chunks[1].text.startswith("### Подраздел")


def test_never_splits_fence_table_or_html_comment() -> None:
    fence = "```python\nprint('a')\n\nprint('b')\n```\n\n"
    table = "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
    comment = "<!--\nслужебный комментарий\n--!>".replace("--!>", "-->") + "\n\n"
    text = "Начало\n\n" + fence + table + comment + "Конец\n"

    chunks = split_markdown(text, max_chars=48)

    assert "".join(chunk.text for chunk in chunks) == text
    assert any(fence in chunk.text for chunk in chunks)
    assert any(table in chunk.text for chunk in chunks)
    assert any(comment in chunk.text for chunk in chunks)


def test_indices_line_ranges_and_hashes_are_stable() -> None:
    text = "Вступление\n\n## Один\nТекст\n\n## Два\nФинал"

    first = split_markdown(text, max_chars=1_000)
    second = split_markdown(text, max_chars=1_000)

    assert first == second
    assert [chunk.index for chunk in first] == ["000", "001", "002"]
    assert [(chunk.start_line, chunk.end_line) for chunk in first] == [(1, 2), (3, 5), (6, 7)]
    assert first[1].sha256 == hashlib.sha256(first[1].text.encode("utf-8")).hexdigest()


def test_single_indivisible_block_over_limit_raises() -> None:
    text = "```text\n" + "x" * 100 + "\n```\n"

    with pytest.raises(ChunkingError, match="неделимый Markdown-блок"):
        split_markdown(text, max_chars=40)


@pytest.mark.parametrize("max_chars", [0, -1])
def test_non_positive_limit_raises(max_chars: int) -> None:
    with pytest.raises(ValueError, match="max_chars"):
        split_markdown("Текст", max_chars=max_chars)
