"""Создаёт унаследованный набор SVG после перенумерации глав.

Первые десять схем и схема игры «Оборотни» относятся к текущей главе 10.
Схема VLA остаётся рисунком 9-11. Рисунки 10-3 и 10-12 поддерживаются
отдельно и этим генератором не создаются.
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
#  fig9-1: Общий и раздельный контекст
# ════════════════════════════════════════════════════════════════════


def fig9_1() -> None:
    W, H = 780, 560
    s = SVG(W, H)

    s.text(W // 2, 30, "Общий и раздельный контекст", size=FS_TITLE, bold=True)

    col_w = 350
    lx, rx = 20, W - col_w - 20

    # ── Слева: общий контекст ──
    s.group_box(lx, 55, col_w, 480, "Общий контекст (один AI-агент, несколько этапов)")

    ctx_x, ctx_w = lx + 15, col_w - 30
    phases = [
        (
            "Этап 1: аналитик требований",
            "medium",
            [
                'sys: "Полностью уточните требования..."',
                "tools: [ask_question, save_req]",
                'user: "Напишите скрипт анализа CSV"',
                'agent: "Какие типы файлов нужно обрабатывать?"',
            ],
        ),
        (
            "Этап 2: разработчик",
            "light",
            [
                'sys: "Напишите код по согласованным требованиям..."',
                "tools: [write_file, execute_code]",
                'agent: write_file("analyze.py", ...)',
                'agent: execute_code("python test.py")',
            ],
        ),
        (
            "Этап 3: рецензент кода",
            "light",
            [
                'sys: "Проверьте качество и безопасность кода..."',
                "tools: [run_linter, run_tests]",
                "agent: run_linter → 2 предупреждения",
                "agent: approve_code()",
            ],
        ),
    ]

    cy = 82
    for title, fill, lines in phases:
        ph = 18 + len(lines) * 18 + 10
        s.rect(ctx_x, cy, ctx_w, ph, fill=fill, rx=4)
        s.text(ctx_x + 8, cy + 14, title, size=FS_SMALL, bold=True, anchor="start")
        for i, ln in enumerate(lines):
            s.mono(ctx_x + 12, cy + 32 + i * 18, ln, size=12)
        cy += ph + 2

    s.rect(ctx_x, cy, ctx_w, 28, fill="code_bg", rx=3)
    s.text(
        ctx_x + ctx_w // 2,
        cy + 14,
        "↑ Все этапы используют общую историю диалога",
        size=FS_TINY,
        bold=True,
    )
    cy += 36

    s.text(
        lx + col_w // 2, cy + 10, "✓ Полная история выполнения", size=FS_SMALL, fill="text_light"
    )
    s.text(
        lx + col_w // 2, cy + 32, "✗ Контекст быстро разрастается", size=FS_SMALL, fill="text_light"
    )

    # ── Справа: раздельный контекст ──
    s.group_box(rx, 55, col_w, 480, "Раздельный контекст (несколько AI-агентов)")

    agents_data = [
        (
            "Агент глоссария",
            [
                'sys: "Найдите и переведите термины..."',
                "tools: [search_dict, write_file]",
                "→ glossary.json",
            ],
        ),
        (
            "Агент перевода",
            [
                'sys: "Переведите эту главу..."',
                "tools: [read_file, write_file]",
                "→ chapter3_zh.md",
            ],
        ),
        (
            "Агент редактуры",
            [
                'sys: "Проверьте единообразие терминов..."',
                "tools: [read_file, write_file]",
                "→ review_report.md",
            ],
        ),
    ]

    ay = 82
    for name, lines in agents_data:
        ah = 18 + len(lines) * 18 + 8
        s.rect(rx + 15, ay, ctx_w, ah, fill="light", rx=4)
        s.text(rx + 23, ay + 14, name, size=FS_SMALL, bold=True, anchor="start")
        for i, ln in enumerate(lines):
            s.mono(rx + 27, ay + 32 + i * 18, ln, size=12)
        ay += ah + 8

    fs_y = ay + 5
    s.rect(rx + 15, fs_y, ctx_w, 65, fill="medium", rx=4)
    s.text(rx + 15 + ctx_w // 2, fs_y + 16, "Общая файловая система", size=FS_SMALL, bold=True)
    files = ["glossary.json", "chapter3_zh.md", "review_report.md"]
    s.mono(rx + 27, fs_y + 38, "  ".join(files), size=11)
    s.text(
        rx + 15 + ctx_w // 2,
        fs_y + 55,
        "+ структурированные данные через параметры вызова инструмента",
        size=FS_TINY,
        fill="text_light",
    )

    s.text(
        rx + col_w // 2,
        fs_y + 82,
        "✓ Модульно · масштабируемо · параллельно",
        size=FS_SMALL,
        fill="text_light",
    )
    s.text(rx + col_w // 2, fs_y + 104, "✗ Сложная синхронизация", size=FS_SMALL, fill="text_light")

    s.save(os.path.join(_output_dir, "fig10-1.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-2: Смена ролей по этапам
# ════════════════════════════════════════════════════════════════════


def fig9_2() -> None:
    W, H = 780, 520
    s = SVG(W, H)

    s.text(W // 2, 28, "Смена ролей по этапам: три этапа Coding Agent", size=FS_TITLE, bold=True)

    phases = [
        (
            "Аналитик требований",
            "medium",
            '"Ваша задача — понять требования.\nНе переходите к реализации: сейчас\nнужно задавать вопросы и уточнять."',
            [
                "ask_clarifying_question(q)",
                "save_requirement(k, v)",
                "complete_requirements_analysis()",
            ],
            "complete_requirements_analysis()",
        ),
        (
            "Разработчик",
            "light",
            '"Напишите качественный Python-код\nпо согласованным требованиям.\nСледуйте лучшим практикам модульности и обработки ошибок."',
            ["write_file(path, content)", "read_file(path)", "execute_code(code)"],
            "submit_for_review()",
        ),
        (
            "Рецензент кода",
            "#e8e8e8",
            '"Оцените код по нескольким аспектам:\nкорректность, стиль и\nбезопасность. Мыслите критически."',
            ["run_linter(file)", "run_tests(file)", "analyze_complexity(file)"],
            None,
        ),
    ]

    s.rect(30, 55, W - 60, 28, fill="code_bg", rx=3)
    s.text(
        W // 2,
        69,
        "▼ Единый контекст — история диалога сохраняется между этапами ▼",
        size=FS_SMALL,
        bold=True,
    )

    pw = 225
    gap = 18
    px_start = (W - 3 * pw - 2 * gap) // 2
    py = 100

    for i, (role, fill, prompt, tools, trigger) in enumerate(phases):
        x = px_start + i * (pw + gap)

        s.rect(x, py, pw, 380, fill=fill, rx=6)
        s.text(x + pw // 2, py + 22, f"Этап {i + 1}", size=FS_TINY, fill="text_light")
        s.text(x + pw // 2, py + 42, role, size=FS_BODY, bold=True)

        s.rect(x + 8, py + 60, pw - 16, 88, fill="code_bg", rx=3)
        s.text(x + 14, py + 75, "Системный промпт", size=FS_TINY, fill="text_light", anchor="start")
        for j, ln in enumerate(prompt.split("\n")):
            s.text(x + 14, py + 92 + j * 16, ln, size=12, anchor="start", fill="text_light")

        s.rect(x + 8, py + 158, pw - 16, 18 + len(tools) * 20, fill="white", rx=3)
        s.text(
            x + 14, py + 172, "Набор инструментов", size=FS_TINY, fill="text_light", anchor="start"
        )
        for j, tool in enumerate(tools):
            s.mono(x + 14, py + 190 + j * 20, tool, size=11)

        if trigger:
            ty = py + 290
            s.rect(x + 8, ty, pw - 16, 48, fill="dark", rx=12)
            s.text(x + pw // 2, ty + 16, "Запуск перехода", size=FS_TINY, fill="white")
            s.mono(x + pw // 2, ty + 34, trigger, size=10, anchor="middle", fill="white")

        if i < 2:
            ax1 = x + pw + 2
            ax2 = x + pw + gap - 2
            ay = py + 310
            s.arrow(ax1, ay, ax2, ay)

    s.text(
        W // 2,
        H - 10,
        "Смена роли: новый системный промпт и набор инструментов при сохранении истории и состояния",
        size=FS_SMALL,
        fill="text_light",
    )

    s.save(os.path.join(_output_dir, "fig10-2.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-3: Цикл Proposer-Reviewer (создание Slidev PPT)
# ════════════════════════════════════════════════════════════════════


def fig9_3() -> None:
    W, H = 780, 520
    s = SVG(W, H)

    s.text(W // 2, 28, "Цикл Proposer-Reviewer: создание Slidev PPT", size=FS_TITLE, bold=True)

    # Редактор (Proposer)
    ex, ey, ew, eh = 30, 65, 300, 200
    s.rect(ex, ey, ew, eh, fill="light")
    s.text(ex + ew // 2, ey + 22, "Агент-редактор", size=FS_BODY, bold=True)
    s.text(
        ex + 12,
        ey + 48,
        "Вход: расширенная аннотация статьи (2000 знаков)",
        size=FS_TINY,
        anchor="start",
        fill="text_light",
        max_width=W // 2 - 90,
    )
    editor_lines = [
        "---",
        "theme: academic",
        "---",
        "# Механизм внимания Transformer",
        "",
        "## Основная идея",
        "- Самовнимание вычисляет Q·K^T/√d",
        "- Несколько голов работают параллельно",
    ]
    s.code_block(ex + 10, ey + 62, ew - 20, editor_lines, font_size=11, line_h=14)
    s.text(
        ex + ew // 2,
        ey + eh - 10,
        "Понять структуру → разбить на слайды",
        size=FS_TINY,
        fill="text_light",
    )

    # Рецензент (Reviewer)
    cx, cy, cw, ch_h = 450, 65, 300, 200
    s.rect(cx, cy, cw, ch_h, fill="medium")
    s.text(cx + cw // 2, cy + 22, "Агент-рецензент", size=FS_BODY, bold=True)

    s.rect(cx + 10, cy + 42, cw - 20, 38, fill="code_bg", rx=3)
    s.text(cx + 18, cy + 55, "① Рендеринг Slidev → PDF/PNG", size=FS_TINY, anchor="start")
    s.text(cx + 18, cy + 70, "② Многоаспектная оценка Vision LLM", size=FS_TINY, anchor="start")

    feedback_items = [
        "Стр. Тип проблемы   Критичность",
        "P3   Слишком плотно высокая",
        "P7   Мелкий шрифт    средняя",
        "P11  Плохие цвета    низкая",
    ]
    s.rect(cx + 10, cy + 86, cw - 20, 75, fill="code_bg", rx=3)
    s.text(
        cx + 18,
        cy + 100,
        "Структурированная обратная связь:",
        size=FS_TINY,
        anchor="start",
        bold=True,
    )
    for i, fb in enumerate(feedback_items):
        s.mono(cx + 18, cy + 118 + i * 15, fb, size=11)
    s.text(
        cx + cw // 2,
        cy + ch_h - 10,
        "Рендеринг + визуальный анализ → конкретные правки",
        size=FS_TINY,
        fill="text_light",
    )

    # Стрелки между редактором и рецензентом
    mid_y1 = ey + 70
    mid_y2 = ey + eh - 50
    s.arrow(ex + ew + 2, mid_y1, cx - 2, mid_y1)
    s.text((ex + ew + cx) / 2, mid_y1 - 12, "Код Slidev", size=FS_SMALL, bold=True)

    s.arrow(cx - 2, mid_y2, ex + ew + 2, mid_y2)
    s.text((ex + ew + cx) / 2, mid_y2 + 16, "Отзыв", size=FS_SMALL, bold=True)

    # Ход итераций
    iy = 290
    s.rect(30, iy, W - 60, 100, fill="code_bg", rx=4)
    s.text(W // 2, iy + 18, "Итеративная доработка", size=FS_BODY, bold=True)

    rounds = [
        ("Раунд 1", "Черновик, 12 страниц\n5 проблем", "light"),
        ("Раунд 2", "14 страниц (перегруженные страницы разделены)\n2 проблемы", "light"),
        ("Раунд 3", "14 страниц (шрифт исправлен)\n0 проблем ✓", "medium"),
    ]
    rw = 190
    rx_start = (W - 3 * rw - 2 * 30) // 2
    for i, (name, desc, fill) in enumerate(rounds):
        rx = rx_start + i * (rw + 30)
        ry = iy + 35
        s.box(rx, ry, rw, 52, name, fill=fill, sublabel=desc, bold=True, font_size=FS_SMALL)
        if i < 2:
            s.arrow(rx + rw + 4, ry + 26, rx + rw + 26, ry + 26, color="dark")

    # Почему не один агент
    wy = 405
    s.rect(30, wy, W - 60, 90, fill="light", rx=4)
    s.text(W // 2, wy + 20, "Почему не один AI-агент?", size=FS_BODY, bold=True)

    single_x = 60
    dual_x = W // 2 + 20
    s.text(
        single_x,
        wy + 45,
        "Один агент: рендеры ×N раундов → контекст разрастается",
        size=FS_TINY,
        anchor="start",
        fill="text_light",
        max_width=W // 2 - 90,
    )
    s.text(
        single_x,
        wy + 63,
        "(снимок 1080p = тысячи токенов × 14 страниц × 5 раундов)",
        size=FS_TINY,
        anchor="start",
        fill="text_light",
        max_width=W // 2 - 90,
    )
    s.text(
        dual_x,
        wy + 45,
        "Два агента: рецензент видит текущую версию",
        size=FS_TINY,
        anchor="start",
        max_width=W // 2 - 70,
    )
    s.text(
        dual_x,
        wy + 63,
        "Редактор копит только отзывы → чистый контекст",
        size=FS_TINY,
        anchor="start",
        max_width=W // 2 - 70,
    )

    s.save(os.path.join(_output_dir, "fig10-4.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-4: Последовательная координация менеджером
# ════════════════════════════════════════════════════════════════════


def fig9_4() -> None:
    W, H = 780, 480
    s = SVG(W, H)

    s.text(
        W // 2,
        28,
        "Последовательная координация менеджером: субагент как инструмент",
        size=FS_TITLE,
        bold=True,
    )

    # Менеджер
    mx, my, mw, mh = 240, 60, 300, 100
    s.rect(mx, my, mw, mh, fill="medium")
    s.text(mx + mw // 2, my + 22, "Агент-менеджер", size=FS_BODY, bold=True)
    s.text(
        mx + mw // 2,
        my + 46,
        "Понимание → декомпозиция → диспетчеризация → сводка",
        size=FS_TINY,
        fill="text_light",
    )
    s.text(
        mx + mw // 2,
        my + 66,
        "Инструменты: [call_agent_A, call_agent_B,",
        size=FS_TINY,
        fill="text_light",
    )
    s.text(
        mx + mw // 2, my + 82, "call_agent_C, search, write_file]", size=FS_TINY, fill="text_light"
    )

    # Последовательность субагентов
    agents = [
        ("Субагент A", "Сбор данных", "Поиск документации\nИзвлечение фактов", "light"),
        ("Субагент B", "Анализ", "Сопоставление данных\nПодготовка статистики", "light"),
        ("Субагент C", "Подготовка отчёта", "Написание отчёта\nФорматирование результата", "light"),
    ]
    aw = 210
    ax_start = (W - 3 * aw - 2 * 25) // 2
    ay = 240

    for i, (name, role, desc, fill) in enumerate(agents):
        x = ax_start + i * (aw + 25)
        s.rect(x, ay, aw, 120, fill=fill, rx=6)
        s.text(x + aw // 2, ay + 20, name, size=FS_SMALL, bold=True)
        s.text(x + aw // 2, ay + 40, f"Роль: {role}", size=FS_TINY, fill="text_light")
        for j, ln in enumerate(desc.split("\n")):
            s.text(x + aw // 2, ay + 62 + j * 18, ln, size=FS_TINY, fill="text_light")

        badge_labels = [f"Шаг {i + 1}"]
        s.badge(x + aw - 55, ay + 95, 50, 20, badge_labels[0], fill="dark", font_size=FS_TINY)

        # Стрелка от менеджера к субагенту
        s.arrow(mx + mw // 2 - 100 + i * 100, my + mh + 2, x + aw // 2, ay - 2, color="dark")

        # Стрелка между последовательными субагентами
        if i < 2:
            s.arrow(x + aw + 2, ay + 60, x + aw + 23, ay + 60)

    # Поток данных
    dy = 380
    s.rect(30, dy, W - 60, 80, fill="code_bg", rx=4)
    s.text(W // 2, dy + 18, "Последовательный поток", size=FS_BODY, bold=True)

    flow_items = [
        "Менеджер вызвал агента A",
        "→ A вернул данные",
        "→ Менеджер передал их B",
        "→ B вернул анализ",
        "→ Менеджер передал его C",
        "→ C вернул отчёт",
    ]
    fx_start = 55
    for i, item in enumerate(flow_items):
        s.text(
            fx_start + i * 118,
            dy + 42,
            item,
            size=FS_TINY,
            anchor="start",
            fill="text" if "вызвал" in item or "вернул" in item else "text_light",
            max_width=110,
        )

    s.text(
        W // 2,
        dy + 65,
        "Для менеджера вызов агента равен вызову инструмента (запрос → ответ)",
        size=FS_SMALL,
        fill="text_light",
    )

    s.save(os.path.join(_output_dir, "fig10-5.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-5: Архитектура агентов для перевода книги (эксперимент 9.4)
# ════════════════════════════════════════════════════════════════════


def fig9_5() -> None:
    W, H = 780, 540
    s = SVG(W, H)

    s.text(
        W // 2, 28, "Эксперимент 9.4: перевод книги — схема с менеджером", size=FS_TITLE, bold=True
    )

    # Менеджер сверху
    mx, my, mw, mh = 240, 55, 300, 70
    s.rect(mx, my, mw, mh, fill="medium")
    s.text(mx + mw // 2, my + 22, "Агент-менеджер", size=FS_BODY, bold=True)
    s.text(
        mx + mw // 2,
        my + 48,
        "Планирование · контроль · обработка сбоев · сводка",
        size=FS_TINY,
        fill="text_light",
    )

    # Три субагента
    sub_agents = [
        (
            30,
            "Агент глоссария",
            "Таблица терминов",
            [
                "Получить книгу → найти термины",
                "Свериться со словарями и правилами",
                "Результат: glossary.json",
            ],
            [
                '{"attention": "внимание",',
                ' "transformer": "Transformer",',
                ' "backprop": "обратное распространение"}',
            ],
        ),
        (
            270,
            "Агенты перевода ×N",
            "Перевод глав",
            [
                "Вход: глава + глоссарий + правила",
                "Строго соблюдать глоссарий",
                "Результат: chapter{n}_zh.md",
            ],
            ['"...механизм внимания вычисляет', ' сходство Query·Key^T..."'],
        ),
        (
            520,
            "Агент редактуры",
            "Редактура книги",
            [
                "Проверить единообразие терминов",
                "Проверить естественность и читаемость",
                "Результат: review_report.md",
            ],
            ['P3: "внимание"→"фокус" — разнобой', "P8: длинное предложение разбить"],
        ),
    ]

    aw = 230
    ay = 170

    for x, name, role, desc, output in sub_agents:
        s.rect(x, ay, aw, 185, fill="light", rx=6)
        s.text(x + aw // 2, ay + 20, name, size=FS_SMALL, bold=True)
        s.text(x + aw // 2, ay + 38, role, size=FS_TINY, fill="text_light")

        for i, ln in enumerate(desc):
            s.text(x + 12, ay + 60 + i * 18, ln, size=FS_TINY, anchor="start", fill="text_light")

        s.rect(x + 8, ay + 115, aw - 16, 10 + len(output) * 15, fill="code_bg", rx=3)
        for i, ln in enumerate(output):
            s.mono(x + 14, ay + 128 + i * 15, ln, size=10)

        # Стрелка от менеджера
        s.arrow(mx + mw // 2, my + mh + 2, x + aw // 2, ay - 2, color="dark")

    # Стрелки между последовательными субагентами
    s.arrow(30 + aw + 4, ay + 90, 270 - 4, ay + 90)
    s.arrow(270 + aw + 4, ay + 90, 520 - 4, ay + 90)

    # Общая файловая система
    fy = 375
    s.rect(30, fy, W - 60, 70, fill="medium", rx=6)
    s.text(W // 2, fy + 18, "Общая файловая система", size=FS_BODY, bold=True)
    files = [
        ("glossary.json", "Таблица терминов"),
        ("chapter{1..10}_zh.md", "Переводы глав"),
        ("review_report.md", "Отчёт редактора"),
        ("translation_guide.md", "Правила перевода"),
    ]
    fw = (W - 80) // len(files)
    for i, (fname, desc) in enumerate(files):
        cx = 50 + i * fw + fw // 2
        s.mono(cx, fy + 40, fname, size=11, anchor="middle")
        s.text(cx, fy + 58, desc, size=FS_TINY, fill="text_light")

    # Ключевая идея
    ky = 460
    s.rect(30, ky, W - 60, 60, fill="code_bg", rx=4)
    s.text(W // 2, ky + 18, "Преимущество изоляции контекста", size=FS_BODY, bold=True)
    s.text(
        W // 2,
        ky + 42,
        "Глоссарий: только термины | Перевод: текущая глава+глоссарий | Менеджер: индекс файлов",
        size=FS_TINY,
        fill="text_light",
    )

    s.save(os.path.join(_output_dir, "fig10-6.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-6: Параллельная координация менеджером
# ════════════════════════════════════════════════════════════════════


def fig9_6() -> None:
    W, H = 780, 500
    s = SVG(W, H)

    s.text(
        W // 2, 28, "Параллельная координация менеджером: шина сообщений", size=FS_TITLE, bold=True
    )

    # Агент-оркестратор
    ox, oy, ow, oh = 240, 55, 300, 70
    s.rect(ox, oy, ow, oh, fill="medium")
    s.text(ox + ow // 2, oy + 22, "Агент-оркестратор", size=FS_BODY, bold=True)
    s.text(
        ox + ow // 2,
        oy + 48,
        "Параллельный запуск · контроль в реальном времени · сводка",
        size=FS_TINY,
        fill="text_light",
    )

    # Шина сообщений
    bus_y = 155
    s.rect(50, bus_y, W - 100, 36, fill="dark", rx=4)
    s.text(
        W // 2, bus_y + 18, "Шина сообщений (Message Bus)", size=FS_SMALL, fill="white", bold=True
    )

    s.arrow(ox + ow // 2, oy + oh + 2, ox + ow // 2, bus_y - 2)

    # Параллельные агенты
    agents = [
        ("Агент 1", "Сбор данных", "работает ◎", "light"),
        ("Агент 2", "Анализ содержимого", "работает ◎", "light"),
        ("Агент 3", "Создание диаграмм", "завершён ✓", "medium"),
        ("Агент 4", "Проверка формата", "ожидает ○", "code_bg"),
    ]
    aw = 160
    gap = 14
    total = len(agents) * aw + (len(agents) - 1) * gap
    ax_start = (W - total) // 2
    ay = 225

    for i, (name, role, status, fill) in enumerate(agents):
        x = ax_start + i * (aw + gap)
        s.rect(x, ay, aw, 100, fill=fill, rx=6)
        s.text(x + aw // 2, ay + 20, name, size=FS_SMALL, bold=True)
        s.text(x + aw // 2, ay + 40, role, size=FS_TINY, fill="text_light")
        s.text(
            x + aw // 2,
            ay + 65,
            status,
            size=FS_TINY,
            fill="text_light" if "ожидает" in status else "text",
        )
        s.text(x + aw // 2, ay + 82, "Отдельный контекст", size=FS_TINY, fill="text_light")

        s.arrow(x + aw // 2, bus_y + 38, x + aw // 2, ay - 2, color="dark")

    # Примеры сообщений
    my = 350
    s.rect(30, my, W - 60, 125, fill="code_bg", rx=4)
    s.text(W // 2, my + 18, "Примеры обмена через шину сообщений", size=FS_BODY, bold=True)

    messages = [
        (
            "Orch → Агент 1",
            '{"type":"start","task":"собрать статьи arxiv","params":{"query":"LLM-агент"}}',
        ),
        ("Агент 3 → Orch", '{"type":"completed","agent_id":"3","result":"charts/fig1.svg создан"}'),
        ("Агент 1 → Агент 2", '{"type":"data_ready","source":"agent_1","file":"raw_data.json"}'),
        ("Orch → Агент 4", '{"type":"start","depends_on":["agent_2","agent_3"]}'),
    ]
    for i, (sender, msg) in enumerate(messages):
        y = my + 40 + i * 22
        s.text(40, y, sender, size=FS_TINY, bold=True, anchor="start")
        s.mono(200, y, msg, size=10, anchor="start")

    s.save(os.path.join(_output_dir, "fig10-7.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-7: Два агента: телефон и компьютер (эксперименты 9.5/9.6)
# ════════════════════════════════════════════════════════════════════


def fig9_7() -> None:
    W, H = 780, 560
    s = SVG(W, H)

    s.text(
        W // 2,
        28,
        "Эксперименты 9.5/9.6: два AI-агента — телефон и компьютер",
        size=FS_TITLE,
        bold=True,
    )

    # Телефонный агент (слева)
    px, py, pw, ph = 30, 65, 310, 240
    s.rect(px, py, pw, ph, fill="light", rx=6)
    s.text(px + pw // 2, py + 22, "Телефонный агент", size=FS_BODY, bold=True)
    s.text(
        px + pw // 2,
        py + 42,
        "Node.js · голосовая связь в реальном времени",
        size=FS_TINY,
        fill="text_light",
    )

    phone_pipeline = [
        ("Речь пользователя", "Вход с микрофона", "medium"),
        ("VAD + ASR", "Silero VAD → расшифровка STT", "light"),
        ("Инференс LLM", "Понять намерение + извлечь данные", "light"),
        ("Синтез TTS", "Создать и воспроизвести ответ", "medium"),
    ]
    for i, (label, desc, fill) in enumerate(phone_pipeline):
        y = py + 60 + i * 42
        s.rect(px + 10, y, pw - 20, 36, fill=fill, rx=3)
        s.text(px + 20, y + 14, label, size=FS_TINY, bold=True, anchor="start")
        s.text(px + 20, y + 28, desc, size=11, anchor="start", fill="text_light")
        if i < len(phone_pipeline) - 1:
            s.arrow(px + pw // 2, y + 38, px + pw // 2, y + 42, color="dark")

    # Компьютерный агент (справа)
    cx, cy, cw, ch_h = 440, 65, 310, 240
    s.rect(cx, cy, cw, ch_h, fill="light", rx=6)
    s.text(cx + cw // 2, cy + 22, "Компьютерный агент", size=FS_BODY, bold=True)
    s.text(
        cx + cw // 2, cy + 42, "Python · автоматизация браузера", size=FS_TINY, fill="text_light"
    )

    comp_pipeline = [
        ("Снимок экрана", "Текущая страница браузера", "medium"),
        ("Vision LLM", "Понять структуру и поля формы", "light"),
        ("План действий", "Найти поля → выбрать порядок ввода", "light"),
        ("Выполнение", "Нажать / ввести / отправить", "medium"),
    ]
    for i, (label, desc, fill) in enumerate(comp_pipeline):
        y = cy + 60 + i * 42
        s.rect(cx + 10, y, cw - 20, 36, fill=fill, rx=3)
        s.text(cx + 20, y + 14, label, size=FS_TINY, bold=True, anchor="start")
        s.text(cx + 20, y + 28, desc, size=11, anchor="start", fill="text_light")
        if i < len(comp_pipeline) - 1:
            s.arrow(cx + cw // 2, y + 38, cx + cw // 2, y + 42, color="dark")

    # Соединение агентов по WebSocket
    ws_y = py + ph + 15
    s.rect(30, ws_y, W - 60, 36, fill="dark", rx=4)
    s.text(
        W // 2,
        ws_y + 18,
        "Двусторонняя связь WebSocket (ws://localhost:8849)",
        size=FS_SMALL,
        fill="white",
        bold=True,
    )

    s.arrow(px + pw // 2, py + ph + 2, px + pw // 2, ws_y - 2, color="dark")
    s.arrow(cx + cw // 2, cy + ch_h + 2, cx + cw // 2, ws_y - 2, color="dark")

    # Примеры сообщений
    my = ws_y + 50
    s.rect(30, my, W - 60, 150, fill="code_bg", rx=4)
    s.text(
        W // 2,
        my + 18,
        "Двусторонний поток в реальном времени: звонок и работа за компьютером одновременно",
        size=FS_BODY,
        bold=True,
    )

    msgs = [
        ("Телефон → Компьютер", "[FROM_PHONE_AGENT] Пользователь назвал имя Чжан Сань", "→"),
        ("Компьютер → Телефон", "[FROM_COMPUTER_AGENT] Имя заполнено, нужен номер документа", "←"),
        ("Телефон → Компьютер", "[FROM_PHONE_AGENT] Номер документа 310101199001011234", "→"),
        (
            "Компьютер → Телефон",
            "[FROM_COMPUTER_AGENT] Форма отправлена, регистрация завершена",
            "←",
        ),
    ]
    for i, (sender, content, direction) in enumerate(msgs):
        y = my + 42 + i * 26
        s.text(
            42,
            y,
            sender,
            size=FS_TINY,
            bold=True,
            anchor="start",
            fill="text" if "→" == direction else "text_light",
        )
        s.mono(210, y, content, size=10, anchor="start")

    # Ключевая идея
    s.text(
        W // 2,
        my + 140,
        "Важно: два агента параллельно выполняют независимые циклы ReAct без блокировок",
        size=FS_SMALL,
        fill="text_light",
    )

    s.save(os.path.join(_output_dir, "fig10-8.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-8: Агенты для параллельного сбора данных с сайтов (эксперимент 9.7)
# ════════════════════════════════════════════════════════════════════


def fig9_8() -> None:
    W, H = 780, 530
    s = SVG(W, H)

    s.text(
        W // 2,
        28,
        "Эксперимент 10.7: параллельный Web Scraping — каскадная остановка",
        size=FS_TITLE,
        bold=True,
    )

    # Агент-оркестратор
    ox, oy, ow, oh = 230, 55, 320, 65
    s.rect(ox, oy, ow, oh, fill="medium")
    s.text(ox + ow // 2, oy + 20, "Агент-оркестратор", size=FS_BODY, bold=True)
    s.text(
        ox + ow // 2,
        oy + 44,
        "Динамическое создание · контроль в реальном времени · каскадная остановка",
        size=FS_TINY,
        fill="text_light",
    )

    # Параллельные агенты Computer Use
    agents = [
        ("Агент 1", "cs.edu.cn", "поиск... ◎", "light"),
        ("Агент 2", "math.edu.cn", "не найден ✗", "#e8e8e8"),
        ("Агент 3", "phys.edu.cn", "найден! ✓", "medium"),
        ("Агент 4", "chem.edu.cn", "остановлен ⊘", "code_bg"),
        ("Агент 5", "bio.edu.cn", "остановлен ⊘", "code_bg"),
    ]
    aw = 130
    gap = 12
    total_w = len(agents) * aw + (len(agents) - 1) * gap
    ax_start = (W - total_w) // 2
    ay = 160

    for i, (name, url, status, fill) in enumerate(agents):
        x = ax_start + i * (aw + gap)
        s.rect(x, ay, aw, 95, fill=fill, rx=4)
        s.text(x + aw // 2, ay + 16, name, size=FS_SMALL, bold=True)
        s.mono(x + aw // 2, ay + 35, url, size=10, anchor="middle")
        s.text(x + aw // 2, ay + 55, "Поиск в каталоге", size=FS_TINY, fill="text_light")
        s.text(
            x + aw // 2,
            ay + 75,
            status,
            size=FS_TINY,
            bold=("найден" in status),
            fill="text" if "найден" in status else "text_light",
        )

        s.arrow(ox + ow // 2, oy + oh + 2, x + aw // 2, ay - 2, color="dark")

    # Ход каскадной остановки
    ty = 280
    s.rect(30, ty, W - 60, 120, fill="code_bg", rx=4)
    s.text(W // 2, ty + 18, "Хронология каскадной остановки", size=FS_BODY, bold=True)

    timeline = [
        ("t=0s", "Запущены 5 агентов\nИщут преподавателя «Чжан Вэй»"),
        ("t=12s", "Агент 2 завершил работу\nЦель не найдена → штатный выход"),
        ("t=18s", "Агент 3 нашёл цель!\nОтправлен target_found"),
        ("t=18.1s", "Orch передаёт terminate\nагентам 1,4,5"),
        ("t=19s", "Остановка подтверждена\nРезультаты собраны"),
    ]
    tw = 130
    tx_start = (W - len(timeline) * tw) // 2
    for i, (time, desc) in enumerate(timeline):
        x = tx_start + i * tw
        s.text(x + tw // 2, ty + 42, time, size=FS_SMALL, bold=True, max_width=tw - 8)
        for j, ln in enumerate(desc.split("\n")):
            s.text(
                x + tw // 2,
                ty + 60 + j * 16,
                ln,
                size=FS_TINY,
                fill="text_light",
                max_width=tw - 8,
            )
        if i < len(timeline) - 1:
            s.arrow(x + tw - 2, ty + 55, x + tw + 4, ty + 55, color="dark")

    # Результат и сравнение
    ry = 420
    s.rect(30, ry, 340, 85, fill="light", rx=4)
    s.text(200, ry + 18, "Найденный результат", size=FS_BODY, bold=True)
    result_lines = [
        "Имя: Чжан Вэй  Факультет: физический",
        "Должность: профессор  Область: квантовые вычисления",
        "Почта: zhangwei@phys.edu.cn",
    ]
    for i, ln in enumerate(result_lines):
        s.mono(50, ry + 40 + i * 16, ln, size=11)

    s.rect(400, ry, 350, 85, fill="medium", rx=4)
    s.text(575, ry + 18, "Сравнение производительности", size=FS_BODY, bold=True)
    s.text(
        420,
        ry + 42,
        "Последовательно: 10 сайтов × 30s = ~5 минут",
        size=FS_TINY,
        anchor="start",
        fill="text_light",
    )
    s.text(
        420,
        ry + 60,
        "Параллельно: поиск 18 секунд + остановка 1 секунда = 19 секунд",
        size=FS_TINY,
        anchor="start",
        bold=True,
    )
    s.text(
        420,
        ry + 78,
        "Ускорение: ~15× (с каскадной остановкой)",
        size=FS_TINY,
        anchor="start",
        fill="text_light",
    )

    s.save(os.path.join(_output_dir, "fig10-9.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-9: Цепочка Handoff
# ════════════════════════════════════════════════════════════════════


def fig9_9() -> None:
    W, H = 780, 440
    s = SVG(W, H)

    s.text(
        W // 2,
        28,
        "Цепочка Handoff: равноправная передача и контрактное взаимодействие",
        size=FS_TITLE,
        bold=True,
    )

    nodes = [
        ("Агент A", "Анализ требований", "Результат: требования\nspec.json", "medium"),
        ("Агент B", "Проектирование", "Результат: техпроект\ndesign.md", "light"),
        ("Агент C", "Реализация", "Результат: исходный код\nsrc/*.py", "light"),
        ("Агент D", "Тестирование", "Результат: отчёт\ntest_report.md", "medium"),
    ]

    nw, nh = 160, 130
    gap = 22
    total_w = len(nodes) * nw + (len(nodes) - 1) * gap
    nx_start = (W - total_w) // 2
    ny = 60

    for i, (name, role, output, fill) in enumerate(nodes):
        x = nx_start + i * (nw + gap)
        s.rect(x, ny, nw, nh, fill=fill, rx=6)
        s.text(x + nw // 2, ny + 20, name, size=FS_SMALL, bold=True)
        s.text(x + nw // 2, ny + 40, role, size=FS_TINY, fill="text_light")

        s.rect(x + 8, ny + 55, nw - 16, 50, fill="code_bg", rx=3)
        for j, ln in enumerate(output.split("\n")):
            s.text(x + nw // 2, ny + 72 + j * 16, ln, size=FS_TINY, fill="text_light")

        s.text(x + nw // 2, ny + nh - 8, "После завершения →", size=FS_TINY, fill="text_light")

        if i < len(nodes) - 1:
            s.arrow(x + nw + 4, ny + nh // 2, x + nw + gap - 4, ny + nh // 2)

    # Содержимое Handoff
    hy = 215
    s.rect(30, hy, W - 60, 90, fill="code_bg", rx=4)
    s.text(W // 2, hy + 18, "Данные Handoff (пример: агент A → агент B)", size=FS_BODY, bold=True)

    handoff_fields = [
        ("Условие", "A завершил требования → is_complete=True"),
        ("Целевой агент", 'target="architect" (агент B)'),
        ("Данные", 'files=["spec.json"] + summary="Магазин: 3 микросервиса, REST API"'),
        ("После передачи", 'status="выход" (освободить ресурсы, не ожидать)'),
    ]
    for i, (field, value) in enumerate(handoff_fields):
        y = hy + 38 + i * 16
        s.text(42, y, field + ":", size=FS_TINY, bold=True, anchor="start", max_width=100)
        s.text(150, y, value, size=FS_TINY, anchor="start", fill="text_light")

    # Сравнение со схемой с менеджером
    cy = 320
    s.rect(30, cy, 340, 100, fill="light", rx=4)
    s.text(200, cy + 18, "Плюсы децентрализации", size=FS_SMALL, bold=True)
    advantages = [
        "✓ Менеджеру не нужно знать все роли",
        "✓ Чёткие границы и слабая связанность",
        "✓ Несколько инженеров работают параллельно",
    ]
    for i, adv in enumerate(advantages):
        s.text(48, cy + 42 + i * 20, adv, size=FS_TINY, anchor="start", fill="text_light")

    s.rect(400, cy, 350, 100, fill="light", rx=4)
    s.text(575, cy + 18, "Минусы децентрализации", size=FS_SMALL, bold=True)
    limits = [
        "✗ Нет глобальной оптимизации",
        "✗ Сложная обработка сбоев без координатора",
        "✗ Фиксированный процесс трудно менять",
    ]
    for i, lim in enumerate(limits):
        s.text(418, cy + 42 + i * 20, lim, size=FS_TINY, anchor="start", fill="text_light")

    s.save(os.path.join(_output_dir, "fig10-10.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-10: Конвейер SOP в MetaGPT
# ════════════════════════════════════════════════════════════════════


def fig9_10() -> None:
    W, H = 780, 530
    s = SVG(W, H)

    s.text(
        W // 2,
        28,
        "Конвейер SOP в MetaGPT: на основе стандартизированных документов",
        size=FS_TITLE,
        bold=True,
    )

    roles = [
        (
            "Менеджер продукта",
            "medium",
            "Вход: требования пользователя",
            ["Функции + приоритеты", "Пользовательские истории (5)", "Критерии приёмки"],
            "docs/PRD.md",
        ),
        (
            "Архитектор",
            "light",
            "Вход: PRD.md",
            ["Стек: FastAPI+React", "Спецификация API (OpenAPI)", "Схема базы данных"],
            "docs/design.md",
        ),
        (
            "Инженеры ×3",
            "light",
            "Вход: design.md + спецификации",
            ["Модуль A: пользователи", "Модуль B: заказы", "Модуль C: платежи"],
            "src/*.py",
        ),
        (
            "QA-инженер",
            "medium",
            "Вход: src/ + PRD.md",
            ["Модульные тесты (pytest)", "Интеграционные тесты (API)", "Ошибки → инженеру"],
            "docs/test_report.md",
        ),
    ]

    rw = 170
    gap = 16
    total_w = len(roles) * rw + (len(roles) - 1) * gap
    rx_start = (W - total_w) // 2
    ry = 55

    for i, (name, fill, input_desc, outputs, artifact) in enumerate(roles):
        x = rx_start + i * (rw + gap)

        s.rect(x, ry, rw, 230, fill=fill, rx=6)
        s.text(x + rw // 2, ry + 20, name, size=FS_SMALL, bold=True)

        s.text(x + 8, ry + 42, input_desc, size=11, anchor="start", fill="text_light")

        s.rect(x + 8, ry + 58, rw - 16, 20 + len(outputs) * 16, fill="code_bg", rx=3)
        s.text(x + 14, ry + 72, "Результат:", size=FS_TINY, bold=True, anchor="start")
        for j, out in enumerate(outputs):
            s.text(x + 14, ry + 88 + j * 16, out, size=11, anchor="start", fill="text_light")

        s.rect(x + 8, ry + 168, rw - 16, 30, fill="dark", rx=12)
        s.mono(x + rw // 2, ry + 183, artifact, size=11, anchor="middle", fill="white")

        if i < len(roles) - 1:
            ax1 = x + rw + 2
            ax2 = x + rw + gap - 2
            s.arrow(ax1, ry + 115, ax2, ry + 115)

    # Обратная связь от QA к инженеру
    qa_x = rx_start + 3 * (rw + gap) + rw // 2
    eng_x = rx_start + 2 * (rw + gap) + rw // 2
    s.arrow_curved(
        qa_x, ry + 230 + 5, eng_x, ry + 230 + 5, curve=-30, label="Исправление ошибок", dash=True
    )

    # Общая файловая система
    fy = 310
    s.rect(30, fy, W - 60, 50, fill="medium", rx=4)
    s.text(W // 2, fy + 16, "Общий каталог проекта", size=FS_SMALL, bold=True)
    s.mono(
        W // 2,
        fy + 36,
        "docs/PRD.md  docs/design.md  src/*.py  docs/test_report.md",
        size=11,
        anchor="middle",
    )

    # Ключевая идея
    ky = 375
    s.rect(30, ky, W - 60, 130, fill="code_bg", rx=4)
    s.text(W // 2, ky + 18, "Основные принципы MetaGPT", size=FS_BODY, bold=True)

    insights = [
        ("Стандартные документы", "Роль выдаёт заданный формат — далее не нужен ход рассуждений"),
        ("Слабая связанность", "Более мощный PM при том же формате PRD не требует правок далее"),
        ("Без менеджера", "Управление идёт по DAG: PM→Arch→Eng→QA, без диспетчера"),
        ("Канал ошибок", "Сбой QA → отчёт по модулю инженеру → новая итерация"),
    ]
    for i, (title, desc) in enumerate(insights):
        y = ky + 42 + i * 24
        s.text(
            42,
            y,
            "▸ " + title,
            size=FS_SMALL,
            bold=True,
            anchor="start",
            max_width=130,
        )
        s.text(180, y, desc, size=FS_TINY, anchor="start", fill="text_light", max_width=W - 210)

    s.save(os.path.join(_output_dir, "fig10-11.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-11: Архитектура VLA (Vision-Language-Action) — сравнение трёх подходов
# ════════════════════════════════════════════════════════════════════


def fig9_11() -> None:
    W, H = 900, 620
    s = SVG(W, H)

    # Общий вход
    in_x, in_y, in_w, in_h = 230, 55, 440, 64
    s.rect(in_x, in_y, in_w, in_h, fill="medium", rx=6)
    s.text(
        in_x + in_w / 2,
        in_y + 22,
        "Общий вход: изображение с камеры + текстовая команда",
        size=FS_SMALL,
        bold=True,
    )
    s.text(
        in_x + in_w / 2,
        in_y + 44,
        "«Положи красный кубик в синюю коробку»",
        size=FS_TINY,
        fill="text_light",
    )

    # Стрелки к трём ветвям
    s.arrow(in_x + 70, in_y + in_h + 2, 145, 165)  # → OpenVLA
    s.arrow(W / 2, in_y + in_h + 2, W / 2, 165)  # → π₀
    s.arrow(in_x + in_w - 70, in_y + in_h + 2, 755, 165)  # → RT-2

    # Три колонки архитектуры
    col_w, col_gap = 270, 30
    cols_total = 3 * col_w + 2 * col_gap
    sx0 = (W - cols_total) / 2  # = 30

    columns = [
        (
            "OpenVLA",
            "Открытая модель · дискретные токены действий",
            "light",
            [
                ("Визуальный энкодер", "DINOv2 + SigLIP", "Извлекает признаки из пикселей"),
                ("Основа LLM", "Llama 2 (7B)", "Понимает команду и сцену"),
                (
                    "Декодирование",
                    "Авторегрессия · текстовые токены",
                    "Действия разбиты на дискретные варианты",
                ),
                (
                    "Выходное действие",
                    'токены "a=[3,−2,5,...]"',
                    "Пошаговая генерация 7-DOF-команд управления",
                ),
            ],
        ),
        (
            "π₀ (Pi-Zero)",
            "Диффузионная стратегия · плавная траектория",
            "medium",
            [
                (
                    "Визуальный энкодер",
                    "ViT с объединением нескольких ракурсов",
                    "Извлекает признаки из пикселей",
                ),
                (
                    "Mixture-of-Transformers",
                    "Разделение быстрых и медленных ветвей",
                    "Язык мыслит медленно, управление быстро",
                ),
                (
                    "Декодирование",
                    "Итеративное диффузионное шумоподавление",
                    "Уточняет всю траекторию от грубого приближения к точному",
                ),
                (
                    "Выходное действие",
                    "Непрерывная последовательность (50 шагов/пакет)",
                    "Плавные высокочастотные управляющие сигналы",
                ),
            ],
        ),
        (
            "RT-2",
            "Языковая модель как модель действий",
            "light",
            [
                ("Визуально-языковая основа", "PaLI-X / PaLM-E", "Сквозное понимание VLM"),
                (
                    "Представление действий",
                    "Действия → токены естественного языка",
                    "«сдвинуть руку на 5 см вправо»",
                ),
                ("Декодирование", "Авторегрессия VLM", "Общие веса с генерацией текста"),
                ("Выходное действие", "Текст → разбор контроллером", "Наследует обобщение VLM"),
            ],
        ),
    ]

    top_y = 165
    title_h = 50
    row_h = 80
    for i, (name, tag, fill, rows) in enumerate(columns):
        cx = sx0 + i * (col_w + col_gap)
        # Контейнер колонки
        col_total_h = title_h + len(rows) * row_h + 14
        s.rect(cx, top_y, col_w, col_total_h, fill="white", stroke="border")
        # Заголовок колонки
        s.rect(cx, top_y, col_w, title_h, fill=fill)
        s.text(cx + col_w / 2, top_y + 18, name, size=FS_BODY, bold=True)
        s.text(cx + col_w / 2, top_y + 38, tag, size=FS_TINY, fill="text_light")

        # Строки
        for j, (label, value, hint) in enumerate(rows):
            ry = top_y + title_h + 8 + j * row_h
            s.rect(cx + 10, ry, col_w - 20, row_h - 8, fill="code_bg", rx=4)
            s.text(cx + col_w / 2, ry + 18, label, size=FS_TINY, bold=True)
            s.text(cx + col_w / 2, ry + 38, value, size=FS_TINY)
            s.text(cx + col_w / 2, ry + 56, hint, size=FS_TINY, fill="text_light")

    # Внизу: единый выходной слой
    out_y = top_y + title_h + 4 * row_h + 14 + 24
    s.rect(30, out_y, W - 60, 50, fill="darker", rx=6)
    s.text(
        W / 2,
        out_y + 18,
        "Сигналы управления роботом: углы сочленений 7-DOF / поза концевого эффектора",
        size=FS_SMALL,
        bold=True,
        fill="white",
    )
    s.text(
        W / 2,
        out_y + 36,
        "Подходы различаются тем, как сообщают роботу, каким должно быть следующее движение, но в итоге используют единый интерфейс управления",
        size=FS_TINY,
        fill="white",
    )

    s.save(os.path.join(_output_dir, "fig9-11.svg"))


# ════════════════════════════════════════════════════════════════════
#  fig9-12: Система агентов для голосовой игры «Оборотни» (эксперимент 9.9)
# ════════════════════════════════════════════════════════════════════


def fig9_12() -> None:
    W, H = 780, 550
    s = SVG(W, H)

    s.text(
        W // 2,
        28,
        "Эксперимент 9.9: голосовые «Оборотни» — контроль доступа",
        size=FS_TITLE,
        bold=True,
    )

    # Ведущий (управляется кодом)
    jx, jy, jw, jh = 260, 55, 260, 75
    s.rect(jx, jy, jw, jh, fill="dark", rx=6)
    s.text(
        jx + jw // 2, jy + 20, "Ведущий (управляется кодом)", size=FS_BODY, bold=True, fill="white"
    )
    s.text(
        jx + jw // 2,
        jy + 42,
        "Состояние игры · этапы · раздача информации",
        size=FS_TINY,
        fill="white",
    )
    s.text(jx + jw // 2, jy + 58, "Night → Day → Vote → Settle", size=FS_TINY, fill="white")

    # Агенты с ролями
    roles = [
        (
            40,
            "Оборотень 1",
            "🐺",
            "medium",
            ["Видит: союзников", "Стратегия: притвориться мирным", "Ночью: выбрать цель"],
        ),
        (
            185,
            "Оборотень 2",
            "🐺",
            "medium",
            ["Видит: союзников", "Стратегия: голосовать вместе", "Ночью: согласовать цель"],
        ),
        (
            330,
            "Провидец",
            "🔮",
            "light",
            [
                "Видит: результаты проверки",
                "Стратегия: вовремя раскрыться",
                "Ночью: проверить 1 игрока",
            ],
        ),
        (
            475,
            "Ведьма",
            "🧪",
            "light",
            [
                "Видит: смерть/спасение",
                "Стратегия: беречь зелья",
                "Ночью: спасти/отравить 1 игрока",
            ],
        ),
        (
            620,
            "Мирные ×2",
            "👤",
            "#e8e8e8",
            [
                "Видят: только публичную информацию",
                "Стратегия: логический анализ",
                "Днём: анализировать речи",
            ],
        ),
    ]

    aw, ay = 135, 180
    for x, name, icon, fill, info in roles:
        s.rect(x, ay, aw, 140, fill=fill, rx=6)
        s.text(x + aw // 2, ay + 18, f"{icon} {name}", size=FS_SMALL, bold=True)
        for i, ln in enumerate(info):
            s.text(x + aw // 2, ay + 42 + i * 20, ln, size=11, fill="text_light")

        # Стрелка от ведущего
        s.arrow(jx + jw // 2, jy + jh + 2, x + aw // 2, ay - 2, color="dark")

        # Метка доступа
        if "Оборотень" in name:
            s.badge(x + aw - 45, ay + aw - 15, 40, 18, "свои", fill="darker", font_size=11)
        elif "Провидец" in name:
            s.badge(
                x + aw - 55, ay + aw - 15, 50, 18, "результат проверки", fill="darker", font_size=10
            )

    # Контроль доступа к информации
    iy = 340
    s.rect(30, iy, W - 60, 90, fill="code_bg", rx=4)
    s.text(
        W // 2,
        iy + 18,
        "Контроль доступа: ведущий фильтрует контекст по роли",
        size=FS_BODY,
        bold=True,
    )

    perms = [
        ("Оборотни", "Личности всех оборотней + ночное обсуждение + публичные высказывания"),
        ("Провидец", "Результаты только своих проверок + публичные высказывания"),
        ("Ведьма", "Жертва этой ночи + статус противоядия и яда + публичные высказывания"),
        ("Мирные", "Только публичные высказывания + история голосования (без закрытых данных)"),
    ]
    pw = (W - 80) // 2
    for i, (role, perm) in enumerate(perms):
        row, col = i // 2, i % 2
        x = 50 + col * pw
        y = iy + 40 + row * 22
        s.text(x, y, role + ":", size=FS_TINY, bold=True, anchor="start", max_width=50)
        s.text(
            x + 55,
            y,
            perm,
            size=FS_TINY,
            anchor="start",
            fill="text_light",
            max_width=pw - 65,
        )

    # Голосовое взаимодействие
    vy = 445
    s.rect(30, vy, W - 60, 85, fill="light", rx=4)
    s.text(
        W // 2,
        vy + 18,
        "Голосовое взаимодействие в реальном времени (ASR + LLM + TTS)",
        size=FS_BODY,
        bold=True,
    )

    voice_flow = [
        ("Обсуждение днём", "Ведущий задаёт порядок\nВыступают по местам"),
        ("Голосование", "Собрать голоса игроков\nПодсчитать и объявить итог"),
        ("Ночной этап", "Ведущий будит роли по очереди\nЗакрытые голосовые каналы"),
        ("Живой игрок", "Случайная роль\nГолосует и выступает"),
    ]
    vw = (W - 80) // len(voice_flow)
    for i, (title, desc) in enumerate(voice_flow):
        cx = 50 + i * vw + vw // 2
        s.text(cx, vy + 42, title, size=FS_SMALL, bold=True, max_width=vw - 8)
        for j, ln in enumerate(desc.split("\n")):
            s.text(
                cx,
                vy + 60 + j * 16,
                ln,
                size=FS_TINY,
                fill="text_light",
                max_width=vw - 8,
            )

    s.save(os.path.join(_output_dir, "fig10-13.svg"))


# ════════════════════════════════════════════════════════════════════
#  Точка входа
# ════════════════════════════════════════════════════════════════════


def main(output_dir: str) -> None:
    global _output_dir
    _output_dir = output_dir
    os.makedirs(_output_dir, exist_ok=True)

    figs = [
        ("fig10-1", fig9_1),
        ("fig10-2", fig9_2),
        ("fig10-4", fig9_3),
        ("fig10-5", fig9_4),
        ("fig10-6", fig9_5),
        ("fig10-7", fig9_6),
        ("fig10-8", fig9_7),
        ("fig10-9", fig9_8),
        ("fig10-10", fig9_9),
        ("fig10-11", fig9_10),
        ("fig9-11", fig9_11),
        ("fig10-13", fig9_12),
    ]

    for name, func in figs:
        func()
        print(f"  ✓ {name}")

    print(f"\nСоздано {len(figs)} иллюстраций в {_output_dir}/")


if __name__ == "__main__":
    main(parse_output_dir(_output_dir))
