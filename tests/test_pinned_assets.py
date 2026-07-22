from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

from scripts.check_translation import CJK_RE

ROOT = Path(__file__).resolve().parents[1]
GENERATED_SVGS = {
    *(f"book/images/fig1-{index}.svg" for index in range(1, 11)),
    *(f"book/images/fig2-{index}.svg" for index in range(1, 12)),
    *(f"book/images/fig3-{index}.svg" for index in range(1, 15)),
    *(f"book/images/fig4-{index}.svg" for index in range(1, 8)),
    *(f"book/images/fig5-{index}.svg" for index in range(1, 12)),
    *(f"book/images/fig8-{index}.svg" for index in range(1, 8)),
    "book/images/fig9-11.svg",
    "book/images/fig10-1.svg",
    "book/images/fig10-2.svg",
    *(f"book/images/fig10-{index}.svg" for index in range(4, 12)),
    "book/images/fig10-13.svg",
}
STATIC_LOCALIZED_SVGS = {
    "book/images/fig0-1.svg",
    "book/images/fig0-2.svg",
    *(
        f"book/images/fig1-wf-{name}.svg"
        for name in (
            "chaining",
            "evaluator",
            "orchestrator",
            "parallel",
            "routing",
        )
    ),
    "book/images/fig10-3.svg",
    "book/images/fig10-12.svg",
    *(f"book/images/fig2-{index}.svg" for index in range(12, 18)),
    "book/images/fig3-15.svg",
    *(f"book/images/fig6-{index}.svg" for index in range(1, 10)),
    *(f"book/images/fig7-{index}.svg" for index in range(1, 22)),
    *(f"book/images/fig9-{index}.svg" for index in (*range(1, 7), *range(8, 11), 12, 13)),
    "book/images/fig9-7.svg",
}
LOCALIZED_SVGS = GENERATED_SVGS | STATIC_LOCALIZED_SVGS


def _manifest() -> dict[str, Any]:
    return json.loads((ROOT / "upstream.json").read_text(encoding="utf-8"))


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity


def _assert_blob(relative_path: str, expected_sha1: str) -> None:
    path = ROOT / relative_path
    assert path.is_file(), relative_path
    assert not path.is_symlink(), relative_path
    assert _git_blob_sha1(path) == expected_sha1, relative_path


def test_all_133_images_preserve_the_pinned_inventory() -> None:
    images = _manifest()["images"]
    entries = images["files"]
    expected = {entry["path"] for entry in entries}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "book/images").rglob("*")
        if path.is_file()
    }

    assert images["file_count"] == 133
    assert len(entries) == 133
    assert actual == expected
    for entry in entries:
        if entry["path"] in LOCALIZED_SVGS:
            continue
        _assert_blob(entry["path"], entry["blob_sha1"])


def test_localized_generated_images_differ_from_upstream() -> None:
    upstream_images = {
        entry["path"]: entry["blob_sha1"] for entry in _manifest()["images"]["files"]
    }

    assert len(GENERATED_SVGS) == 72
    for relative_path in GENERATED_SVGS:
        assert _git_blob_sha1(ROOT / relative_path) != upstream_images[relative_path]


def test_all_static_svg_labels_are_localized_and_differ_from_upstream() -> None:
    upstream_images = {
        entry["path"]: entry["blob_sha1"] for entry in _manifest()["images"]["files"]
    }

    assert len(STATIC_LOCALIZED_SVGS) == 58
    for relative_path in STATIC_LOCALIZED_SVGS:
        svg = (ROOT / relative_path).read_text(encoding="utf-8")
        assert CJK_RE.search(svg) is None, relative_path
        assert _git_blob_sha1(ROOT / relative_path) != upstream_images[relative_path]


def test_all_svg_assets_contain_no_cjk() -> None:
    for path in sorted((ROOT / "book/images").glob("*.svg")):
        svg = html.unescape(path.read_text(encoding="utf-8"))
        assert CJK_RE.search(svg) is None, path.relative_to(ROOT).as_posix()


def test_localized_generators_differ_from_upstream() -> None:
    manifest = _manifest()

    for entry in manifest["generators"]:
        path = ROOT / entry["path"]
        assert path.is_file(), entry["path"]
        assert not path.is_symlink(), entry["path"]
        assert _git_blob_sha1(path) != entry["blob_sha1"], entry["path"]


def test_localized_pdf_support_differs_from_upstream() -> None:
    manifest = _manifest()

    for entry in manifest["build_support"]:
        destination = f"book/{Path(entry['path']).name}"
        path = ROOT / destination
        assert path.is_file(), destination
        assert not path.is_symlink(), destination
        assert _git_blob_sha1(path) != entry["blob_sha1"], destination


def test_book_markdown_is_not_a_byte_for_byte_upstream_copy() -> None:
    upstream_markdown = {entry["path"]: entry["blob_sha1"] for entry in _manifest()["markdown"]}
    translated_markdown = sorted((ROOT / "book").glob("*.md"))

    for path in translated_markdown:
        relative_path = path.relative_to(ROOT).as_posix()
        assert relative_path in upstream_markdown
        assert _git_blob_sha1(path) != upstream_markdown[relative_path]
