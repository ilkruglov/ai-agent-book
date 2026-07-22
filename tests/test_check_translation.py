from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from scripts.check_translation import (
    BOOK_TITLE,
    TRANSLATION_NOTICE,
    find_cjk,
    load_glossary,
    main,
    validate_pdf_text,
    validate_translation,
)
from scripts.markdown_chunks import split_markdown

SOURCE = """# 原标题

## 第一节

```python
print("ok")
```

| A | B |
|---|---|
| 1 | 2 |

![原图](images/a.svg)
"""

TARGET = f"""{TRANSLATION_NOTICE}

# Русский заголовок

## Первый раздел

```python
print("ok")
```

| А | Б |
|---|---|
| 1 | 2 |

![Русская подпись](images/a.svg)
"""


def _write_pair(tmp_path: Path, target_text: str = TARGET) -> tuple[Path, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    glossary = tmp_path / "glossary.yml"
    source.write_text(SOURCE, encoding="utf-8")
    target.write_text(target_text, encoding="utf-8")
    glossary.write_text(
        """schema_version: 1
attribution: "Русский перевод: community edition"
terms:
  - id: ai_agent
    source: ["AI Agent"]
    preferred: "AI-агент"
    status: accepted
    rule: "Первое упоминание"
    forbidden: ["ИИ-агент", "ИИ агент"]
  - id: prompt
    source: ["prompt"]
    preferred: "промпт"
    status: candidate
    rule: "Проверить по benchmark"
    forbidden: ["подсказка"]
""",
        encoding="utf-8",
    )
    return source, target, glossary


def _codes(tmp_path: Path, target_text: str) -> set[str]:
    source, target, glossary = _write_pair(tmp_path, target_text)
    issues = validate_translation(source, target, load_glossary(glossary))
    return {issue.code for issue in issues}


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _runtime(response_sha256: str) -> dict[str, object]:
    return {
        "requested_model": "gpt-5.6-sol",
        "reported_model": "gpt-5.6-sol",
        "provider": "openai",
        "thread_id": "thread-1",
        "turn_id": "turn-1",
        "ephemeral": True,
        "fallback_allowed": False,
        "sandbox_type": "readOnly",
        "completion_observed": True,
        "usage_observed": True,
        "command_sha256": "a" * 64,
        "prompt_sha256": "b" * 64,
        "response_sha256": response_sha256,
        "stdout_sha256": "d" * 64,
        "stderr_sha256": "e" * 64,
    }


def _write_manifest(
    tmp_path: Path,
    source: Path,
    target: Path,
    mutate: object | None = None,
) -> Path:
    source_text = source.read_text(encoding="utf-8")
    target_text = target.read_text(encoding="utf-8")
    prefix = f"{TRANSLATION_NOTICE}\n\n"
    assert target_text.startswith(prefix)
    final_body = target_text[len(prefix) :]
    source_chunks = split_markdown(source_text, max_chars=100_000)
    final_chunks = split_markdown(final_body, max_chars=100_000)
    assert len(source_chunks) == len(final_chunks)
    source_offset = 0
    final_offset = 0
    chunks: list[dict[str, object]] = []
    for source_chunk, final_chunk in zip(source_chunks, final_chunks, strict=True):
        source_end = source_offset + len(source_chunk.text)
        final_end = final_offset + len(final_chunk.text)
        draft_sha256 = _sha256(final_chunk.text)
        final_sha256 = _sha256(final_chunk.text)
        chunks.append(
            {
                "index": source_chunk.index,
                "start_line": source_chunk.start_line,
                "end_line": source_chunk.end_line,
                "source_start": source_offset,
                "source_end": source_end,
                "final_start": final_offset,
                "final_end": final_end,
                "source_sha256": source_chunk.sha256,
                "draft_sha256": draft_sha256,
                "final_sha256": final_sha256,
                "passes": {
                    "translation": _runtime(draft_sha256),
                    "source_verification": _runtime("f" * 64),
                },
            }
        )
        source_offset = source_end
        final_offset = final_end

    document: dict[str, object] = {
        "schema_version": 1,
        "upstream_commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
        "model_id": "gpt-5.6-sol",
        "transport": {
            "name": "codex-app-server",
            "provider_fallback": False,
            "sandbox": "read-only",
            "ephemeral": True,
        },
        "files": [
            {
                "path": target.name,
                "source": {
                    "path": f"book/{target.name}",
                    "blob_sha1": _git_blob_sha1(source.read_bytes()),
                    "sha256": _sha256(source_text),
                },
                "final_sha256": _sha256(target_text),
                "chunks": chunks,
            }
        ],
    }
    if callable(mutate):
        mutate(document)
    manifest = tmp_path / "translation-manifest.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    (tmp_path / "upstream.json").write_text(
        json.dumps(
            {
                "commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
                "markdown": [
                    {
                        "path": f"book/{target.name}",
                        "blob_sha1": _git_blob_sha1(source.read_bytes()),
                        "size": len(source.read_bytes()),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest


def test_matching_markdown_shape_passes_with_translated_headings_and_alt_text(
    tmp_path: Path,
) -> None:
    source, target, glossary = _write_pair(tmp_path)

    issues = validate_translation(source, target, load_glossary(glossary))

    assert issues == []


def test_matching_manifest_provenance_passes(tmp_path: Path) -> None:
    source, target, glossary = _write_pair(tmp_path)
    manifest = _write_manifest(tmp_path, source, target)

    issues = validate_translation(
        source,
        target,
        load_glossary(glossary),
        manifest_path=manifest,
    )

    assert issues == []


def test_manifest_rejects_missing_second_pass_evidence(tmp_path: Path) -> None:
    source, target, glossary = _write_pair(tmp_path)

    def remove_second_pass(document: dict[str, object]) -> None:
        files = cast(list[dict[str, object]], document["files"])
        chunks = cast(list[dict[str, object]], files[0]["chunks"])
        passes = cast(dict[str, object], chunks[0]["passes"])
        del passes["source_verification"]

    manifest = _write_manifest(tmp_path, source, target, remove_second_pass)

    issues = validate_translation(
        source,
        target,
        load_glossary(glossary),
        manifest_path=manifest,
    )

    assert {issue.code for issue in issues} == {"manifest-second-pass"}


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("source", "manifest-source-hash"),
        ("final", "manifest-final-hash"),
        ("model", "manifest-model"),
        ("runtime", "manifest-runtime"),
        ("range", "manifest-chunks"),
    ],
)
def test_manifest_rejects_tampered_provenance(
    tmp_path: Path,
    field: str,
    expected_code: str,
) -> None:
    source, target, glossary = _write_pair(tmp_path)

    def tamper(document: dict[str, object]) -> None:
        files = cast(list[dict[str, object]], document["files"])
        file_entry = files[0]
        if field == "source":
            cast(dict[str, object], file_entry["source"])["sha256"] = "0" * 64
        elif field == "final":
            file_entry["final_sha256"] = "0" * 64
        elif field == "model":
            document["model_id"] = "other-model"
        elif field == "range":
            chunks = cast(list[dict[str, object]], file_entry["chunks"])
            chunks[0]["start_line"] = 999
        else:
            chunks = cast(list[dict[str, object]], file_entry["chunks"])
            passes = cast(dict[str, dict[str, object]], chunks[0]["passes"])
            passes["translation"]["usage_observed"] = False

    manifest = _write_manifest(tmp_path, source, target, tamper)
    issues = validate_translation(
        source,
        target,
        load_glossary(glossary),
        manifest_path=manifest,
    )

    assert expected_code in {issue.code for issue in issues}


@pytest.mark.parametrize(
    "target_text",
    [
        TARGET.replace("\n## Первый раздел\n", "\n"),
        TARGET.replace("\n## Первый раздел\n", "\n## Первый раздел\n\n### Лишний\n"),
    ],
)
def test_missing_or_extra_heading_fails(tmp_path: Path, target_text: str) -> None:
    assert "heading-structure" in _codes(tmp_path, target_text)


@pytest.mark.parametrize(
    "target_text",
    [
        TARGET.replace("```python", "```text"),
        TARGET.replace("```python", "````python").replace("\n```\n", "\n````\n"),
        TARGET.replace('print("ok")\n```', 'print("ok")'),
    ],
)
def test_code_fence_mismatch_fails(tmp_path: Path, target_text: str) -> None:
    assert "fence-structure" in _codes(tmp_path, target_text)


def test_translated_image_alt_passes_but_changed_destination_fails(tmp_path: Path) -> None:
    changed = TARGET.replace("images/a.svg", "images/b.svg")

    assert "image-structure" in _codes(tmp_path, changed)


def test_missing_table_separator_fails(tmp_path: Path) -> None:
    changed = TARGET.replace("|---|---|", "| А | Б |")

    assert "table-structure" in _codes(tmp_path, changed)


def test_missing_translation_notice_fails(tmp_path: Path) -> None:
    changed = TARGET.replace(f"{TRANSLATION_NOTICE}\n\n", "")

    assert "translation-notice" in _codes(tmp_path, changed)


def test_cjk_in_prose_fails_and_find_cjk_reports_line(tmp_path: Path) -> None:
    changed = TARGET.replace("Первый раздел", "Первый раздел 原文")

    source, target, glossary = _write_pair(tmp_path, changed)
    issues = validate_translation(source, target, load_glossary(glossary))

    assert "cjk-unexpected" in {issue.code for issue in issues}
    assert find_cjk(changed)[0].line == 5


def test_cjk_with_documented_allow_reason_passes(tmp_path: Path) -> None:
    allowed = TARGET.replace(
        "## Первый раздел",
        "## Первый раздел\n\n"
        '<!-- cjk-allow: reason="Имя исходного API" -->\n'
        "原文\n"
        "<!-- /cjk-allow -->",
    )

    assert "cjk-unexpected" not in _codes(tmp_path, allowed)
    assert "cjk-allow-reason" not in _codes(tmp_path, allowed)


def test_empty_cjk_allow_reason_fails(tmp_path: Path) -> None:
    allowed = TARGET.replace(
        "## Первый раздел",
        '## Первый раздел\n\n<!-- cjk-allow: reason="" -->\n原文\n<!-- /cjk-allow -->',
    )

    assert "cjk-allow-reason" in _codes(tmp_path, allowed)


@pytest.mark.parametrize("forbidden", ["ИИ-агент", "ИИ агент"])
def test_forbidden_accepted_glossary_spelling_fails(
    tmp_path: Path,
    forbidden: str,
) -> None:
    changed = TARGET.replace("Первый раздел", forbidden)

    assert "glossary-forbidden" in _codes(tmp_path, changed)


def test_forbidden_glossary_spelling_does_not_match_inside_words(tmp_path: Path) -> None:
    changed = TARGET.replace("Первый раздел", "Об участии агента")

    assert "glossary-forbidden" not in _codes(tmp_path, changed)


def test_candidate_glossary_spelling_is_not_enforced(tmp_path: Path) -> None:
    changed = TARGET.replace("Первый раздел", "подсказка")

    assert "glossary-forbidden" not in _codes(tmp_path, changed)


def test_only_option_checks_requested_pair(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    (source_dir / "chapter2.md").write_text(SOURCE, encoding="utf-8")
    (target_dir / "chapter2.md").write_text(TARGET, encoding="utf-8")
    _, _, glossary = _write_pair(tmp_path / "pair")

    exit_code = main(
        [
            "--source",
            str(source_dir),
            "--target",
            str(target_dir),
            "--glossary",
            str(glossary),
            "--only",
            "chapter2.md",
        ]
    )

    assert exit_code == 0


def test_cli_checks_manifest_for_requested_pair(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    source = source_dir / "chapter2.md"
    target = target_dir / "chapter2.md"
    source.write_text(SOURCE, encoding="utf-8")
    target.write_text(TARGET, encoding="utf-8")
    _, _, glossary = _write_pair(tmp_path / "pair")
    manifest = _write_manifest(tmp_path, source, target)

    exit_code = main(
        [
            "--source",
            str(source_dir),
            "--target",
            str(target_dir),
            "--glossary",
            str(glossary),
            "--manifest",
            str(manifest),
            "--only",
            "chapter2.md",
        ]
    )

    assert exit_code == 0


def test_cli_returns_two_when_source_snapshot_is_missing(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    _, _, glossary = _write_pair(tmp_path / "pair")

    exit_code = main(
        [
            "--source",
            str(tmp_path / "missing-source"),
            "--target",
            str(target_dir),
            "--glossary",
            str(glossary),
        ]
    )

    assert exit_code == 2


@pytest.mark.parametrize(
    ("pdf_text", "expected_code"),
    [
        ("Введение\nГлава 1", "pdf-title"),
        (f"{BOOK_TITLE}\nВведение", "pdf-heading"),
        (f"{BOOK_TITLE}\nВведение\nГлава 1\n�", "pdf-replacement-character"),
        (f"{BOOK_TITLE}\nВведение\nГлава 1\n残留中文", "pdf-cjk-unexpected"),
    ],
)
def test_pdf_text_validation_detects_required_content(
    pdf_text: str,
    expected_code: str,
) -> None:
    issues = validate_pdf_text(pdf_text, ("Введение", "Глава 1"))

    assert expected_code in {issue.code for issue in issues}


def test_valid_pdf_text_passes() -> None:
    pdf_text = f"{BOOK_TITLE}\nВведение\nГлава 1\n"

    assert validate_pdf_text(pdf_text, ("Введение", "Глава 1")) == []


def test_pdf_text_validation_normalizes_layout_and_markdown_heading_attributes() -> None:
    pdf_text = (
        "AI-агенты изнутри:\n"
        "принципы проектирования и инженерная практика\n"
        "Введение\n"
        "Послесловие: возвращаясь к формуле\n"
        "«AI-агент = LLM + контекст + инструменты»\n"
    )
    expected_h1 = (
        "Введение {.unnumbered}",
        "Послесловие: возвращаясь к формуле «AI-агент = LLM + контекст + инструменты» "
        "{.unnumbered}",
    )

    assert validate_pdf_text(pdf_text, expected_h1) == []
