from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_instruction_set_example_uses_sse42() -> None:
    text = (ROOT / "book/chapter3.md").read_text()
    assert "SSE4.2 добавлены инструкции сравнения строк" in text
    assert "SSE4.1 добавлены инструкции сравнения строк" not in text


def test_contextual_retrieval_results_are_experiment_specific() -> None:
    text = (ROOT / "book/chapter3.md").read_text()
    assert "не универсальный тариф" in text
    assert "относительно исходного уровня" in text
