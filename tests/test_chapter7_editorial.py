from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "incorrect",
    [
        "Если переход на более сильную модель не повышает оценку, узким местом является Harness.",
        "неизбежная цена бинарного вознаграждения",
        "но остальные четыре компонента сохраняются",
        "все четыре уровня проверки τ²-bench также реализованы программно",
        "доказывает отсутствие новых дефектов",
        "перед публикацией отсеяно 71%",
        "агент постепенно учится избегать типов ошибок, которые оценивающая модель плохо обнаруживает",
        "если задачу ещё можно спасти, ошибка произошла после k",
        "следовательно, проблема заключалась не в промпте",
        "Общее ранжирование двух алгоритмов должно совпадать",
        "Если модель способна вывести содержимое с этим GUID, значит",
        "следует распознать их как одного человека",
        "высокие оценки почти всегда соответствуют длинным ответам, значит",
        "Агент не может подделать вывод",
        "OpenClaw разрешает это противоречие с помощью системы типов",
        "обязательной мгновенной обратной связи",
        "обучение предъявляет новые требования, о которых на этапе оценки можно не беспокоиться",
    ],
)
def test_rejected_evaluation_claims_do_not_return(incorrect: str) -> None:
    assert incorrect not in (ROOT / "book/chapter7.md").read_text()


def test_repeated_seeds_do_not_become_independent_tasks() -> None:
    text = (ROOT / "book/chapter7.md").read_text()
    assert "бутстрэп по задачам" in text
    assert "не считать все пары task×seed независимыми" in text


def test_nl_evaluator_is_explicitly_model_based() -> None:
    text = (ROOT / "book/chapter7.md").read_text()
    assert "`nl_assertions` оценивает LLM" in text


def test_five_components_remain_present_without_user_simulator() -> None:
    text = (ROOT / "book/chapter7.md").read_text()
    assert "симулятор пользователя отсутствует, но все пять компонентов сохраняются" in text


def test_androidworld_figure_matches_reported_small_experiment() -> None:
    svg = (ROOT / "book/images/fig7-8.svg").read_text()
    assert "88%→94%" not in svg
    assert "25% → 25%" in svg
    assert "H5C" in svg
    assert "4 задачи" in svg


def test_figure_does_not_call_grpo_pairwise_or_reward_free() -> None:
    svg = (ROOT / "book/images/fig7-6.svg").read_text()
    assert "GRPO: попарное сравнение" not in svg
    assert "без явной" not in svg


def test_openvla_example_is_not_an_unadapted_bimanual_checkpoint() -> None:
    text = (ROOT / "book/chapter7.md").read_text()
    assert "не готовая возможность исходного checkpoint OpenVLA" in text
