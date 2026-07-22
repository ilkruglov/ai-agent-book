#!/usr/bin/env python3
"Создаёт все SVG-иллюстрации для главы 3 (База знаний и RAG).\n\nИллюстрации (всего 14):\n  fig3-1:  Карта главы\n  fig3-2:  Сквозной конвейер RAG (конкретный пример)\n  fig3-3:  Эволюция плотных эмбеддингов (размерности и обучение)\n  fig3-4:  Структура индекса HNSW (увеличенная)\n  fig3-5:  Механизм оценки BM25 (увеличенный)\n  fig3-6:  Гибридный поиск + переранжирование и переранжирование (с оценками)\n  fig3-7:  Древовидная структура RAPTOR (увеличенная)\n  fig3-8:  Сеть связей GraphRAG (увеличенная)\n  fig3-9:  AI-агентный и неагентный RAG (конкретные запросы)\n  fig3-10: Архитектура агентного RAG (эксп. 3.6)\n  fig3-11: Контекстный поиск (конкретный пример префикса)\n  fig3-12: Конвейер извлечения структурированных знаний (эксп. 3.10)\n  fig3-13: Внешний цикл обучения (конкретный пример)\n  fig3-14: Обучение на опыте GAIA (эксп. 3.11)\n"

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    COLORS,
    FS_BODY,
    FS_SMALL,
    FS_TINY,
    FS_TITLE,
    STROKE_W,
    SVG,
    parse_output_dir,
)

_output_dir = os.path.join(os.path.dirname(__file__), "images")


# ──────────────────────── fig3-1 ────────────────────────


def fig3_1() -> None:
    """Карта знаний главы"""
    w, h = 860, 580
    svg = SVG(w, h)

    svg.text(w / 2, 32, "Глава 3: база знаний и RAG — карта главы", size=FS_TITLE, bold=True)

    # --- Ряд 1: основы RAG ---
    r1_y = 70
    svg.rect(30, r1_y, 800, 130, fill="white", stroke="border", dash=True)
    svg.text(80, r1_y + 20, "Основы RAG", size=FS_BODY, bold=True, anchor="start")

    boxes_r1 = [
        ("Плотные эмбеддинги", 50, "Word2Vec → BGE-M3"),
        ("Разреженные эмбеддинги", 230, "TF-IDF / BM25"),
        ("Гибридный поиск + переранжирование", 410, "Два канала поиска + Cross-Encoder"),
        ("Мультимодальное извлечение", 650, "Напрямую / текст / инструменты"),
    ]
    for label, bx, sub in boxes_r1:
        svg.box(bx, r1_y + 38, 160, 50, label, fill="light", bold=True, font_size=FS_SMALL)
        svg.text(bx + 80, r1_y + 38 + 50 + 18, sub, size=FS_TINY, fill="text_light")

    # --- Стрелка вниз ---
    svg.arrow(w / 2, r1_y + 130, w / 2, r1_y + 160)

    # --- Ряд 2: расширенное структурирование знаний ---
    r2_y = 230
    svg.rect(30, r2_y, 800, 100, fill="white", stroke="border", dash=True)
    svg.text(80, r2_y + 20, "Обучение на готовых знаниях", size=FS_BODY, bold=True, anchor="start")

    boxes_r2 = [
        ("RAPTOR\nИерархический индекс", 50),
        ("GraphRAG\nГраф связей сущностей", 230),
        ("AI-агентный RAG\nПоиск как инструмент", 410),
        ("Контекстный поиск\nСводка в префиксе", 590),
    ]
    for label, bx in boxes_r2:
        svg.box(bx, r2_y + 35, 160, 55, label, fill="medium", font_size=FS_SMALL)

    # --- Стрелка вниз ---
    svg.arrow(w / 2, r2_y + 100, w / 2, r2_y + 130)

    # --- Ряд 3: обучение на опыте ---
    r3_y = 360
    svg.rect(30, r3_y, 800, 100, fill="white", stroke="border", dash=True)
    svg.text(
        80,
        r3_y + 20,
        "Обучение через самостоятельное исследование",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )

    boxes_r3 = [
        ("Постобучение\nRL → «мышечная память»", 100),
        ("Контекстное обучение\nМягкий поиск при инференсе", 330),
        ("Экстернализованное обучение\nБаза знаний + создание инструментов", 560),
    ]
    for label, bx in boxes_r3:
        svg.box(bx, r3_y + 35, 200, 55, label, fill="light", font_size=FS_SMALL)

    # --- Внизу: ключевая идея ---
    svg.rect(180, 490, 500, 44, fill="dark")
    svg.text(
        w / 2,
        512,
        "Горький урок: поиск + обучение = универсальный подход",
        size=FS_BODY,
        fill="white",
        bold=True,
    )
    svg.arrow(w / 2, r3_y + 100, w / 2, 488)

    svg.save(os.path.join(_output_dir, "fig3-1.svg"))


# ──────────────────────── fig3-2 ────────────────────────


