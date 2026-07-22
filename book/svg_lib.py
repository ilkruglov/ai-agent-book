"""Библиотека генерации SVG-диаграмм для иллюстраций книги.

Стиль рассчитан на чёрно-белую и полутоновую печать.
"""

from __future__ import annotations

import argparse
import math
import os
import textwrap
from collections.abc import Sequence
from os import PathLike
from typing import cast

type Number = int | float

COLORS: dict[str, str] = {
    "white": "#ffffff",
    "light": "#f0f0f0",
    "medium": "#d0d0d0",
    "dark": "#999999",
    "darker": "#666666",
    "border": "#333333",
    "text": "#333333",
    "text_light": "#666666",
    "bg": "#ffffff",
    "code_bg": "#f5f5f5",
}

FONT = "Arial, 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif"
MONO = "'Courier New', Courier, monospace"
STROKE_W = 2
CORNER_R = 6

FS_TITLE = 24
FS_BODY = 20
FS_SMALL = 16
FS_TINY = 14
FS_LABEL = 16

# По правилам академического оформления заголовок указывают в тексте, а не на рисунке.
# При OMIT_TITLE=True любой «заголовочный» текст с font_size==FS_TITLE (кроме коротких
# символов вроде VS/→/+) считается заголовком рисунка и не отрисовывается независимо
# от его положения сверху или в центре рисунка (включая заголовки разделов на составных
# рисунках). Короткие символы сохраняются по порогу длины TITLE_MIN_LEN.
OMIT_TITLE = True
TITLE_Y_THRESHOLD = (
    60  # Сохранено для совместимости со старой логикой, отдельно больше не используется
)
TITLE_MIN_LEN = 4  # Текст FS_TITLE длиной >= этого значения считается заголовком и удаляется
TITLE_CROP_PX = 20
BOX_MIN_FONT_SIZE = 9.0
BOX_CHAR_WIDTH_FACTOR = 0.58
BOX_PADDING_X = 12.0
BOX_PADDING_Y = 8.0


