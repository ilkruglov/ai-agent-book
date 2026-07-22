#!/usr/bin/env python3
"""Сгенерировать изображение для обложки книги с помощью модели генерации изображений.

Вполне уместно, что книга сама применяет описанный в ней подход: обложка книги
об AI-агентах создаётся посредством вызова модели генерации изображений.
Запустите скрипт один раз; при наличии images/cover-image.png файл обложки
(cover.tex) автоматически переключится на это изображение — другие изменения
не требуются. После этого в колофоне можно указать, что обложка сгенерирована
искусственным интеллектом.

Использование (OpenAI, поставщик по умолчанию):
    pip install openai
    export OPENAI_API_KEY=sk-...
    python gen_cover.py

Смена поставщика: отредактируйте функцию generate() ниже. Добавлены заготовки
и примечания для «Тунъи Ваньсян» (DashScope), Jimeng/Kolors и Flux
(fal / Replicate) — выберите доступный вам вариант. Главное здесь — промпт,
который не зависит от поставщика.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from svg_lib import parse_output_dir

# ── Промпт ────────────────────────────────────────────────────────────────
# Оммаж «книгам с животными» O'Reilly: одно изображение животного в стиле
# ксилографии или гравюры на чистом белом фоне, поверх которого cover.tex
# размещает заголовок с засечками. Осьминог подходит для книги об агентах:
# он очень умён, известен использованием инструментов, а восемь его относительно
# автономных щупалец напоминают один мозг с множеством инструментов или рук
# и даже многоагентную систему. При желании замените животное в промпте.
PROMPT = (
    "Vintage scientific engraving illustration of an octopus, in the classic style of "
    "19th-century natural-history woodcuts and the O'Reilly animal book covers. Finely "
    "detailed black pen-and-ink crosshatching and fine line work; pure black line art, "
    "no color, no gray wash, no shading fills. The whole octopus rendered elegantly with "
    "gracefully curling tentacles, anatomically believable, slightly stylized. Perfectly "
    "clean pure white background, no scenery, no frame, no border, no text, no lettering, "
    "no numbers. Centered composition, crisp, high detail."
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "cover-image.png")


class _ImageData(Protocol):
    b64_json: str | None
    url: str | None


class _ImageResponse(Protocol):
    data: Sequence[_ImageData]


class _ImagesEndpoint(Protocol):
    def generate(
        self,
        *,
        model: str,
        prompt: str,
        size: str,
        quality: str,
        n: int,
        style: str = "natural",
    ) -> _ImageResponse: ...


class _OpenAIClient(Protocol):
    images: _ImagesEndpoint


def generate_openai(prompt: str, out: str) -> None:
    """OpenAI Images API. Использует gpt-image-1, если она доступна, иначе dall-e-3."""
    import base64
    import urllib.request

    factory = cast(Callable[[], _OpenAIClient], import_module("openai").OpenAI)
    client = factory()
    try:
        # gpt-image-1: лучше всего следует промпту; возвращает данные в base64.
        # Портретный формат 1024x1536.
        r = client.images.generate(
            model="gpt-image-1", prompt=prompt, size="1024x1536", quality="high", n=1
        )
        encoded = r.data[0].b64_json
        if encoded is None:
            raise RuntimeError("gpt-image-1 не вернула изображение в base64")
        Path(out).write_bytes(base64.b64decode(encoded))
    except Exception as e:
        print(f"gpt-image-1 недоступна ({e}); переход на dall-e-3 …")
        r = client.images.generate(
            model="dall-e-3", prompt=prompt, size="1024x1792", quality="hd", style="natural", n=1
        )
        url = r.data[0].url
        if url is None:
            raise RuntimeError("dall-e-3 не вернула URL изображения") from e
        urllib.request.urlretrieve(url, out)


# ── Альтернативные поставщики (раскомментируйте и адаптируйте нужный) ─────
# def generate_dashscope(prompt, out):   # Alibaba «Тунъи Ваньсян» (wanx)
#     import dashscope  # pip install dashscope ; export DASHSCOPE_API_KEY=...
#     rsp = dashscope.ImageSynthesis.call(model="wanx-v1", prompt=prompt,
#                                         n=1, size="1024*1536")
#     import urllib.request
#     urllib.request.urlretrieve(rsp.output.results[0].url, out)
#
# def generate_fal(prompt, out):         # Flux через fal.ai
#     import fal_client, urllib.request   # pip install fal-client ; export FAL_KEY=...
#     r = fal_client.run("fal-ai/flux-pro/v1.1",
#                        arguments={"prompt": prompt, "image_size": "portrait_4_3"})
#     urllib.request.urlretrieve(r["images"][0]["url"], out)


def generate(prompt: str, out: str) -> None:
    generate_openai(prompt, out)  # ← укажите здесь своего поставщика


def main(output_dir: str) -> None:
    out = os.path.join(output_dir, "cover-image.png")
    os.makedirs(output_dir, exist_ok=True)
    print("Генерация изображения для обложки …")
    generate(PROMPT, out)
    print(f"Сохранено в {out}")
    print("Теперь пересоберите книгу: bash build_pdf.sh")


if __name__ == "__main__":
    main(parse_output_dir(os.path.dirname(OUT)))
