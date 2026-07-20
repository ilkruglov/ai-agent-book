from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

ModelName = Literal["gpt-5.6-sol", "claude-opus-4-8"]


@dataclass(frozen=True)
class ModelSpec:
    name: ModelName
    executable: str


@dataclass(frozen=True)
class RuntimeEvidence:
    requested_model: ModelName
    reported_model: str
    runtime_id: str
    completion_observed: bool
    usage_observed: bool
    command_sha256: str


@dataclass(frozen=True)
class ModelResult:
    model: ModelName
    command: tuple[str, ...]
    output_path: Path
    response: str
    prompt_sha256: str
    response_sha256: str
    stdout_sha256: str
    stderr_sha256: str
    evidence: RuntimeEvidence


class ModelRunError(RuntimeError):
    """Exact model runtime не смог вернуть проверяемый результат."""


MODEL_SPECS: dict[ModelName, ModelSpec] = {
    "gpt-5.6-sol": ModelSpec(name="gpt-5.6-sol", executable="codex"),
    "claude-opus-4-8": ModelSpec(name="claude-opus-4-8", executable="claude"),
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validated_output(repo_root: Path, output_path: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    output = output_path.resolve()
    temporary_root = (root / ".tmp").resolve()
    if output == temporary_root or not output.is_relative_to(temporary_root):
        raise ValueError(f"Model output должен находиться внутри {temporary_root}")
    return root, output


def build_command(
    model: ModelName,
    repo_root: Path,
    output_path: Path,
) -> tuple[str, ...]:
    if model not in MODEL_SPECS:
        raise ValueError(f"Неподдерживаемая модель: {model}")
    root, output = _validated_output(repo_root, output_path)
    if model == "gpt-5.6-sol":
        return (
            "codex",
            "exec",
            "-m",
            "gpt-5.6-sol",
            "-s",
            "read-only",
            "-C",
            str(root),
            "--ephemeral",
            "--ignore-user-config",
            "--json",
            "-o",
            str(output),
            "-",
        )
    return (
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


def _json_mapping(text: str, context: str) -> dict[str, object]:
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError as error:
        raise ModelRunError(f"{context}: runtime вернул некорректный JSON") from error
    if not isinstance(raw, dict):
        raise ModelRunError(f"{context}: runtime JSON должен быть object")
    return cast(dict[str, object], raw)


def _codex_evidence(
    stdout: str,
) -> tuple[str, str, bool, bool]:
    reported_model = ""
    runtime_id = ""
    completion_observed = False
    usage_observed = False
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        event = _json_mapping(line, f"Codex JSONL line {line_number}")
        event_type = event.get("type")
        if event_type == "thread.started" and isinstance(event.get("thread_id"), str):
            runtime_id = cast(str, event["thread_id"])
        if event_type == "turn.completed":
            completion_observed = True
        model = event.get("model")
        if isinstance(model, str):
            reported_model = model
        usage = event.get("usage")
        if isinstance(usage, dict) and usage:
            usage_observed = True
    return reported_model, runtime_id, completion_observed, usage_observed


def _claude_result(
    stdout: str,
) -> tuple[str, str, str, bool, bool]:
    payload = _json_mapping(stdout, "Claude JSON")
    completion_observed = (
        payload.get("type") == "result"
        and payload.get("subtype") == "success"
        and payload.get("is_error") is False
    )
    usage = payload.get("usage")
    usage_observed = False
    if isinstance(usage, dict):
        usage_observed = len(cast(dict[object, object], usage)) > 0
    response = payload.get("result")
    if not isinstance(response, str):
        raise ModelRunError("Claude JSON не содержит строковое поле result")

    reported_model = ""
    direct_model = payload.get("model")
    if isinstance(direct_model, str):
        reported_model = direct_model
    model_usage = payload.get("modelUsage")
    if isinstance(model_usage, dict):
        model_usage_mapping = cast(dict[object, object], model_usage)
        if "claude-opus-4-8" in model_usage_mapping:
            reported_model = "claude-opus-4-8"
        elif len(model_usage_mapping) == 1:
            only_key = next(iter(model_usage_mapping))
            if isinstance(only_key, str):
                reported_model = only_key

    runtime_id = ""
    for key in ("session_id", "uuid"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            runtime_id = value
            break
    return response, reported_model, runtime_id, completion_observed, usage_observed


def _validated_evidence(
    model: ModelName,
    reported_model: str,
    runtime_id: str,
    completion_observed: bool,
    usage_observed: bool,
    command: tuple[str, ...],
) -> RuntimeEvidence:
    if not completion_observed or not usage_observed:
        raise ModelRunError("Runtime не предоставил completion/usage evidence")
    if not runtime_id:
        raise ModelRunError("Runtime не предоставил completion/session ID")
    if not reported_model:
        raise ModelRunError("Runtime не сообщил model ID")
    if reported_model != model:
        raise ModelRunError(
            f"Runtime вернул model ID {reported_model!r}, ожидался exact ID {model!r}"
        )
    return RuntimeEvidence(
        requested_model=model,
        reported_model=reported_model,
        runtime_id=runtime_id,
        completion_observed=completion_observed,
        usage_observed=usage_observed,
        command_sha256=_sha256("\0".join(command)),
    )


def run_model(
    model: ModelName,
    prompt: str,
    repo_root: Path,
    output_path: Path,
    timeout_seconds: int,
) -> ModelResult:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds должен быть положительным")
    root, output = _validated_output(repo_root, output_path)
    command = build_command(model, root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    try:
        completed = subprocess.run(
            command,
            cwd=root,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as error:
        raise ModelRunError(f"Runtime executable не найден: {command[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise ModelRunError(
            f"Exact model {model} превысил timeout {timeout_seconds} секунд"
        ) from error

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "без diagnostics"
        raise ModelRunError(
            f"Exact model {model} завершился с кодом {completed.returncode}: {detail}"
        )

    if model == "gpt-5.6-sol":
        reported_model, runtime_id, completion, usage = _codex_evidence(completed.stdout)
        if not output.is_file():
            raise ModelRunError("Codex runtime не создал output file")
        response = output.read_text(encoding="utf-8")
    else:
        response, reported_model, runtime_id, completion, usage = _claude_result(completed.stdout)
        output.write_text(response, encoding="utf-8")

    if not response.strip():
        raise ModelRunError(f"Exact model {model} вернул пустой response")
    evidence = _validated_evidence(
        model,
        reported_model,
        runtime_id,
        completion,
        usage,
        command,
    )
    return ModelResult(
        model=model,
        command=command,
        output_path=output,
        response=response,
        prompt_sha256=_sha256(prompt),
        response_sha256=_sha256(response),
        stdout_sha256=_sha256(completed.stdout),
        stderr_sha256=_sha256(completed.stderr),
        evidence=evidence,
    )