def fig3_2() -> None:
    """Сквозной конвейер RAG (конкретный пример)"""
    w, h = 880, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Сквозной конвейер RAG", size=FS_TITLE, bold=True)

    # Шаг 1: пользовательский запрос
    svg.box(20, 65, 180, 55, "① Запрос пользователя", fill="medium", bold=True, font_size=FS_BODY)
    q_lines = ['"Как наказывают за убийство?"']
    svg.text(110, 145, q_lines[0], size=FS_SMALL, fill="text_light")

    svg.arrow(200, 92, 238, 92)

    # Шаг 2: поиск
    svg.box(240, 65, 180, 55, "② Поиск", fill="light", bold=True, font_size=FS_BODY)
    svg.text(330, 140, "Плотный поиск + BM25", size=FS_SMALL, fill="text_light")
    svg.text(330, 160, "→ Top-K фрагментов", size=FS_SMALL, fill="text_light")

    svg.arrow(420, 92, 458, 92)

    # Шаг 3: дополнение
    svg.box(460, 65, 180, 55, "③ Дополнение", fill="light", bold=True, font_size=FS_BODY)
    svg.text(550, 140, "Запрос + результаты поиска", size=FS_SMALL, fill="text_light")
    svg.text(550, 160, "→ полный промпт", size=FS_SMALL, fill="text_light")

    svg.arrow(640, 92, 678, 92)

    # Шаг 4: генерация
    svg.box(680, 65, 180, 55, "④ Генерация", fill="medium", bold=True, font_size=FS_BODY)
    svg.text(770, 140, "LLM объединяет контекст", size=FS_SMALL, fill="text_light")
    svg.text(770, 160, "→ создаёт ответ", size=FS_SMALL, fill="text_light")

    # Конкретный пример потока данных
    svg.line(20, 195, 860, 195, color="dark", dash=True)
    svg.text(w / 2, 215, "Пример потока данных", size=FS_BODY, bold=True)

    # Найденные фрагменты
    svg.rect(20, 235, 400, 90, fill="code_bg", stroke="dark", rx=4)
    svg.text(220, 253, "Найденные фрагменты", size=FS_SMALL, bold=True)
    svg.mono(30, 278, "УК КНР, ст. 232: за убийство — смертная казнь,", size=FS_TINY)
    svg.mono(30, 298, "пожизненный срок или не менее 10 лет...", size=FS_TINY)

    # Дополненный промпт
    svg.rect(440, 235, 420, 90, fill="code_bg", stroke="dark", rx=4)
    svg.text(650, 253, "Дополненный промпт", size=FS_SMALL, bold=True)
    svg.mono(450, 278, "Ответьте по приведённой норме закона:", size=FS_TINY)
    svg.mono(450, 298, "[УК КНР, ст. 232...] Вопрос: как наказывают за убийство?", size=FS_TINY)

    # Сгенерированный ответ
    svg.rect(20, 345, 840, 80, fill="light", stroke="border")
    svg.text(w / 2, 363, "Сгенерированный ответ", size=FS_SMALL, bold=True)
    svg.mono(
        30,
        390,
        "По ст. 232 УК КНР: смертная казнь, пожизненное заключение или не менее 10 лет;",
        size=FS_TINY,
    )
    svg.mono(30, 412, "в менее тяжких случаях — от 3 до 10 лет лишения свободы.", size=FS_TINY)

    svg.save(os.path.join(_output_dir, "fig3-2.svg"))


# ──────────────────────── fig3-3 ────────────────────────


def fig3_3() -> None:
    """Эволюция плотных эмбеддингов"""
    w, h = 860, 340
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Эволюция плотных эмбеддингов", size=FS_TITLE, bold=True)

    items = [
        (
            "Word2Vec",
            "2013",
            "300 измерений\nСтатический вектор слова",
            "Совместная встречаемость\nОбучение предсказанию",
        ),
        (
            "GloVe",
            "2014",
            "300 измерений\nОбщая статистика",
            "Разложение матрицы\n+ совместные частоты",
        ),
        ("BERT", "2018", "768 измерений\nУчёт контекста", "Transformer\nПредобучение MLM"),
        (
            "Sentence-BERT",
            "2019",
            "768 измерений\nЭмбеддинг предложения",
            "Сиамская сеть\nКонтрастивное обучение",
        ),
        (
            "BGE-M3",
            "2024",
            "1024 измерения\nДлинные многоязычные тексты",
            "Несколько этапов\nСмешанное обучение",
        ),
    ]
    n = len(items)
    pad_l, pad_r = 80, 80
    usable = w - pad_l - pad_r
    gap = usable / (n - 1)
    line_y = 90

    svg.line(pad_l - 30, line_y, w - pad_r + 30, line_y, color="dark")
    svg.elems.append(
        f'<polygon points="{w - pad_r + 30},{line_y - 6} {w - pad_r + 42},{line_y} '
        f'{w - pad_r + 30},{line_y + 6}" fill="{COLORS["dark"]}"/>'
    )

    for i, (name, year, dims, training) in enumerate(items):
        x = pad_l + i * gap
        svg.circle(x, line_y, 8, fill="dark")
        svg.text(x, line_y - 30, name, size=FS_BODY, bold=True)
        svg.text(x, line_y + 28, year, size=FS_SMALL, fill="text_light")

        svg.rect(x - 65, line_y + 50, 130, 55, fill="light")
        for j, dl in enumerate(dims.split("\n")):
            svg.text(x, line_y + 68 + j * 22, dl, size=FS_SMALL)

        svg.rect(x - 65, line_y + 115, 130, 55, fill="code_bg", stroke="dark", rx=4)
        for j, tl in enumerate(training.split("\n")):
            svg.text(x, line_y + 133 + j * 22, tl, size=FS_SMALL, fill="text_light")

    # Нижние подписи
    svg.text(
        pad_l + gap * 0.5,
        h - 18,
        "Статические векторы (один на слово)",
        size=FS_SMALL,
        fill="text_light",
    )
    svg.text(
        pad_l + gap * 3.5,
        h - 18,
        "Контекстные эмбеддинги (несколько на слово)",
        size=FS_SMALL,
        fill="text_light",
    )

    svg.line(pad_l + gap * 1.5, 75, pad_l + gap * 1.5, h - 35, color="dark", dash=True)

    svg.save(os.path.join(_output_dir, "fig3-3.svg"))


