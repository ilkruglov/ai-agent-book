"""Создаёт все иллюстрации главы 2.

Всего 9 иллюстраций (от fig2-1 до fig2-9):
  fig2-1:  Состав контекстного окна (переработано — с реальными фрагментами содержимого)
  fig2-2:  Архитектура вызова инструментов локальной LLM (НОВОЕ — эксперимент 2.1)
  fig2-3:  Структура токенов шаблона чата (переработано — увеличены шрифты)
  fig2-4:  Повторное использование префикса KV-кэша (переработано — конкретные последовательности токенов)
  fig2-5:  Внедрение системных подсказок (переработано — реальный текст подсказки)
  fig2-6:  Сравнение стратегий сжатия контекста (переработано — визуализация данных)
  fig2-7:  Варианты конвейера сжатия контекста (НОВОЕ — эксперимент 2.7)
  fig2-8:  Постепенное раскрытие Skills (переработано — конкретный пример PPTX)
  fig2-9:  Сравнение стратегий памяти (НОВОЕ — эксперимент 2.10)

Удалено (больше не создаётся):
  прежняя fig2-4: Структурирование промпта (в тексте уже есть примеры кода)
  прежняя fig2-8: Рабочая память → долговременная память (достаточно объяснено в тексте)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    FS_BODY,
    FS_SMALL,
    FS_TINY,
    FS_TITLE,
    SVG,
    parse_output_dir,
)

_output_dir = os.path.join(os.path.dirname(__file__), "images")


# ════════════════════════════════════════════════════════════════════
#  fig2-1: Состав контекстного окна (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_1() -> None:
    """Контекстное окно с реальными фрагментами содержимого каждого слоя."""
    W, H = 820, 620
    s = SVG(W, H)

    s.text(410, 30, "Обзор состава контекстного окна", size=FS_TITLE, bold=True)

    lx, lw = 40, 700
    layers = [
        (
            "Системный промпт (System Prompt)",
            "medium",
            [
                '"Вы — полезный ассистент. Вы ОБЯЗАНЫ отвечать кратко."',
                '"Используйте инструменты, когда пользователь запрашивает актуальную информацию."',
            ],
        ),
        (
            "Определения инструментов (Tool Definitions)",
            "light",
            [
                '{"name": "web_search", "description": "Поиск в интернете",',
                ' "parameters": {"query": {"type": "string"}}}',
            ],
        ),
        (
            "История диалога (Conversation History)",
            "light",
            [
                'user: "Какая сегодня погода в Пекине?"',
                'assistant: [tool_call] → get_weather("Пекин")',
                'tool: {"temp": "23°C", "conditions": "ясно"}',
            ],
        ),
        (
            "Трассировка рассуждений (Reasoning Trace)",
            "#e8e8e8",
            [
                "<think>Пользователь спрашивает о погоде, результат инструмента уже получен,",
                "можно сразу обобщить и ответить без нового вызова инструмента.</think>",
            ],
        ),
        (
            "Текущая позиция генерации →",
            "white",
            [
                'assistant: "Сегодня в Пекине ясно, 23°C..."  ← LLM генерирует',
            ],
        ),
    ]

    y = 60
    for title, fill, snippets in layers:
        block_h = 30 + len(snippets) * 22 + 10
        s.rect(lx, y, lw, block_h, fill=fill)
        s.text(lx + 15, y + 20, title, size=FS_BODY, bold=True, anchor="start")
        for i, line in enumerate(snippets):
            s.mono(lx + 25, y + 42 + i * 22, line, size=FS_TINY)
        y += block_h + 8

    # Фигурная скобка справа
    brace_top = 60
    brace_bot = y - 8
    s.brace_right(lx + lw + 8, brace_top, brace_bot)
    s.text(
        lx + lw + 15,
        (brace_top + brace_bot) / 2 - 12,
        "контекстное",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    s.text(
        lx + lw + 15,
        (brace_top + brace_bot) / 2 + 12,
        "окно",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )

    # Нижнее примечание
    s.rect(100, y + 15, 620, 50, fill="code_bg", stroke="dark", rx=4)
    s.text(
        410, y + 32, "Размер окна: Qwen3 = 32K токенов | Claude = 200K | Gemini = 2M", size=FS_SMALL
    )
    s.text(
        410,
        y + 52,
        "Всё сериализуется в поток токенов → обработка механизмом внимания Transformer",
        size=FS_SMALL,
        fill="text_light",
    )

    s.save(f"{_output_dir}/fig2-1.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-2: Архитектура вызова инструментов локальной LLM (НОВОЕ — эксперимент 2.1)
# ════════════════════════════════════════════════════════════════════


def fig2_2() -> None:
    """Qwen3-0.6B на локальном оборудовании, реестр инструментов и цикл ReAct."""
    W, H = 820, 540
    s = SVG(W, H)

    s.text(
        410,
        30,
        "Эксперимент 2.1: архитектура вызова инструментов локальной LLM",
        size=FS_TITLE,
        bold=True,
    )

    # Блок оборудования (слева)
    s.group_box(30, 65, 220, 130, "Локальное оборудование")
    s.box(50, 100, 180, 35, "Apple M2 / 16GB", fill="light", font_size=FS_SMALL)
    s.box(50, 145, 180, 35, "Бэкенд инференса MLX", fill="light", font_size=FS_SMALL)

    # Блок модели (в центре)
    s.rect(290, 65, 240, 130, fill="medium")
    s.text(410, 95, "Qwen3-0.6B", size=FS_BODY, bold=True)
    s.text(410, 120, "0.6B параметров · квантование Q4", size=FS_SMALL, fill="text_light")
    s.text(410, 145, "> 100 токенов/с", size=FS_SMALL, fill="text_light")
    s.text(410, 170, "ReAct + вызов инструментов", size=FS_SMALL)

    # Реестр инструментов (справа)
    s.group_box(570, 65, 220, 130, "Реестр инструментов")
    s.box(590, 100, 180, 35, "get_current_time", fill="code_bg", font_size=FS_SMALL)
    s.box(590, 145, 180, 35, "get_temperature", fill="code_bg", font_size=FS_SMALL)

    # Стрелки: оборудование → модель, модель ↔ инструменты
    s.arrow(252, 130, 288, 130)
    s.arrow(532, 122, 568, 122)
    s.arrow(568, 138, 532, 138)

    # Цикл ReAct (ниже)
    s.group_box(50, 220, 720, 290, "Цикл ReAct")

    # Шаг 1: запрос пользователя
    s.rect(80, 260, 300, 40, fill="light")
    s.text(90, 280, 'user: "Который час и какая погода в Ванкувере?"', size=FS_TINY, anchor="start")

    # Шаг 2: рассуждение
    s.rect(80, 310, 300, 55, fill="#e8e8e8")
    s.text(90, 328, "<think>", size=FS_TINY, anchor="start", bold=True)
    s.text(90, 348, "Нужно вызвать get_current_time", size=FS_TINY, anchor="start")
    s.text(90, 363, "и get_temperature", size=FS_TINY, anchor="start")
    s.arrow(230, 302, 230, 308)

    # Шаг 3: вызовы инструментов
    s.rect(80, 375, 300, 50, fill="code_bg", stroke="dark", rx=4)
    s.mono(90, 393, "<tool_call>", size=FS_TINY)
    s.mono(90, 411, '{"name":"get_current_time",...}', size=FS_TINY)
    s.arrow(230, 367, 230, 373)

    # Шаг 4: результаты инструментов
    s.rect(80, 435, 300, 40, fill="light")
    s.text(
        90, 455, '<tool_response> {"time":"05:18","temp":"13.2°C"}', size=FS_TINY, anchor="start"
    )
    s.arrow(230, 427, 230, 433)

    # Справа: стрелка цикла и итоговый вывод
    # Стрелка цикла проходит снаружи слева, чтобы не перекрывать текст в колонке
    s.arrow_curved(80, 455, 80, 280, curve=-40, color="dark")
    s.text(30, 367, "продолжить цикл", size=FS_TINY, fill="text_light", bold=True)

    # Блок итогового вывода
    s.rect(430, 280, 320, 55, fill="medium")
    s.text(440, 298, "Итоговый вывод:", size=FS_SMALL, bold=True, anchor="start")
    s.text(440, 318, '"Ванкувер: 05:18 утра, 13.2°C,', size=FS_TINY, anchor="start")
    s.text(440, 335, '  ясно, влажность 93%"', size=FS_TINY, anchor="start")

    # Примечание о потоковой обработке
    s.rect(430, 360, 320, 80, fill="code_bg", stroke="dark", rx=4)
    s.text(590, 378, "Порядок потоковой обработки", size=FS_SMALL, bold=True)
    s.text(440, 400, "<think>...  → скрывать от пользователя", size=FS_TINY, anchor="start")
    s.text(440, 418, "Обычный текст → выводить в реальном времени", size=FS_TINY, anchor="start")
    s.text(440, 436, "<tool_call> → разобрать и выполнить", size=FS_TINY, anchor="start")

    s.save(f"{_output_dir}/fig2-2.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-3: Структура токенов шаблона чата (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_3() -> None:
    """Структура токенов шаблона чата с реальным содержимым и крупными шрифтами."""
    W, H = 920, 580
    s = SVG(W, H)

    s.text(W / 2, 30, "Структура токенов шаблона чата", size=FS_TITLE, bold=True)

    lx = 40
    rw = 800

    y = 65
    segments: list[tuple[str, str, str, list[str]]] = [
        (
            "<|im_start|>system",
            "darker",
            "white",
            [
                "# Инструменты",
                "Можно вызвать одну или несколько функций...",
                '<tools>{"name":"get_weather",...}</tools>',
                '<tool_call>{"name":..., "arguments":...}</tool_call>',
            ],
        ),
        ("<|im_end|>", "dark", "white", []),
        (
            "<|im_start|>user",
            "darker",
            "white",
            [
                '"Какая сегодня погода в Пекине?"',
            ],
        ),
        ("<|im_end|>", "dark", "white", []),
        (
            "<|im_start|>assistant",
            "darker",
            "white",
            [
                "<think>Нужно узнать погоду через get_weather</think>",
                '<tool_call>{"name":"get_weather","args":{"city":"Пекин"}}</tool_call>',
            ],
        ),
        ("<|im_end|>", "dark", "white", []),
        (
            "<|im_start|>user",
            "darker",
            "white",
            [
                '<tool_response>{"temp":"23°C","sky":"ясно"}</tool_response>',
            ],
        ),
        ("<|im_end|>", "dark", "white", []),
        (
            "<|im_start|>assistant",
            "darker",
            "white",
            [
                "← Здесь LLM начинает генерировать новый токен",
            ],
        ),
    ]

    for tag, tag_fill, _, content_lines in segments:
        if not content_lines:
            # Конечный токен — небольшая метка
            s.badge(lx, y, 140, 24, tag, fill=tag_fill, font_size=FS_TINY)
            y += 32
        else:
            total_h = 26 + len(content_lines) * 20 + 8
            s.rect(lx, y, rw, total_h, fill="light")
            s.badge(lx + 5, y + 4, 200, 22, tag, fill=tag_fill, font_size=FS_TINY)
            for i, line in enumerate(content_lines):
                s.mono(lx + 220, y + 8 + i * 20 + 12, line, size=FS_TINY)
            y += total_h + 4

    # Примечание справа
    s.text(lx + rw + 5, 80, "Особые", size=FS_SMALL, anchor="start", bold=True)
    s.text(lx + rw + 5, 100, "маркеры", size=FS_SMALL, anchor="start", bold=True)

    s.save(f"{_output_dir}/fig2-3.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-4: Повторное использование префикса KV-кэша (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_4() -> None:
    """KV-кэш с конкретными последовательностями токенов для повторного использования префикса."""
    W, H = 820, 480
    s = SVG(W, H)

    s.text(410, 30, "Повторное использование префикса KV-кэша", size=FS_TITLE, bold=True)

    lx = 40

    # Запрос 1
    s.text(lx, 70, "Запрос 1", size=FS_BODY, bold=True, anchor="start")
    # Часть системного промпта (кэшируется)
    s.rect(lx, 85, 380, 40, fill="medium")
    s.text(lx + 190, 105, "Системный промпт + инструменты (1200 токенов)", size=FS_SMALL)
    # Сообщение пользователя
    s.rect(lx + 385, 85, 180, 40, fill="light")
    s.text(lx + 475, 105, 'user: "Какая погода?"', size=FS_SMALL)
    # KV вычислен
    s.rect(lx + 570, 85, 170, 40, fill="#e8e8e8")
    s.text(lx + 655, 105, "→ Генерация ответа", size=FS_SMALL)

    # Запрос 2 (попадание в кэш)
    s.text(lx, 155, "Запрос 2", size=FS_BODY, bold=True, anchor="start")
    # Тот же префикс — берётся из кэша
    s.rect(lx, 170, 380, 40, fill="medium")
    s.text(lx + 190, 190, "Системный промпт + инструменты (попадание в кэш ✓)", size=FS_SMALL)
    # Другое сообщение пользователя
    s.rect(lx + 385, 170, 180, 40, fill="light")
    s.text(lx + 475, 190, 'user: "Который час?"', size=FS_SMALL)
    s.rect(lx + 570, 170, 170, 40, fill="#e8e8e8")
    s.text(lx + 655, 190, "→ Генерация ответа", size=FS_SMALL)

    # Стрелка повторного использования кэша
    s.arrow(lx + 190, 127, lx + 190, 168, label="Повторное использование KV-кэша", color="dark")

    # Запрос 3 (промах кэша)
    s.text(lx, 245, "Запрос 3", size=FS_BODY, bold=True, anchor="start", max_width=75)
    s.text(
        lx + 85,
        245,
        "(системный промпт изменился)",
        size=FS_SMALL,
        anchor="start",
        fill="text_light",
        max_width=250,
    )
    s.rect(lx, 260, 400, 40, fill="white", dash=True)
    s.text(lx + 200, 280, 'Система + инструменты + "Время: 10:30:45"', size=FS_SMALL)
    s.rect(lx + 405, 260, 160, 40, fill="light")
    s.text(lx + 485, 280, 'user: "Какая погода?"', size=FS_SMALL)
    s.rect(lx + 570, 260, 170, 40, fill="#e8e8e8")
    s.text(lx + 655, 280, "→ Полный пересчёт ✗", size=FS_SMALL)

    # Сравнение производительности
    s.rect(80, 330, 660, 130, fill="code_bg", stroke="dark", rx=4)
    s.text(
        410, 355, "Сравнение производительности (контекст 3000 токенов)", size=FS_BODY, bold=True
    )

    # Заголовок таблицы
    s.line(100, 370, 720, 370, color="dark")
    s.text(230, 390, "Попадание в кэш", size=FS_SMALL, bold=True)
    s.text(490, 390, "Инвалидация кэша", size=FS_SMALL, bold=True)
    s.line(100, 405, 720, 405, color="dark")

    # Строки
    s.text(130, 425, "TTFT", size=FS_SMALL, anchor="start")
    s.text(230, 425, "~0.5 с", size=FS_SMALL)
    s.text(490, 425, "3 - 5 с", size=FS_SMALL)

    s.text(100, 450, "Стоимость", size=FS_SMALL, anchor="start", max_width=95)
    s.text(260, 450, "Только новые токены", size=FS_SMALL, max_width=110)
    s.text(490, 450, "Повторная оплата всех токенов", size=FS_SMALL)

    s.save(f"{_output_dir}/fig2-4.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-5: Архитектура внедрения строки состояния агента (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_5() -> None:
    """Показывает место внедрения подсказок и их реальный текст."""
    W, H = 820, 580
    s = SVG(W, H)

    s.text(410, 30, "Архитектура внедрения системных подсказок", size=FS_TITLE, bold=True)

    # Слева: БЕЗ подсказок
    col_w = 350
    col_gap = 70
    lx1 = 30
    lx2 = lx1 + col_w + col_gap

    s.text(lx1 + col_w / 2, 65, "Без системных подсказок", size=FS_BODY, bold=True)
    s.text(lx2 + col_w / 2, 65, "С системными подсказками", size=FS_BODY, bold=True)

    # Левая колонка: исходная траектория
    y = 90
    left_items = [
        ("system", "Системный промпт + инструменты", "medium", 35),
        ("user", '"Помоги снизить цену у Xfinity"', "light", 35),
        ("assistant", "phone_call(Xfinity) → вызов 1", "#e8e8e8", 35),
        ("tool", "Результат: ожидание 45 минут, соединиться не удалось", "light", 35),
        ("assistant", 'web_search("скидки Xfinity")', "#e8e8e8", 35),
        ("tool", "Результат: [много результатов...]", "light", 35),
        ("assistant", "phone_call(Xfinity) → вызов 2", "#e8e8e8", 35),
        ("tool", "Ответили, предложение: $65/мес.", "light", 35),
        ("assistant", "phone_call(Xfinity) → вызов 3", "#e8e8e8", 35),
        ("tool", "Результат: цена снижена до $59/мес.", "light", 35),
        ("user", '"Можно позвонить ещё раз и поторопить их?"', "light", 35),
    ]

    for role, content, fill, h in left_items:
        s.rect(lx1, y, col_w, h, fill=fill, rx=4)
        s.text(
            lx1 + 8,
            y + h / 2,
            f"{role}:",
            size=FS_TINY,
            anchor="start",
            bold=True,
            max_width=50,
        )
        s.mono(lx1 + 65, y + h / 2, content, size=FS_TINY - 2, max_width=col_w - 75)
        y += h + 3

    s.text(
        lx1 + col_w / 2,
        y + 15,
        "→ Модели нужно просмотреть весь контекст",
        size=FS_SMALL,
        fill="text_light",
    )
    s.text(
        lx1 + col_w / 2,
        y + 35,
        "и посчитать звонки — легко ошибиться",
        size=FS_SMALL,
        fill="text_light",
    )

    # Правая колонка: с системными подсказками
    y = 90
    right_items = [
        ("system", "Системный промпт + инструменты", "medium", 35),
        ("user", '"Помоги снизить цену у Xfinity"', "light", 35),
        ("...", "[ та же траектория ]", "#e8e8e8", 90),
        ("user", '"Можно позвонить ещё раз и поторопить их?"', "light", 35),
    ]
    for role, content, fill, h in right_items:
        s.rect(lx2, y, col_w, h, fill=fill, rx=4)
        s.text(lx2 + 8, y + h / 2, f"{role}:", size=FS_TINY, anchor="start", bold=True)
        s.mono(lx2 + 65, y + h / 2, content, size=FS_TINY - 2)
        y += h + 3

    # Выделенный блок системной подсказки
    hint_y = y
    hint_h = 150
    s.rect(lx2, hint_y, col_w, hint_h, fill="medium", stroke="border", rx=4)
    s.text(lx2 + 10, hint_y + 18, "<agent_status>", size=FS_SMALL, bold=True, anchor="start")
    hints = [
        "phone_call вызван 3 раза (Xfinity: 3)",
        "Ограничение: достигнут предел (3/3) ✗",
        "TODO: [✓]связаться с Xfinity [✓]подтвердить снижение цены",
        "Текущее время: 2025-09-14 10:30",
        "Состояние: ожидание подтверждения",
    ]
    for i, h in enumerate(hints):
        s.mono(lx2 + 15, hint_y + 40 + i * 20, h, size=FS_TINY - 2)
    s.text(
        lx2 + col_w - 10,
        hint_y + hint_h - 12,
        "</agent_status>",
        size=FS_SMALL,
        bold=True,
        anchor="end",
    )

    s.text(
        lx2 + col_w / 2,
        hint_y + hint_h + 18,
        "→ Модель читает готовое состояние",
        size=FS_SMALL,
        fill="text_light",
    )
    s.text(
        lx2 + col_w / 2,
        hint_y + hint_h + 38,
        "соблюдает предел и больше не звонит",
        size=FS_SMALL,
        fill="text_light",
    )

    # Разделитель VS
    s.text(lx1 + col_w + col_gap / 2, 300, "VS", size=FS_BODY, bold=True)

    s.save(f"{_output_dir}/fig2-5.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-6: Сравнение стратегий сжатия контекста (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_6() -> None:
    """Визуализация сравнения 6 стратегий с реальными числовыми данными эксперимента."""
    W, H = 820, 530
    s = SVG(W, H)

    s.text(
        410,
        30,
        "Сравнение стратегий сжатия контекста: поиск основателей OpenAI",
        size=FS_TITLE,
        bold=True,
    )

    # Макет таблицы
    tx = 30
    tw = 760

    # Позиции столбцов
    cols = [
        (tx, 145, "Стратегия"),
        (tx + 150, 90, "Токены"),
        (tx + 250, 65, "Сжатие"),
        (tx + 325, 55, "Итерации"),
        (tx + 400, 65, "Результат"),
        (tx + 475, 280, "График расхода токенов"),
    ]

    header_y = 65
    for cx, cw, label in cols:
        s.text(cx + cw / 2, header_y, label, size=FS_SMALL, bold=True)

    s.line(tx, header_y + 12, tx + tw, header_y + 12)

    strategies = [
        ("Без сжатия", "> 110K", "100%", "5 (сбой)", False, 110000),
        ("Отдельные сводки", "123,205", "6.8%", "24", True, 123205),
        ("Общая сводка", "55,462", "2.1%", "21", True, 55462),
        ("С учётом контекста", "25,198", "0.9%", "15", True, 25198),
        ("Контекст+ссылки", "45,544", "1.4%", "17", True, 45544),
        ("Адаптивное окно", "181,372", "—", "8", True, 181372),
    ]

    max_tokens = 190000
    bar_x = tx + 475
    bar_max_w = 280

    for i, (name, tokens, ratio, iters, success, token_val) in enumerate(strategies):
        y = header_y + 30 + i * 62

        # Название стратегии
        s.text(
            tx + 72,
            y + 15,
            name,
            size=FS_SMALL,
            anchor="middle",
            bold=(name == "С учётом контекста"),
        )

        # Число токенов
        s.text(tx + 195, y + 15, tokens, size=FS_SMALL)

        # Степень сжатия
        s.text(tx + 282, y + 15, ratio, size=FS_SMALL)

        # Итерации
        s.text(tx + 352, y + 15, iters, size=FS_SMALL)

        # Результат
        result_text = "✓ Успех" if success else "✗ Сбой"
        result_color = "text" if success else "dark"
        s.text(tx + 432, y + 15, result_text, size=FS_SMALL, fill=result_color)

        # Полоса
        bar_w = (token_val / max_tokens) * bar_max_w
        bar_fill = "#e8e8e8" if name != "С учётом контекста" else "medium"
        if not success:
            bar_fill = "white"
        s.rect(bar_x, y, bar_w, 30, fill=bar_fill, stroke="border", rx=3)

    # Выделение лучшей стратегии
    best_y = header_y + 30 + 3 * 62 - 5
    s.rect(tx - 2, best_y, tw + 4, 42, fill="white", stroke="border", rx=4, dash=True)

    # Основной вывод внизу
    s.rect(100, H - 60, 620, 45, fill="code_bg", stroke="dark", rx=4)
    s.text(
        410,
        H - 45,
        "Учёт контекста: на 77% меньше токенов, максимальная доля успешных результатов, минимум итераций",
        size=FS_SMALL,
        bold=True,
    )
    s.text(
        410,
        H - 25,
        "Ключ: учитывать цель запроса и уже известные данные при сжатии",
        size=FS_SMALL,
        fill="text_light",
    )

    s.save(f"{_output_dir}/fig2-6.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-7: Варианты конвейера сжатия контекста (НОВОЕ — эксперимент 2.7)
# ════════════════════════════════════════════════════════════════════


def fig2_7() -> None:
    """6 стратегий сжатия как варианты конвейера обработки."""
    W, H = 820, 600
    s = SVG(W, H)

    s.text(
        410,
        30,
        "Эксперимент 2.7: процессы обработки для шести стратегий сжатия",
        size=FS_TITLE,
        bold=True,
    )

    # Примечание о входных данных
    s.text(
        410,
        58,
        "Каждый результат поиска: ~70K символов → разная обработка",
        size=FS_SMALL,
        fill="text_light",
    )

    strategies = [
        (
            "① Без сжатия",
            "Сохранить всё",
            "Полный исходный текст в контексте",
            "> 110K токенов → переполнение",
            False,
        ),
        (
            "② Отдельные сводки",
            "Независимые сводки",
            "Для каждого результата сводка из 2-3 абзацев",
            "123K токенов · 6.8%",
            True,
        ),
        (
            "③ Общая сводка",
            "Общая сводка",
            "Объединить все результаты и сжать",
            "55K токенов · 2.1%",
            True,
        ),
        (
            "④ С контекстом",
            "Умное сжатие",
            "Запрос + контекст → целевое сжатие",
            "25K токенов · 0.9%",
            True,
        ),
        (
            "⑤ Контекст + ссылки",
            "Умное+источники",
            "Сжатый текст + URL-метки источников",
            "45K токенов · 1.4%",
            True,
        ),
        (
            "⑥ Адаптивное окно",
            "Сжатие позже",
            "< 80% окна — исходник, затем пакетное сжатие",
            "181K токенов · макс. точность",
            True,
        ),
    ]

    lx = 30
    row_h = 78
    start_y = 75

    for i, (name, method, desc, result, success) in enumerate(strategies):
        y = start_y + i * row_h

        # Метка названия стратегии
        fill = "darker" if i == 3 else "dark"
        s.badge(lx, y, 130, 26, name, fill=fill, font_size=FS_TINY)

        # Блок метода
        s.rect(lx, y + 30, 120, 40, fill="#e8e8e8", rx=4)
        s.text(lx + 60, y + 50, method, size=FS_SMALL)

        # Стрелка
        s.arrow(lx + 122, y + 50, lx + 135, y + 50)

        # Описание
        s.rect(lx + 138, y + 30, 330, 40, fill="code_bg", stroke="dark", rx=4)
        s.text(lx + 303, y + 50, desc, size=FS_TINY)

        # Стрелка
        s.arrow(lx + 470, y + 50, lx + 483, y + 50)

        # Результат
        res_fill = "medium" if i == 3 else ("white" if not success else "light")
        s.rect(lx + 486, y + 30, 275, 40, fill=res_fill, rx=4)
        s.text(lx + 623, y + 50, result, size=FS_TINY)

    s.save(f"{_output_dir}/fig2-7.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-8: Постепенное раскрытие Skills (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_8() -> None:
    """Три уровня Agent Skills на конкретном примере PPTX."""
    W, H = 820, 540
    s = SVG(W, H)

    s.text(410, 30, "Постепенное раскрытие Skills (пример PPTX Skill)", size=FS_TITLE, bold=True)

    # Уровень 1: метаданные (загружаются всегда)
    y1 = 70
    s.rect(40, y1, 740, 90, fill="medium")
    s.text(
        60,
        y1 + 20,
        "Уровень 1: метаданные (при запуске, ~200 токенов)",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    s.rect(60, y1 + 40, 700, 40, fill="code_bg", rx=4)
    s.mono(
        70,
        y1 + 60,
        'skills: [{name: "PPTX", desc: "Создание презентаций PowerPoint из материалов"}',
        size=FS_TINY,
    )
    s.mono(
        70,
        y1 + 75,
        '        {name: "PDF",  desc: "Извлечение и анализ PDF-документов"}, ...]',
        size=FS_TINY - 2,
    )

    # Стрелка активации
    s.arrow(410, y1 + 92, 410, y1 + 115)
    s.text(
        430,
        y1 + 103,
        'Задача-триггер: "создать PPT по статье"',
        size=FS_SMALL,
        anchor="start",
        fill="text_light",
    )

    # Уровень 2: основной SKILL.md
    y2 = y1 + 120
    s.rect(40, y2, 740, 130, fill="light")
    s.text(
        60,
        y2 + 20,
        "Уровень 2: основной процесс SKILL.md (по запросу, ~2K токенов)",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    s.rect(60, y2 + 40, 700, 80, fill="code_bg", rx=4)
    lines2 = [
        "Основной процесс PPTX Skill:",
        "1. Извлечь текст через markitdown → 2. Распаковать PPTX для доступа к XML",
        "3. Изменить содержимое slide{N}.xml → 4. Повторно упаковать в .pptx",
        "Ссылки: → html2pptx.md | → reference.md | → scripts/",
    ]
    for i, line in enumerate(lines2):
        s.mono(70, y2 + 56 + i * 19, line, size=FS_TINY)

    # Стрелка активации
    s.arrow(410, y2 + 132, 410, y2 + 155)
    s.text(
        430,
        y2 + 143,
        'Нужны детали: "создать PPT из HTML-шаблона"',
        size=FS_SMALL,
        anchor="start",
        fill="text_light",
    )

    # Уровень 3: дополнительные документы
    y3 = y2 + 160
    s.rect(40, y3, 740, 130, fill="white", dash=True)
    s.text(
        60,
        y3 + 20,
        "Уровень 3: дополнительные документы (выборочно, по запросу)",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )

    doc_w = 215
    docs = [
        ("html2pptx.md", "Полный процесс:\nHTML-шаблон → PPT"),
        ("reference.md", "Спецификация XML\nи технические детали"),
        ("scripts/*.py", "Исполняемые инструменты:\nthumbnail.py и др."),
    ]
    for i, (name, desc) in enumerate(docs):
        dx = 60 + i * (doc_w + 20)
        s.rect(dx, y3 + 45, doc_w, 70, fill="code_bg", stroke="dark", rx=4)
        s.text(dx + doc_w / 2, y3 + 62, name, size=FS_SMALL, bold=True)
        desc_lines = desc.split("\n")
        for j, dl in enumerate(desc_lines):
            s.text(dx + doc_w / 2, y3 + 82 + j * 16, dl, size=FS_TINY, fill="text_light")

    # Внизу: примечание о KV-кэше
    s.rect(100, y3 + 140, 620, 35, fill="code_bg", stroke="dark", rx=4)
    s.text(
        410,
        y3 + 158,
        "Метаданные неизменны → подходят для KV-кэша | Динамический контент добавляется в конец → кэш не инвалидируется",
        size=FS_SMALL,
    )

    s.save(f"{_output_dir}/fig2-8.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-9: Архитектура Mem0 (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_9() -> None:
    """Архитектура Mem0 с реальным потоком данных и конкретными примерами памяти."""
    W, H = 820, 530
    s = SVG(W, H)

    s.text(410, 30, "Архитектура управления памятью Mem0", size=FS_TITLE, bold=True)

    # Входной диалог
    s.rect(30, 70, 250, 80, fill="light")
    s.text(40, 88, "Новый диалог:", size=FS_SMALL, bold=True, anchor="start")
    s.mono(40, 110, 'user: "Я переехал в Шэньчжэнь,', size=FS_TINY)
    s.mono(40, 128, 'новый адрес — технопарк Наньшань"', size=FS_TINY)

    # MemoryBase (в центре)
    s.rect(310, 65, 200, 100, fill="medium")
    s.text(410, 85, "MemoryBase", size=FS_BODY, bold=True)
    s.text(410, 108, "Управление жизненным циклом памяти", size=FS_SMALL, fill="text_light")
    s.text(410, 130, "Анализ → классификация → решение", size=FS_SMALL, fill="text_light")
    s.arrow(282, 110, 308, 110)

    # LLMBase (над MemoryBase)
    s.rect(330, 185, 160, 50, fill="#e8e8e8")
    s.text(410, 203, "LLMBase", size=FS_SMALL, bold=True)
    s.text(410, 222, "Семантика + оценка связей", size=FS_TINY)
    s.arrow(410, 167, 410, 183, color="dark")
    s.arrow(410, 183, 410, 167, color="dark")

    # Результат решения
    s.rect(310, 255, 200, 80, fill="code_bg", stroke="dark", rx=4)
    s.text(320, 273, "Результат:", size=FS_SMALL, bold=True, anchor="start")
    s.mono(320, 293, 'Было: "Живёт в пекинском районе Хайдянь"', size=FS_TINY)
    s.mono(320, 311, '→ UPDATE: "Живёт в районе Наньшань в Шэньчжэне"', size=FS_TINY)
    s.mono(320, 329, '→ ADD: "Переехал в Шэньчжэнь"', size=FS_TINY - 2)
    s.arrow(410, 237, 410, 253, color="dark")

    # EmbeddingBase (справа)
    s.rect(560, 70, 220, 70, fill="light")
    s.text(670, 90, "EmbeddingBase", size=FS_SMALL, bold=True)
    s.text(670, 112, "Текст → вектор (много вычислений)", size=FS_TINY, fill="text_light")
    s.arrow(512, 95, 558, 90)

    # VectorStoreBase (справа, ниже)
    s.rect(560, 160, 220, 100, fill="light")
    s.text(670, 180, "VectorStoreBase", size=FS_SMALL, bold=True)
    s.text(670, 200, "Хранение + поиск (много I/O)", size=FS_TINY, fill="text_light")
    s.text(670, 225, "Chroma / Qdrant / Milvus", size=FS_TINY, fill="text_light")
    s.text(670, 248, "(индекс HNSW / LSH)", size=FS_TINY, fill="text_light")
    s.arrow(670, 142, 670, 158)

    # Примеры сохранённых воспоминаний
    s.rect(560, 290, 220, 120, fill="code_bg", stroke="dark", rx=4)
    s.text(570, 310, "Записи в памяти:", size=FS_SMALL, bold=True, anchor="start")
    s.mono(570, 332, '"Живёт в технопарке Наньшань (Шэньчжэнь)"', size=FS_TINY)
    s.mono(570, 352, '"Почта: john@x.com"', size=FS_TINY)
    s.mono(570, 372, '"Предпочитает общаться на китайском"', size=FS_TINY)
    s.mono(570, 392, '"Работа: ML-инженер"', size=FS_TINY)
    s.arrow(670, 262, 670, 288, color="dark")

    # Примечание о механизме плагинов
    s.rect(30, 170, 250, 60, fill="code_bg", stroke="dark", rx=4)
    s.text(155, 192, "Механизм плагинов", size=FS_SMALL, bold=True)
    s.text(
        155,
        212,
        "Сменные LLM / модели эмбеддингов / бэкенды хранилища",
        size=FS_TINY,
        fill="text_light",
    )

    # Путь поиска
    s.rect(30, 390, 250, 80, fill="light")
    s.text(40, 408, "Поиск в памяти:", size=FS_SMALL, bold=True, anchor="start")
    s.mono(40, 430, 'query: "Где живёт пользователь?"', size=FS_TINY)
    s.mono(40, 450, "→ Поиск по близости векторов", size=FS_TINY)
    s.mono(40, 468, '→ "Живёт в технопарке Наньшань (Шэньчжэнь)"', size=FS_TINY)
    s.arrow_curved(282, 430, 558, 350, curve=-30, label="Поиск", color="dark")

    s.save(f"{_output_dir}/fig2-10.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-11: Многотипная архитектура памяти Memobase (переработано)
# ════════════════════════════════════════════════════════════════════


def fig2_11_memobase() -> None:
    """4 типа памяти Memobase с конкретными примерами."""
    W, H = 820, 560
    s = SVG(W, H)

    s.text(410, 30, "Многотипная архитектура памяти Memobase", size=FS_TITLE, bold=True)

    types = [
        (
            "Эпизодическая",
            "Память о событиях",
            [
                "2025-09-10 бронь Шанхай→Токио",
                "2025-09-12 вылет перенесён на 9/20",
                "2025-09-13 отель сменён на Синдзюку",
            ],
            "События с метками времени",
        ),
        (
            "Семантическая",
            "Память о фактах",
            [
                "Пользователь → профессия → ML-инженер",
                "Пользователь → аллергия на арахис",
                "Пользователь → предпочитает → место у окна",
            ],
            "Сеть сущностей и связей",
        ),
        (
            "Процедурная",
            "Память о действиях",
            [
                "Шаблон планирования поездки:",
                "  направление→бюджет→транспорт→жильё→занятия",
                "(извлечено автоматически из диалогов)",
            ],
            "Переиспользуемая стратегия",
        ),
        (
            "Рабочая",
            "Память задачи",
            [
                "Задача: забронировать отель в Токио",
                "Готово: билет куплен (ANA NH919)",
                "Осталось: выбор отеля + трансфер из аэропорта",
            ],
            "Текущее состояние задачи",
        ),
    ]

    col_w = 185
    gap = 10
    total = len(types) * col_w + (len(types) - 1) * gap
    start_x = (W - total) / 2

    for i, (name, eng, examples, desc) in enumerate(types):
        x = start_x + i * (col_w + gap)

        # Заголовок
        s.rect(x, 65, col_w, 55, fill="medium")
        s.text(x + col_w / 2, 82, name, size=FS_BODY, bold=True)
        s.text(x + col_w / 2, 105, eng, size=FS_TINY, fill="text_light")

        # Примеры
        ex_h = len(examples) * 20 + 20
        s.rect(x, 130, col_w, ex_h, fill="code_bg", stroke="dark", rx=4)
        for j, ex in enumerate(examples):
            s.mono(x + 8, 148 + j * 20, ex, size=FS_TINY - 2)

        # Описание
        s.text(x + col_w / 2, 130 + ex_h + 18, desc, size=FS_TINY, fill="text_light")

    # Стрелки взаимодействия между рабочей и долговременной памятью
    arrow_y = 280
    wm_x = start_x + 3 * (col_w + gap) + col_w / 2

    for i in range(3):
        lt_x = start_x + i * (col_w + gap) + col_w / 2
        s.arrow_curved(wm_x - 20, arrow_y, lt_x + 20, arrow_y, curve=-30, dash=True, color="dark")

    s.text(
        410,
        arrow_y - 10,
        "Динамический обмен: рабочая ↔ долговременная память",
        size=FS_SMALL,
        fill="text_light",
    )

    # Раздел сжатия памяти (ниже)
    comp_y = 310
    s.rect(40, comp_y, 740, 110, fill="light")
    s.text(
        60, comp_y + 22, "Сжатие и упорядочивание памяти", size=FS_BODY, bold=True, anchor="start"
    )

    comp_stages = [
        (
            "Оценка важности",
            ["частота доступа × временное затухание", "× сила эмоций × уникальность"],
        ),
        ("Сжатие кластеров", ["группировка похожих записей", "→ репрезентативная сводка"]),
        ("Обобщение", ["эпизодическая → семантическая", "события → общие правила"]),
    ]

    stage_w = 220
    stage_gap = 15
    sx = 60
    for j, (title, desc_lines) in enumerate(comp_stages):
        cx = sx + j * (stage_w + stage_gap)
        s.rect(cx, comp_y + 45, stage_w, 55, fill="code_bg", stroke="dark", rx=4)
        s.text(cx + stage_w / 2, comp_y + 62, title, size=FS_SMALL, bold=True)
        for k, dl in enumerate(desc_lines):
            s.text(cx + stage_w / 2, comp_y + 78 + k * 15, dl, size=FS_TINY, fill="text_light")
        if j > 0:
            s.arrow(cx - stage_gap + 2, comp_y + 72, cx - 2, comp_y + 72, color="dark")

    # Раздел защиты данных
    priv_y = comp_y + 125
    s.rect(40, priv_y, 740, 90, fill="#e8e8e8")
    s.text(
        60,
        priv_y + 20,
        "Защита данных: многоуровневое хранение",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )

    levels = [
        ("L1 открытые", "имя, почта", "открытый текст"),
        ("L2 внутренние", "телефон, адрес", "частичная маска"),
        ("L3 секретные", "ID, пароль", "замена маркером"),
    ]

    lev_w = 230
    for j, (level, info, strategy) in enumerate(levels):
        lx = 55 + j * (lev_w + 10)
        s.rect(lx, priv_y + 38, lev_w, 40, fill="code_bg", stroke="dark", rx=4)
        s.text(lx + 8, priv_y + 58, f"{level}: {info} → {strategy}", size=FS_TINY, anchor="start")

    s.save(f"{_output_dir}/fig2-11.svg")


# ════════════════════════════════════════════════════════════════════
#  fig2-9: Сравнение стратегий памяти (НОВОЕ — эксперимент 2.10)
# ════════════════════════════════════════════════════════════════════


def fig2_9_memory_comparison() -> None:
    """4 режима памяти, по-разному сохраняющие одни и те же сведения."""
    W, H = 820, 620
    s = SVG(W, H)

    s.text(410, 30, "Эксперимент 2.10: четыре стратегии памяти", size=FS_TITLE, bold=True)

    # Пример входного диалога
    s.rect(40, 60, 740, 55, fill="light")
    s.text(50, 78, "Исходный диалог:", size=FS_SMALL, bold=True, anchor="start")
    s.mono(
        50,
        98,
        '"Я старший инженер в TechCorp: 3 года в ML, руковожу командой из 5 человек по рекомендательным системам"',
        size=FS_TINY,
    )

    strategies = [
        (
            "Простые заметки",
            "Отдельные факты",
            [
                '"Компания: TechCorp"',
                '"Должность: старший инженер"',
                '"Команда: 5 человек"',
                '"Специализация: рекомендательные системы"',
            ],
            "Плюсы: O(1), минимум накладных расходов\nМинусы: связи полностью теряются",
        ),
        (
            "Расшир. заметки",
            "Полный абзац",
            [
                '"Пользователь — старший инженер',
                "ПО в TechCorp, три года в ML,",
                "руководит командой из 5 человек",
                'и делает систему рекомендаций."',
            ],
            "Плюсы: сохранение семантики\nМинусы: повторы + сложные обновления",
        ),
        (
            "JSON-карточки",
            "Иерархия",
            [
                "work:",
                '  company: "TechCorp"',
                '  title: "старший инженер"',
                "  team_size: 5",
            ],
            "Плюсы: частичные обновления\nМинусы: жёсткие категории",
        ),
        (
            "Расш. JSON-карточки",
            "Знания с контекстом",
            [
                '{category: "work",',
                ' title: "старший инженер",',
                ' backstory: "самопрезентация",',
                ' ts: "09-14"}',
            ],
            "Плюсы: устранение неоднозначности + отслеживание источников\nМинусы: высокая стоимость генерации",
        ),
    ]

    col_w = 185
    gap = 10
    total = len(strategies) * col_w + (len(strategies) - 1) * gap
    start_x = (W - total) / 2

    for i, (name, approach, storage, tradeoff) in enumerate(strategies):
        x = start_x + i * (col_w + gap)

        # Заголовок
        s.rect(x, 130, col_w, 50, fill="medium")
        s.text(x + col_w / 2, 148, name, size=FS_SMALL, bold=True)
        s.text(x + col_w / 2, 168, approach, size=FS_TINY, fill="text_light")

        # Стрелка от входных данных
        s.arrow(x + col_w / 2, 117, x + col_w / 2, 128, color="dark")

        # Представление хранимых данных
        storage_h = len(storage) * 18 + 16
        s.rect(x, 190, col_w, storage_h, fill="code_bg", stroke="dark", rx=4)
        for j, line in enumerate(storage):
            s.mono(x + 8, 205 + j * 18, line, size=FS_TINY - 2)

        # Компромиссы
        tradeoff_lines = tradeoff.split("\n")
        for j, tl in enumerate(tradeoff_lines):
            s.text(
                x + col_w / 2,
                200 + storage_h + 18 + j * 18,
                tl,
                size=FS_TINY,
                fill="text_light",
                max_width=col_w - 8,
            )

    # Система оценки (внизу)
    eval_y = 420
    s.rect(40, eval_y, 740, 180, fill="light")
    s.text(60, eval_y + 22, "Трёхуровневая система оценки", size=FS_BODY, bold=True, anchor="start")

    eval_levels = [
        (
            "Уровень 1: прямой поиск",
            "Хранение и поиск явных данных",
            '"Мой номер участника — 12345" → точный ответ',
            "light",
        ),
        (
            "Уровень 2: поиск между сессиями",
            "Связывание данных из разных сессий и вывод по ним",
            '"Запиши авто на ТО" → найти обе машины',
            "#e8e8e8",
        ),
        (
            "Уровень 3: проактивность",
            "Помощь на основе всей памяти",
            "Бронирование международного рейса → обнаружен скорый конец срока паспорта",
            "medium",
        ),
    ]

    for i, (level, desc, example, fill) in enumerate(eval_levels):
        ey = eval_y + 45 + i * 45
        s.rect(60, ey, 180, 38, fill=fill, rx=4)
        s.text(150, ey + 19, level, size=FS_SMALL, bold=True)
        s.text(252, ey + 12, desc, size=FS_TINY, anchor="start")
        s.mono(252, ey + 29, example, size=FS_TINY - 2, anchor="start")

    s.save(f"{_output_dir}/fig2-9.svg")


# ════════════════════════════════════════════════════════════════════
#  Точка входа
# ════════════════════════════════════════════════════════════════════


def main(output_dir: str) -> None:
    global _output_dir
    _output_dir = output_dir
    os.makedirs(_output_dir, exist_ok=True)
    fig2_1()
    fig2_2()
    fig2_3()
    fig2_4()
    fig2_5()
    fig2_6()
    fig2_7()
    fig2_8()
    fig2_9()
    fig2_11_memobase()
    fig2_9_memory_comparison()
    print("Глава 2: создано 11 иллюстраций.")


if __name__ == "__main__":
    main(parse_output_dir(_output_dir))
