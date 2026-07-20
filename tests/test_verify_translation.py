from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from threading import Barrier
from typing import cast

import pytest

from scripts.check_translation import (
    TRANSLATION_NOTICE,
    load_glossary,
    validate_translation,
)
from scripts.markdown_chunks import restore_missing_newline_boundaries, split_markdown
from scripts.model_runner import ModelResult, RuntimeEvidence
from scripts.verify_translation import VerificationError, verify_file

ROOT = Path(__file__).resolve().parents[1]

SOURCE = """## 第一节
原文一。

```python
print("ok")
```

| A | B |
|---|---|
| 1 | 2 |

![原图](images/a.svg)

## 第二节
原文二。
"""

DRAFT_CHUNKS = (
    """## Первый раздел
Русский текст.

```python
print("ok")
```

| A | B |
|---|---|
| 1 | 2 |

![Русская подпись](images/a.svg)""",
    """## Второй раздел
Ещё русский текст.""",
)


def test_verification_schema_types_const_fields_for_structured_output() -> None:
    schema = json.loads(
        (ROOT / "prompts/verify_translation.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["model_id"] == {
        "type": "string",
        "const": "gpt-5.6-sol",
    }


def test_verification_prompt_requires_russian_grammar_review() -> None:
    prompt = (ROOT / "prompts/verify_translation.txt").read_text(encoding="utf-8")

    assert "русскую грамматику" in prompt
    assert "согласование подлежащего и сказуемого" in prompt


def test_verification_prompt_requires_documented_cjk_allowlist() -> None:
    prompt = (ROOT / "prompts/verify_translation.txt").read_text(encoding="utf-8")

    assert "cjk-allow" in prompt
    assert "CJK-текст вне документированного allowlist" in prompt


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity


def _runtime(thread_id: str) -> dict[str, object]:
    return {
        "requested_model": "gpt-5.6-sol",
        "reported_model": "gpt-5.6-sol",
        "provider": "openai",
        "thread_id": thread_id,
        "turn_id": f"turn-{thread_id}",
        "ephemeral": True,
        "fallback_allowed": False,
        "sandbox_type": "readOnly",
        "completion_observed": True,
        "usage_observed": True,
        "command_sha256": "a" * 64,
        "prompt_sha256": "b" * 64,
        "response_sha256": "c" * 64,
        "stdout_sha256": "d" * 64,
        "stderr_sha256": "e" * 64,
    }


def _prepare_repo(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    source = repo / ".tmp/upstream/book/chapter.md"
    draft = repo / ".tmp/drafts/chapter.md"
    translation_evidence = repo / ".tmp/evidence/chapter.translation.json"
    output = repo / ".tmp/verified/chapter.md"
    verification_evidence = repo / ".tmp/evidence/chapter.verification.json"
    fragment = repo / ".tmp/evidence/chapter.manifest.json"
    glossary = repo / "glossary.yml"
    source.parent.mkdir(parents=True)
    draft.parent.mkdir(parents=True)
    (repo / "prompts").mkdir()
    source.write_text(SOURCE, encoding="utf-8")
    source_chunks = split_markdown(SOURCE, max_chars=40_000)
    stitched_draft_chunks = restore_missing_newline_boundaries(source_chunks, DRAFT_CHUNKS)
    draft_text = f"{TRANSLATION_NOTICE}\n\n{''.join(stitched_draft_chunks)}"
    draft.write_text(draft_text, encoding="utf-8")
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
""",
        encoding="utf-8",
    )
    shutil.copyfile(
        ROOT / "prompts/verify_translation.txt", repo / "prompts/verify_translation.txt"
    )
    shutil.copyfile(
        ROOT / "prompts/verify_translation.schema.json",
        repo / "prompts/verify_translation.schema.json",
    )

    chunk_dir = repo / ".tmp/drafts/.chunks/chapter"
    chunk_dir.mkdir(parents=True)
    chunks: list[dict[str, object]] = []
    for source_chunk, draft_chunk in zip(source_chunks, DRAFT_CHUNKS, strict=True):
        response_path = chunk_dir / f"{source_chunk.index}.md"
        response_path.write_text(draft_chunk, encoding="utf-8")
        runtime = _runtime(f"translation-{source_chunk.index}")
        runtime["response_sha256"] = _sha256(draft_chunk)
        chunks.append(
            {
                "index": source_chunk.index,
                "start_line": source_chunk.start_line,
                "end_line": source_chunk.end_line,
                "source_sha256": source_chunk.sha256,
                "draft_sha256": _sha256(draft_chunk),
                "response_path": response_path.relative_to(repo).as_posix(),
                "runtime": runtime,
            }
        )
    translation_evidence.parent.mkdir(parents=True)
    translation_evidence.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pass": "translation",
                "model_id": "gpt-5.6-sol",
                "source_path": source.relative_to(repo).as_posix(),
                "draft_path": draft.relative_to(repo).as_posix(),
                "source_sha256": _sha256(SOURCE),
                "draft_sha256": _sha256(draft_text),
                "max_chars": 40_000,
                "chunks": chunks,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "upstream.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
                "markdown": [
                    {
                        "path": "book/chapter.md",
                        "blob_sha1": _git_blob_sha1(SOURCE.encode()),
                        "size": len(SOURCE.encode()),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return (
        repo,
        source,
        draft,
        translation_evidence,
        output,
        verification_evidence,
        fragment,
        glossary,
    )


def _result(output_path: Path, response: str, ordinal: int) -> ModelResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response, encoding="utf-8")
    return ModelResult(
        model="gpt-5.6-sol",
        command=("codex", "app-server"),
        output_path=output_path,
        response=response,
        prompt_sha256=_sha256(f"prompt-{ordinal}"),
        response_sha256=_sha256(response),
        stdout_sha256=_sha256(f"stdout-{ordinal}"),
        stderr_sha256=_sha256(""),
        evidence=RuntimeEvidence(
            requested_model="gpt-5.6-sol",
            reported_model="gpt-5.6-sol",
            provider="openai",
            thread_id=f"verification-{ordinal}",
            turn_id=f"turn-verification-{ordinal}",
            ephemeral=True,
            fallback_allowed=False,
            sandbox_type="readOnly",
            completion_observed=True,
            usage_observed=True,
            command_sha256=_sha256("codex-app-server"),
        ),
    )


def _payloads(
    mutator: Callable[[dict[str, object], int], None] | None = None,
) -> Iterator[str]:
    source_chunks = split_markdown(SOURCE, max_chars=40_000)
    for ordinal, (source_chunk, draft_chunk) in enumerate(
        zip(source_chunks, DRAFT_CHUNKS, strict=True)
    ):
        payload: dict[str, object] = {
            "source_sha256": source_chunk.sha256,
            "draft_sha256": _sha256(draft_chunk),
            "model_id": "gpt-5.6-sol",
            "issues": [],
            "corrected_translation": draft_chunk,
        }
        if mutator is not None:
            mutator(payload, ordinal)
        yield json.dumps(payload, ensure_ascii=False)


def _issue() -> dict[str, object]:
    return {
        "category": "semantic",
        "severity": "major",
        "source_start_line": 1,
        "source_end_line": 1,
        "draft_start_line": 1,
        "draft_end_line": 1,
        "evidence": "Перевод меняет проверяемый смысл source",
        "correction": "Восстановить смысл source",
    }


def _run_with_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutator: Callable[[dict[str, object], int], None] | None = None,
) -> tuple[Path, Path, Path]:
    (
        repo,
        source,
        draft,
        translation_evidence,
        output,
        verification_evidence,
        fragment,
        glossary,
    ) = _prepare_repo(tmp_path)
    responses = _payloads(mutator)
    ordinal = 0

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
        output_schema: Mapping[str, object] | None = None,
    ) -> ModelResult:
        nonlocal ordinal
        assert model == "gpt-5.6-sol"
        assert repo_root == repo
        assert timeout_seconds == 60
        assert "Accepted glossary" in prompt
        assert output_schema is not None
        properties = cast(Mapping[str, object], output_schema["properties"])
        issue_schema = cast(Mapping[str, object], properties["issues"])
        item_schema = cast(Mapping[str, object], issue_schema["items"])
        assert item_schema["type"] == "object"
        response = next(responses)
        result = _result(output_path, response, ordinal)
        ordinal += 1
        return result

    monkeypatch.setattr("scripts.verify_translation.run_model", fake_run_model)
    verify_file(
        source,
        draft,
        translation_evidence,
        output,
        verification_evidence,
        fragment,
        glossary,
        repo,
        60,
    )
    return output, verification_evidence, fragment


def test_verifier_binds_hashes_and_emits_two_pass_fragment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output, evidence, fragment = _run_with_payloads(tmp_path, monkeypatch)

    verified = output.read_text(encoding="utf-8")
    stored_evidence = json.loads(evidence.read_text(encoding="utf-8"))
    stored_fragment = json.loads(fragment.read_text(encoding="utf-8"))
    source_chunks = split_markdown(SOURCE, max_chars=40_000)
    stitched_draft_chunks = restore_missing_newline_boundaries(source_chunks, DRAFT_CHUNKS)
    assert verified == f"{TRANSLATION_NOTICE}\n\n{''.join(stitched_draft_chunks)}"
    assert stored_evidence["source_sha256"] == _sha256(SOURCE)
    assert stored_evidence["draft_sha256"] == _sha256(verified)
    assert stored_evidence["final_sha256"] == _sha256(verified)
    assert stored_fragment["path"] == "chapter.md"
    assert stored_fragment["source"]["path"] == "book/chapter.md"
    assert stored_fragment["final_sha256"] == _sha256(verified)
    assert set(stored_fragment["chunks"][0]["passes"]) == {
        "translation",
        "source_verification",
    }
    fragment_text = fragment.read_text(encoding="utf-8")
    assert "原文" not in fragment_text
    assert "corrected_translation" not in fragment_text
    assert '"issues"' not in fragment_text

    repo = output.parents[2]
    global_manifest = repo / "translation-manifest.json"
    global_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "upstream_commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
                "model_id": "gpt-5.6-sol",
                "transport": {
                    "name": "codex-app-server",
                    "provider_fallback": False,
                    "sandbox": "read-only",
                    "ephemeral": True,
                },
                "files": [stored_fragment],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    issues = validate_translation(
        repo / ".tmp/upstream/book/chapter.md",
        output,
        load_glossary(repo / "glossary.yml"),
        manifest_path=global_manifest,
    )
    assert issues == []


def test_verifier_runs_chunks_in_parallel_and_preserves_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        repo,
        source,
        draft,
        translation_evidence,
        output,
        verification_evidence,
        fragment,
        glossary,
    ) = _prepare_repo(tmp_path)
    barrier = Barrier(2)
    responses = tuple(_payloads())

    def fake_run_model(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
        output_schema: Mapping[str, object] | None = None,
    ) -> ModelResult:
        del model, prompt, repo_root, timeout_seconds, output_schema
        barrier.wait(timeout=2)
        ordinal = int(output_path.stem)
        return _result(output_path, responses[ordinal], ordinal)

    monkeypatch.setattr("scripts.verify_translation.run_model", fake_run_model)

    manifest = verify_file(
        source,
        draft,
        translation_evidence,
        output,
        verification_evidence,
        fragment,
        glossary,
        repo,
        60,
        jobs=2,
    )

    assert [chunk.index for chunk in manifest.chunks] == ["000", "001"]


def test_verifier_reuses_valid_chunks_and_reruns_only_selected_chunk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def preserve_correction(payload: dict[str, object], ordinal: int) -> None:
        if ordinal == 1:
            payload["issues"] = [_issue()]
            payload["corrected_translation"] = DRAFT_CHUNKS[1].replace(
                "Ещё русский", "Исправленный русский"
            )

    output, evidence, fragment = _run_with_payloads(
        tmp_path,
        monkeypatch,
        preserve_correction,
    )
    repo = output.parents[2]
    reuse_run = repo / ".tmp/failed/reuse-run"
    (reuse_run / "evidence").mkdir(parents=True)
    (reuse_run / "responses").mkdir()
    shutil.move(output, reuse_run / output.name)
    shutil.move(evidence, reuse_run / "evidence" / evidence.name)
    shutil.move(fragment, reuse_run / "evidence" / fragment.name)
    shutil.move(
        output.parent / ".responses" / output.stem,
        reuse_run / "responses" / output.stem,
    )
    source = repo / ".tmp/upstream/book/chapter.md"
    draft = repo / ".tmp/drafts/chapter.md"
    translation_evidence = repo / ".tmp/evidence/chapter.translation.json"
    glossary = repo / "glossary.yml"
    source_chunks = split_markdown(SOURCE, max_chars=40_000)
    selected = source_chunks[1]
    payload: dict[str, object] = {
        "source_sha256": selected.sha256,
        "draft_sha256": _sha256(DRAFT_CHUNKS[1]),
        "model_id": "gpt-5.6-sol",
        "issues": [_issue()],
        "corrected_translation": DRAFT_CHUNKS[1].replace("Ещё русский", "Исправленный русский"),
    }
    calls: list[str] = []

    def fake_retry(
        model: str,
        prompt: str,
        repo_root: Path,
        output_path: Path,
        timeout_seconds: int,
        output_schema: Mapping[str, object] | None = None,
    ) -> ModelResult:
        del model, repo_root, timeout_seconds, output_schema
        assert "Предыдущий исправленный перевод" in prompt
        assert "Исправленный русский" in prompt
        assert "Проверь согласование" in prompt
        calls.append(output_path.stem)
        return _result(output_path, json.dumps(payload, ensure_ascii=False), 9)

    monkeypatch.setattr("scripts.verify_translation.run_model", fake_retry)

    verify_file(
        source,
        draft,
        translation_evidence,
        output,
        evidence,
        fragment,
        glossary,
        repo,
        60,
        jobs=2,
        reuse_run=reuse_run,
        rerun_chunks=frozenset({"001"}),
        review_notes={"001": "Проверь согласование"},
    )

    stored = json.loads(evidence.read_text(encoding="utf-8"))
    assert calls == ["001"]
    assert stored["chunks"][0]["runtime"]["thread_id"] == "verification-0"
    assert stored["chunks"][1]["runtime"]["thread_id"] == "verification-9"
    assert sorted(path.name for path in (output.parent / ".responses/chapter").iterdir()) == [
        "000.json",
        "001.json",
    ]


def test_verifier_accepts_source_newline_boundary_restored_by_gpt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutate(payload: dict[str, object], ordinal: int) -> None:
        if ordinal == 0:
            payload["corrected_translation"] = DRAFT_CHUNKS[0] + "\n\n"

    output, _, _ = _run_with_payloads(tmp_path, monkeypatch, mutate)

    source_chunks = split_markdown(SOURCE, max_chars=40_000)
    stitched_draft_chunks = restore_missing_newline_boundaries(source_chunks, DRAFT_CHUNKS)
    assert output.read_text(encoding="utf-8") == (
        f"{TRANSLATION_NOTICE}\n\n{''.join(stitched_draft_chunks)}"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_sha256", "0" * 64, "source_sha256"),
        ("draft_sha256", "0" * 64, "draft_sha256"),
        ("model_id", "other-model", "model_id"),
    ],
)
def test_rejects_identity_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    message: str,
) -> None:
    def mutate(payload: dict[str, object], ordinal: int) -> None:
        if ordinal == 0:
            payload[field] = value

    with pytest.raises(VerificationError, match=message):
        _run_with_payloads(tmp_path, monkeypatch, mutate)


def test_rejects_unknown_second_pass_json_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutate(payload: dict[str, object], ordinal: int) -> None:
        if ordinal == 0:
            payload["unexpected"] = True

    with pytest.raises(VerificationError, match="JSON Schema"):
        _run_with_payloads(tmp_path, monkeypatch, mutate)


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("Без заголовка.", "heading-structure"),
        ("```markdown\n## Раздел\nТекст\n```\n", "внешний Markdown fence"),
        (DRAFT_CHUNKS[0].replace("```python", "```text"), "fence-structure"),
        (DRAFT_CHUNKS[0].replace("|---|---|", "| A | B |"), "table-structure"),
        (DRAFT_CHUNKS[0].replace("images/a.svg", "images/b.svg"), "image-structure"),
        (DRAFT_CHUNKS[0].replace("Русский текст", "原文"), "cjk-unexpected"),
        (DRAFT_CHUNKS[0] + "\n\n\n", "newline boundary"),
    ],
)
def test_rejects_invalid_corrected_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement: str,
    message: str,
) -> None:
    def mutate(payload: dict[str, object], ordinal: int) -> None:
        if ordinal == 0:
            payload["corrected_translation"] = replacement
            payload["issues"] = [_issue()]

    with pytest.raises(VerificationError, match=message):
        _run_with_payloads(tmp_path, monkeypatch, mutate)


def test_rejects_changed_translation_without_source_backed_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutate(payload: dict[str, object], ordinal: int) -> None:
        if ordinal == 0:
            payload["corrected_translation"] = DRAFT_CHUNKS[0].replace(
                "Русский текст",
                "Переписанный русский текст",
            )

    with pytest.raises(VerificationError, match="без связанной issue"):
        _run_with_payloads(tmp_path, monkeypatch, mutate)


def test_rejects_corrupt_translation_evidence_and_unsafe_outputs(
    tmp_path: Path,
) -> None:
    (
        repo,
        source,
        draft,
        translation_evidence,
        output,
        verification_evidence,
        fragment,
        glossary,
    ) = _prepare_repo(tmp_path)
    document = json.loads(translation_evidence.read_text(encoding="utf-8"))
    document["draft_sha256"] = "0" * 64
    translation_evidence.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(VerificationError, match="translation evidence.*draft"):
        verify_file(
            source,
            draft,
            translation_evidence,
            output,
            verification_evidence,
            fragment,
            glossary,
            repo,
            60,
        )

    with pytest.raises(VerificationError, match=r"\.tmp/verified"):
        verify_file(
            source,
            draft,
            translation_evidence,
            repo / "book/chapter.md",
            verification_evidence,
            fragment,
            glossary,
            repo,
            60,
        )