def parse_output_dir(default: str, argv: Sequence[str] | None = None) -> str:
    """Разобрать общий CLI-параметр каталога для воспроизводимой генерации."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=default)
    args = parser.parse_args(argv)
    return os.path.abspath(cast(str, args.output_dir))


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _marker_def() -> str:
    return (
        "<defs>"
        '<marker id="ah" markerWidth="12" markerHeight="8" refX="12" refY="4" orient="auto">'
        f'<polygon points="0 0, 12 4, 0 8" fill="{COLORS["border"]}"/>'
        "</marker>"
        '<marker id="ah-light" markerWidth="12" markerHeight="8" refX="12" refY="4" orient="auto">'
        f'<polygon points="0 0, 12 4, 0 8" fill="{COLORS["dark"]}"/>'
        "</marker>"
        "</defs>"
    )


def _wrap_box_line(line: str, max_chars: int) -> list[str]:
    """Перенести строку по словам, сохраняя неделимые технические токены."""
    if not line:
        return [""]
    return textwrap.wrap(
        line,
        width=max(max_chars, 1),
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def _fit_box_lines(
    label: str,
    sublabel: str | None,
    width: Number,
    height: Number,
    initial_font_size: Number,
) -> tuple[list[tuple[str, bool]], float, float]:
    """Подобрать переносы и размер шрифта под внутреннюю область блока."""
    available_width = max(float(width) - BOX_PADDING_X, 1.0)
    available_height = max(float(height) - BOX_PADDING_Y, 1.0)
    font_size = float(initial_font_size)

    while True:
        sublabel_size = max(font_size - 2.0, BOX_MIN_FONT_SIZE)
        lines: list[tuple[str, bool]] = []
        for raw_line in label.split("\n"):
            max_chars = int(available_width / (font_size * BOX_CHAR_WIDTH_FACTOR))
            lines.extend((line, False) for line in _wrap_box_line(raw_line, max_chars))
        if sublabel:
            for raw_line in sublabel.split("\n"):
                max_chars = int(available_width / (sublabel_size * BOX_CHAR_WIDTH_FACTOR))
                lines.extend((line, True) for line in _wrap_box_line(raw_line, max_chars))

        line_height = font_size * 1.15
        if len(lines) * line_height <= available_height or font_size <= BOX_MIN_FONT_SIZE:
            return lines, font_size, line_height
        font_size -= 1.0


class SVG:
    """Конструктор SVG-диаграмм."""

    def __init__(self, width: Number, height: Number) -> None:
        self.width = width
        self.height = height
        self.elems: list[str] = []
        self._rectangles: list[tuple[float, float, float, float]] = []

    def rect(
        self,
        x: Number,
        y: Number,
        w: Number,
        h: Number,
        fill: str = "light",
        stroke: str = "border",
        rx: Number = CORNER_R,
        dash: bool = False,
    ) -> None:
        self._rectangles.append((float(x), float(y), float(w), float(h)))
        c_fill = COLORS.get(fill, fill)
        c_stroke = COLORS.get(stroke, stroke)
        d = ' stroke-dasharray="8,4"' if dash else ""
        self.elems.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{c_fill}" stroke="{c_stroke}" stroke-width="{STROKE_W}"{d}/>'
        )

    def box(
        self,
        x: Number,
        y: Number,
        w: Number,
        h: Number,
        label: str,
        fill: str = "light",
        sublabel: str | None = None,
        bold: bool = False,
        font_size: Number = FS_BODY,
    ) -> None:
        self.rect(x, y, w, h, fill=fill)
        lines, fitted_font_size, line_height = _fit_box_lines(
            label,
            sublabel,
            w,
            h,
            font_size,
        )
        total = len(lines)
        start_y = y + h / 2 - (total - 1) * line_height / 2
        available_width = max(float(w) - BOX_PADDING_X, 1.0)
        for i, (line, is_sublabel) in enumerate(lines):
            ly = start_y + i * line_height
            fs = max(fitted_font_size - 2.0, BOX_MIN_FONT_SIZE) if is_sublabel else fitted_font_size
            fc = COLORS["text_light"] if is_sublabel else COLORS["text"]
            w2 = "bold" if bold else "normal"
            estimated_width = len(line) * fs * BOX_CHAR_WIDTH_FACTOR
            fit = (
                f' textLength="{available_width}" lengthAdjust="spacingAndGlyphs"'
                if estimated_width > available_width
                else ""
            )
            self.elems.append(
                f'<text x="{x + w / 2}" y="{ly}" font-family="{FONT}" font-size="{fs}" '
                f'fill="{fc}" text-anchor="middle" dominant-baseline="central" '
                f'font-weight="{w2}"{fit}>'
                f"{_escape(line)}</text>"
            )

    def text(
        self,
        x: Number,
        y: Number,
        content: str,
        size: Number = FS_BODY,
        bold: bool = False,
        anchor: str = "middle",
        fill: str = "text",
        baseline: str = "central",
        max_width: Number | None = None,
    ) -> None:
        # Пропускаем заголовки внутри рисунка по правилам академического оформления
        # (заголовки указываются в основном тексте). Удаляем любую фразу с размером
        # FS_TITLE независимо от положения на рисунке, но сохраняем короткие символы
        # (VS / → / + и т. п.), для которых также используется размер заголовка.
        if OMIT_TITLE and size == FS_TITLE and len(str(content).strip()) >= TITLE_MIN_LEN:
            return
        c = COLORS.get(fill, fill)
        fw = "bold" if bold else "normal"
        fitted_width = (
            float(max_width)
            if max_width is not None
            else self._containing_text_width(float(x), float(y), anchor)
        )
        if fitted_width is None:
            fitted_width = self._canvas_text_width(float(x), anchor)
        estimated_width = len(str(content)) * float(size) * BOX_CHAR_WIDTH_FACTOR
        fit = (
            f' textLength="{fitted_width}" lengthAdjust="spacingAndGlyphs"'
            if estimated_width > fitted_width
            else ""
        )
        self.elems.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{c}" '
            f'text-anchor="{anchor}" dominant-baseline="{baseline}" font-weight="{fw}"{fit}>'
            f"{_escape(content)}</text>"
        )

    def _containing_text_width(self, x: float, y: float, anchor: str) -> float | None:
        """Вернуть доступную ширину в наименьшем содержащем текст прямоугольнике."""
        candidates = [
            rect
            for rect in self._rectangles
            if rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]
        ]
        if not candidates:
            return None
        left, _top, width, _height = min(candidates, key=lambda rect: rect[2] * rect[3])
        right = left + width
        if anchor == "start":
            available = right - x - BOX_PADDING_X / 2
        elif anchor == "end":
            available = x - left - BOX_PADDING_X / 2
        else:
            available = 2 * min(x - left, right - x) - BOX_PADDING_X
        return max(available, 1.0)

    def _canvas_text_width(self, x: float, anchor: str) -> float:
        """Вернуть ширину, доступную тексту до ближайшего края холста."""
        width = float(self.width)
        if anchor == "start":
            available = width - x - BOX_PADDING_X / 2
        elif anchor == "end":
            available = x - BOX_PADDING_X / 2
        else:
            available = 2 * min(x, width - x) - BOX_PADDING_X
        return max(available, 1.0)

    def mono(
        self,
        x: Number,
        y: Number,
        content: str,
        size: Number = FS_SMALL,
        anchor: str = "start",
        fill: str = "text",
        max_width: Number | None = None,
    ) -> None:
        """Моноширинный текст для фрагментов кода."""
        c = COLORS.get(fill, fill)
        fitted_width = (
            float(max_width)
            if max_width is not None
            else self._containing_text_width(float(x), float(y), anchor)
        )
        if fitted_width is None:
            fitted_width = self._canvas_text_width(float(x), anchor)
        estimated_width = len(str(content)) * float(size) * 0.62
        fit = (
            f' textLength="{fitted_width}" lengthAdjust="spacingAndGlyphs"'
            if estimated_width > fitted_width
            else ""
        )
        self.elems.append(
            f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{c}" '
            f'text-anchor="{anchor}" dominant-baseline="central"{fit}>'
            f"{_escape(content)}</text>"
        )

    def code_block(
        self,
        x: Number,
        y: Number,
        w: Number,
        lines: Sequence[str],
        font_size: Number = FS_SMALL,
        line_h: Number | None = None,
    ) -> Number:
        """Отрисовать блок строк моноширинного кода с фоном."""
        if line_h is None:
            line_h = font_size * 1.5
        h = len(lines) * line_h + 12
        self.rect(x, y, w, h, fill="code_bg", stroke="dark", rx=4)
        for i, line in enumerate(lines):
            ly = y + 10 + i * line_h + line_h / 2
            self.mono(x + 10, ly, line, size=font_size)
        return h

    def multiline_text(
        self,
        x: Number,
        y: Number,
        lines: Sequence[str],
        size: Number = FS_BODY,
        anchor: str = "middle",
        fill: str = "text",
        line_h: Number | None = None,
        bold: bool = False,
    ) -> None:
        """Отрисовать многострочный текст."""
        if line_h is None:
            line_h = size * 1.4
        for i, line in enumerate(lines):
            ly = y + i * line_h
            self.text(x, ly, line, size=size, anchor=anchor, fill=fill, bold=bold)

    def arrow(
        self,
        x1: Number,
        y1: Number,
        x2: Number,
        y2: Number,
        label: str | None = None,
        dash: bool = False,
        color: str = "border",
    ) -> None:
        c = COLORS.get(color, color)
        d = ' stroke-dasharray="8,4"' if dash else ""
        mk = "ah-light" if color in ("dark", COLORS["dark"]) else "ah"
        self.elems.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{c}" stroke-width="{STROKE_W}"{d} marker-end="url(#{mk})"/>'
        )
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.elems.append(
                f'<text x="{mx}" y="{my - 10}" font-family="{FONT}" font-size="{FS_LABEL}" '
                f'fill="{COLORS["text_light"]}" text-anchor="middle">{_escape(label)}</text>'
            )

    def arrow_curved(
        self,
        x1: Number,
        y1: Number,
        x2: Number,
        y2: Number,
        curve: Number = 30,
        label: str | None = None,
        dash: bool = False,
        color: str = "border",
    ) -> None:
        """Нарисовать изогнутую стрелку квадратичной кривой Безье."""
        c = COLORS.get(color, color)
        d = ' stroke-dasharray="8,4"' if dash else ""
        mk = "ah-light" if color in ("dark", COLORS["dark"]) else "ah"
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            nx, ny = -dy / dist * curve, dx / dist * curve
        else:
            nx, ny = 0, -curve
        cx, cy = mx + nx, my + ny
        self.elems.append(
            f'<path d="M {x1},{y1} Q {cx},{cy} {x2},{y2}" fill="none" '
            f'stroke="{c}" stroke-width="{STROKE_W}"{d} marker-end="url(#{mk})"/>'
        )
        if label:
            lx, ly = (x1 + 2 * cx + x2) / 4, (y1 + 2 * cy + y2) / 4
            self.text(lx, ly - 10, label, size=FS_LABEL, fill="text_light")

    def line(
        self,
        x1: Number,
        y1: Number,
        x2: Number,
        y2: Number,
        dash: bool = False,
        color: str = "border",
    ) -> None:
        c = COLORS.get(color, color)
        d = ' stroke-dasharray="8,4"' if dash else ""
        self.elems.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{c}" stroke-width="{STROKE_W}"{d}/>'
        )

    def circle(
        self,
        cx: Number,
        cy: Number,
        r: Number,
        fill: str = "light",
        label: str | None = None,
        font_size: Number = FS_SMALL,
    ) -> None:
        c = COLORS.get(fill, fill)
        self.elems.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}" '
            f'stroke="{COLORS["border"]}" stroke-width="{STROKE_W}"/>'
        )
        if label:
            self.elems.append(
                f'<text x="{cx}" y="{cy}" font-family="{FONT}" font-size="{font_size}" '
                f'fill="{COLORS["text"]}" text-anchor="middle" dominant-baseline="central">'
                f"{_escape(label)}</text>"
            )

    def diamond(
        self,
        cx: Number,
        cy: Number,
        w: Number,
        h: Number,
        fill: str = "light",
        label: str | None = None,
        font_size: Number = FS_SMALL,
    ) -> None:
        c = COLORS.get(fill, fill)
        pts = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"  # noqa: E501
        self.elems.append(
            f'<polygon points="{pts}" fill="{c}" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}"/>'  # noqa: E501
        )
        if label:
            self.elems.append(
                f'<text x="{cx}" y="{cy}" font-family="{FONT}" font-size="{font_size}" '
                f'fill="{COLORS["text"]}" text-anchor="middle" dominant-baseline="central">'
                f"{_escape(label)}</text>"
            )

    def brace_right(
        self,
        x: Number,
        y1: Number,
        y2: Number,
        label: str | None = None,
    ) -> None:
        my = (y1 + y2) / 2
        d = (
            f"M {x},{y1} C {x + 20},{y1} {x + 20},{my - 5} {x + 25},{my} "
            f"C {x + 20},{my + 5} {x + 20},{y2} {x},{y2}"
        )
        self.elems.append(
            f'<path d="{d}" fill="none" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}"/>'
        )
        if label:
            self.text(x + 35, my, label, size=FS_SMALL, anchor="start")

    def group_box(
        self,
        x: Number,
        y: Number,
        w: Number,
        h: Number,
        label: str,
        fill: str = "white",
    ) -> None:
        """Пунктирная граница группы с подписью в левом верхнем углу."""
        self.rect(x, y, w, h, fill=fill, rx=8, dash=True)
        self.text(
            x + 12, y + 18, label, size=FS_SMALL, bold=True, fill="text_light", anchor="start"
        )

    def badge(
        self,
        x: Number,
        y: Number,
        w: Number,
        h: Number,
        label: str,
        fill: str = "dark",
        font_size: Number = FS_SMALL,
    ) -> None:
        """Небольшая скруглённая метка."""
        self.rect(x, y, w, h, fill=fill, rx=h // 2)
        self.text(x + w / 2, y + h / 2, label, size=font_size, fill="white", bold=True)

    def render(self) -> str:
        if OMIT_TITLE:
            crop = TITLE_CROP_PX
            vb = f"0 {crop} {self.width} {self.height - crop}"
            h_attr = self.height - crop
        else:
            vb = f"0 0 {self.width} {self.height}"
            h_attr = self.height
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
            f'width="{self.width}" height="{h_attr}" '
            f'style="background:{COLORS["bg"]}">',
            _marker_def(),
        ]
        parts.extend(self.elems)
        parts.append("</svg>")
        return "\n".join(parts)

    def save(self, path: str | PathLike[str]) -> None:
        path_string = os.fspath(path)
        os.makedirs(os.path.dirname(path_string), exist_ok=True)
        with open(path_string, "w", encoding="utf-8") as f:
            f.write(self.render())


def flow_lr(
    nodes: Sequence[str],
    width: Number = 800,
    node_h: Number = 55,
    node_w: Number | None = None,
    fills: Sequence[str] | None = None,
    spacing: Number = 25,
) -> SVG:
    """Горизонтальная блок-схема: узлы соединены стрелками слева направо."""
    n = len(nodes)
    if node_w is None:
        node_w = min(150, (width - spacing * (n + 1)) // n)
    total_w = n * node_w + (n - 1) * spacing
    x_start = (width - total_w) / 2
    height = node_h + 70
    svg = SVG(width, height)
    y = (height - node_h) / 2
    positions: list[tuple[Number, Number]] = []
    for i, label in enumerate(nodes):
        x = x_start + i * (node_w + spacing)
        f = (fills[i] if fills else "light") if fills and i < len(fills) else "light"
        svg.box(x, y, node_w, node_h, label, fill=f)
        positions.append((x, y))
        if i > 0:
            px = positions[i - 1][0] + node_w
            svg.arrow(px + 2, y + node_h / 2, x - 2, y + node_h / 2)
    return svg


def flow_tb(
    nodes: Sequence[str],
    width: Number = 350,
    node_h: Number = 55,
    node_w: Number = 240,
    fills: Sequence[str] | None = None,
    spacing: Number = 35,
    arrow_labels: Sequence[str] | None = None,
) -> SVG:
    """Вертикальная блок-схема сверху вниз."""
    n = len(nodes)
    height = n * node_h + (n - 1) * spacing + 50
    svg = SVG(width, height)
    x = (width - node_w) / 2
    positions: list[tuple[Number, Number]] = []
    for i, label in enumerate(nodes):
        y = 25 + i * (node_h + spacing)
        f = (fills[i] if fills else "light") if fills and i < len(fills) else "light"
        svg.box(x, y, node_w, node_h, label, fill=f)
        positions.append((x, y))
        if i > 0:
            al = arrow_labels[i - 1] if arrow_labels and i - 1 < len(arrow_labels) else None
            svg.arrow(
                x + node_w / 2, positions[i - 1][1] + node_h + 2, x + node_w / 2, y - 2, label=al
            )
    return svg


def tree_diagram(
    root: str,
    children: Sequence[str],
    width: Number = 750,
    root_h: Number = 60,
    child_h: Number = 55,
    child_w: Number | None = None,
    root_w: Number = 220,
) -> SVG:
    """Древовидная диаграмма: корневой узел с дочерними узлами снизу."""
    n = len(children)
    if child_w is None:
        child_w = min(170, (width - 20) // max(n, 1))
    spacing = 20
    total_cw = n * child_w + (n - 1) * spacing
    x_start = (width - total_cw) / 2
    height = root_h + child_h + 120
    svg = SVG(width, height)
    rx = (width - root_w) / 2
    svg.box(rx, 20, root_w, root_h, root, fill="medium", bold=True)
    root_cx = width / 2
    root_bot = 20 + root_h
    for i, label in enumerate(children):
        cx = x_start + i * (child_w + spacing) + child_w / 2
        cy = root_bot + 55
        svg.line(root_cx, root_bot, cx, cy)
        svg.box(x_start + i * (child_w + spacing), cy, child_w, child_h, label)
    return svg


def layer_diagram(
    layers: Sequence[tuple[str, str]],
    width: Number = 600,
    layer_h: Number = 55,
    spacing: Number = 14,
) -> SVG:
    """Стек горизонтальных слоёв (первый слой сверху)."""
    n = len(layers)
    lw = width - 80
    height = n * layer_h + (n - 1) * spacing + 50
    svg = SVG(width, height)
    x = 40
    for i, (label, fill) in enumerate(layers):
        y = 25 + i * (layer_h + spacing)
        svg.box(x, y, lw, layer_h, label, fill=fill)
    return svg


def comparison_lr(
    left_title: str,
    left_items: Sequence[str],
    right_title: str,
    right_items: Sequence[str],
    width: Number = 750,
    item_h: Number = 45,
) -> SVG:
    "Диаграмма сравнения с расположением элементов рядом."
    col_w = (width - 100) // 2
    n = max(len(left_items), len(right_items))
    height = 80 + n * (item_h + 10) + 25
    svg = SVG(width, height)
    lx = 25
    rx = width - col_w - 25
    svg.box(lx, 20, col_w, 50, left_title, fill="medium", bold=True)
    svg.box(rx, 20, col_w, 50, right_title, fill="medium", bold=True)
    for i, label in enumerate(left_items):
        y = 85 + i * (item_h + 10)
        svg.box(lx, y, col_w, item_h, label, fill="light")
    for i, label in enumerate(right_items):
        y = 85 + i * (item_h + 10)
        svg.box(rx, y, col_w, item_h, label, fill="light")
    return svg


def cycle_diagram(
    nodes: Sequence[str],
    width: Number = 480,
    height: Number = 480,
    radius: Number = 160,
) -> SVG:
    """Циклическая диаграмма со стрелками между узлами."""
    n = len(nodes)
    cx, cy = width / 2, height / 2
    svg = SVG(width, height)
    node_w, node_h = 120, 50
    positions: list[tuple[Number, Number]] = []
    for i in range(n):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        nx = cx + radius * math.cos(angle)
        ny = cy + radius * math.sin(angle)
        positions.append((nx, ny))
        svg.box(
            nx - node_w / 2,
            ny - node_h / 2,
            node_w,
            node_h,
            nodes[i],
            fill="light",
            font_size=FS_SMALL,
        )

    for i in range(n):
        j = (i + 1) % n
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        offset_start = max(node_w, node_h) / 2 + 5
        offset_end = max(node_w, node_h) / 2 + 5
        svg.arrow(
            x1 + ux * offset_start,
            y1 + uy * offset_start,
            x2 - ux * offset_end,
            y2 - uy * offset_end,
        )
    return svg
