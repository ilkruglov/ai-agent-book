from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = "c3352738f4b6fe42fe34e3cf6a79bcb424a133b8"
ATTRIBUTION = "Русский перевод: community edition"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

EXPECTED_MARKDOWN = {
    entry["path"]: (entry["blob_sha1"], entry["size"])
    for entry in json.loads((ROOT / "updates/v2.0/upstream.json").read_text())["markdown"]
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
    assert manifest["version"] == "v2.0"
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
    assert images["tree_sha1"] == "d61026dc6768434b0dcf28849152add3f4af1c8d"
    assert images["file_count"] == 135
    assert len(files) == 135
    assert len(images["included_files"]) == 114
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
    assert manifest["generator_source_commit"] == "97de455e9aa44cf9f93441ce0c771c9aa9643d92"
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


def test_translation_manifest_has_exact_gpt_transport() -> None:
    manifest = json.loads((ROOT / "translation-manifest.json").read_text(encoding="utf-8"))

    assert {key: value for key, value in manifest.items() if key != "files"} == {
        "schema_version": 1,
        "upstream_commit": UPSTREAM_COMMIT,
        "model_id": "gpt-5.6-sol",
        "transport": {
            "name": "codex-app-server",
            "provider_fallback": False,
            "sandbox": "read-only",
            "ephemeral": True,
        },
    }
    assert isinstance(manifest["files"], list)