# ──────────────────────── fig3-4 ────────────────────────


def fig3_4() -> None:
    """Структура индекса HNSW"""
    w, h = 750, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Структура индекса HNSW", size=FS_TITLE, bold=True)

    layers = [
        ("Уровень 2 (разреженный · дальние связи)", 70, 3),
        ("Уровень 1 (средняя плотность)", 185, 6),
        ("Уровень 0 (плотный · все узлы)", 300, 10),
    ]
    for label, base_y, count in layers:
        svg.rect(30, base_y - 30, w - 60, 90, fill="white", stroke="dark", dash=True)
        svg.text(100, base_y - 14, label, size=FS_SMALL, fill="text_light", anchor="start")
        spacing = (w - 140) / (count + 1)
        positions: list[tuple[float, float]] = []
        for j in range(count):
            cx = 70 + spacing * (j + 1)
            cy = base_y + 25
            svg.circle(cx, cy, 14, fill="light")
            positions.append((cx, cy))
        for j in range(count - 1):
            skip = 1 if count <= 6 else (2 if j % 2 == 0 else 1)
            if j + skip < count:
                x1, y1 = positions[j]
                x2, y2 = positions[j + skip]
                svg.line(x1 + 14, y1, x2 - 14, y2, color="dark")

    # Стрелки маршрута поиска
    svg.arrow(w / 2, 130, w / 2 - 50, 165, color="border")
    svg.text(w / 2 + 80, 148, "Поиск начинается сверху", size=FS_SMALL, fill="text_light")
    svg.arrow(w / 2 - 50, 245, w / 2 - 80, 280, color="border")
    svg.text(w / 2 + 60, 263, "Уточнение на каждом уровне", size=FS_SMALL, fill="text_light")

    # Ключевые свойства
    svg.rect(50, h - 45, 300, 32, fill="light")
    svg.text(200, h - 29, "Инкрементное обновление · высокая полнота", size=FS_SMALL, bold=True)
    svg.rect(400, h - 45, 300, 32, fill="code_bg", stroke="dark", rx=4)
    svg.text(550, h - 29, "Сложность запроса O(log N)", size=FS_SMALL)

    svg.save(os.path.join(_output_dir, "fig3-4.svg"))


# ──────────────────────── fig3-5 ────────────────────────


def fig3_5() -> None:
    """Механизм оценки BM25"""
    w, h = 800, 380
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Механизм оценки BM25", size=FS_TITLE, bold=True)

    # Формула
    svg.rect(40, 50, w - 80, 50, fill="code_bg", stroke="dark", rx=4)
    svg.mono(
        60,
        75,
        "Score(Q,D) = Σ IDF(qi) × TF(qi,D)×(k1+1) / (TF + k1×(1-b+b×|D|/avgdl))",
        size=FS_SMALL,
    )

    # Три компонента
    boxes = [
        (
            "Насыщение частоты термина (TF)",
            40,
            "light",
            [
                "k₁ задаёт скорость насыщения",
                "Частота ↑, но вклад растёт всё медленнее",
                "Пример: 5→10 вхождений",
                "Оценка растёт лишь на ~20%",
            ],
        ),
        (
            "Обратная документная частота (IDF)",
            290,
            "light",
            [
                "Показывает редкость слова",
                '"и" → IDF ≈ 0',
                '"наказание" → IDF ≈ 5.2',
                "Вес редких слов >> веса частых слов",
            ],
        ),
        (
            "Нормализация длины (b)",
            540,
            "light",
            [
                "b ∈ [0,1] — сила нормализации",
                "b=0: длина не учитывается",
                "b=1: полная нормализация",
                "Без перекоса к длинным текстам",
            ],
        ),
    ]
    for title, bx, fill, details in boxes:
        svg.rect(bx, 120, 220, 170, fill=fill)
        svg.text(bx + 110, 148, title, size=FS_BODY, bold=True)
        svg.line(bx + 20, 163, bx + 200, 163, color="dark")
        for k, line in enumerate(details):
            svg.text(bx + 110, 190 + k * 28, line, size=FS_SMALL, fill="text_light")

    # Итоговая полоса
    for bx in [150, 400, 650]:
        svg.line(bx, 290, bx, 315, color="dark")
    svg.rect(40, 315, w - 80, 48, fill="medium")
    svg.text(
        w / 2,
        339,
        "Итоговая оценка = Σ  (насыщение TF × вес IDF × нормализация длины)",
        size=FS_BODY,
        bold=True,
    )

    svg.save(os.path.join(_output_dir, "fig3-5.svg"))


# ──────────────────────── fig3-6 ────────────────────────


