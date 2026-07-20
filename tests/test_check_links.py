from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.check_links import check_book, collect_anchors, github_anchor, main


def _write(root: Path, relative_path: str, text: str = "") -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _codes(root: Path) -> set[str]:
    return {issue.code for issue in check_book(root, (), None)}


def test_existing_local_markdown_link_passes(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Глава](chapter1.md)\n")
    _write(tmp_path, "chapter1.md", "# Глава\n")

    assert check_book(tmp_path, (), None) == []


def test_missing_local_markdown_link_fails(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Глава](missing.md)\n")

    assert "missing-target" in _codes(tmp_path)


def test_existing_image_passes_and_missing_image_fails(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "![Схема](images/ok.svg)\n")
    _write(tmp_path, "images/ok.svg", "<svg/>\n")
    assert check_book(tmp_path, (), None) == []

    (tmp_path / "images/ok.svg").unlink()
    assert "missing-image" in _codes(tmp_path)


def test_same_file_and_cross_file_cyrillic_anchors_pass(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "index.md",
        "# Оглавление\n\n[Здесь](#оглавление)\n[Там](chapter.md#русский-раздел)\n",
    )
    _write(tmp_path, "chapter.md", "# Русский раздел\n")

    assert check_book(tmp_path, (), None) == []


def test_missing_anchor_fails(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Раздел](chapter.md#нет-раздела)\n")
    _write(tmp_path, "chapter.md", "# Другой раздел\n")

    assert "missing-anchor" in _codes(tmp_path)


def test_duplicate_heading_suffix_matches_github_style(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Второй](chapter.md#повтор-1)\n")
    chapter = _write(tmp_path, "chapter.md", "# Повтор\n\n# Повтор\n")

    assert collect_anchors(chapter.read_text(encoding="utf-8")) == {"повтор", "повтор-1"}
    assert check_book(tmp_path, (), None) == []


def test_percent_decoded_path_and_anchor_pass(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Раздел](Глава%201.md#важный-раздел)\n")
    _write(tmp_path, "Глава 1.md", "# Важный раздел\n")

    assert check_book(tmp_path, (), None) == []


def test_links_inside_code_fences_are_ignored(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "index.md",
        "```markdown\n[Не ссылка](missing.md)\n![Не картинка](missing.png)\n```\n",
    )

    assert check_book(tmp_path, (), None) == []


def test_external_links_are_skipped_without_network_access(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "index.md",
        "[Web](https://example.invalid/no)\n"
        "[HTTP](http://example.invalid/no)\n"
        "[Mail](mailto:author@example.invalid)\n",
    )

    assert check_book(tmp_path, (), None) == []


@pytest.mark.parametrize(
    "target",
    [
        "../.tmp/upstream/book/chapter1.md",
        "../book-zh/chapter1.md",
        "/home/user/private.md",
    ],
)
def test_forbidden_source_or_absolute_link_fails(tmp_path: Path, target: str) -> None:
    _write(tmp_path, "index.md", f"[Запрещено]({target})\n")

    assert "forbidden-target" in _codes(tmp_path)


def test_partial_manifest_allows_only_declared_pending_markdown(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Будущая](chapter2.md)\n[Ошибка](other.md)\n")
    manifest = tmp_path / "upstream.json"
    manifest.write_text(
        json.dumps({"markdown": [{"path": "book/chapter2.md"}]}),
        encoding="utf-8",
    )

    issues = check_book(tmp_path, (), manifest)

    assert [(issue.code, issue.target) for issue in issues] == [("missing-target", "other.md")]


def test_strict_mode_rejects_declared_but_missing_markdown(tmp_path: Path) -> None:
    _write(tmp_path, "index.md", "[Будущая](chapter2.md)\n")

    assert "missing-target" in _codes(tmp_path)


def test_only_option_skips_unselected_invalid_file(tmp_path: Path) -> None:
    _write(tmp_path, "good.md", "# Готово\n")
    _write(tmp_path, "bad.md", "[Ошибка](missing.md)\n")

    exit_code = main([str(tmp_path), "--only", "good.md"])

    assert exit_code == 0


def test_github_anchor_preserves_unicode_and_numbers() -> None:
    assert github_anchor("Раздел 2: API и RAG", 0) == "раздел-2-api-и-rag"
    assert github_anchor("Раздел 2: API и RAG", 1) == "раздел-2-api-и-rag-1"
