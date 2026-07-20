from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from scripts.model_runner import (
    ModelName,
    ModelRunError,
    build_command,
    run_model,
)


def test_builds_exact_codex_command(tmp_path: Path) -> None:
    output = tmp_path / ".tmp/result.md"

    command = build_command("gpt-5.6-sol", tmp_path, output)

    assert command == (
        "codex",
        "exec",
        "-m",
        "gpt-5.6-sol",
        "-s",
        "read-only",
        "-C",
        str(tmp_path.resolve()),
        "--ephemeral",
        "--ignore-user-config",
        "--json",
        "-o",
        str(output.resolve()),
        "-",
    )


def test_builds_exact_claude_command(tmp_path: Path) -> None:
    output = tmp_path / ".tmp/result.md"

    command = build_command("claude-opus-4-8", tmp_path, output)

    assert command == (
        "claude",
        "-p",
        "--model",
        "claude-opus-4-8",
        "--safe-mode",
        "--no-session-persistence",
        "--tools",
        "",
        "--permission-mode",
        "dontAsk",
        "--output-format",
        "json",
    )


def test_rejects_unknown_model_and_output_outside_tmp(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Неподдерживаемая модель"):
        build_command(cast(ModelName, "other-model"), tmp_path, tmp_path / ".tmp/out")

    with pytest.raises(ValueError, match=r"внутри.*\.tmp"):
        build_command("gpt-5.6-sol", tmp_path, tmp_path / "tracked.md")


def test_codex_result_requires_completion_usage_and_exact_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / ".tmp/codex.md"

    def fake_run(
        args: Sequence[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        assert kwargs["input"] == "Переведи"
        output.write_text("Русский текст", encoding="utf-8")
        stdout = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "model": "gpt-5.6-sol",
                        "usage": {"input_tokens": 10, "output_tokens": 3},
                    }
                ),
            ]
        )
        return subprocess.CompletedProcess(list(args), 0, stdout, "")

    monkeypatch.setattr("scripts.model_runner.subprocess.run", fake_run)

    result = run_model("gpt-5.6-sol", "Переведи", tmp_path, output, 60)

    assert result.response == "Русский текст"
    assert result.response_sha256 == hashlib.sha256("Русский текст".encode()).hexdigest()
    assert result.prompt_sha256 == hashlib.sha256("Переведи".encode()).hexdigest()
    assert result.evidence.requested_model == "gpt-5.6-sol"
    assert result.evidence.reported_model == "gpt-5.6-sol"
    assert result.evidence.completion_observed is True
    assert result.evidence.usage_observed is True
    assert result.evidence.runtime_id == "thread-1"


def test_claude_json_result_is_written_to_tmp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / ".tmp/claude.txt"
    payload: dict[str, object] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "duration_ms": 50,
        "duration_api_ms": 40,
        "num_turns": 1,
        "result": "Замечаний нет",
        "session_id": "session-1",
        "total_cost_usd": 0.01,
        "usage": {"input_tokens": 20, "output_tokens": 4},
        "modelUsage": {
            "claude-opus-4-8": {
                "inputTokens": 20,
                "outputTokens": 4,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
                "webSearchRequests": 0,
                "costUSD": 0.01,
                "contextWindow": 1_000_000,
                "maxOutputTokens": 32_000,
            }
        },
        "permission_denials": [],
        "uuid": "result-1",
    }

    def fake_run(
        args: Sequence[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(list(args), 0, json.dumps(payload), "")

    monkeypatch.setattr("scripts.model_runner.subprocess.run", fake_run)

    result = run_model("claude-opus-4-8", "Проверь", tmp_path, output, 60)

    assert output.read_text(encoding="utf-8") == "Замечаний нет"
    assert result.response == "Замечаний нет"
    assert result.evidence.reported_model == "claude-opus-4-8"
    assert result.evidence.runtime_id == "session-1"


def test_nonzero_exit_is_fatal_and_never_retries_with_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: Sequence[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(tuple(args))
        return subprocess.CompletedProcess(list(args), 7, "", "runtime unavailable")

    monkeypatch.setattr("scripts.model_runner.subprocess.run", fake_run)

    with pytest.raises(ModelRunError, match="кодом 7"):
        run_model(
            "gpt-5.6-sol",
            "Переведи",
            tmp_path,
            tmp_path / ".tmp/failure.md",
            60,
        )

    assert len(calls) == 1
    assert "gpt-5.6-sol" in calls[0]
    assert "claude-opus-4-8" not in calls[0]


def test_mismatched_runtime_model_is_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / ".tmp/codex.md"

    def fake_run(
        args: Sequence[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        output.write_text("Текст", encoding="utf-8")
        stdout = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "model": "gpt-5.5",
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                    }
                ),
            ]
        )
        return subprocess.CompletedProcess(list(args), 0, stdout, "")

    monkeypatch.setattr("scripts.model_runner.subprocess.run", fake_run)

    with pytest.raises(ModelRunError, match="вернул model ID"):
        run_model("gpt-5.6-sol", "Переведи", tmp_path, output, 60)


def test_missing_runtime_completion_or_usage_is_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / ".tmp/codex.md"

    def fake_run(
        args: Sequence[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        output.write_text("Текст", encoding="utf-8")
        stdout = json.dumps({"type": "thread.started", "thread_id": "thread-1"})
        return subprocess.CompletedProcess(list(args), 0, stdout, "")

    monkeypatch.setattr("scripts.model_runner.subprocess.run", fake_run)

    with pytest.raises(ModelRunError, match="completion/usage evidence"):
        run_model("gpt-5.6-sol", "Переведи", tmp_path, output, 60)
