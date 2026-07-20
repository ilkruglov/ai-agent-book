from __future__ import annotations

from pathlib import Path

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
    forbidden: ["ИИ-агент"]
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


def test_matching_markdown_shape_passes_with_translated_headings_and_alt_text(
    tmp_path: Path,
) -> None:
    source, target, glossary = _write_pair(tmp_path)

    issues = validate_translation(source, target, load_glossary(glossary))

    assert issues == []


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


def test_forbidden_accepted_glossary_spelling_fails(tmp_path: Path) -> None:
    changed = TARGET.replace("Первый раздел", "ИИ-агент")

    assert "glossary-forbidden" in _codes(tmp_path, changed)


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