def fig3_6() -> None:
    """Конвейер гибридного поиска и переранжирования (с примерами оценок)"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(
        w / 2, 30, "Гибридный поиск + переранжирование и переранжирование", size=FS_TITLE, bold=True
    )

    # Запрос
    svg.rect(30, 55, 160, 50, fill="medium")
    svg.text(110, 73, "Запрос пользователя", size=FS_BODY, bold=True)
    svg.mono(110, 93, '"поведение котёнка"', size=FS_TINY, anchor="middle")

    # Плотный поиск
    svg.arrow(190, 68, 238, 68)
    svg.box(240, 50, 180, 50, "Плотный поиск", fill="light", bold=True, font_size=FS_BODY)
    svg.text(330, 118, "Смысл: котёнок ≈ кошка", size=FS_SMALL, fill="text_light")

    dense_results = [
        ('doc3: "повадки кошачьих и игры кошек..."', "cos=0.87"),
        ('doc7: "уход кошек за шерстью..."', "cos=0.82"),
        ('doc1: "основы ухода за питомцем..."', "cos=0.71"),
    ]
    for i, (doc, score) in enumerate(dense_results):
        y = 140 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill="text_light", anchor="start")

    # Разреженный поиск
    svg.arrow(190, 90, 238, 270)
    svg.box(
        240, 250, 180, 50, "Разреженный поиск (BM25)", fill="light", bold=True, font_size=FS_BODY
    )
    svg.text(330, 318, 'Точное совпадение: "котёнок"', size=FS_SMALL, fill="text_light")

    sparse_results = [
        ('doc5: "приучение котёнка к лотку..."', "BM25=8.4"),
        ('doc9: "как взять котёнка из приюта..."', "BM25=6.1"),
        ('doc2: "советы о здоровье котят..."', "BM25=3.2"),
    ]
    for i, (doc, score) in enumerate(sparse_results):
        y = 340 + i * 32
        svg.mono(250, y, doc, size=FS_TINY)
        svg.text(700, y, score, size=FS_TINY, fill="text_light", anchor="start")

    # Слияние и переранжирование
    svg.arrow(770, 180, 808, 220)
    svg.arrow(770, 370, 808, 330)

    svg.rect(790, 215, 70, 120, fill="medium")
    svg.text(825, 250, "Слияние", size=FS_BODY, bold=True)
    svg.text(825, 275, "Без дублей", size=FS_BODY, bold=True)
    svg.text(825, 300, "6→5", size=FS_SMALL, fill="text_light")

    svg.save(os.path.join(_output_dir, "fig3-6.svg"))


# ──────────────────────── fig3-7 ────────────────────────


def fig3_7() -> None:
    """Древовидная структура RAPTOR"""
    w, h = 800, 440
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Иерархический индекс RAPTOR", size=FS_TITLE, bold=True)

    # Корень
    svg.box(300, 55, 200, 50, "Общая сводка", fill="dark", bold=True, font_size=FS_BODY)
    svg.text(
        300 + 200 + 15, 80, "← Корневой узел", size=FS_SMALL, fill="text_light", anchor="start"
    )

    # Средний уровень
    mid_nodes = [("Сводка кластера A", 80), ("Сводка кластера B", 320), ("Сводка кластера C", 560)]
    for label, x in mid_nodes:
        svg.box(x, 150, 160, 48, label, fill="medium", font_size=FS_BODY)
    svg.line(400, 105, 160, 150, color="border")
    svg.line(400, 105, 400, 150, color="border")
    svg.line(400, 105, 640, 150, color="border")
    svg.text(35, 230, "Средний уровень ↑", size=FS_SMALL, fill="text_light", anchor="start")

    # Листовые узлы — 7 равномерно распределённых узких блоков без наложения
    chunks = [
        [
            (40, "Фрагмент 1"),
            (140, "Фрагмент 2"),
            (240, "Фрагмент 3"),
        ],  # Кластер A → центр кластера ~160
        [(360, "Фрагмент 4"), (460, "Фрагмент 5")],  # Кластер B → центр кластера ~410
        [(560, "Фрагмент 6"), (660, "Фрагмент 7")],  # Кластер C → центр кластера ~640
    ]
    leaf_w = 88
    mid_cxs = [160, 400, 640]
    for gi, group in enumerate(chunks):
        for cx, label in group:
            svg.box(cx, 250, leaf_w, 40, label, fill="light", font_size=FS_SMALL)
            svg.line(cx + leaf_w / 2, 250, mid_cxs[gi], 198, color="dark")
    svg.text(35, 295, "Листовой уровень ↑", size=FS_SMALL, fill="text_light", anchor="start")

    # Исходный документ
    svg.rect(40, 320, 720, 55, fill="white", stroke="dark", dash=True)
    svg.text(400, 340, "Исходный документ", size=FS_BODY, fill="text_light")
    for bx in range(60, 720, 110):
        svg.rect(bx, 350, 90, 16, fill="light")

    # Нижняя подпись
    svg.text(
        w / 2,
        h - 20,
        "Рекурсивное обобщение снизу вверх: детали → темы → обзор",
        size=FS_BODY,
        fill="text_light",
    )

    svg.save(os.path.join(_output_dir, "fig3-7.svg"))


# ──────────────────────── fig3-8 ────────────────────────


def fig3_8() -> None:
    """Сеть связей GraphRAG"""
    w, h = 750, 430
    svg = SVG(w, h)
    svg.text(w / 2, 28, "Граф сущностей и связей GraphRAG", size=FS_TITLE, bold=True)

    nodes = [
        ("Intel", 375, 100, "medium"),
        ("SSE", 150, 190, "light"),
        ("AVX", 550, 190, "light"),
        ("Регистр XMM", 100, 320, "light"),
        ("ADDPS", 280, 340, "light"),
        ("Регистр YMM", 520, 320, "light"),
        ("FP-операции", 375, 250, "light"),
    ]
    node_r = 42

    # Область сообщества рисуется первой как фон, чтобы не перекрывать узлы и связи
    svg.rect(50, 275, 300, 110, fill="none", stroke="border", dash=True)
    svg.text(200, 395, "Сообщество: набор инструкций SSE", size=FS_SMALL, fill="text_light")

    for label, x, y, fill in nodes:
        svg.circle(x, y, node_r, fill=fill, label=label, font_size=FS_SMALL)

    edges = [
        (0, 1, "разработала"),
        (0, 2, "разработала"),
        (1, 3, "использует"),
        (1, 6, ""),
        (1, 4, "содержит"),
        (2, 5, "использует"),
        (2, 6, "выполняет"),
        (6, 3, ""),
        (6, 5, "работает с"),
    ]
    for i, j, elabel in edges:
        x1, y1 = nodes[i][1], nodes[i][2]
        x2, y2 = nodes[j][1], nodes[j][2]
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        ax1 = x1 + ux * (node_r + 3)
        ay1 = y1 + uy * (node_r + 3)
        ax2 = x2 - ux * (node_r + 14)
        ay2 = y2 - uy * (node_r + 14)
        svg.arrow(ax1, ay1, ax2, ay2, label=elabel, color="dark")

    svg.save(os.path.join(_output_dir, "fig3-8.svg"))


# ──────────────────────── fig3-9 ────────────────────────


def fig3_9() -> None:
    """Сравнение агентного и неагентного RAG (конкретный пример)"""
    w, h = 880, 560
    svg = SVG(w, h)
    col_w = 400
    lx, rx = 20, 460

    # --- Слева: неагентный RAG ---
    svg.rect(lx, 50, col_w, 45, fill="medium")
    svg.text(lx + col_w / 2, 73, "Неагентный RAG", size=FS_BODY, bold=True)

    steps_l = [
        (
            'Запрос: "Как назначают наказание за тяжкий вред по неосторожности\nв состоянии опьянения при судимости за кражу?"',
            "light",
        ),
        ('Однократный поиск:\n"наказание за тяжкий вред по неосторожности"', "light"),
        ("Результат: лишь базовая норма о вреде по неосторожности\n(контекст неполон)", "code_bg"),
        ("Прямой ответ: не учтены опьянение\nи судимость", "light"),
    ]
    prev_y = 95
    for i, (s, fill) in enumerate(steps_l):
        y = 110 + i * 108
        svg.box(lx + 30, y, 340, 80, s, fill=fill, font_size=FS_SMALL)
        if i > 0:
            svg.arrow(lx + 200, prev_y + 80 + 2, lx + 200, y - 2)
        prev_y = y

    svg.text(
        lx + col_w / 2, h - 15, "Один проход · неполные данные", size=FS_BODY, fill="text_light"
    )

    # --- Разделитель ---
    svg.line(440, 50, 440, h - 5, color="dark", dash=True)

    # --- Справа: агентный RAG ---
    svg.rect(rx, 50, col_w, 45, fill="medium")
    svg.text(rx + col_w / 2, 73, "AI-агентный RAG (ReAct)", size=FS_BODY, bold=True)

    steps_r = [
        ("Размышление: нужны 3 подвопроса", "light"),
        (
            'Поиск①: "наказание за тяжкий вред по неосторожности"\nПоиск②: "ответственность при опьянении"\nПоиск③: "влияние судимости за кражу"',
            "code_bg",
        ),
        (
            "Наблюдение: базовая норма есть,\nно нет связи судимости с вредом по неосторожности",
            "light",
        ),
        ('Поиск④: "рецидив, разные составы\nразъяснения суда"', "code_bg"),
        ("Синтез: полный ответ со всеми\nнормами и анализом наказания", "medium"),
    ]
    ys: list[float] = []
    for i, (s, fill) in enumerate(steps_r):
        y = 105 + i * 86
        hh = 68
        svg.box(rx + 30, y, 340, hh, s, fill=fill, font_size=FS_SMALL)
        ys.append(y)
        if i > 0:
            svg.arrow(rx + 200, ys[i - 1] + hh + 2, rx + 200, y - 2)

    # Стрелка цикла
    loop_x = rx + 370 + 10
    svg.elems.append(
        f'<path d="M {loop_x},{ys[2] + 34} C {loop_x + 28},{ys[2] + 34} '
        f'{loop_x + 28},{ys[1] + 34} {loop_x},{ys[1] + 34}" '
        f'fill="none" stroke="{COLORS["border"]}" stroke-width="{STROKE_W}" '
        f'stroke-dasharray="6,3" marker-end="url(#ah)"/>'
    )
    svg.text(
        loop_x + 4,
        (ys[1] + ys[2]) / 2 + 34,
        "Итерация",
        size=FS_SMALL,
        fill="text_light",
        anchor="start",
    )

    svg.text(
        rx + col_w / 2,
        h - 15,
        "Несколько итераций · полные данные",
        size=FS_BODY,
        fill="text_light",
    )

    svg.save(os.path.join(_output_dir, "fig3-9.svg"))


# ──────────────────────── fig3-10 ────────────────────────


def fig3_10() -> None:
    """Архитектура агентного RAG (эксперимент 3.6)"""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Эксперимент 3.6: архитектура агентного RAG", size=FS_TITLE, bold=True)

    # Ядро агента
    svg.rect(220, 55, 440, 200, fill="white", stroke="border")
    svg.text(440, 78, "AI-агент (цикл ReAct)", size=FS_BODY, bold=True)

    # Шаги ReAct внутри агента
    react_items = [
        ("① Размышление", 240, 100, 180, 45, "light"),
        ("② Действие", 460, 100, 180, 45, "medium"),
        ("③ Наблюдение", 350, 180, 180, 45, "light"),
    ]
    for label, bx, by, bw, bh, fill in react_items:
        svg.box(bx, by, bw, bh, label, fill=fill, font_size=FS_SMALL, bold=True)

    svg.arrow(420, 122, 458, 122)
    svg.arrow(640, 130, 530, 178, color="border")
    svg.arrow(350, 202, 280, 145, color="border")

    # Подпись цикла
    svg.text(360, 165, "Цикл до получения достаточной информации", size=FS_TINY, fill="text_light")

    # Пользователь
    svg.box(20, 95, 160, 55, "Запрос пользователя", fill="medium", bold=True, font_size=FS_BODY)
    svg.arrow(180, 122, 218, 122)

    # Итоговый ответ
    svg.box(700, 95, 160, 55, "Итоговый ответ", fill="medium", bold=True, font_size=FS_BODY)
    svg.arrow(660, 122, 698, 122)

    # Слой инструментов
    svg.rect(100, 290, 680, 85, fill="white", stroke="border", dash=True)
    svg.text(440, 312, "Слой инструментов", size=FS_BODY, bold=True)
    tools = [
        ("knowledge_base_search", 120, 330, 220),
        ("web_search", 370, 330, 140),
        ("code_interpreter", 540, 330, 160),
    ]
    for label, tx, ty, tw in tools:
        svg.rect(tx, ty, tw, 35, fill="light")
        svg.mono(tx + tw / 2, ty + 17, label, size=FS_TINY, anchor="middle")

    svg.arrow(440, 255, 440, 288)
    svg.arrow(440, 288, 440, 255)

    # Серверные компоненты базы знаний
    svg.rect(100, 400, 680, 85, fill="white", stroke="dark", dash=True)
    svg.text(440, 420, "Сменные бэкенды базы знаний", size=FS_BODY, bold=True)
    backends = [
        ("retrieval-pipeline\nГибридный поиск + переранжирование", 120),
        ("structured-index\nRAPTOR/GraphRAG", 340),
        ("contextual-retrieval\nКонтекстный поиск", 560),
    ]
    for label, bx in backends:
        svg.box(bx, 435, 180, 45, label, fill="light", font_size=FS_SMALL)

    svg.arrow(230, 365, 230, 398)
    svg.arrow(440, 375, 440, 398)

    svg.save(os.path.join(_output_dir, "fig3-10.svg"))


# ──────────────────────── fig3-11 ────────────────────────


def fig3_11() -> None:
    """Контекстный поиск (конкретный пример префикса)"""
    w, h = 880, 430
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Контекстный поиск", size=FS_TITLE, bold=True)

    # Слева: обычное разбиение
    svg.rect(20, 55, 400, 170, fill="white", stroke="border")
    svg.text(220, 78, "Обычные фрагменты (без контекста)", size=FS_BODY, bold=True)

    svg.rect(40, 95, 360, 50, fill="code_bg", stroke="dark", rx=4)
    svg.mono(50, 112, "Выручка компании за второй квартал выросла на 3%,", size=FS_TINY)
    svg.mono(50, 132, "главным образом благодаря новой линейке.", size=FS_TINY)

    svg.text(220, 170, "Вопрос: что за компания и какой год?", size=FS_SMALL, fill="text_light")
    svg.text(
        220,
        195,
        "→ Поиск находит данные о выручке множества нерелевантных компаний",
        size=FS_SMALL,
        fill="text_light",
    )

    # Справа: фрагмент с контекстом
    svg.rect(460, 55, 400, 170, fill="white", stroke="border")
    svg.text(660, 78, "Фрагмент с контекстом", size=FS_BODY, bold=True)

    svg.rect(480, 95, 360, 35, fill="medium")
    svg.mono(490, 113, "[ACME · отчёт за Q2 2025 · ключевые показатели]", size=FS_TINY)

    svg.rect(480, 130, 360, 50, fill="code_bg", stroke="dark", rx=4)
    svg.mono(490, 148, "Выручка компании за второй квартал выросла на 3%,", size=FS_TINY)
    svg.mono(490, 168, "главным образом благодаря новой линейке.", size=FS_TINY)

    svg.text(
        660, 200, "→ Точное совпадение: ACME + Q2 + рост выручки", size=FS_SMALL, fill="text_light"
    )

    # Стрелка между блоками
    svg.text(440, 140, "→", size=FS_TITLE, bold=True)

    # Поток обработки
    svg.line(20, 250, 860, 250, color="dark", dash=True)
    svg.text(w / 2, 275, "Индексация: LLM создаёт контекстный префикс", size=FS_BODY, bold=True)

    flow_y = 300
    svg.box(30, flow_y, 180, 55, "Исходный документ", fill="light", bold=True, font_size=FS_BODY)
    svg.arrow(210, flow_y + 27, 248, flow_y + 27)

    svg.box(250, flow_y, 180, 55, "Разбиение", fill="light", bold=True, font_size=FS_BODY)
    svg.arrow(430, flow_y + 27, 468, flow_y + 27)

    svg.box(
        470,
        flow_y,
        180,
        55,
        "LLM создаёт префикс\n(кэширование промпта)",
        fill="medium",
        font_size=FS_SMALL,
        bold=True,
    )
    svg.arrow(650, flow_y + 27, 688, flow_y + 27)

    svg.box(
        690,
        flow_y,
        170,
        55,
        "Префикс + текст\n→ индекс",
        fill="light",
        font_size=FS_SMALL,
        bold=True,
    )

    # Статистика
    svg.text(
        w / 2,
        h - 20,
        "Результат: ошибок поиска ↓49% (+BM25), ↓67% (+переранжирование) — данные Anthropic",
        size=FS_SMALL,
        fill="text_light",
    )

    svg.save(os.path.join(_output_dir, "fig3-11.svg"))


# ──────────────────────── fig3-12 ────────────────────────


def fig3_12() -> None:
    """Конвейер извлечения структурированных знаний (эксперимент 3.10)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Эксперимент 3.10: извлечение структурированных знаний (судебные решения)",
        size=FS_TITLE,
        bold=True,
    )

    # Заголовок этапа 1
    svg.rect(20, 55, 840, 200, fill="white", stroke="border")
    svg.text(440, 78, "Этап 1: извлечение и структурирование знаний", size=FS_BODY, bold=True)

    # Исходные решения
    svg.rect(40, 95, 180, 65, fill="code_bg", stroke="dark", rx=4)
    svg.text(130, 113, "Исходные решения", size=FS_SMALL, bold=True)
    svg.mono(50, 138, "Набор данных CAIL2018", size=FS_TINY)

    svg.arrow(220, 127, 258, 127)

    # Извлечение с помощью LLM
    svg.rect(260, 95, 180, 65, fill="medium")
    svg.text(350, 113, "LLM выявляет факторы", size=FS_SMALL, bold=True)
    svg.text(350, 138, "Схема снизу вверх", size=FS_SMALL, fill="text_light")

    svg.arrow(440, 127, 478, 127)

    # Структурированный JSON
    svg.rect(480, 95, 200, 65, fill="code_bg", stroke="dark", rx=4)
    svg.text(580, 113, "Структурированный JSON", size=FS_SMALL, bold=True)
    svg.mono(490, 138, "{явка:true, выплата:500 тыс.,", size=FS_TINY)
    svg.mono(490, 155, " тяжкий_вред:степень II}", size=FS_TINY)

    # Подробности схемы
    svg.rect(40, 170, 400, 70, fill="light")
    svg.text(240, 188, "Модульная схема данных", size=FS_SMALL, bold=True)
    svg.text(
        240,
        212,
        "Основная схема (явка/выплата/судимости) + схема расширения по составу",
        size=FS_SMALL,
        fill="text_light",
    )
    svg.text(240, 232, "(кража→сумма, вред→степень тяжести)", size=FS_SMALL, fill="text_light")

    # Заголовок этапа 2
    svg.rect(20, 270, 840, 200, fill="white", stroke="border")
    svg.text(440, 293, "Этап 2: анализ факторов и моделирование знаний", size=FS_BODY, bold=True)

    # Векторизация
    svg.rect(40, 310, 200, 65, fill="light")
    svg.text(140, 328, "Векторизация признаков", size=FS_SMALL, bold=True)
    svg.text(
        140, 350, "One-hot-кодирование + multi-hot-кодирование", size=FS_SMALL, fill="text_light"
    )
    svg.text(140, 370, "+ логарифмирование + стандартизация", size=FS_SMALL, fill="text_light")

    svg.arrow(240, 342, 278, 342)

    # Кластеризация
    svg.rect(280, 310, 200, 65, fill="medium")
    svg.text(380, 328, "Кластеризация HDBSCAN", size=FS_SMALL, bold=True)
    svg.text(380, 350, 'Выявляет "прототипы дел"', size=FS_SMALL, fill="text_light")
    svg.text(380, 370, "Напр.: ссора→лёгкий вред", size=FS_SMALL, fill="text_light")

    svg.arrow(480, 342, 518, 342)

    # Значимость факторов
    svg.rect(520, 310, 200, 65, fill="light")
    svg.text(620, 328, "Модель значимости факторов", size=FS_SMALL, bold=True)
    svg.text(620, 350, "Оценивает вес факторов", size=FS_SMALL, fill="text_light")
    svg.text(620, 370, "Строит логику назначения наказания", size=FS_SMALL, fill="text_light")

    # Применение
    svg.arrow(620, 375, 620, 400)
    svg.rect(40, 400, 720, 60, fill="light")
    svg.text(400, 420, "Применение: агент для юридических консультаций", size=FS_BODY, bold=True)
    svg.text(
        400,
        445,
        "Уточняет важные факторы → ищет прототипы похожих дел → анализирует наказание по данным",
        size=FS_SMALL,
        fill="text_light",
    )

    svg.save(os.path.join(_output_dir, "fig3-12.svg"))


