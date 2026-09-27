from __future__ import annotations

import os
import re
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def _image(width: int, height: int) -> bytes:
    row = b"\0" + b"\xff\xff\xff" * width
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(row * height))
        + _chunk(b"IEND", b"")
    )


def test_tall_figure_is_readable_and_fits_with_multiline_caption() -> None:
    build_root = ROOT / ".tmp"
    build_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pdf-image-size-", dir=build_root) as directory:
        work = Path(directory)
        image = work / "figure.png"
        image.write_bytes(_image(780, 832))
        tex = work / "probe.tex"
        tex.write_text(
            rf"""\documentclass[lang=en,cyan,device=normal]{{elegantbook}}
\newenvironment{{Shaded}}{{}}{{}}
\input{{{ROOT / "book/preamble.tex"}}}
\newsavebox{{\probeimage}}
\newsavebox{{\probefigure}}
\begin{{document}}
\sbox{{\probeimage}}{{\includegraphics{{{image}}}}}
\setbox\probefigure=\vbox{{
  \hsize=\linewidth
  \centering
  \includegraphics{{{image}}}\par
  \captionof{{figure}}{{Рисунок 0-1. Достаточно длинная подпись к рисунку,
  занимающая несколько строк и поясняющая его архитектуру.}}
}}
\typeout{{PROBE-LINEWIDTH=\the\linewidth}}
\typeout{{PROBE-TEXTHEIGHT=\the\textheight}}
\typeout{{PROBE-IMAGE-WIDTH=\the\wd\probeimage}}
\typeout{{PROBE-IMAGE-HEIGHT=\the\ht\probeimage}}
\typeout{{PROBE-FIGURE-HEIGHT=\the\dimexpr\ht\probefigure+\dp\probefigure\relax}}
\end{{document}}
""",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-no-pdf", tex.name],
            cwd=work,
            env={
                **os.environ,
                "TEXINPUTS": (
                    f"{ROOT / 'book/vendor/elegantbook'}:{os.environ.get('TEXINPUTS', '')}"
                ),
            },
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout
        sizes = {
            name: float(value)
            for name, value in re.findall(r"PROBE-([A-Z-]+)=([0-9.]+)pt", result.stdout)
        }
        assert sizes.keys() == {
            "LINEWIDTH",
            "TEXTHEIGHT",
            "IMAGE-WIDTH",
            "IMAGE-HEIGHT",
            "FIGURE-HEIGHT",
        }
        assert sizes["IMAGE-HEIGHT"] >= 450, sizes
        assert sizes["IMAGE-WIDTH"] <= sizes["LINEWIDTH"] + 0.1
        assert abs(sizes["IMAGE-HEIGHT"] / sizes["IMAGE-WIDTH"] - 832 / 780) < 0.01
        assert sizes["FIGURE-HEIGHT"] <= sizes["TEXTHEIGHT"] - 20


def test_circled_digits_have_glyphs_in_xelatex() -> None:
    build_root = ROOT / ".tmp"
    build_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pdf-circled-digits-", dir=build_root) as directory:
        work = Path(directory)
        tex = work / "probe.tex"
        tex.write_text(
            rf"""\documentclass[lang=en,cyan,device=normal]{{elegantbook}}
\newenvironment{{Shaded}}{{}}{{}}
\input{{{ROOT / "book/preamble.tex"}}}
\begin{{document}}
①②③④⑤
\end{{document}}
""",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-no-pdf", tex.name],
            cwd=work,
            env={
                **os.environ,
                "TEXINPUTS": (
                    f"{ROOT / 'book/vendor/elegantbook'}:{os.environ.get('TEXINPUTS', '')}"
                ),
            },
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout
        log = tex.with_suffix(".log").read_text(encoding="utf-8", errors="replace")
        assert "Missing character:" not in log
