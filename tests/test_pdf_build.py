from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "book/build_pdf.sh"
TABLE_WIDTH_FILTER = ROOT / "book/table_widths.lua"
EXPECTED_CHAPTERS = [
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
]
REQUIRED_COMMANDS = (
    "pandoc",
    "xelatex",
    "google-chrome",
    "pdfinfo",
    "pdftotext",
    "python3",
    "kpsewhich",
)
ELEGANTBOOK_SHA256 = "9791679f528b3886e8f736f0ca13fad43fd42cf44187df28d9b3f326d9a4c753"


def _build_script_text() -> str:
    return BUILD_SCRIPT.read_text(encoding="utf-8")


def test_build_uses_ordered_twelve_file_input_and_russian_metadata() -> None:
    script = _build_script_text()
    chapter_block = re.search(r"CHAPTERS=\(\n(?P<body>.*?)\n\)", script, re.DOTALL)

    assert chapter_block is not None
    assert re.findall(r"^\s+([a-z0-9.]+)$", chapter_block["body"], re.MULTILINE) == (
        EXPECTED_CHAPTERS
    )
    assert 'OUT_NAME="AI-Agents-in-Depth-RU-v1.2.pdf"' in script
    assert 'BUILD_DIR="$ROOT_DIR/.tmp/pdf-build"' in script
    assert '--metadata title-meta="AI-агенты изнутри: принципы проектирования' in script
    assert '--metadata author-meta="Bojie Li; Русский перевод: community edition"' in script
    assert 'SVG_RENDER_SCALE="4"' in script
    assert "--jobs 1" in script
    assert "--lua-filter=rasterize_svg.lua" in script


def test_table_width_filter_rebalances_columns_for_russian_content() -> None:
    markdown = (
        "| Функция | Основной принцип | Практический пример | Подробнее |\n"
        "|------|-----------------------------------------------|"
        "-----------------------------------|-------|\n"
        "| Контекст | Достаточность информации в каждой точке принятия решения | "
        "Системный промпт и база знаний | Главы 2 и 3 |\n"
        "| Ограничения | Безопасные значения по умолчанию для всех возможностей | "
        "Разрешения пользователя | Глава 4 |\n"
        "| Исправление | Не показывать промежуточное состояние до проверки | "
        "Незаметные повторные попытки | Главы 2 и 5 |\n"
    )
    result = subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown",
            "--to",
            "json",
            f"--lua-filter={TABLE_WIDTH_FILTER}",
        ],
        input=markdown,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    document = json.loads(result.stdout)
    colspecs = document["blocks"][0]["c"][2]
    widths = [spec[1]["c"] for spec in colspecs]

    assert math.isclose(sum(widths), 1.0)
    assert widths[0] >= 0.14
    assert widths[3] >= 0.12
    assert widths[1] > widths[0]
    assert widths[2] > widths[3]


def test_table_width_filter_preserves_minimum_width_in_six_column_tables() -> None:
    result = subprocess.run(
        [
            "pandoc",
            str(ROOT / "book/chapter7.md"),
            "--from",
            "markdown",
            "--to",
            "json",
            f"--lua-filter={TABLE_WIDTH_FILTER}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    document = json.loads(result.stdout)
    six_column_tables = [
        block for block in document["blocks"] if block["t"] == "Table" and len(block["c"][2]) == 6
    ]

    assert len(six_column_tables) == 1
    colspecs = six_column_tables[0]["c"][2]
    widths = [spec[1]["c"] for spec in colspecs]

    assert math.isclose(sum(widths), 1.0)
    assert min(widths) >= 0.14


def test_table_width_filter_adds_latex_break_after_slash() -> None:
    markdown = """\
| Фреймворк/платформа | Основное назначение |
|---|---|
| OpenAI Agents SDK | Разработка агентов |
"""
    result = subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown",
            "--to",
            "latex",
            f"--lua-filter={TABLE_WIDTH_FILTER}",
        ],
        input=markdown,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert r"\hspace{0pt}Фреймворк/\allowbreak{}платформа" in result.stdout


def test_build_applies_table_width_filter_before_rendering_latex() -> None:
    script = _build_script_text()

    table_widths = script.index("--lua-filter=table_widths.lua")
    crossrefs = script.index("--lua-filter=crossref.lua")

    assert table_widths < crossrefs


def test_dependency_preflight_reports_every_missing_command(tmp_path: Path) -> None:
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    result = subprocess.run(
        ["/bin/bash", str(BUILD_SCRIPT), "--check-deps"],
        cwd=ROOT,
        env={**os.environ, "PATH": str(empty_path)},
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    for command in REQUIRED_COMMANDS:
        assert f"MISSING: {command}" in result.stdout


def test_pdf_is_smoke_tested_before_dist_promotion() -> None:
    script = _build_script_text()

    smoke = script.index('smoke_test_pdf "$WORK_PDF"')
    promote = script.index('cp -- "$WORK_PDF" "$DIST_PDF"')
    assert smoke < promote
    assert '"$BUILD_DIR/book.txt"' in script
    assert "U+FFFD" in script


def test_pdf_support_is_localized_for_russian() -> None:
    preamble = (ROOT / "book/preamble.tex").read_text(encoding="utf-8")
    cover = (ROOT / "book/cover.tex").read_text(encoding="utf-8")
    crossref = (ROOT / "book/crossref.lua").read_text(encoding="utf-8")
    boxes = (ROOT / "book/experiment_box.lua").read_text(encoding="utf-8")

    assert "DejaVu Serif" in preamble
    assert "DejaVu Sans" in preamble
    assert r"\usepackage{ragged2e}" in preamble
    assert r"\AtBeginEnvironment{longtable}{\let\raggedright\RaggedRight\sloppy}" in preamble
    assert "Вопросы для размышления" in preamble
    assert "AI-агенты изнутри" in cover
    assert "Русский перевод: community edition" in cover
    assert "Рисунок" in crossref
    assert "рисунке" in crossref
    assert "Глава" in crossref
    assert "главе" in crossref
    assert "Эксперимент" in boxes
    assert "Вопросы для размышления" in boxes


def test_elegantbook_v45_is_vendored_with_its_license() -> None:
    class_path = ROOT / "book/vendor/elegantbook/elegantbook.cls"
    license_path = ROOT / "book/vendor/elegantbook/LICENSE"

    assert hashlib.sha256(class_path.read_bytes()).hexdigest() == ELEGANTBOOK_SHA256
    assert "2022/12/31 v4.5 ElegantBook document class" in class_path.read_text(encoding="utf-8")
    assert "LaTeX Project Public License" in license_path.read_text(encoding="utf-8")

    script = _build_script_text()
    assert 'ELEGANTBOOK_DIR="$SCRIPT_DIR/vendor/elegantbook"' in script
    assert 'export TEXINPUTS="$ELEGANTBOOK_DIR:${TEXINPUTS:-}"' in script
