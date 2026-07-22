from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TypedDict, cast

SCHEMA_VERSION = 1
EXPLICIT_SCRIPT_INPUTS = (
    "scripts/render_svg_assets.py",
    "scripts/pdf_provenance.py",
)


class ProvenanceDocument(TypedDict):
    schema_version: int
    source_sha256: str
    pdf_sha256: str


class ProvenanceError(RuntimeError):
    """Собранный PDF не соответствует текущим исходникам или provenance."""


def _iter_source_files(root: Path) -> Iterator[Path]:
    book_dir = root / "book"
    if not book_dir.is_dir():
        raise ProvenanceError(f"Не найден каталог исходников: {book_dir}")
    for path in sorted(book_dir.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            yield path
    for relative_path in EXPLICIT_SCRIPT_INPUTS:
        path = root / relative_path
        if path.is_file():
            yield path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_fingerprint(root: Path) -> str:
    resolved_root = root.resolve()
    digest = hashlib.sha256(b"ai-agent-book-pdf-sources-v1\0")
    files = tuple(_iter_source_files(resolved_root))
    if not files:
        raise ProvenanceError("Список исходников PDF пуст")
    for path in files:
        relative = path.relative_to(resolved_root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def record_provenance(root: Path, pdf: Path, output: Path) -> None:
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise ProvenanceError(f"PDF не найден или пуст: {pdf}")
    document: ProvenanceDocument = {
        "schema_version": SCHEMA_VERSION,
        "source_sha256": source_fingerprint(root),
        "pdf_sha256": _file_sha256(pdf),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        json.dump(document, temporary_file, ensure_ascii=False, indent=2)
        temporary_file.write("\n")
    temporary_path.replace(output)


def _load_provenance(path: Path) -> ProvenanceDocument:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProvenanceError(f"Не удалось прочитать provenance: {path}") from error
    if not isinstance(raw, dict):
        raise ProvenanceError("Некорректный формат provenance")
    document = cast(dict[str, object], raw)
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ProvenanceError("Неподдерживаемая версия provenance")
    source_sha256 = document.get("source_sha256")
    pdf_sha256 = document.get("pdf_sha256")
    if not isinstance(source_sha256, str) or not isinstance(pdf_sha256, str):
        raise ProvenanceError("В provenance отсутствуют SHA-256")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_sha256": source_sha256,
        "pdf_sha256": pdf_sha256,
    }


def verify_provenance(root: Path, pdf: Path, provenance: Path) -> None:
    document = _load_provenance(provenance)
    if source_fingerprint(root) != document["source_sha256"]:
        raise ProvenanceError("PDF собран из другой версии исходников")
    if not pdf.is_file() or _file_sha256(pdf) != document["pdf_sha256"]:
        raise ProvenanceError("PDF не соответствует записанному SHA-256")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Записать или проверить provenance PDF")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("record", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--root", required=True, type=Path)
        subparser.add_argument("--pdf", required=True, type=Path)
        subparser.add_argument("--provenance", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "record":
            record_provenance(arguments.root, arguments.pdf, arguments.provenance)
        else:
            verify_provenance(arguments.root, arguments.pdf, arguments.provenance)
    except ProvenanceError as error:
        print(f"pdf-provenance-error: {error}", file=sys.stderr)
        return 1
    print(f"PDF provenance: {arguments.command} OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
