from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


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


def test_all_133_pinned_images_are_imported_byte_for_byte() -> None:
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
        _assert_blob(entry["path"], entry["blob_sha1"])


def test_pinned_generators_and_pdf_support_are_imported_byte_for_byte() -> None:
    manifest = _manifest()

    for entry in manifest["generators"]:
        _assert_blob(entry["path"], entry["blob_sha1"])
    for entry in manifest["build_support"]:
        destination = f"book/{Path(entry['path']).name}"
        _assert_blob(destination, entry["blob_sha1"])


def test_book_markdown_is_not_a_byte_for_byte_upstream_copy() -> None:
    upstream_markdown = {entry["path"]: entry["blob_sha1"] for entry in _manifest()["markdown"]}
    translated_markdown = sorted((ROOT / "book").glob("*.md"))

    for path in translated_markdown:
        relative_path = path.relative_to(ROOT).as_posix()
        assert relative_path in upstream_markdown
        assert _git_blob_sha1(path) != upstream_markdown[relative_path]
