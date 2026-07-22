from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PIXEL_SIZE_RE = re.compile(r"\s*(\d+(?:\.\d+)?)\s*")
RENDER_TIMEOUT_SECONDS = 60


class SvgRenderError(RuntimeError):
    """SVG нельзя безопасно отрендерить браузером для PDF."""


def _pixel_size(value: str | None) -> float | None:
    if value is None:
        return None
    match = PIXEL_SIZE_RE.fullmatch(value)
    if match is None:
        raise SvgRenderError(f"Некорректный размер SVG: {value!r}")
    size = float(match.group(1))
    if not math.isfinite(size) or size <= 0:
        raise SvgRenderError(f"Некорректный размер SVG: {value!r}")
    return size


def parse_svg_size(path: Path) -> tuple[int, int]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise SvgRenderError(f"Некорректный XML в {path}: {error}") from error

    width = _pixel_size(root.get("width"))
    height = _pixel_size(root.get("height"))
    if width is None or height is None:
        raw_viewbox = root.get("viewBox", "").replace(",", " ").split()
        if len(raw_viewbox) != 4:
            raise SvgRenderError(f"Не удалось определить размер SVG: {path}")
        try:
            width = float(raw_viewbox[2])
            height = float(raw_viewbox[3])
        except ValueError as error:
            raise SvgRenderError(f"Некорректный viewBox в {path}") from error
        if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
            raise SvgRenderError(f"Некорректный viewBox в {path}")
    return math.ceil(width), math.ceil(height)


def build_chrome_command(
    *,
    chrome: str,
    source: Path,
    output: Path,
    width: int,
    height: int,
    scale: int,
) -> tuple[str, ...]:
    return (
        chrome,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--run-all-compositor-stages-before-draw",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        f"--screenshot={output.resolve()}",
        source.resolve().as_uri(),
    )


def render_svg(
    source: Path,
    output: Path,
    *,
    chrome: str,
    scale: int,
) -> None:
    width, height = parse_svg_size(source)
    try:
        result = subprocess.run(
            build_chrome_command(
                chrome=chrome,
                source=source,
                output=output,
                width=width,
                height=height,
                scale=scale,
            ),
            check=False,
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise SvgRenderError(
            f"Chrome не завершил рендер {source.name} за {RENDER_TIMEOUT_SECONDS} с"
        ) from error
    if result.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
        detail = result.stderr.strip() or result.stdout.strip() or "без diagnostics"
        raise SvgRenderError(f"Chrome не отрендерил {source.name}: {detail}")


def render_directory(
    input_dir: Path,
    output_dir: Path,
    *,
    chrome: str,
    scale: int,
    jobs: int,
) -> int:
    sources = sorted(input_dir.glob("*.svg"))
    if not sources:
        raise SvgRenderError(f"В каталоге нет SVG: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    def render(source: Path) -> None:
        render_svg(
            source,
            output_dir / f"{source.stem}.png",
            chrome=chrome,
            scale=scale,
        )

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        list(executor.map(render, sources))
    return len(sources)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Отрендерить SVG браузером в PNG высокого разрешения для PDF"
    )
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--chrome", default="google-chrome")
    parser.add_argument("--scale", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.scale < 1 or arguments.jobs < 1:
        print("svg-render-error: scale и jobs должны быть положительными", file=sys.stderr)
        return 2
    try:
        count = render_directory(
            arguments.input_dir.resolve(),
            arguments.output_dir.resolve(),
            chrome=arguments.chrome,
            scale=arguments.scale,
            jobs=arguments.jobs,
        )
    except (OSError, SvgRenderError) as error:
        print(f"svg-render-error: {error}", file=sys.stderr)
        return 1
    print(f"SVG browser render: OK, файлов {count}, scale {arguments.scale}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
