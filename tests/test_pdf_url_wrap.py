from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_long_bare_footnote_url_is_linked_and_wraps_inside_page() -> None:
    parser = re.search(r"--from ([\w+-]+)", (ROOT / "book/build_pdf.sh").read_text())
    assert parser is not None
    markdown = (
        "Текст со ссылкой[^source].\n\n"
        "[^source]: XLeRobot, документация. "
        "https://xlerobot.readthedocs.io/en/latest/software/getting_started/LLM_agent.html.\n\n"
        "~~~python\npass\n~~~\n"
    )
    generated = subprocess.run(
        [
            "pandoc",
            "--from",
            parser[1],
            "--to",
            "latex",
            "--standalone",
            "-V",
            "documentclass=elegantbook",
            "-V",
            "classoption=lang=en",
            "-V",
            "classoption=device=normal",
            "-V",
            "lang=ru-RU",
            "-H",
            str(ROOT / "book/preamble.tex"),
        ],
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
    )
    assert r"\url{https://xlerobot.readthedocs.io/" in generated.stdout
    build_root = ROOT / ".tmp"
    build_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pdf-url-wrap-", dir=build_root) as directory:
        work = Path(directory)
        (work / "probe.tex").write_text(generated.stdout)
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-no-pdf", "probe.tex"],
            cwd=work,
            env={**os.environ, "TEXINPUTS": f"{ROOT / 'book/vendor/elegantbook'}:"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout
        log = (work / "probe.log").read_text(errors="replace")
        assert "Overfull \\hbox" not in log
        assert "Missing character:" not in log
