from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.model_runner import ModelResult, RuntimeEvidence
from scripts.translate_file import TranslationError, translate_file

SOURCE = """## 第一节
原文一。

## 第二节
原文二。
"""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _prepare_repo(tmp_path: Path, approved: bool = True) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    source = repo / ".tmp/upstream/book/chapter.md"
    output = repo / ".tmp/drafts/chapter.md"
    glossary = repo / "glossary.yml"
    source.parent.mkdir(parents=True)
    (repo / "prompts").mkdir()
    (repo / "evals").mkdir()
    source.write_text(SOURCE, encoding="utf-8")
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
    (repo / "prompts/translate.txt").write_text(
        "PATH={{SOURCE_PATH}}\nLINES={{START_LINE}}-{{END_LINE}}\n"
        "HASH={{SOURCE_SHA256}}\nGLOSSARY:\n{{GLOSSARY}}\nSOURCE:\n{{SOURCE}}",
        encoding="utf-8",
    )
    benchmark = {
        "primary_model": "gpt-5.6-sol",
        "gate": {"blocked": False},
        "decision": {"approved_primary": approved},
    }
    (repo / "evals/translation-benchmark.json").write_text(
        json.dumps(benchmark),
        encoding="utf-8",
    )
    return repo, source, output, glossary


def _result(output_path: Path, response: str) -> ModelResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response, encoding="utf-8")
    return ModelResult(
        model="gpt-5.6-sol",
        command=("codex",),
        output_path=output_path,
        response=response,
        prompt_sha256=_sha256("prompt"),
        response_sha256=_sha256(response),
        stdout_sha256=_sha256("stdout"),
        stderr_sha256=_sha256(""),
        evidence=RuntimeEvidence(
            requested_model="gpt-5.6-sol",
            reported_model="gpt-5.6-sol",
            runtime_id="thread-test",
            completion_observed=True,
            usage_observed=True,
            command_sha256=_sha256("codex"),
        ),
    )


def test_translates_lossless_chunks_with_same_accepted_glossary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, output, glossary = _prepare_repo(tmp_path)
    responses: Iterator[str] = iter(
        ["## Первый раздел\nРусский текст.\n\n", "## Второй раздел\nЕщё текст.\n"]
    )
    prompts: list[str] = []

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        assert model == "gpt-5.6-sol"
        assert repo_root == repo
        assert timeout_seconds == 3_600
        prompts.append(prompt)
        return _result(output_path, next(responses))

    monkeypatch.setattr("scripts.translate_file.run_model", fake_run_model)

    manifest = translate_file(source, output, glossary, "gpt-5.6-sol", repo, 40_000)

    draft = output.read_text(encoding="utf-8")
    assert draft.startswith("<!-- Русский перевод: community edition.")
    assert "## Первый раздел" in draft
    assert "## Второй раздел" in draft
    assert len(prompts) == 2
    assert all("AI-агент" in prompt for prompt in prompts)
    assert all("НЕ-ПЕРЕДАВАТЬ" not in prompt for prompt in prompts)
    assert prompts[0] != prompts[1]
    assert manifest.source_sha256 == _sha256(SOURCE)
    assert manifest.draft_sha256 == _sha256(draft)
    assert [chunk.index for chunk in manifest.chunks] == ["000", "001"]


def test_rejects_source_outside_pinned_upstream(tmp_path: Path) -> None:
    repo, _, output, glossary = _prepare_repo(tmp_path)
    outside = repo / "tracked-source.md"
    outside.write_text(SOURCE, encoding="utf-8")

    with pytest.raises(TranslationError, match=r"\.tmp/upstream/book"):
        translate_file(outside, output, glossary, "gpt-5.6-sol", repo, 40_000)


def test_rejects_output_outside_drafts(tmp_path: Path) -> None:
    repo, source, _, glossary = _prepare_repo(tmp_path)

    with pytest.raises(TranslationError, match=r"\.tmp/drafts"):
        translate_file(
            source,
            repo / "book/chapter.md",
            glossary,
            "gpt-5.6-sol",
            repo,
            40_000,
        )


def test_refuses_translation_before_approved_benchmark(tmp_path: Path) -> None:
    repo, source, output, glossary = _prepare_repo(tmp_path, approved=False)

    with pytest.raises(TranslationError, match="benchmark gate"):
        translate_file(source, output, glossary, "gpt-5.6-sol", repo, 40_000)


def test_rejects_editor_model_for_primary_translation(tmp_path: Path) -> None:
    repo, source, output, glossary = _prepare_repo(tmp_path)

    with pytest.raises(TranslationError, match="gpt-5.6-sol"):
        translate_file(source, output, glossary, "claude-opus-4-8", repo, 40_000)


def test_rejects_extra_outer_markdown_fence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, output, glossary = _prepare_repo(tmp_path)

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        response = "```markdown\n## Раздел\nТекст\n```\n"
        return _result(output_path, response)

    monkeypatch.setattr("scripts.translate_file.run_model", fake_run_model)

    with pytest.raises(TranslationError, match="внешний Markdown fence"):
        translate_file(source, output, glossary, "gpt-5.6-sol", repo, 40_000)


def test_rejects_assembled_draft_with_changed_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, source, output, glossary = _prepare_repo(tmp_path)
    responses: Iterator[str] = iter(["Без заголовка.\n", "Тоже без заголовка.\n"])

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        return _result(output_path, next(responses))

    monkeypatch.setattr("scripts.translate_file.run_model", fake_run_model)

    with pytest.raises(TranslationError, match="heading-structure"):
        translate_file(source, output, glossary, "gpt-5.6-sol", repo, 40_000)
