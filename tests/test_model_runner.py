from __future__ import annotations

import hashlib
import json
from collections import deque
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

from scripts.model_runner import (
    JsonObject,
    ModelName,
    ModelResult,
    ModelRunError,
    RuntimeEvidence,
    build_command,
    build_thread_start_request,
    run_model,
    run_smoke,
)


class FakeJsonRpcStream:
    def __init__(self, messages: list[JsonObject], stderr_text: str = "") -> None:
        self._messages = deque(messages)
        self.sent: list[JsonObject] = []
        self.closed = False
        self.stdout_text = "\n".join(
            json.dumps(message, ensure_ascii=False) for message in messages
        )
        self.stderr_text = stderr_text

    def send(self, message: Mapping[str, object]) -> None:
        self.sent.append(dict(message))

    def receive(self, timeout_seconds: float) -> JsonObject:
        if not self._messages:
            raise TimeoutError(f"no message within {timeout_seconds}")
        return self._messages.popleft()

    def close(self) -> None:
        self.closed = True


def _valid_messages(repo_root: Path, response: str = "Русский текст") -> list[JsonObject]:
    return [
        {"id": 1, "result": {"serverInfo": {"name": "codex", "version": "0.144.6"}}},
        {
            "id": 2,
            "result": {
                "thread": {
                    "id": "thread-1",
                    "ephemeral": True,
                    "modelProvider": "openai",
                },
                "model": "gpt-5.6-sol",
                "modelProvider": "openai",
                "cwd": str(repo_root.resolve()),
                "approvalPolicy": "never",
                "approvalsReviewer": "user",
                "sandbox": {"type": "readOnly", "networkAccess": False},
                "activePermissionProfile": {"id": ":read-only"},
            },
        },
        {
            "id": 3,
            "result": {"turn": {"id": "turn-1", "status": "inProgress", "items": []}},
        },
        {
            "method": "item/completed",
            "params": {
                "threadId": "thread-1",
                "turnId": "turn-1",
                "completedAtMs": 1,
                "item": {
                    "id": "message-1",
                    "type": "agentMessage",
                    "phase": "final_answer",
                    "text": response,
                },
            },
        },
        {
            "method": "thread/tokenUsage/updated",
            "params": {
                "threadId": "thread-1",
                "turnId": "turn-1",
                "tokenUsage": {
                    "last": {
                        "inputTokens": 10,
                        "cachedInputTokens": 0,
                        "outputTokens": 3,
                        "reasoningOutputTokens": 1,
                        "totalTokens": 13,
                    },
                    "total": {
                        "inputTokens": 10,
                        "cachedInputTokens": 0,
                        "outputTokens": 3,
                        "reasoningOutputTokens": 1,
                        "totalTokens": 13,
                    },
                },
            },
        },
        {
            "method": "turn/completed",
            "params": {
                "threadId": "thread-1",
                "turn": {"id": "turn-1", "status": "completed", "items": []},
            },
        },
    ]


def _patch_stream(
    monkeypatch: pytest.MonkeyPatch,
    stream: FakeJsonRpcStream,
) -> None:
    def fake_open_transport(command: tuple[str, ...], cwd: Path) -> FakeJsonRpcStream:
        assert command == build_command()
        assert cwd.is_absolute()
        return stream

    monkeypatch.setattr("scripts.model_runner._open_transport", fake_open_transport)


def _set_nested(message: JsonObject, path: tuple[str, ...], value: object) -> None:
    current: JsonObject = message
    for key in path[:-1]:
        nested = current[key]
        assert isinstance(nested, dict)
        current = cast(JsonObject, nested)
    current[path[-1]] = value


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_builds_exact_app_server_command() -> None:
    assert build_command() == (
        "codex",
        "app-server",
        "--stdio",
        "-c",
        "mcp_servers={}",
    )


def test_thread_start_disables_fallback_and_is_ephemeral(tmp_path: Path) -> None:
    request = build_thread_start_request(tmp_path)

    assert request["id"] == 2
    assert request["method"] == "thread/start"
    params = request["params"]
    assert isinstance(params, dict)
    assert params["model"] == "gpt-5.6-sol"
    assert params["allowProviderModelFallback"] is False
    assert params["ephemeral"] is True
    assert params["permissions"] == ":read-only"
    assert params["approvalPolicy"] == "never"
    assert params["cwd"] == str(tmp_path.resolve())
    assert params["dynamicTools"] == []


def test_runs_json_rpc_lifecycle_and_records_exact_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = FakeJsonRpcStream(_valid_messages(tmp_path))
    _patch_stream(monkeypatch, stream)
    output = tmp_path / ".tmp/result.md"

    result = run_model("gpt-5.6-sol", "Переведи", tmp_path, output, 60)

    assert result.response == "Русский текст"
    assert output.read_text(encoding="utf-8") == "Русский текст"
    assert result.response_sha256 == _sha256("Русский текст")
    assert result.prompt_sha256 == _sha256("Переведи")
    assert result.evidence == RuntimeEvidence(
        requested_model="gpt-5.6-sol",
        reported_model="gpt-5.6-sol",
        provider="openai",
        thread_id="thread-1",
        turn_id="turn-1",
        ephemeral=True,
        fallback_allowed=False,
        sandbox_type="readOnly",
        completion_observed=True,
        usage_observed=True,
        command_sha256=_sha256("\0".join(build_command())),
    )
    assert [message.get("method") for message in stream.sent] == [
        "initialize",
        "initialized",
        "thread/start",
        "turn/start",
    ]
    assert stream.closed is True