# ──────────────────────── fig3-13 ────────────────────────


def fig3_13() -> None:
    """Цикл внешнего обучения (конкретный пример)"""
    w, h = 880, 490
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Внешнее обучение: цикл от опыта к навыку", size=FS_TITLE, bold=True)

    # Центральный агент
    cx, cy = 440, 210
    svg.circle(cx, cy, 55, fill="medium", label="AI-агент", font_size=FS_BODY)

    # 5 шагов цикла
    steps = [
        ("① Выполнить задачу", 120, 100, "Обработать возврат\nВызвать API поддержки"),
        (
            "② Получить обратную связь",
            680,
            100,
            "Возврат $45 выполнен\nТребуется проверка последних четырёх цифр",
        ),
        (
            "③ Осмыслить и обобщить",
            680,
            310,
            'LLM обобщает опыт:\n"Для возврата в компании A нужна проверка"',
        ),
        ("④ Сохранить в базе знаний", 340, 380, "Опыт→векторный индекс\nПроцесс→код инструмента"),
        (
            "⑤ Найти и применить снова",
            120,
            310,
            "Похожая задача→поиск опыта\nИтерация успешной стратегии",
        ),
    ]

    positions: list[tuple[float, float]] = []
    for label, x, y, detail in steps:
        svg.box(x, y, 200, 80, label + "\n" + detail, fill="light", font_size=FS_SMALL)
        positions.append((x + 100, y + 40))

    # Стрелки между шагами
    arrow_pairs = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 0),
    ]
    for si, ei in arrow_pairs:
        sx, sy = positions[si]
        ex, ey = positions[ei]
        dx, dy = ex - sx, ey - sy
        dist = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / dist, dy / dist
        svg.arrow(sx + ux * 105, sy + uy * 45, ex - ux * 105, ey - uy * 45, color="dark")

    # Два типа результатов
    svg.rect(30, 395, 180, 28, fill="dark")
    svg.text(120, 409, "Знания: сводка/древовидная сводка", size=FS_SMALL, fill="white")
    svg.rect(670, 395, 180, 28, fill="dark")
    svg.text(760, 409, "Инструмент: процесс→код", size=FS_SMALL, fill="white")

    svg.save(os.path.join(_output_dir, "fig3-13.svg"))


