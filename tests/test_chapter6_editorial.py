from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mps_is_attributed_to_realtime_variant() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "Step-Audio R1.1 (Realtime)" in text
    assert "Step-Audio R1 реализует" not in text


def test_pine_result_is_attributed_and_uses_cited_benchmark() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "τ³-Voice Leaderboard" not in text
    assert "По данным Pine AI" in text
    assert "τ²-bench" in text


def test_illustrations_do_not_invent_training_or_measured_latency() -> None:
    for name in ("fig6-12.svg", "fig6-14.svg"):
        text = (ROOT / "book/images" / name).read_text()
        assert "разрешение обучения" not in text.lower()
        assert "разрешения обучения" not in text.lower()
    queue = (ROOT / "book/images/fig6-8.svg").read_text()
    assert "M/M/1" in queue
    assert "В продакшене ρ обычно" not in queue


def test_resolution_examples_are_not_training_provenance() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "Claude обучался с разрешениями" not in text
    assert "согласованное обратное преобразование" in text


def test_provisional_asr_does_not_authorize_irreversible_effects() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "До подтверждения итоговой реплики" in text


def test_teleoperation_is_evidence_not_proof_of_unique_cause() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "однозначным диагностическим свидетельством" not in text
    assert "не доказывает, что оборудование не влияет" in text


def test_external_webhooks_are_not_denied() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "Настоящий недостаток заключается в отсутствии канала" not in text
    assert "`/hooks/wake`" in text
    assert "`/hooks/agent`" in text


def test_isolation_is_not_an_unconditional_guarantee() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "в худшем случае приведут к сбою виртуальной среды" not in text
    assert "общие каталоги" in text


def test_cancellation_does_not_claim_external_rollback() -> None:
    text = (ROOT / "book/chapter6.md").read_text()
    assert "немедленно прекращает поток выполнения и отменяет асинхронный инструмент" not in text
    assert "не выполнит неправильную операцию" not in text
    assert "запрос отмены" in text
