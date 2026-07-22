from __future__ import annotations

from pathlib import Path

import pytest

from scripts.pdf_provenance import (
    ProvenanceError,
    record_provenance,
    source_fingerprint,
    verify_provenance,
)


def _source_tree(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "book").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "book/chapter.md").write_text("исходник", encoding="utf-8")
    (root / "book/build_pdf.sh").write_text("pandoc", encoding="utf-8")
    (root / "scripts/render_svg_assets.py").write_text("scale = 4", encoding="utf-8")
    return root


def test_source_fingerprint_tracks_build_inputs_but_ignores_dist(tmp_path: Path) -> None:
    root = _source_tree(tmp_path)
    original = source_fingerprint(root)

    (root / "dist").mkdir()
    (root / "dist/book.pdf").write_bytes(b"published")
    assert source_fingerprint(root) == original

    (root / "book/chapter.md").write_text("изменённый исходник", encoding="utf-8")
    assert source_fingerprint(root) != original


def test_provenance_rejects_changed_source_or_pdf(tmp_path: Path) -> None:
    root = _source_tree(tmp_path)
    pdf = root / ".tmp/book.pdf"
    pdf.parent.mkdir()
    pdf.write_bytes(b"pdf-v1")
    provenance = root / ".tmp/pdf-provenance.json"
    record_provenance(root, pdf, provenance)

    verify_provenance(root, pdf, provenance)

    chapter = root / "book/chapter.md"
    original_chapter = chapter.read_text(encoding="utf-8")
    chapter.write_text("новая версия", encoding="utf-8")
    with pytest.raises(ProvenanceError, match="исходник"):
        verify_provenance(root, pdf, provenance)

    chapter.write_text(original_chapter, encoding="utf-8")
    pdf.write_bytes(b"pdf-v2")
    with pytest.raises(ProvenanceError, match="PDF"):
        verify_provenance(root, pdf, provenance)