# ──────────────────────── fig3-14 ────────────────────────


def fig3_14() -> None:
    """Система обучения на опыте GAIA (эксперимент 3.11)"""
    w, h = 880, 510
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Эксперимент 3.11: обучение на опыте GAIA", size=FS_TITLE, bold=True)

    box_h = 60
    step_gap = 75
    base_y = 100

    # --- Слева: режим обучения ---
    lx = 20
    svg.rect(lx, 55, 400, 420, fill="white", stroke="border")
    svg.text(lx + 200, 80, "Режим обучения", size=FS_BODY, bold=True)

    learn_steps = [
        ("Задача GAIA", "medium", "Сложный многоэтапный вопрос"),
        ("AI-агент выполняет", "light", "Браузер + файлы + интерпретатор кода"),
        ("Задача решена?", "light", "Автооценка (AWorld)"),
        ("LLM анализирует и обобщает", "medium", "Краткое описание стратегии"),
        ("Опыт → векторизация", "light", "Сохранение в базе опыта"),
    ]
    for i, (label, fill, sub) in enumerate(learn_steps):
        y = base_y + i * step_gap
        svg.box(
            lx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY
        )
        if i > 0:
            svg.arrow(lx + 200, base_y + (i - 1) * step_gap + box_h + 2, lx + 200, y - 2)

    # --- Справа: режим применения ---
    rx = 460
    svg.rect(rx, 55, 400, 420, fill="white", stroke="border")
    svg.text(rx + 200, 80, "Режим применения", size=FS_BODY, bold=True)

    apply_steps = [
        ("Новая задача GAIA", "medium", "Получение нового вопроса"),
        ("Семантический поиск опыта", "light", "Поиск похожих задач в базе опыта"),
        ("Вставка в системный промпт", "medium", "Успешные стратегии как примеры"),
        ("AI-агент выполняет", "light", "Опыт помогает решить задачу быстрее"),
        ("Успешность ↑ Эффективность ↑", "dark", "Саморазвитие: всё сильнее с каждой задачей"),
    ]
    for i, (label, fill, sub) in enumerate(apply_steps):
        y = base_y + i * step_gap
        svg.box(
            rx + 50, y, 300, box_h, label, sublabel=sub, fill=fill, bold=True, font_size=FS_BODY
        )
        if i > 0:
            svg.arrow(rx + 200, base_y + (i - 1) * step_gap + box_h + 2, rx + 200, y - 2)

    # Стрелка от обучения к применению: база опыта по центру вертикали
    kb_cy = base_y + 2 * step_gap + box_h / 2  # Выровнено по центру шага 3
    kb_x1, kb_x2 = 375, 505
    svg.rect(kb_x1, kb_cy - 25, kb_x2 - kb_x1, 50, fill="dark")
    svg.text((kb_x1 + kb_x2) / 2, kb_cy - 8, "База опыта", size=FS_SMALL, fill="white", bold=True)
    svg.text((kb_x1 + kb_x2) / 2, kb_cy + 12, "(векторный индекс)", size=FS_TINY, fill="white")

    # От середины справа последнего шага обучения → к базе слева
    last_y = base_y + 4 * step_gap + box_h / 2
    svg.arrow(lx + 350, last_y, kb_x1 - 2, kb_cy + 10)
    # От базы справа → к середине слева второго шага применения
    apply2_y = base_y + 1 * step_gap + box_h / 2
    svg.arrow(kb_x2 + 2, kb_cy - 10, rx + 50, apply2_y)

    svg.save(os.path.join(_output_dir, "fig3-14.svg"))


# ──────────────────────── Запуск ────────────────────────

ALL_FIGS = [
    fig3_1,
    fig3_2,
    fig3_3,
    fig3_4,
    fig3_5,
    fig3_6,
    fig3_7,
    fig3_8,
    fig3_9,
    fig3_10,
    fig3_11,
    fig3_12,
    fig3_13,
    fig3_14,
]


def main(output_dir: str) -> None:
    global _output_dir
    _output_dir = output_dir
    os.makedirs(_output_dir, exist_ok=True)
    for fn in ALL_FIGS:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nГотово — {len(ALL_FIGS)} SVG сохранено в {_output_dir}/")


if __name__ == "__main__":
    main(parse_output_dir(_output_dir))
