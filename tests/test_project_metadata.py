from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = "97de455e9aa44cf9f93441ce0c771c9aa9643d92"
ATTRIBUTION = "Русский перевод: community edition"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

EXPECTED_MARKDOWN = {
    "book/introduction.md": ("edfd6ed34b3d14760cac5114cfb3622745a30969", 20_731),
    "book/chapter1.md": ("fc40590687d38b2b330bd3035a3ea1cba30ea037", 66_344),
    "book/chapter2.md": ("50db6e6945cb54a40de703795491f1a58eebaa12", 134_173),
    "book/chapter3.md": ("8472fef633914e90be30b9b67b4dcdc15c576efc", 106_898),
    "book/chapter4.md": ("d145d863e9106cd0ad69b543d64849eda50ef7ca", 92_542),
    "book/chapter5.md": ("fe2c17b954d8165b1d490b0fde35d7ea76f1b6ed", 113_297),
    "book/chapter6.md": ("2ea2974b75b8430e83a6b947ca59da111604b3c6", 100_135),
    "book/chapter7.md": ("5e8421aec0a98672991dc693b0cc2ee604a65c43", 136_396),
    "book/chapter8.md": ("0aa3a04b24ef65bfc3082ddb0e12ecadfcb4f104", 67_878),
    "book/chapter9.md": ("9109acb6ac1a240e9a25fdb5ecf989f8bfbd02c2", 91_363),
    "book/chapter10.md": ("0f608bcfcd12a6a73d392a0b44fe89acdae2c03b", 98_472),
    "book/afterword.md": ("90dafce3240e7b1a6f1e2fefbc59bd54efe2c34f", 11_121),
}

EXPECTED_GENERATORS = {
    "book/gen_ch1_figs.py",
    "book/gen_ch2_figs.py",
    "book/gen_ch3_figs.py",
    "book/gen_ch4_figs.py",
    "book/gen_ch5_figs.py",
    "book/gen_ch8_figs.py",
    "book/gen_ch9_figs.py",
    "book/gen_cover.py",
    "book/svg_lib.py",
}

EXPECTED_BUILD_SUPPORT = {
    "book-en/build_pdf.sh",
    "book-en/preamble.tex",
    "book-en/cover.tex",
    "book-en/crossref.lua",
    "book-en/experiment_box.lua",
}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_manifest() -> dict[str, Any]:
    return json.loads((ROOT / "upstream.json").read_text(encoding="utf-8"))


def test_upstream_metadata_is_pinned() -> None:
    manifest = _load_manifest()

    assert manifest["schema_version"] == 1
    assert manifest["repository"] == "https://github.com/bojieli/ai-agent-book"
    assert manifest["branch"] == "main"
    assert manifest["commit"] == UPSTREAM_COMMIT
    assert manifest["version"] == "v1.2"
    assert manifest["source_directory"] == "book"
    assert manifest["license"] == {
        "path": "LICENSE",
        "blob_sha1": "bd3e071f150cf46f86c91d3341d36644f16e11cb",
        "size": 11_338,
    }


def test_markdown_manifest_matches_pinned_blobs() -> None:
    markdown = _load_manifest()["markdown"]
    actual = {item["path"]: (item["blob_sha1"], item["size"]) for item in markdown}

    assert actual == EXPECTED_MARKDOWN
    assert [item["path"] for item in markdown] == list(EXPECTED_MARKDOWN)


def test_asset_manifest_has_complete_shape() -> None:
    images = _load_manifest()["images"]
    files = images["files"]

    assert images["path"] == "book/images"
    assert images["tree_sha1"] == "b0d9cbe7700caa4a8d5eff9fe9cc929d03756cfd"
    assert images["file_count"] == 133
    assert len(files) == 133
    assert [item["path"] for item in files] == sorted(item["path"] for item in files)
    for item in files:
        assert item["path"].startswith("book/images/")
        assert SHA1_RE.fullmatch(item["blob_sha1"])
        assert isinstance(item["size"], int) and item["size"] > 0


def test_support_file_manifests_are_complete() -> None:
    manifest = _load_manifest()
    generators = manifest["generators"]
    build_support = manifest["build_support"]

    assert {item["path"] for item in generators} == EXPECTED_GENERATORS
    assert {item["path"] for item in build_support} == EXPECTED_BUILD_SUPPORT
    for item in [*generators, *build_support]:
        assert SHA1_RE.fullmatch(item["blob_sha1"])
        assert isinstance(item["size"], int) and item["size"] > 0


def test_tmp_is_ignored_and_untracked() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", ".tmp/probe"],
        cwd=ROOT,
        check=False,
    )

    assert ignored.returncode == 0
    assert _git("ls-files", ".tmp") == ""


def test_attribution_is_present_in_project_metadata() -> None:
    for relative_path in ("README.md", "NOTICE", "glossary.yml"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert ATTRIBUTION in text, relative_path


def test_license_is_the_pinned_upstream_blob() -> None:
    assert _git("hash-object", "LICENSE") == "bd3e071f150cf46f86c91d3341d36644f16e11cb"


def test_translation_manifest_starts_with_exact_gpt_transport() -> None:
    manifest = json.loads((ROOT / "translation-manifest.json").read_text(encoding="utf-8"))

    assert manifest == {
        "schema_version": 1,
        "upstream_commit": UPSTREAM_COMMIT,
        "model_id": "gpt-5.6-sol",
        "transport": {
            "name": "codex-app-server",
            "provider_fallback": False,
            "sandbox": "read-only",
            "ephemeral": True,
        },
        "files": [],
    }
