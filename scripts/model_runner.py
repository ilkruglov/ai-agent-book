from __future__ import annotations

import argparse
import hashlib
import json
import queue
import re
import secrets
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TextIO, cast

type JsonObject = dict[str, object]
type ModelName = Literal["gpt-5.6-sol"]

EXACT_MODEL: ModelName = "gpt-5.6-sol"
EXPECTED_PROVIDER = "openai"
READ_ONLY_PROFILE = ":read-only"
TRANSIENT_RECONNECT_RE = re.compile(r"Reconnecting\.\.\. [1-5]/5")


@dataclass(frozen=True)
class RuntimeEvidence:
    requested_model: ModelName
    reported_model: str
    provider: str
    thread_id: str
    turn_id: str
    ephemeral: bool
    fallback_allowed: bool
    sandbox_type: str
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


class JsonRpcTransport(Protocol):
    @property
    def stdout_text(self) -> str: ...

    @property
    def stderr_text(self) -> str: ...

    def send(self, message: Mapping[str, object]) -> None: ...

    def receive(self, timeout_seconds: float) -> JsonObject: ...

    def close(self) -> None: ...


class _StdioJsonRpcTransport:
    def __init__(self, command: tuple[str, ...], cwd: Path) -> None:
        try:
            self._process = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="strict",
                bufsize=1,
            )
        except FileNotFoundError as error:
            raise ModelRunError(f"Runtime executable не найден: {command[0]}") from error
        if (
            self._process.stdin is None
            or self._process.stdout is None
            or self._process.stderr is None
        ):
            self._process.kill()
            raise ModelRunError("app-server не предоставил stdio pipes")

        self._stdin = self._process.stdin
        self._stdout_queue: queue.Queue[str | None] = queue.Queue()
        self._stdout_lines: list[str] = []
        self._stderr_lines: list[str] = []
        self._stdout_thread = threading.Thread(
            target=self._drain_stdout,
            args=(self._process.stdout,),
            daemon=True,
            name="codex-app-server-stdout",
        )
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(self._process.stderr,),
            daemon=True,
            name="codex-app-server-stderr",
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

    @property
    def stdout_text(self) -> str:
        return "".join(self._stdout_lines)

    @property
    def stderr_text(self) -> str:
        return "".join(self._stderr_lines)

    def _drain_stdout(self, stream: TextIO) -> None:
        try:
            for line in stream:
                self._stdout_lines.append(line)
                self._stdout_queue.put(line.rstrip("\r\n"))
        finally:
            self._stdout_queue.put(None)

    def _drain_stderr(self, stream: TextIO) -> None:
        for line in stream:
            self._stderr_lines.append(line)

    def send(self, message: Mapping[str, object]) -> None:
        if self._process.poll() is not None:
            detail = self.stderr_text.strip() or "без diagnostics"
            raise ModelRunError(f"app-server завершился до отправки запроса: {detail}")
        payload = json.dumps(dict(message), ensure_ascii=False, separators=(",", ":"))
        try:
            self._stdin.write(f"{payload}\n")
            self._stdin.flush()
        except BrokenPipeError as error:
            detail = self.stderr_text.strip() or "без diagnostics"
            raise ModelRunError(f"app-server закрыл stdin: {detail}") from error

    def receive(self, timeout_seconds: float) -> JsonObject:
        if timeout_seconds <= 0:
            raise TimeoutError("app-server timeout")
        try:
            line = self._stdout_queue.get(timeout=timeout_seconds)
        except queue.Empty as error:
            raise TimeoutError("app-server timeout") from error
        if line is None:
            detail = self.stderr_text.strip() or "без diagnostics"
            code = self._process.poll()
            raise ModelRunError(f"app-server закрыл stdout, exit={code}: {detail}")
        try:
            raw: object = json.loads(line)
        except json.JSONDecodeError as error:
            raise ModelRunError("app-server вернул некорректный JSONL") from error
        return _as_mapping(raw, "app-server message")

    def close(self) -> None:
        try:
            self._stdin.close()
        except OSError:
            pass
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._stdout_thread.join(timeout=1)
        self._stderr_thread.join(timeout=1)


