from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

GENERATOR_OUTPUTS: dict[str, tuple[str, ...]] = {
    "gen_ch1_figs.py": tuple(f"fig1-{index}.svg" for index in range(1, 11)),
    "gen_ch2_figs.py": tuple(f"fig2-{index}.svg" for index in range(1, 12)),
    "gen_ch3_figs.py": tuple(f"fig3-{index}.svg" for index in range(1, 15)),
    "gen_ch4_figs.py": tuple(f"fig4-{index}.svg" for index in range(1, 13)),
    "gen_ch5_figs.py": tuple(f"fig5-{index}.svg" for index in range(1, 12)),
    "gen_ch8_figs.py": tuple(f"fig8-{index}.svg" for index in range(1, 8)),
    # Upstream kept the old filename after chapter renumbering. Most figures now belong
    # to Chapter 10, while its VLA figure remains the current Chapter 9 figure 11.
    "gen_ch9_figs.py": (
        "fig9-11.svg",
        "fig10-1.svg",
        "fig10-2.svg",
        *(f"fig10-{index}.svg" for index in range(4, 12)),
        "fig10-13.svg",
    ),
}
EXPECTED_OUTPUTS = {
    output_name for output_names in GENERATOR_OUTPUTS.values() for output_name in output_names
}
PROMOTED_OUTPUTS = EXPECTED_OUTPUTS - {
    *(f"fig4-{index}.svg" for index in range(8, 13)),
}
CJK_ALLOWLIST: dict[str, tuple[str, ...]] = {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_generator(generator: str, run_root: Path) -> Path:
    isolated_book = run_root / "book"
    isolated_book.mkdir(parents=True)
    shutil.copy2(ROOT / "book" / generator, isolated_book / generator)
    shutil.copy2(ROOT / "book/svg_lib.py", isolated_book / "svg_lib.py")
    output_dir = run_root / "generated"

    result = subprocess.run(
        [
            sys.executable,
            str(isolated_book / generator),
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert not (isolated_book / "images").exists(), (
        f"{generator} ignored --output-dir and wrote beside its source"
    )
    return output_dir


@pytest.mark.parametrize(("generator", "expected"), GENERATOR_OUTPUTS.items())
def test_generator_writes_exact_localized_deterministic_svg_set(
    generator: str,
    expected: tuple[str, ...],
    tmp_path: Path,
) -> None:
    first = _run_generator(generator, tmp_path / "first")
    second = _run_generator(generator, tmp_path / "second")

    first_outputs = {path.name for path in first.glob("*.svg")}
    second_outputs = {path.name for path in second.glob("*.svg")}
    assert first_outputs == set(expected)
    assert second_outputs == set(expected)

    for output_name in expected:
        first_svg = (first / output_name).read_text(encoding="utf-8")
        second_svg = (second / output_name).read_text(encoding="utf-8")
        assert CYRILLIC_RE.search(first_svg), output_name
        cjk_checked_svg = first_svg
        for allowed_text in CJK_ALLOWLIST.get(output_name, ()):
            assert allowed_text in cjk_checked_svg, output_name
            cjk_checked_svg = cjk_checked_svg.replace(allowed_text, "")
        assert not CJK_RE.search(cjk_checked_svg), output_name
        assert first_svg == second_svg, output_name


def test_generator_inventory_contains_exactly_77_svg_outputs() -> None:
    assert len(EXPECTED_OUTPUTS) == 77


def test_derived_files_manifest_matches_promoted_outputs() -> None:
    # These generators reproduce the preserved v1.2 edition, not v2 figure numbers.
    manifest_path = ROOT / "updates/v1.2/derived-files.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert {key: value for key, value in manifest.items() if key != "outputs"} == {
        "schema_version": 1,
        "upstream_commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
    }
    records = cast(list[dict[str, str]], manifest["outputs"])
    assert isinstance(records, list)
    assert len(records) == 72
    assert [record["path"] for record in records] == sorted(
        f"book/images/{output_name}" for output_name in PROMOTED_OUTPUTS
    )

    for record in records:
        assert set(record) == {
            "path",
            "sha256",
            "generator",
            "generator_sha256",
            "command",
            "status",
        }
        generator_path = ROOT / record["generator"]
        assert generator_path.is_file()
        assert SHA256_RE.fullmatch(record["sha256"])
        assert SHA256_RE.fullmatch(record["generator_sha256"])
        baseline = ROOT / "updates/v1.2/images" / Path(record["path"]).name
        assert record["sha256"] == _sha256(baseline)
        assert record["generator_sha256"] == _sha256(generator_path)
        assert record["command"].endswith("--output-dir .tmp/generated-images")
        assert record["status"] == "generated"


def test_current_derived_manifest_covers_only_current_assets() -> None:
    manifest = json.loads((ROOT / "derived-files.json").read_text())
    assert manifest["schema_version"] == 2
    assert manifest["upstream_commit"] == "c3352738f4b6fe42fe34e3cf6a79bcb424a133b8"
    assert len(manifest["outputs"]) == 114
    for record in manifest["outputs"]:
        assert record["sha256"] == _sha256(ROOT / record["path"])
        assert record["status"] in {
            "baseline-reuse",
            "gpt-translation",
            "upstream-technical-labels",
            "editorial-correction",
        }
