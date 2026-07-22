from __future__ import annotations

from book.svg_lib import SVG


def test_box_wraps_long_russian_label_inside_narrow_box() -> None:
    svg = SVG(200, 100)

    svg.box(40, 20, 120, 60, "Очень длинная русская подпись блока")

    rendered = svg.render()
    assert rendered.count("<text ") >= 2
    assert "Очень длинная русская подпись блока" not in rendered


def test_box_wraps_sublabel_and_preserves_muted_style() -> None:
    svg = SVG(240, 120)

    svg.box(
        20,
        20,
        200,
        80,
        "Основной этап",
        sublabel="Подробное русское пояснение для схемы",
    )

    rendered = svg.render()
    assert rendered.count('fill="#666666"') >= 2
    assert "Подробное русское пояснение для схемы" not in rendered


def test_text_fits_inside_the_smallest_containing_rectangle() -> None:
    svg = SVG(300, 120)
    svg.rect(50, 20, 120, 60)

    svg.text(110, 50, "Длинная русская подпись внутри прямоугольника")

    rendered = svg.render()
    assert 'textLength="108.0"' in rendered
    assert 'lengthAdjust="spacingAndGlyphs"' in rendered


def test_free_text_fits_inside_canvas_edges() -> None:
    svg = SVG(300, 120)

    svg.text(40, 60, "Длинная подпись у левого края холста")

    rendered = svg.render()
    assert 'textLength="68.0"' in rendered


def test_monospace_text_fits_inside_containing_rectangle() -> None:
    svg = SVG(300, 120)
    svg.rect(20, 30, 180, 50)

    svg.mono(30, 55, "very_long_technical_identifier_with_arguments")

    rendered = svg.render()
    assert 'textLength="164.0"' in rendered
