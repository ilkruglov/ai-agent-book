from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import translation_baseline as baseline
from scripts.check_translation import TRANSLATION_NOTICE


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    source = "## Context\n\nKeep the history unchanged.\n"
    translated = "## Контекст\n\nСохраняйте историю без изменений.\n"
    target = TRANSLATION_NOTICE + "\n\n" + translated
    (source_root / "chapter2.md").write_text(source)
    (target_root / "chapter2.md").write_text(target)

    def sha(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    runtime: dict[str, object] = {
        "requested_model": "gpt-5.6-sol",
        "reported_model": "gpt-5.6-sol",
        "provider": "openai",
        "thread_id": "previous-translation",
        "turn_id": "old-turn",
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

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "chapter2.md",
                        "source": {"sha256": sha(source)},
                        "final_sha256": sha(target),
                        "chunks": [
                            {
                                "source_start": 0,
                                "source_end": len(source),
                                "final_start": 0,
                                "final_end": len(translated),
                                "source_sha256": sha(source),
                                "final_sha256": sha(translated),
                                "passes": {"translation": runtime, "source_verification": runtime},
                            }
                        ],
                    }
                ]
            }
        )
    )
    return source_root, target_root, manifest


def test_loads_verified_pairs_and_exact_reuse(tmp_path: Path) -> None:
    source_root, target_root, manifest = _fixture(tmp_path)
    pairs = baseline.load_baseline(source_root, target_root, manifest)
    selected = baseline.select_baseline("## Context\n\nKeep the history unchanged.\n", pairs)
    assert len(selected) == 1
    assert selected[0].translation == "## Контекст\n\nСохраняйте историю без изменений.\n"
    assert selected[0].path == "chapter2.md"
    assert selected[0].runtime["thread_id"] == "previous-translation"


@pytest.mark.parametrize("tamper", ["source", "translation", "range", "chunk_hash"])
def test_rejects_stale_or_corrupt_baseline(tmp_path: Path, tamper: str) -> None:
    source_root, target_root, manifest = _fixture(tmp_path)
    if tamper == "source":
        (source_root / "chapter2.md").write_text("Modified source")
    elif tamper == "translation":
        (target_root / "chapter2.md").write_text("Modified translation")
    else:
        data = json.loads(manifest.read_text())
        chunk = data["files"][0]["chunks"][0]
        chunk["source_end" if tamper == "range" else "final_sha256"] = (
            3 if tamper == "range" else "0" * 64
        )
        manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="baseline"):
        baseline.load_baseline(source_root, target_root, manifest)


def test_matches_moved_and_edited_section_not_unrelated_text(tmp_path: Path) -> None:
    source_root, target_root, manifest = _fixture(tmp_path)
    pairs = baseline.load_baseline(source_root, target_root, manifest)
    assert baseline.select_baseline(
        "## Context\n\nKeep the history unchanged, except summaries.\n", pairs
    )
    assert baseline.select_baseline("全新章节：语音与机器人。", pairs) == ()


def test_context_contains_old_pair_and_preservation_rule(tmp_path: Path) -> None:
    source_root, target_root, manifest = _fixture(tmp_path)
    pairs = baseline.load_baseline(source_root, target_root, manifest)
    context = baseline.render_baseline(pairs)
    assert "Keep the history unchanged." in context
    assert "Сохраняйте историю без изменений." in context
    assert "дословно" in context


@pytest.mark.parametrize("tamper", ["missing_review", "wrong_model", "fallback", "missing_usage"])
def test_rejects_unverified_or_non_gpt_baseline(tmp_path: Path, tamper: str) -> None:
    source_root, target_root, manifest = _fixture(tmp_path)
    data = json.loads(manifest.read_text())
    passes = data["files"][0]["chunks"][0]["passes"]
    if tamper == "missing_review":
        del passes["source_verification"]
    elif tamper == "wrong_model":
        passes["translation"]["reported_model"] = "other-model"
    elif tamper == "fallback":
        passes["source_verification"]["fallback_allowed"] = True
    else:
        del passes["source_verification"]["usage_observed"]
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="baseline"):
        baseline.load_baseline(source_root, target_root, manifest)
