from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

from scripts.check_translation import CJK_RE, parse_markdown

ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict[str, Any]:
    return json.loads((ROOT / "upstream.json").read_text(encoding="utf-8"))


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()  # noqa: S324


def test_v2_image_inventory_exactly_covers_referenced_figures() -> None:
    images = _manifest()["images"]
    expected = set(images["included_files"])
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "book/images").iterdir()}
    referenced = {
        f"book/{destination}"
        for md in (ROOT / "book").glob("*.md")
        for destination in parse_markdown(md.read_text()).image_destinations
    }
    assert len(expected) == 114
    assert actual == expected == referenced
    assert expected <= {e["path"] for e in images["files"]}
    assert all((ROOT / p).is_file() and not (ROOT / p).is_symlink() for p in actual)


def test_localized_assets_match_recorded_final_hashes() -> None:
    manifest = json.loads((ROOT / "asset-translation-manifest.json").read_text())
    assert len(manifest["files"]) == 114
    upstream = {e["path"]: e["blob_sha1"] for e in _manifest()["images"]["files"]}
    for record in manifest["files"]:
        path = ROOT / record["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["final_sha256"]
        assert record["source_blob_sha1"] == upstream[record["path"]]
        if record["origin"] == "gpt-translation":
            assert _git_blob_sha1(path) != upstream[record["path"]]


def test_all_svg_assets_contain_no_cjk() -> None:
    for path in sorted((ROOT / "book/images").glob("*.svg")):
        assert CJK_RE.search(html.unescape(path.read_text())) is None, path.name


def test_legacy_localized_generators_retain_recorded_source_lineage() -> None:
    manifest = _manifest()
    assert manifest["generator_source_commit"] == "97de455e9aa44cf9f93441ce0c771c9aa9643d92"
    for entry in manifest["generators"]:
        path = ROOT / entry["path"]
        assert path.is_file() and not path.is_symlink()
        assert _git_blob_sha1(path) != entry["blob_sha1"]


def test_localized_pdf_support_differs_from_upstream() -> None:
    for entry in _manifest()["build_support"]:
        path = ROOT / "book" / Path(entry["path"]).name
        assert path.is_file() and not path.is_symlink()
        assert _git_blob_sha1(path) != entry["blob_sha1"]


def test_all_thirteen_manuscripts_differ_from_upstream() -> None:
    expected = {e["path"]: e["blob_sha1"] for e in _manifest()["markdown"]}
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "book").glob("*.md")}
    assert len(actual) == 13
    assert actual == set(expected)
    for name, blob in expected.items():
        assert _git_blob_sha1(ROOT / name) != blob
