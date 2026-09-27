from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import cast

if __package__:
    from scripts.check_translation import MANIFEST_RUNTIME_KEYS, TRANSLATION_NOTICE
    from scripts.model_runner import EXACT_MODEL
else:
    from check_translation import (  # pyright: ignore[reportImplicitRelativeImport]
        MANIFEST_RUNTIME_KEYS,
        TRANSLATION_NOTICE,
    )
    from model_runner import EXACT_MODEL  # pyright: ignore[reportImplicitRelativeImport]


@dataclass(frozen=True)
class BaselinePair:
    path: str
    source: str
    translation: str
    runtime: dict[str, object]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("baseline: expected object")
    return cast(dict[str, object], value)


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("baseline: expected array")
    return cast(list[object], value)


def _slice(text: str, item: dict[str, object], prefix: str) -> tuple[str, int, int]:
    start, end = item.get(prefix + "_start"), item.get(prefix + "_end")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        raise ValueError("baseline: invalid chunk range")
    return text[start:end], start, end


def _runtime(value: object) -> dict[str, object]:
    runtime = _object(value)
    expected: dict[str, object] = {
        "requested_model": EXACT_MODEL,
        "reported_model": EXACT_MODEL,
        "provider": "openai",
        "ephemeral": True,
        "fallback_allowed": False,
        "sandbox_type": "readOnly",
        "completion_observed": True,
        "usage_observed": True,
    }
    if set(runtime) != MANIFEST_RUNTIME_KEYS or any(
        type(runtime.get(key)) is not type(value) or runtime.get(key) != value
        for key, value in expected.items()
    ):
        raise ValueError("baseline: GPT runtime evidence incomplete or contradictory")
    for key in MANIFEST_RUNTIME_KEYS - expected.keys():
        field = runtime.get(key)
        if not isinstance(field, str) or not field:
            raise ValueError("baseline: missing runtime identity")
        if key.endswith("_sha256") and re.fullmatch(r"[0-9a-f]{64}", field) is None:
            raise ValueError("baseline: invalid runtime hash")
    return runtime


def load_baseline(
    source_root: Path, translation_root: Path, manifest_path: Path
) -> tuple[BaselinePair, ...]:
    document = _object(json.loads(manifest_path.read_text(encoding="utf-8")))
    pairs: list[BaselinePair] = []
    for raw_entry in _list(document.get("files")):
        entry = _object(raw_entry)
        name = entry.get("path")
        if not isinstance(name, str) or Path(name).name != name or not name.endswith(".md"):
            raise ValueError("baseline: unsafe file path")
        source = (source_root / name).read_text(encoding="utf-8")
        target = (translation_root / name).read_text(encoding="utf-8")
        if _sha(source) != _object(entry.get("source")).get("sha256"):
            raise ValueError(f"baseline: source hash mismatch: {name}")
        if _sha(target) != entry.get("final_sha256"):
            raise ValueError(f"baseline: translation hash mismatch: {name}")
        notice = TRANSLATION_NOTICE + "\n\n"
        if not target.startswith(notice):
            raise ValueError(f"baseline: missing attribution: {name}")
        translated = target[len(notice) :]
        source_end = final_end = 0
        for raw_chunk in _list(entry.get("chunks")):
            chunk = _object(raw_chunk)
            old_source, start, end = _slice(source, chunk, "source")
            old_translation, tstart, tend = _slice(translated, chunk, "final")
            if start != source_end or tstart != final_end:
                raise ValueError(f"baseline: non-contiguous chunks: {name}")
            if _sha(old_source) != chunk.get("source_sha256"):
                raise ValueError(f"baseline: source chunk hash mismatch: {name}")
            if _sha(old_translation) != chunk.get("final_sha256"):
                raise ValueError(f"baseline: translation chunk hash mismatch: {name}")
            passes = _object(chunk.get("passes"))
            runtime = _runtime(passes.get("translation"))
            _runtime(passes.get("source_verification"))
            pairs.append(BaselinePair(name, old_source, old_translation, runtime))
            source_end, final_end = end, tend
        if source_end != len(source) or final_end != len(translated):
            raise ValueError(f"baseline: incomplete coverage: {name}")
    return tuple(pairs)


def select_baseline(source: str, pairs: tuple[BaselinePair, ...]) -> tuple[BaselinePair, ...]:
    exact = tuple(pair for pair in pairs if pair.source == source)
    if exact:
        return exact[:1]
    # Line-based comparison avoids quadratic character matching on long chapters.
    # Headings and unchanged paragraphs survive chapter moves and renumbering.
    scored: list[tuple[float, BaselinePair]] = []
    for pair in pairs:
        matcher = SequenceMatcher(
            None, pair.source.splitlines(), source.splitlines(), autojunk=False
        )
        matches = sum(block.size for block in matcher.get_matching_blocks())
        nonblank_matches = sum(
            bool(line.strip())
            for block in matcher.get_matching_blocks()
            for line in pair.source.splitlines()[block.a : block.a + block.size]
        )
        if nonblank_matches and matches:
            scored.append((matcher.ratio(), pair))
        elif source.splitlines()[:1] == pair.source.splitlines()[:1]:
            scored.append((0.01, pair))
    scored.sort(key=lambda item: item[0], reverse=True)
    return tuple(pair for _, pair in scored[:3])


def render_baseline(pairs: tuple[BaselinePair, ...]) -> str:
    if not pairs:
        return ""
    sections = [
        "\n\nОбновление существующего русского издания. Ниже — проверенные пары из старой версии. "
        "Используй их только как редакционную опору, не как новый источник. "
        "Для фрагментов, которые не изменились в новом китайском source, сохраняй наш русский "
        "перевод дословно. Переводи только новое и изменённое, удалённое не возвращай. "
        "Все номера глав, рисунков, экспериментов и ссылки бери из нового source. "
        "Верни только перевод НОВОГО chunk, не старые разделы целиком."
    ]
    for pair in pairs:
        sections.append(
            f"\nСтарая пара ({pair.path}):\nКитайский оригинал v1.2:\n{pair.source}"
            f"\nНаш проверенный русский перевод v1.2:\n{pair.translation}"
        )
    return "\n".join(sections)