def test_passes_output_schema_to_turn_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = FakeJsonRpcStream(_valid_messages(tmp_path, response='{"ok":true}'))
    _patch_stream(monkeypatch, stream)
    schema: JsonObject = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ok"],
        "properties": {"ok": {"type": "boolean"}},
    }

    run_model(
        "gpt-5.6-sol",
        "Верни JSON",
        tmp_path,
        tmp_path / ".tmp/result.json",
        60,
        output_schema=schema,
    )

    turn_start = stream.sent[-1]
    params = turn_start["params"]
    assert isinstance(params, dict)
    assert params["outputSchema"] == schema


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("result", "model"), "gpt-5.5", "effective model"),
        (("result", "modelProvider"), "other", "provider"),
        (("result", "thread", "ephemeral"), False, "ephemeral"),
        (("result", "sandbox", "type"), "workspaceWrite", "read-only"),
        (("result", "activePermissionProfile", "id"), ":workspace", "read-only"),
    ],
)
def test_rejects_invalid_thread_start_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    value: object,
    message: str,
) -> None:
    messages = _valid_messages(tmp_path)
    _set_nested(messages[1], path, value)
    stream = FakeJsonRpcStream(messages)
    _patch_stream(monkeypatch, stream)

    with pytest.raises(ModelRunError, match=message):
        run_model("gpt-5.6-sol", "nonce", tmp_path, tmp_path / ".tmp/out.txt", 60)

    assert stream.closed is True


@pytest.mark.parametrize(
    ("drop_method", "message"),
    [
        ("thread/tokenUsage/updated", "usage evidence"),
        ("item/completed", "final agent message"),
    ],
)
def test_rejects_incomplete_event_stream(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drop_method: str,
    message: str,
) -> None:
    messages = [item for item in _valid_messages(tmp_path) if item.get("method") != drop_method]
    stream = FakeJsonRpcStream(messages)
    _patch_stream(monkeypatch, stream)

    with pytest.raises(ModelRunError, match=message):
        run_model("gpt-5.6-sol", "nonce", tmp_path, tmp_path / ".tmp/out.txt", 60)


def test_rejects_failed_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _valid_messages(tmp_path)
    messages[-1] = {
        "method": "turn/completed",
        "params": {
            "threadId": "thread-1",
            "turn": {
                "id": "turn-1",
                "status": "failed",
                "items": [],
                "error": {"message": "provider unavailable"},
            },
        },
    }
    _patch_stream(monkeypatch, FakeJsonRpcStream(messages))

    with pytest.raises(ModelRunError, match="provider unavailable"):
        run_model("gpt-5.6-sol", "nonce", tmp_path, tmp_path / ".tmp/out.txt", 60)


def test_rejects_timeout_unknown_model_and_unsafe_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_stream(monkeypatch, FakeJsonRpcStream([]))

    with pytest.raises(ModelRunError, match="timeout"):
        run_model("gpt-5.6-sol", "nonce", tmp_path, tmp_path / ".tmp/out.txt", 1)
    with pytest.raises(ValueError, match="Неподдерживаемая модель"):
        run_model(cast(ModelName, "other"), "nonce", tmp_path, tmp_path / ".tmp/out.txt", 1)
    with pytest.raises(ValueError, match=r"внутри.*\.tmp"):
        run_model("gpt-5.6-sol", "nonce", tmp_path, tmp_path / "tracked.txt", 1)

    existing = tmp_path / ".tmp/existing.txt"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("partial", encoding="utf-8")
    with pytest.raises(ModelRunError, match="уже существует"):
        run_model("gpt-5.6-sol", "nonce", tmp_path, existing, 1)


def test_smoke_writes_fail_closed_runtime_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_model(
        model: ModelName,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        nonce = prompt.rsplit(" ", maxsplit=1)[-1]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(nonce, encoding="utf-8")
        evidence = RuntimeEvidence(
            requested_model=model,
            reported_model=model,
            provider="openai",
            thread_id="thread-smoke",
            turn_id="turn-smoke",
            ephemeral=True,
            fallback_allowed=False,
            sandbox_type="readOnly",
            completion_observed=True,
            usage_observed=True,
            command_sha256=_sha256("command"),
        )
        return ModelResult(
            model=model,
            command=build_command(),
            output_path=output_path,
            response=nonce,
            prompt_sha256=_sha256(prompt),
            response_sha256=_sha256(nonce),
            stdout_sha256=_sha256("stdout"),
            stderr_sha256=_sha256(""),
            evidence=evidence,
        )

    monkeypatch.setattr("scripts.model_runner.run_model", fake_run_model)

    def fake_token_hex(_length: int) -> str:
        return "abc123"

    monkeypatch.setattr("scripts.model_runner.secrets.token_hex", fake_token_hex)
    record_path = tmp_path / ".tmp/model-smoke.json"

    record = run_smoke(tmp_path, record_path, 60)

    assert json.loads(record_path.read_text(encoding="utf-8")) == record
    assert record["schema_version"] == 1
    assert record["model_id"] == "gpt-5.6-sol"
    assert record["nonce_sha256"] == _sha256("abc123")
    assert record["runtime"] == {
        "reported_model": "gpt-5.6-sol",
        "provider": "openai",
        "ephemeral": True,
        "fallback_allowed": False,
        "completion_observed": True,
        "usage_observed": True,
    }


def test_smoke_rejects_non_exact_echo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_model(
        model: ModelName,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
    ) -> ModelResult:
        raise ModelRunError("nonce mismatch")

    monkeypatch.setattr("scripts.model_runner.run_model", fake_run_model)

    with pytest.raises(ModelRunError, match="nonce mismatch"):
        run_smoke(tmp_path, tmp_path / ".tmp/model-smoke.json", 60)
