from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.translate_svg_text import (
    SvgTranslationError,
    apply_mapping,
    extract_records,
    validate_mapping,
)


def _write_svg(directory: Path) -> Path:
    directory.mkdir(parents=True)
    path = directory / "figure.svg"
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
<!-- 固定不变 -->
<text x="10" y="20">第一层：评估环境</text>
<text x="10" y="40">API call</text>
</svg>
""",
        encoding="utf-8",
    )
    return path


def test_extract_records_finds_cjk_text_and_comments_in_document_order(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    _write_svg(source_dir)

    records = extract_records(source_dir, re.compile(r"figure\.svg"))

    assert [(record.id, record.kind, record.source) for record in records] == [
        ("figure.svg:0000", "comment", "固定不变"),
        ("figure.svg:0001", "text", "第一层：评估环境"),
    ]


def test_validate_mapping_fails_closed_on_missing_extra_or_cjk_values(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    _write_svg(source_dir)
    records = extract_records(source_dir, re.compile(r"figure\.svg"))

    with pytest.raises(SvgTranslationError, match="ключи"):
        validate_mapping(records, {records[0].id: "Неизменно"})
    with pytest.raises(SvgTranslationError, match="ключи"):
        validate_mapping(
            records,
            {
                records[0].id: "Неизменно",
                records[1].id: "Первый слой",
                "extra": "Лишнее",
            },
        )
    with pytest.raises(SvgTranslationError, match="CJK"):
        validate_mapping(
            records,
            {
                records[0].id: "Неизменно",
                records[1].id: "Первый 层",
            },
        )


def test_apply_mapping_preserves_svg_markup_and_escapes_translated_text(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source = _write_svg(source_dir)
    records = extract_records(source_dir, re.compile(r"figure\.svg"))
    mapping = {
        records[0].id: "Неизменно",
        records[1].id: "Первый слой: оценка <среды> & инструментов",
    }
    output_dir = tmp_path / "output"

    apply_mapping(source_dir, output_dir, records, mapping)

    output = (output_dir / "figure.svg").read_text(encoding="utf-8")
    assert "<!-- Неизменно -->" in output
    assert "Первый слой: оценка &lt;среды&gt; &amp; инструментов" in output
    assert '<text x="10" y="40">API call</text>' in output
    assert output.replace("Неизменно", "固定不变").replace(
        "Первый слой: оценка &lt;среды&gt; &amp; инструментов",
        "第一层：评估环境",
    ) == source.read_text(encoding="utf-8")


def test_translates_visible_nested_tspan_text_without_literal_markup(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "fig.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text x="10" y="20">'
        'user: "天气如何？<tspan dx="-6">"</tspan></text></svg>',
        encoding="utf-8",
    )
    records = extract_records(source, re.compile(r"fig\.svg"))
    assert records[0].source == 'user: "天气如何？"'
    output = tmp_path / "output"
    apply_mapping(source, output, records, {"fig.svg:0000": 'user: "Как погода?"'})
    translated = (output / "fig.svg").read_text()
    assert 'user: "Как погода?"</text>' in translated
    assert "tspan" not in translated
    assert 'x="10" y="20"' in translated


def test_metadata_translates_separately_without_changing_visible_ids(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "fig.svg").write_text(
        '<svg><title id="title">中文标题</title><desc>中文说明</desc>'
        '<text x="10">中文内容</text></svg>',
        encoding="utf-8",
    )
    pattern = re.compile(r"fig\.svg")
    visible = extract_records(source, pattern)
    metadata = extract_records(source, pattern, metadata_only=True)
    assert [r.id for r in visible] == ["fig.svg:0000"]
    assert [r.id for r in metadata] == ["fig.svg:metadata:0000", "fig.svg:metadata:0001"]
    assert [r.source for r in metadata] == ["中文标题", "中文说明"]
    mapping = {
        "fig.svg:0000": "Текст",
        "fig.svg:metadata:0000": "Заголовок",
        "fig.svg:metadata:0001": "Описание",
    }
    apply_mapping(source, tmp_path / "output", (*visible, *metadata), mapping)
    assert (tmp_path / "output/fig.svg").read_text() == (
        '<svg><title id="title">Заголовок</title><desc>Описание</desc>'
        '<text x="10">Текст</text></svg>'
    )
