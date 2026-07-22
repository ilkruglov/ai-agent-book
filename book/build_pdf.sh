#!/bin/bash
# Build and verify the Russian community edition as a single PDF.

set -euo pipefail

SCRIPT_DIR="$(cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
BUILD_DIR="$ROOT_DIR/.tmp/pdf-build"
DIST_DIR="$ROOT_DIR/dist"
OUT_NAME="AI-Agents-in-Depth-RU-v1.2.pdf"
WORK_PDF="$BUILD_DIR/$OUT_NAME"
DIST_PDF="$DIST_DIR/$OUT_NAME"
ELEGANTBOOK_DIR="$SCRIPT_DIR/vendor/elegantbook"
ELEGANTBOOK_CLASS="$ELEGANTBOOK_DIR/elegantbook.cls"
SVG_RENDER_DIR="$BUILD_DIR/svg-png"
SVG_RENDER_SCALE="4"
export TEXINPUTS="$ELEGANTBOOK_DIR:${TEXINPUTS:-}"

CHAPTERS=(
    introduction.md
    chapter1.md
    chapter2.md
    chapter3.md
    chapter4.md
    chapter5.md
    chapter6.md
    chapter7.md
    chapter8.md
    chapter9.md
    chapter10.md
    afterword.md
)

REQUIRED_COMMANDS=(
    pandoc
    xelatex
    google-chrome
    pdfinfo
    pdftotext
    python3
    kpsewhich
)

check_dependencies() {
    local command_name
    local command_path
    local missing=0

    for command_name in "${REQUIRED_COMMANDS[@]}"; do
        if command_path="$(command -v "$command_name" 2>/dev/null)"; then
            echo "OK: $command_name ($command_path)"
        else
            echo "MISSING: $command_name"
            missing=1
        fi
    done

    return "$missing"
}

check_tex_support() {
    local resource
    local resource_path
    local missing=0

    if [[ -f "$ELEGANTBOOK_CLASS" ]]; then
        echo "OK: elegantbook.cls ($ELEGANTBOOK_CLASS)"
    else
        echo "MISSING: elegantbook.cls"
        missing=1
    fi

    for resource in biblatex.sty TeXGyreTermesX-Regular.otf bbding.sty adforn.sty ragged2e.sty; do
        if resource_path="$(kpsewhich "$resource" 2>/dev/null)" && [[ -n "$resource_path" ]]; then
            echo "OK: $resource ($resource_path)"
        else
            echo "MISSING: $resource"
            missing=1
        fi
    done

    return "$missing"
}

verify_sources() {
    local chapter

    for chapter in "${CHAPTERS[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$chapter" ]]; then
            echo "Ошибка: не найден $SCRIPT_DIR/$chapter" >&2
            return 1
        fi
    done
}

smoke_test_pdf() {
    local pdf_path="$1"
    local info_path="$BUILD_DIR/pdfinfo.txt"
    local text_path="$BUILD_DIR/book.txt"

    if [[ ! -s "$pdf_path" ]]; then
        echo "Ошибка: PDF не создан или пуст: $pdf_path" >&2
        return 1
    fi

    pdfinfo "$pdf_path" >"$info_path"
    pdftotext "$pdf_path" "$text_path"
    python3 - "$info_path" "$text_path" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path


info = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
text = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
normalized = " ".join(text.split())

pages_match = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
if pages_match is None or int(pages_match.group(1)) < 1:
    raise SystemExit("PDF smoke-check: pdfinfo не вернул корректное число страниц")

required_fragments = (
    "AI-агенты изнутри",
    "Основы AI-агентов",
    "Контекстная инженерия",
    "Совместная работа нескольких AI-агентов",
    "Послесловие",
)
for fragment in required_fragments:
    if fragment not in normalized:
        raise SystemExit(f"PDF smoke-check: не найден текст: {fragment}")

if "\ufffd" in text:
    raise SystemExit("PDF smoke-check: в извлечённом тексте найден U+FFFD")
if re.search(r"[㐀-䶿一-鿿豈-﫿]", text):
    raise SystemExit("PDF smoke-check: в извлечённом тексте найден CJK")
if len(normalized) < 100_000:
    raise SystemExit("PDF smoke-check: извлечённый текст подозрительно короткий")

print(f"PDF smoke-check: OK, страниц {pages_match.group(1)}")
PY
}

if [[ "${1:-}" == "--check-deps" ]]; then
    check_dependencies
    check_tex_support
    exit $?
fi

if [[ "${1:-}" == "--promote" ]]; then
    check_dependencies
    check_tex_support
    mkdir -p -- "$BUILD_DIR"
    smoke_test_pdf "$WORK_PDF"
    mkdir -p -- "$DIST_DIR"
    cp -- "$WORK_PDF" "$DIST_PDF"
    echo "Опубликован проверенный PDF: $DIST_PDF"
    exit 0
fi

if [[ $# -ne 0 ]]; then
    echo "Использование: bash book/build_pdf.sh [--check-deps|--promote]" >&2
    exit 2
fi

check_dependencies
check_tex_support
verify_sources
mkdir -p -- "$BUILD_DIR"

# XeTeX requires extra runtime memory for this book. Disabling automatic TFM
# generation prevents a slow failed probe when a platform-specific font is absent.
export extra_mem_top=8000000
export extra_mem_bot=8000000
export MKTEXTFM=0

echo "Сборка PDF из ${#CHAPTERS[@]} файлов..."
python3 "$ROOT_DIR/scripts/render_svg_assets.py" \
    --input-dir "$SCRIPT_DIR/images" \
    --output-dir "$SVG_RENDER_DIR" \
    --chrome "$(command -v google-chrome)" \
    --scale "$SVG_RENDER_SCALE" \
    --jobs 1
export AI_AGENT_BOOK_PDF_IMAGE_DIR="$SVG_RENDER_DIR"
cd -- "$SCRIPT_DIR"

pandoc "${CHAPTERS[@]}" \
    -o "$WORK_PDF" \
    --from markdown+lists_without_preceding_blankline \
    --pdf-engine=xelatex \
    --lua-filter=rasterize_svg.lua \
    --lua-filter=table_widths.lua \
    --lua-filter=crossref.lua \
    --lua-filter=experiment_box.lua \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V documentclass=elegantbook \
    -V classoption=lang=en \
    -V classoption=cyan \
    -V classoption=device=normal \
    -V lang=ru-RU \
    -V author="Bojie Li" \
    --metadata title-meta="AI-агенты изнутри: принципы проектирования и инженерная практика" \
    --metadata author-meta="Bojie Li; Русский перевод: community edition" \
    --metadata version-meta="v1.2-ru.1" \
    -H preamble.tex \
    --include-before-body=cover.tex \
    --highlight-style=kate \
    --columns=80

smoke_test_pdf "$WORK_PDF"
echo "Проверенный PDF готов к дополнительной проверке: $WORK_PDF"
echo "Для публикации после всех проверок: bash book/build_pdf.sh --promote"
