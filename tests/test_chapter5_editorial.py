from pathlib import Path
import re
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_diagrams_preserve_code_review_and_policy_constraints() -> None:
    flow = (ROOT / "book/images/fig5-2.svg").read_text()
    debugging = (ROOT / "book/images/fig5-7.svg").read_text()
    reuse = (ROOT / "book/images/fig5-10.svg").read_text()
    assert "исправить тест" not in flow
    assert "усечение начала и конца" not in flow
    assert "рендеринга" not in flow + debugging
    assert "сходимость за 2-3" not in flow
    assert "предложить страховку" not in debugging
    assert "с нескольких часов до нескольких минут" not in debugging
    assert "качество сохранено" not in reuse
    assert "качество проверяется тестами" in reuse


def test_code_and_rollback_are_not_unconditional_proofs() -> None:
    text = (ROOT / "book/chapter5.md").read_text()
    assert "сам по себе служит доказательством логической непротиворечивости" not in text
    assert "гарантируют обратимость любой ошибки" not in text
    assert "не повредит хосту" not in text


def test_retry_identity_preserves_intent_and_effect_state() -> None:
    text = (ROOT / "book/chapter5.md").read_text()
    assert "однозначно указывает на цикл без прогресса" not in text
    assert "сохраняются только имя и параметры" not in text
    assert "неопределённый исход" in text
    assert "Отпечаток параметров" in text


def test_current_search_capabilities_are_not_denied() -> None:
    text = (ROOT / "book/chapter5.md").read_text()
    assert "Cursor и другие IDE также перешли на поиск на месте" not in text
    assert "Современные распространённые Coding-агенты этот метод не используют" not in text
    assert "LSP" in text


def test_step_is_not_parametric_history_or_machine_instructions() -> None:
    text = (ROOT / "book/chapter5.md").read_text()
    assert "Файл STEP хранит дерево конструктивных элементов" not in text
    assert "непосредственно управлять обработкой на станке" not in text
    assert "CAM" in text


def test_airline_example_does_not_invent_post_purchase_insurance() -> None:
    text = (ROOT / "book/chapter5.md").read_text()
    assert "можно приобрести страховку и затем выполнить отмену" not in text
    assert "учебный" in text


@pytest.mark.parametrize(
    ("insured", "reason", "used", "hours", "expected"),
    [
        (True, "change_of_plan", False, 48, False),
        (True, "health", False, 48, True),
        (False, "health", False, 48, False),
        (False, "change_of_plan", False, 12, True),
        (True, "health", True, 12, False),
    ],
)
def test_cancellation_example_checks_insurance_coverage(
    insured: bool, reason: str, used: bool, hours: int, expected: bool
) -> None:
    text = (ROOT / "book/chapter5.md").read_text()
    code = re.search(r"```python\n(.*?)\n```", text, re.S)
    assert code is not None
    now = datetime(2026, 9, 30)
    reservation = SimpleNamespace(
        cabin_class="economy",
        has_insurance=insured,
        any_segment_used=used,
        booking_time=now - timedelta(hours=hours),
        flight_status="on_time",
    )
    effects: list[str] = []
    namespace: dict[str, object] = {
        "db": SimpleNamespace(get_reservation=lambda _: reservation),
        "server_clock": SimpleNamespace(now=lambda: now),
        "log_mismatch": lambda *args: None,
        "insurance_covers": lambda _, cause: cause == "health",
        "execute_cancellation": effects.append,
    }
    exec(compile(code[1], "chapter5-example", "exec"), namespace)
    result = namespace["cancel_reservation"]("reservation-1", reason)
    assert result["success"] is expected
    assert len(effects) == int(expected)
