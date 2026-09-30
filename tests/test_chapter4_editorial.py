from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cache_text_does_not_guarantee_hits_or_global_invalidation() -> None:
    text = (ROOT / "book/chapter4.md").read_text()
    assert "реальный пересчёт вызывают только две ситуации" not in text
    assert "начиная с точки изменения" in text
    assert "минимальной длины" in text


def test_cache_diagrams_do_not_present_invented_measurements() -> None:
    figures = [(ROOT / "book/images" / name).read_text() for name in ("fig4-3.svg", "fig4-4.svg")]
    assert all("95%" not in figure for figure in figures)
    assert all("постоянные попадания" not in figure for figure in figures)
    assert "полный сброс" not in figures[0]


def test_dimensions_and_tool_direction_are_not_mistranslated() -> None:
    text = (ROOT / "book/chapter4.md").read_text()
    assert "высокомерное" not in text
    assert "пространство высокой размерности" in text
    assert "двух остальных типов инструментов, приводимых в действие внешними событиями" not in text


def test_retry_safety_is_not_reduced_to_approval_or_check_then_act() -> None:
    text = (ROOT / "book/chapter4.md").read_text()
    assert "гонки" in text
    assert "не заменяет защиту от повторного выполнения" in text
    assert "неопределённый исход" in text
