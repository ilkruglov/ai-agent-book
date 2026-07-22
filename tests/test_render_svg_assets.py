from __future__ import annotations

from pathlib import Path

import pytest

from scripts.render_svg_assets import SvgRenderError, build_chrome_command, parse_svg_size


def test_parse_svg_size_reads_explicit_dimensions(tmp_path: Path) -> None:
    svg = tmp_path / "figure.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="780" height="440" viewBox="0 40 780 440"/>',
        encoding="utf-8",
    )

    assert parse_svg_size(svg) == (780, 440)


def test_parse_svg_size_falls_back_to_viewbox(tmp_path: Path) -> None:
    svg = tmp_path / "figure.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 40 950.2 460.1"/>',
        encoding="utf-8",
    )

    assert parse_svg_size(svg) == (951, 461)


def test_parse_svg_size_rejects_non_pixel_units(tmp_path: Path) -> None:
    svg = tmp_path / "figure.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10cm" height="5cm"/>',
        encoding="utf-8",
    )

    with pytest.raises(SvgRenderError, match="размер"):
        parse_svg_size(svg)


def test_chrome_command_requests_three_times_device_scale(tmp_path: Path) -> None:
    source = tmp_path / "figure.svg"
    output = tmp_path / "figure.png"

    command = build_chrome_command(
        chrome="/usr/bin/google-chrome",
        source=source,
        output=output,
        width=780,
        height=440,
        scale=3,
    )

    assert command[0] == "/usr/bin/google-chrome"
    assert "--disable-dev-shm-usage" in command
    assert "--force-device-scale-factor=3" in command
    assert "--window-size=780,440" in command
    assert f"--screenshot={output.resolve()}" in command
    assert command[-1] == source.resolve().as_uri()