def _open_transport(command: tuple[str, ...], cwd: Path) -> JsonRpcTransport:
    return _StdioJsonRpcTransport(command, cwd)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_mapping(value: object, context: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ModelRunError(f"{context} должен быть JSON object")
    return cast(JsonObject, value)


def _required_string(document: JsonObject, key: str, context: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value:
        raise ModelRunError(f"{context} не содержит строковое поле {key}")
    return value


def _validated_output(repo_root: Path, output_path: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    output = output_path.resolve()
    temporary_root = (root / ".tmp").resolve()
    if output == temporary_root or not output.is_relative_to(temporary_root):
        raise ValueError(f"Model output должен находиться внутри {temporary_root}")
    return root, output


def build_command() -> tuple[str, ...]:
    return (
        "codex",
        "app-server",
        "--stdio",
        "-c",
        "mcp_servers={}",
    )


def _build_initialize_request() -> JsonObject:
    return {
        "id": 1,
        "method": "initialize",
        "params": {
            "clientInfo": {
                "name": "ai-agent-book-ru",
                "title": "Russian AI Agent Book translation pipeline",
                "version": "0.1.0",
            },
            "capabilities": {"experimentalApi": True},
        },
    }


def build_thread_start_request(repo_root: Path) -> JsonObject:
    return {
        "id": 2,
        "method": "thread/start",
        "params": {
            "model": EXACT_MODEL,
            "modelProvider": EXPECTED_PROVIDER,
            "allowProviderModelFallback": False,
            "ephemeral": True,
            "permissions": READ_ONLY_PROFILE,
            "approvalPolicy": "never",
            "cwd": str(repo_root.resolve()),
            "baseInstructions": (
                "Perform the requested text transformation without tools. "
                "Return only the requested final payload."
            ),
            "dynamicTools": [],
            "environments": [],
        },
    }


def _build_turn_start_request(
    thread_id: str,
    prompt: str,
    output_schema: Mapping[str, object] | None = None,
) -> JsonObject:
    request: JsonObject = {
        "id": 3,
        "method": "turn/start",
        "params": {
            "threadId": thread_id,
            "model": EXACT_MODEL,
            "input": [{"type": "text", "text": prompt, "text_elements": []}],
        },
    }
    if output_schema is not None:
        params = _as_mapping(request["params"], "turn/start params")
        params["outputSchema"] = dict(output_schema)
    return request


def _remaining_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ModelRunError("app-server timeout")
    return remaining


def _error_message(error_value: object) -> str:
    if not isinstance(error_value, dict):
        return str(error_value)
    error = cast(JsonObject, error_value)
    message = error.get("message")
    return (
        message if isinstance(message, str) and message else json.dumps(error, ensure_ascii=False)
    )


def _await_response(
    transport: JsonRpcTransport,
    request_id: int,
    deadline: float,
) -> tuple[JsonObject, list[JsonObject]]:
    notifications: list[JsonObject] = []
    while True:
        try:
            message = transport.receive(_remaining_seconds(deadline))
        except TimeoutError as error:
            raise ModelRunError("app-server timeout") from error
        if message.get("id") == request_id:
            if "error" in message:
                raise ModelRunError(
                    f"app-server request {request_id}: {_error_message(message['error'])}"
                )
            return _as_mapping(
                message.get("result"), f"app-server response {request_id}"
            ), notifications
        if "id" in message:
            raise ModelRunError(f"app-server вернул неожиданный JSON-RPC id: {message.get('id')}")
        if isinstance(message.get("method"), str):
            notifications.append(message)
            continue
        raise ModelRunError("app-server вернул сообщение без id/method")


@dataclass(frozen=True)
class _ThreadStartEvidence:
    reported_model: str
    provider: str
    thread_id: str
    ephemeral: bool
    sandbox_type: str


def _validate_thread_start(result: JsonObject, repo_root: Path) -> _ThreadStartEvidence:
    reported_model = _required_string(result, "model", "thread/start response")
    if reported_model != EXACT_MODEL:
        raise ModelRunError(
            f"thread/start effective model {reported_model!r}, ожидался {EXACT_MODEL!r}"
        )
    provider = _required_string(result, "modelProvider", "thread/start response")
    if provider != EXPECTED_PROVIDER:
        raise ModelRunError(f"thread/start provider {provider!r}, ожидался {EXPECTED_PROVIDER!r}")

    returned_cwd = _required_string(result, "cwd", "thread/start response")
    if Path(returned_cwd).resolve() != repo_root.resolve():
        raise ModelRunError("thread/start вернул неожиданный cwd")
    if result.get("approvalPolicy") != "never":
        raise ModelRunError("thread/start не подтвердил approvalPolicy=never")

    thread = _as_mapping(result.get("thread"), "thread/start thread")
    thread_id = _required_string(thread, "id", "thread/start thread")
    if thread.get("ephemeral") is not True:
        raise ModelRunError("thread/start не подтвердил ephemeral thread")
    if thread.get("modelProvider") != EXPECTED_PROVIDER:
        raise ModelRunError("thread/start thread provider не совпал с openai")

    sandbox = _as_mapping(result.get("sandbox"), "thread/start sandbox")
    sandbox_type = _required_string(sandbox, "type", "thread/start sandbox")
    profile = _as_mapping(result.get("activePermissionProfile"), "active permission profile")
    if sandbox_type != "readOnly" or profile.get("id") != READ_ONLY_PROFILE:
        raise ModelRunError("thread/start не подтвердил read-only sandbox/profile")

    return _ThreadStartEvidence(
        reported_model=reported_model,
        provider=provider,
        thread_id=thread_id,
        ephemeral=True,
        sandbox_type=sandbox_type,
    )


def _turn_id(result: JsonObject) -> str:
    turn = _as_mapping(result.get("turn"), "turn/start turn")
    return _required_string(turn, "id", "turn/start turn")


@dataclass
class _TurnState:
    final_messages: list[str]
    completion_observed: bool = False
    usage_observed: bool = False


def _validate_event_ids(params: JsonObject, thread_id: str, turn_id: str) -> None:
    if params.get("threadId") != thread_id:
        raise ModelRunError("app-server event содержит неожиданный threadId")
    event_turn_id = params.get("turnId")
    if event_turn_id is not None and event_turn_id != turn_id:
        raise ModelRunError("app-server event содержит неожиданный turnId")


def _consume_notification(
    message: JsonObject,
    state: _TurnState,
    thread_id: str,
    turn_id: str,
) -> None:
    method = message.get("method")
    params = _as_mapping(message.get("params"), f"{method} params")
    if method == "item/completed":
        _validate_event_ids(params, thread_id, turn_id)
        item = _as_mapping(params.get("item"), "item/completed item")
        if item.get("type") == "agentMessage" and item.get("phase") == "final_answer":
            text = item.get("text")
            if isinstance(text, str) and text:
                state.final_messages.append(text)
        return
    if method == "thread/tokenUsage/updated":
        _validate_event_ids(params, thread_id, turn_id)
        token_usage = _as_mapping(params.get("tokenUsage"), "token usage")
        if token_usage:
            state.usage_observed = True
        return
    if method == "turn/completed":
        _validate_event_ids(params, thread_id, turn_id)
        turn = _as_mapping(params.get("turn"), "turn/completed turn")
        if turn.get("id") != turn_id:
            raise ModelRunError("turn/completed содержит неожиданный turn id")
        status = turn.get("status")
        if status != "completed":
            detail = _error_message(turn.get("error")) if turn.get("error") is not None else status
            raise ModelRunError(f"app-server turn завершился со статусом {status}: {detail}")
        state.completion_observed = True
        return
    if method == "error":
        detail = _error_message(params.get("error"))
        if TRANSIENT_RECONNECT_RE.fullmatch(detail) is not None:
            return
        raise ModelRunError(f"app-server error notification: {detail}")


def _collect_turn(
    transport: JsonRpcTransport,
    initial_notifications: list[JsonObject],
    thread_id: str,
    turn_id: str,
    deadline: float,
) -> _TurnState:
    state = _TurnState(final_messages=[])
    pending = deque(initial_notifications)
    while not state.completion_observed:
        if pending:
            message = pending.popleft()
        else:
            try:
                message = transport.receive(_remaining_seconds(deadline))
            except TimeoutError as error:
                raise ModelRunError("app-server timeout") from error
        if "id" in message:
            raise ModelRunError("app-server отправил неожиданный request/response во время turn")
        _consume_notification(message, state, thread_id, turn_id)
    if not state.final_messages:
        raise ModelRunError("app-server не вернул final agent message")
    if not state.usage_observed:
        raise ModelRunError("app-server не вернул usage evidence")
    return state


def run_model(
    model: ModelName,
    prompt: str,
    repo_root: Path,
    output_path: Path,
    timeout_seconds: int,
    *,
    output_schema: Mapping[str, object] | None = None,
) -> ModelResult:
    if model != EXACT_MODEL:
        raise ValueError(f"Неподдерживаемая модель: {model}")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds должен быть положительным")
    root, output = _validated_output(repo_root, output_path)
    if output.exists():
        raise ModelRunError(f"Model output уже существует: {output}")

    command = build_command()
    deadline = time.monotonic() + timeout_seconds
    transport = _open_transport(command, root)
    try:
        transport.send(_build_initialize_request())
        _, initialize_notifications = _await_response(transport, 1, deadline)
        transport.send({"method": "initialized"})
        transport.send(build_thread_start_request(root))
        thread_result, thread_notifications = _await_response(transport, 2, deadline)
        thread_evidence = _validate_thread_start(thread_result, root)

        transport.send(
            _build_turn_start_request(
                thread_evidence.thread_id,
                prompt,
                output_schema,
            )
        )
        turn_result, turn_notifications = _await_response(transport, 3, deadline)
        turn_id = _turn_id(turn_result)
        state = _collect_turn(
            transport,
            initialize_notifications + thread_notifications + turn_notifications,
            thread_evidence.thread_id,
            turn_id,
            deadline,
        )
    finally:
        transport.close()

    response = "".join(state.final_messages)
    if not response.strip():
        raise ModelRunError("Exact model вернул пустой response")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8", newline="") as output_file:
            output_file.write(response)
    except FileExistsError as error:
        raise ModelRunError(f"Model output уже существует: {output}") from error

    evidence = RuntimeEvidence(
        requested_model=model,
        reported_model=thread_evidence.reported_model,
        provider=thread_evidence.provider,
        thread_id=thread_evidence.thread_id,
        turn_id=turn_id,
        ephemeral=thread_evidence.ephemeral,
        fallback_allowed=False,
        sandbox_type=thread_evidence.sandbox_type,
        completion_observed=state.completion_observed,
        usage_observed=state.usage_observed,
        command_sha256=_sha256("\0".join(command)),
    )
    return ModelResult(
        model=model,
        command=command,
        output_path=output,
        response=response,
        prompt_sha256=_sha256(prompt),
        response_sha256=_sha256(response),
        stdout_sha256=_sha256(transport.stdout_text),
        stderr_sha256=_sha256(transport.stderr_text),
        evidence=evidence,
    )


def run_smoke(
    repo_root: Path,
    output_path: Path,
    timeout_seconds: int,
) -> JsonObject:
    root, output = _validated_output(repo_root, output_path)
    if output.exists():
        raise ModelRunError(f"Smoke output уже существует: {output}")
    nonce = secrets.token_hex(16)
    nonce_sha256 = _sha256(nonce)
    response_path = root / ".tmp/model-smoke" / f"{nonce_sha256}.txt"
    prompt = f"Верни ровно этот nonce без кавычек, пояснений и Markdown: {nonce}"
    result = run_model(EXACT_MODEL, prompt, root, response_path, timeout_seconds)
    if result.response.strip() != nonce:
        raise ModelRunError("Exact model не вернул nonce дословно")

    record: JsonObject = {
        "schema_version": 1,
        "model_id": EXACT_MODEL,
        "nonce_sha256": nonce_sha256,
        "runtime": {
            "reported_model": result.evidence.reported_model,
            "provider": result.evidence.provider,
            "ephemeral": result.evidence.ephemeral,
            "fallback_allowed": result.evidence.fallback_allowed,
            "completion_observed": result.evidence.completion_observed,
            "usage_observed": result.evidence.usage_observed,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8", newline="") as output_file:
            json.dump(record, output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")
    except FileExistsError as error:
        raise ModelRunError(f"Smoke output уже существует: {output}") from error
    return record


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Запустить exact GPT через Codex app-server")
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke = subparsers.add_parser("smoke", help="Проверить exact model nonce-запросом")
    smoke.add_argument("--output", required=True, type=Path)
    smoke.add_argument("--timeout-seconds", type=int, default=600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    if arguments.command != "smoke":
        raise AssertionError(f"Неизвестная команда: {arguments.command}")
    try:
        run_smoke(
            repo_root,
            cast(Path, arguments.output),
            cast(int, arguments.timeout_seconds),
        )
    except (OSError, ValueError, ModelRunError) as error:
        print(f"model-run-error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
