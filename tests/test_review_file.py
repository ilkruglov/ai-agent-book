from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from scripts.check_translation import TRANSLATION_NOTICE
from scripts.model_runner import ModelResult, RuntimeEvidence
from scripts.review_file import ReviewError, review_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = """## 第一节
原文一。

## 第二节
原文二。
"""
TRANSLATION_BODY = """## Первый раздел
Русский текст.

## Второй раздел
Ещё текст.
"""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _prepare_repo(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    source = repo / ".tmp/upstream/book/chapter.md"
    translation = repo / "book/chapter.md"
    output = repo / ".tmp/reviews/chapter.json"
    glossary = repo / "glossary.yml"
    source.parent.mkdir(parents=True)
    translation.parent.mkdir(parents=True)
    (repo / "prompts").mkdir()
    source.write_text(SOURCE, encoding="utf-8")
    translation.write_text(
        f"{TRANSLATION_NOTICE}\n\n{TRANSLATION_BODY}",
        encoding="utf-8",
    )
    glossary.write_text(
        """schema_version: 1
attribution: "Русский перевод: community edition"
terms:
  - id: ai_agent
    source: ["AI Agent"]
    preferred: "AI-агент"
    status: accepted
    rule: "Первое упоминание"
    forbidden: ["ИИ-агент"]
  - id: candidate
    source: ["candidate"]
    preferred: "НЕ-ПЕРЕДАВАТЬ"
    status: candidate
    rule: "Не принято"
    forbidden: []
""",
        encoding="utf-8",
    )
    shutil.copyfile(PROJECT_ROOT / "prompts/review.txt", repo / "prompts/review.txt")
    shutil.copyfile(
        PROJECT_ROOT / "prompts/review.schema.json",
        repo / "prompts/review.schema.json",
    )
    return repo, source, translation, output, glossary


def _result(output_path: Path, response: str) -> ModelResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response, encoding="utf-8")
    return ModelResult(
        model="claude-opus-4-8",
        command=("claude",),
        output_path=output_path,
        response=response,
        prompt_sha256=_sha256("prompt"),
        response_sha256=_sha256(response),
        stdout_sha256=_sha256("stdout"),
        stderr_sha256=_sha256(""),
        evidence=RuntimeEvidence(
            requested_model="claude-opus-4-8",
            reported_model="claude-opus-4-8",
            runtime_id="session-test",
            completion_observed=True,
            usage_observed=True,
            command_sha256=_sha256("claude"),
        ),
    )


def _hash_from_prompt(prompt: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}: ([0-9a-f]{{64}})$", prompt, re.MULTILINE)
    assert match is not None
    return match.group(1)


def _valid_payload(prompt: str, issues: list[dict[str, object]] | None = None) -> str:
    return json.dumps(
        {
            "source_sha256": _hash_from_prompt(prompt, "Source SHA-256"),
            "translation_sha256": _hash_from_prompt(prompt, "Translation SHA-256"),
            "model_id": "claude-opus-4-8",
            "issues": issues or [],
        },
        ensure_ascii=False,
    )


def test_reviews_aligned_chunks_with_opus_and_accepted_glossary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, translation, output, glossary = _prepare_repo(tmp_path)
    prompts: list[str] = []

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        assert model == "claude-opus-4-8"
        assert repo_root == repo
        prompts.append(prompt)
        return _result(output_path, _valid_payload(prompt))

    monkeypatch.setattr("scripts.review_file.run_model", fake_run_model)

    manifest = review_file(
        source,
        translation,
        glossary,
        output,
        "claude-opus-4-8",
        repo,
        40_000,
    )

    assert len(manifest.chunks) == 2
    assert len(prompts) == 2
    assert all("AI-агент" in prompt for prompt in prompts)
    assert all("НЕ-ПЕРЕДАВАТЬ" not in prompt for prompt in prompts)
    stored = json.loads(output.read_text(encoding="utf-8"))
    assert stored["model_id"] == "claude-opus-4-8"
    assert len(stored["chunks"]) == 2


def test_rejects_non_opus_model_and_output_outside_reviews(tmp_path: Path) -> None:
    repo, source, translation, _, glossary = _prepare_repo(tmp_path)

    with pytest.raises(ReviewError, match="claude-opus-4-8"):
        review_file(
            source,
            translation,
            glossary,
            repo / ".tmp/reviews/out.json",
            "gpt-5.6-sol",
            repo,
            40_000,
        )

    with pytest.raises(ReviewError, match=r"\.tmp/reviews"):
        review_file(
            source,
            translation,
            glossary,
            repo / "tracked-review.json",
            "claude-opus-4-8",
            repo,
            40_000,
        )


def test_rejects_source_translation_chunk_shape_mismatch(tmp_path: Path) -> None:
    repo, source, translation, output, glossary = _prepare_repo(tmp_path)
    translation.write_text(
        f"{TRANSLATION_NOTICE}\n\nТекст без заголовков.\n",
        encoding="utf-8",
    )

    with pytest.raises(ReviewError, match="структурно не выровнены"):
        review_file(
            source,
            translation,
            glossary,
            output,
            "claude-opus-4-8",
            repo,
            40_000,
        )


def test_rejects_unknown_json_property(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, translation, output, glossary = _prepare_repo(tmp_path)

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        payload = json.loads(_valid_payload(prompt))
        payload["unexpected"] = True
        return _result(output_path, json.dumps(payload))

    monkeypatch.setattr("scripts.review_file.run_model", fake_run_model)

    with pytest.raises(ReviewError, match="JSON Schema"):
        review_file(
            source,
            translation,
            glossary,
            output,
            "claude-opus-4-8",
            repo,
            40_000,
        )


def test_rejects_response_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, translation, output, glossary = _prepare_repo(tmp_path)

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        payload = json.loads(_valid_payload(prompt))
        payload["source_sha256"] = "0" * 64
        return _result(output_path, json.dumps(payload))

    monkeypatch.setattr("scripts.review_file.run_model", fake_run_model)

    with pytest.raises(ReviewError, match="source_sha256"):
        review_file(
            source,
            translation,
            glossary,
            output,
            "claude-opus-4-8",
            repo,
            40_000,
        )


def test_rejects_issue_line_range_outside_chunk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, translation, output, glossary = _prepare_repo(tmp_path)

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        issue: dict[str, object] = {
            "category": "semantic",
            "severity": "major",
            "source_start_line": 999,
            "source_end_line": 999,
            "target_start_line": 3,
            "target_end_line": 3,
            "evidence": "Диапазон намеренно неверен",
            "proposed_replacement": "Исправление",
        }
        return _result(output_path, _valid_payload(prompt, [issue]))

    monkeypatch.setattr("scripts.review_file.run_model", fake_run_model)

    with pytest.raises(ReviewError, match="line range"):
        review_file(
            source,
            translation,
            glossary,
            output,
            "claude-opus-4-8",
            repo,
            40_000,
        )
