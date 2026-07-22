from __future__ import annotations

from pathlib import Path

import pytest

import scripts.render_svg_assets as renderer
from scripts.render_svg_assets import (
    SvgRenderError,
    build_chrome_command,
    parse_svg_size,
    render_svg,
)


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


def test_chrome_command_uses_requested_device_scale(tmp_path: Path) -> None:
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


def test_render_svg_does_not_accept_stale_output_when_chrome_writes_nothing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "figure.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"/>',
        encoding="utf-8",
    )
    output = tmp_path / "figure.png"
    output.write_bytes(b"stale image")
    fake_chrome = tmp_path / "fake-chrome"
    fake_chrome.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_chrome.chmod(0o755)

    with pytest.raises(SvgRenderError, match="не отрендерил"):
        render_svg(source, output, chrome=str(fake_chrome), scale=4)


def test_render_svg_retries_once_after_transient_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "figure.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"/>',
        encoding="utf-8",
    )
    output = tmp_path / "figure.png"
    counter = tmp_path / "attempts"
    fake_chrome = tmp_path / "fake-chrome"
    fake_chrome.write_text(
        "#!/bin/sh\n"
        f"counter='{counter}'\n"
        "attempt=0\n"
        'if [ -f "$counter" ]; then attempt=$(cat "$counter"); fi\n'
        "attempt=$((attempt + 1))\n"
        'printf \'%s\' "$attempt" > "$counter"\n'
        'if [ "$attempt" -eq 1 ]; then sleep 0.2; fi\n'
        'for argument in "$@"; do\n'
        '  case "$argument" in\n'
        "    --screenshot=*) output=${argument#--screenshot=} ; printf 'fresh' > \"$output\" ;;\n"
        "  esac\n"
        "done\n",
        encoding="utf-8",
    )
    fake_chrome.chmod(0o755)
    monkeypatch.setattr(renderer, "RENDER_TIMEOUT_SECONDS", 0.05)

    render_svg(source, output, chrome=str(fake_chrome), scale=4)

    assert counter.read_text(encoding="utf-8") == "2"
    assert output.read_bytes() == b"fresh"
