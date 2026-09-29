from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
RUNTIME_KEYS = {
    "requested_model",
    "reported_model",
    "provider",
    "thread_id",
    "turn_id",
    "ephemeral",
    "fallback_allowed",
    "sandbox_type",
    "completion_observed",
    "usage_observed",
    "command_sha256",
    "prompt_sha256",
    "response_sha256",
    "stdout_sha256",
    "stderr_sha256",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_runtime(runtime: dict[str, object]) -> None:
    assert set(runtime) == RUNTIME_KEYS
    assert runtime["requested_model"] == "gpt-5.6-sol"
    assert runtime["reported_model"] == "gpt-5.6-sol"
    assert runtime["provider"] == "openai"
    assert runtime["ephemeral"] is True
    assert runtime["fallback_allowed"] is False
    assert runtime["sandbox_type"] == "readOnly"
    assert runtime["completion_observed"] is True
    assert runtime["usage_observed"] is True
    for key in (
        "command_sha256",
        "prompt_sha256",
        "response_sha256",
        "stdout_sha256",
        "stderr_sha256",
    ):
        assert isinstance(runtime[key], str)
        assert SHA256_RE.fullmatch(cast(str, runtime[key]))


def test_static_svg_translation_manifest_matches_exact_gpt_outputs() -> None:
    manifest: dict[str, Any] = json.loads(
        (ROOT / "updates/v1.2/asset-translation-manifest.json").read_text(encoding="utf-8")
    )

    assert {key: value for key, value in manifest.items() if key not in {"groups", "files"}} == {
        "schema_version": 1,
        "upstream_commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
        "model_id": "gpt-5.6-sol",
        "transport": {
            "name": "codex-app-server",
            "provider_fallback": False,
            "sandbox": "read-only",
            "ephemeral": True,
        },
    }

    groups = cast(list[dict[str, object]], manifest["groups"])
    assert [(group["name"], group["record_count"]) for group in groups] == [
        ("introduction-chapter6", 432),
        ("chapter7", 449),
        ("chapters9-10", 301),
        ("encoded-introduction-chapter9", 39),
    ]
    for group in groups:
        assert SHA256_RE.fullmatch(cast(str, group["translation_mapping_sha256"]))
        assert SHA256_RE.fullmatch(cast(str, group["verified_mapping_sha256"]))
        _assert_runtime(cast(dict[str, object], group["translation_runtime"]))
        _assert_runtime(cast(dict[str, object], group["verification_runtime"]))

    upstream = json.loads((ROOT / "updates/v1.2/upstream.json").read_text(encoding="utf-8"))
    upstream_images = {entry["path"]: entry["blob_sha1"] for entry in upstream["images"]["files"]}
    files = cast(list[dict[str, object]], manifest["files"])
    assert len(files) == 58
    assert [record["path"] for record in files] == sorted(
        cast(str, record["path"]) for record in files
    )
    assert sum(cast(int, record["translated_text_nodes"]) for record in files) == 1221

    for record in files:
        path = cast(str, record["path"])
        assert set(record) == {
            "path",
            "source_blob_sha1",
            "source_sha256",
            "final_sha256",
            "translated_text_nodes",
            "fitted_text_elements",
        }
        assert record["source_blob_sha1"] == upstream_images[path]
        assert SHA1_RE.fullmatch(cast(str, record["source_blob_sha1"]))
        assert SHA256_RE.fullmatch(cast(str, record["source_sha256"]))
        assert record["final_sha256"] == _sha256(ROOT / "updates/v1.2/images" / Path(path).name)
        assert cast(int, record["translated_text_nodes"]) > 0
        assert cast(int, record["fitted_text_elements"]) >= 0


def test_v2_assets_have_complete_two_pass_or_baseline_provenance() -> None:
    manifest = json.loads((ROOT / "asset-translation-manifest.json").read_text())
    assert manifest["schema_version"] == 2
    assert manifest["upstream_commit"] == "c3352738f4b6fe42fe34e3cf6a79bcb424a133b8"
    assert manifest["model_id"] == "gpt-5.6-sol"
    groups = {group["name"]: group for group in manifest["groups"]}
    assert set(groups) == {"A", "B", "metadata"}
    assert sum(group["record_count"] for group in groups.values()) == 857
    for name, group in groups.items():
        _assert_runtime(group["translation_runtime"])
        _assert_runtime(group["verification_runtime"])
        for stage, field in [
            ("draft", "translation_mapping_sha256"),
            ("verified", "verified_mapping_sha256"),
        ]:
            mapping = json.loads((ROOT / f"updates/v2.0/assets/{name}.{stage}.json").read_text())
            digest = hashlib.sha256(
                json.dumps(
                    mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode()
            ).hexdigest()
            assert digest == group[field]
            assert len(mapping) == group["record_count"]
    records = manifest["files"]
    baseline_sources = {
        item["path"]: item["blob_sha1"]
        for item in json.loads((ROOT / "updates/v1.2/upstream.json").read_text())["images"]["files"]
    }
    assert len(records) == 114
    assert sum(r["origin"] == "baseline-reuse" for r in records) == 74
    assert sum(r["origin"] == "gpt-translation" for r in records) == 38
    assert sum(r["origin"] == "upstream-technical-labels" for r in records) == 1
    assert sum(r["origin"] == "editorial-correction" for r in records) == 1
    for record in records:
        assert _sha256(ROOT / record["path"]) == record["final_sha256"]
        if record["origin"] == "baseline-reuse":
            baseline = ROOT / "updates/v1.2/images" / Path(record["baseline_path"]).name
            assert _sha256(baseline) == record["baseline_sha256"]
            assert record["raw_sha256"] == record["baseline_sha256"]
            assert record["source_blob_sha1"] == baseline_sources[record["baseline_path"]]
        elif record["origin"] == "gpt-translation":
            assert record["groups"] and set(record["groups"]) <= set(groups)
        elif record["origin"] == "editorial-correction":
            baseline = ROOT / "updates/v1.2/images" / Path(record["baseline_path"]).name
            assert record["editorial_correction"]
            assert _sha256(baseline) == record["baseline_sha256"]
            assert record["raw_sha256"] == record["baseline_sha256"]
            assert record["final_sha256"] != record["baseline_sha256"]
        else:
            assert record["raw_sha256"] == record["source_sha256"]


def test_layout_audit_is_bound_to_every_promoted_asset() -> None:
    manifest = json.loads((ROOT / "asset-translation-manifest.json").read_text())
    report = json.loads((ROOT / "updates/v2.0/assets/layout-report.json").read_text())
    records = {Path(record["path"]).name: record for record in manifest["files"]}
    audited = {record["file"]: record for record in report["files"]}
    assert report["flags"] == []
    assert len(report["files"]) == len(audited) == 114
    assert audited.keys() == records.keys()
    for name, audit in audited.items():
        record = records[name]
        assert audit["flags"] == []
        assert audit["raw_sha256"] == record["raw_sha256"]
        assert audit["final_sha256"] == record["final_sha256"]
        assert audit["final_sha256"] == _sha256(ROOT / record["path"])
