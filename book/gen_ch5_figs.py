#!/usr/bin/env python3
"Генерирует все SVG-иллюстрации для главы 5 (Генерация кода).\n\nИллюстрации (всего 11):\n  fig5-1:  Архитектура OpenClaw — агент программирования как ядро универсального AI-агента\n  fig5-2:  Многоэтапный процесс агента программирования (операции с файлами и вызовы инструментов)\n  fig5-3:  Сравнение инструментов поиска (4 типа с реальными примерами запросов)\n  fig5-4:  Сравнение способов редактирования файлов (5 методов с diff кода)\n  fig5-5:  Конвейер создания PPT (автор — рецензент с кодом Slidev)\n  fig5-6:  Эксп. 5.6+5.7 — конвейер преобразования статьи в PPT и видео\n  fig5-7:  Эксп. 5.10 — конвейер диагностики продукционных журналов\n  fig5-8:  Динамическая генерация формы (LLM → HTML-форма → JSON → продолжение)\n  fig5-9:  SQL-агент (режим артефактов, данные обходят LLM)\n  fig5-10: Цикл самозагрузки агента (концепция самовоспроизведения)\n  fig5-11: Эксп. 5.14 — агент, создающий агентов (метаагент)\n"

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    CORNER_R,
    FS_BODY,
    FS_LABEL,
    FS_SMALL,
    FS_TINY,
    FS_TITLE,
    SVG,
    parse_output_dir,
)

_output_dir = os.path.join(os.path.dirname(__file__), "images")


def _pill(
    svg: SVG,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    fill: str = "light",
    font_size: float = FS_SMALL,
    bold: bool = False,
) -> None:
    svg.rect(x, y, w, h, fill=fill, rx=h // 2)
    c = "white" if fill in ("dark", "darker") else "text"
    svg.text(x + w / 2, y + h / 2, label, size=font_size, fill=c, bold=bold)


# ──────────────────────── fig5-1 (НОВОЕ: архитектура OpenClaw) ──────


def fig5_1() -> None:
    """Архитектура OpenClaw: агент программирования как ядро универсального агента"""
    w, h = 980, 600
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Архитектура OpenClaw: агент программирования — ядро универсального агента",
        size=FS_TITLE,
        bold=True,
    )

    # Сверху: многоплатформенный шлюз сообщений
    gw_y, gw_h = 58, 66
    svg.group_box(
        60,
        gw_y,
        w - 120,
        gw_h,
        "Мультиплатформенный шлюз сообщений (уровень взаимодействия с пользователем)",
    )
    channels = ["WhatsApp", "Telegram", "iMessage", "Slack", "CLI"]
    pill_w, pill_h = 130, 32
    total_pw = len(channels) * pill_w + (len(channels) - 1) * 18
    px_start = (w - total_pw) / 2
    for i, ch in enumerate(channels):
        px = px_start + i * (pill_w + 18)
        svg.rect(px, gw_y + 26, pill_w, pill_h, fill="medium", rx=pill_h // 2)
        svg.text(px + pill_w / 2, gw_y + 26 + pill_h / 2, ch, size=FS_SMALL)

    svg.arrow(w / 2, gw_y + gw_h + 2, w / 2, 158)
    svg.text(
        w / 2 + 12,
        134,
        "Запрос на естественном языке",
        size=FS_LABEL,
        fill="text_light",
        anchor="start",
    )

    # В центре: среда агента программирования — расширена для размещения 4 инструментов
    ca_x, ca_y, ca_w, ca_h = 200, 160, 580, 210
    svg.rect(ca_x, ca_y, ca_w, ca_h, fill="light")
    svg.rect(ca_x, ca_y, ca_w, 40, fill="darker", rx=6)
    svg.text(
        ca_x + ca_w / 2,
        ca_y + 20,
        "Среда выполнения агента программирования (инференс + ядро выполнения)",
        size=FS_BODY,
        bold=True,
        fill="white",
    )

    tools = [
        ("Code Interpreter", "Выполнение кода"),
        ("Bash Shell", "Системные команды"),
        ("Read File", "Чтение файлов"),
        ("Write File", "Запись файлов"),
        ("Edit File", "Правка файлов"),
        ("Glob", "Поиск файлов"),
        ("Grep", "Поиск в тексте"),
    ]
    tw, th, tgap = 132, 60, 12
    for ri, row in enumerate([tools[:4], tools[4:]]):
        row_total_w = len(row) * tw + (len(row) - 1) * tgap
        rx_start = ca_x + (ca_w - row_total_w) / 2
        ry = ca_y + 56 + ri * (th + tgap)
        for ci, (name, desc) in enumerate(row):
            tx = rx_start + ci * (tw + tgap)
            svg.rect(tx, ry, tw, th, fill="white")
            svg.text(tx + tw / 2, ry + 22, name, size=FS_TINY, bold=True)
            svg.text(tx + tw / 2, ry + 42, desc, size=FS_TINY, fill="text_light")

    # Слева: Deep Research
    dr_x, dr_y, dr_w, dr_h = 22, 198, 158, 86
    svg.rect(dr_x, dr_y, dr_w, dr_h, fill="medium")
    svg.text(dr_x + dr_w / 2, dr_y + 22, "Модуль веб-поиска", size=FS_SMALL, bold=True)
    svg.text(dr_x + dr_w / 2, dr_y + 44, "Deep Research", size=FS_TINY, fill="text_light")
    svg.text(dr_x + dr_w / 2, dr_y + 66, "Веб-запросы · разбор", size=FS_TINY, fill="text_light")
    svg.arrow(dr_x + dr_w + 2, dr_y + dr_h / 2, ca_x - 2, ca_y + ca_h / 2)

    # Справа: Computer Use
    cu_x, cu_y, cu_w, cu_h = 800, 198, 158, 86
    svg.rect(cu_x, cu_y, cu_w, cu_h, fill="medium")
    svg.text(cu_x + cu_w / 2, cu_y + 22, "Автоматизация браузера", size=FS_SMALL, bold=True)
    svg.text(cu_x + cu_w / 2, cu_y + 44, "Computer Use", size=FS_TINY, fill="text_light")
    svg.text(cu_x + cu_w / 2, cu_y + 66, "Playwright DOM", size=FS_TINY, fill="text_light")
    svg.arrow(ca_x + ca_w + 2, ca_y + ca_h / 2, cu_x - 2, cu_y + cu_h / 2)

    # Снизу: слой файловой системы
    fs_y, fs_h = 410, 140
    svg.arrow(w / 2, ca_y + ca_h + 2, w / 2, fs_y - 2)
    svg.text(
        w / 2 + 12, 390, "Чтение / запись файлов", size=FS_LABEL, fill="text_light", anchor="start"
    )
    svg.group_box(60, fs_y, w - 120, fs_h, "Файловая система (центр памяти, знаний и возможностей)")

    mem_items = [
        ("MEMORY.md", "Факты / предпочтения пользователя"),
        ("daily/YYYY-MM-DD.md", "Архив по дням / журналы взаимодействий"),
        ("SOUL.md", "Идентичность и правила агента"),
        ("Файлы базы знаний", "Опыт задач / саморазвитие"),
        ("Контроль версий Git", "Откат памяти / аудит истории"),
    ]
    item_w, item_h, item_gap = 162, 76, 16
    total_iw = len(mem_items) * item_w + (len(mem_items) - 1) * item_gap
    ix_start = (w - total_iw) / 2
    for i, (title, desc) in enumerate(mem_items):
        ix = ix_start + i * (item_w + item_gap)
        iy = fs_y + 34
        svg.rect(ix, iy, item_w, item_h, fill="white")
        svg.text(ix + item_w / 2, iy + 26, title, size=FS_TINY, bold=True)
        svg.text(ix + item_w / 2, iy + 52, desc, size=FS_TINY, fill="text_light")

    # В самом низу: LLM как операционная система
    os_y = fs_y + fs_h + 16
    svg.rect(60, os_y, w - 120, 38, fill="darker", rx=6)
    svg.text(
        w / 2,
        os_y + 19,
        "LLM = новая ОС: скрывает сложность интеллектуальных функций, предоставляет единую абстракцию",
        size=FS_SMALL,
        bold=True,
        fill="white",
    )

    svg.save(os.path.join(_output_dir, "fig5-1.svg"))


# ──────────────────────── fig5-2 (ранее fig5-1) ────────────────────────


def fig5_2() -> None:
    """Многоэтапный процесс агента программирования (конкретные вызовы инструментов)"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Многоуровневый процесс агента программирования", size=FS_TITLE, bold=True)

    phases = [
        (
            "① Документация",
            "medium",
            [
                ("read_file", "README.md, ARCHITECTURE.md"),
                ("glob", "**/*.py, **/*.ts"),
                ("write_file", "→ создать руководство CLAUDE.md"),
            ],
        ),
        (
            "② Анализ требований",
            "light",
            [
                ("ask_user", '"Цель — задержка или пропускная способность?"'),
                ("grep", '"latency|throughput" src/'),
                ("read_file", "src/config.py (текущие параметры)"),
            ],
        ),
        (
            "③ Документ с проектным решением",
            "light",
            [
                ("write_file", "design.md (сравнение вариантов)"),
                ("ask_user", "отправить проект → ждать одобрения"),
                ("—", "после проверки человеком → продолжить"),
            ],
        ),
        (
            "④ Код и тесты",
            "medium",
            [
                ("edit_file", "old_str→new_str изменить код"),
                ("bash", "pytest tests/ -v"),
                ("edit_file", "исправить тест → перезапустить"),
            ],
        ),
        (
            "⑤ Проверка рендеринга и сдача результата",
            "light",
            [
                ("bash", "ruff check src/ (lint)"),
                ("read_file", "самопроверка: читаемость/безопасность/производительность"),
                ("edit_file", "обновить ARCHITECTURE.md"),
            ],
        ),
    ]

    phase_w = 155
    phase_gap = 12
    total_w = len(phases) * phase_w + (len(phases) - 1) * phase_gap
    sx = (w - total_w) / 2

    for i, (title, fill, steps) in enumerate(phases):
        x = sx + i * (phase_w + phase_gap)
        ph = 240
        svg.rect(x, 55, phase_w, ph, fill=fill)
        svg.text(x + phase_w / 2, 78, title, size=FS_SMALL, bold=True)
        svg.line(x + 8, 92, x + phase_w - 8, 92, color="dark")

        for j, (tool, desc) in enumerate(steps):
            ty = 110 + j * 70
            _pill(svg, x + 8, ty, phase_w - 16, 22, tool, fill="dark", font_size=11, bold=True)
            lines = desc.split("\n") if "\n" in desc else [desc]
            for k, line in enumerate(lines):
                svg.mono(x + 10, ty + 34 + k * 16, line, size=10)

        if i < len(phases) - 1:
            ax = x + phase_w + 2
            svg.arrow(ax, 55 + ph / 2, ax + phase_gap - 4, 55 + ph / 2)

    # Снизу: циклы обратной связи
    svg.line(30, 320, w - 30, 320, color="dark", dash=True)
    svg.text(w / 2, 340, "Механизм замкнутой обратной связи", size=FS_BODY, bold=True)

    loops = [
        ("Тест не пройден → изменить код → повторить тест", "Цикл ④: сходимость за 2-3 итерации"),
        (
            "Ошибка lint → исправить → проверить снова",
            "Цикл ⑤: автоматически запускается после правки",
        ),
        ("Проверка рендеринга выявила дефект → вернуться к ④", "Откат ⑤→④: контроль качества"),
    ]
    ly = 365
    for label, note in loops:
        svg.rect(80, ly, 500, 46, fill="light")
        svg.text(330, ly + 15, label, size=FS_SMALL, bold=True)
        svg.text(330, ly + 34, note, size=FS_TINY, fill="text_light")
        ly += 50

    # Примечания справа
    annots = [
        "Строка состояния агента: cwd, git branch",
        "Строка состояния агента: изменения вне индекса",
        "Вывод инструмента: усечение начала и конца",
        "Постоянный сеанс терминала",
    ]
    for i, ann in enumerate(annots):
        svg.rect(610, 365 + i * 50, 250, 38, fill="code_bg", stroke="dark", rx=4)
        svg.text(735, 384 + i * 50, ann, size=FS_TINY, fill="text_light")

    svg.text(
        w / 2,
        565,
        "Сначала план · Постоянная проверка · Код и документация развиваются вместе",
        size=FS_BODY,
        bold=True,
        fill="darker",
    )

    svg.save(os.path.join(_output_dir, "fig5-2.svg"))


# ──────────────────────── fig5-3 ────────────────────────


def fig5_3() -> None:
    """Сравнение инструментов поиска (четыре инструмента и реальные запросы)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Сравнение четырёх инструментов поиска", size=FS_TITLE, bold=True)

    tools = [
        (
            "Поиск по регулярным выражениям (grep)",
            "medium",
            'rg "def handle_.*" --type py',
            [
                "src/api.py:42:  def handle_request(..)",
                "src/api.py:89:  def handle_timeout(..)",
                "src/ws.py:15:   def handle_connect(..)",
            ],
            "Точный текст → все вхождения",
        ),
        (
            "Поиск файлов (glob)",
            "light",
            "glob: **/test_*.py",
            ["tests/test_api.py", "tests/test_auth.py", "tests/unit/test_parser.py"],
            "Шаблон пути → без чтения файлов",
        ),
        (
            "Семантический поиск по коду",
            "light",
            '"проверка пользовательского ввода"',
            [
                "[0.91] src/validators.py:validate_input()",
                "[0.87] src/forms.py:sanitize_fields()",
                "[0.82] src/api.py:check_params()",
            ],
            "Естественный язык → гибридный поиск: векторы+BM25",
        ),
        (
            "Определения символов и ссылки на них",
            "medium",
            "find_references: UserService",
            [
                "Определение: src/services/user.py:12",
                "Ссылка: src/api/routes.py:34 (import)",
                "Ссылка: src/api/routes.py:56 (вызов)",
                "Ссылка: tests/test_user.py:8 (тест)",
            ],
            "Уровень AST → без путаницы имён",
        ),
    ]

    col_w = (w - 60) // 2
    col_gap = 20

    for i, (title, fill, query, results, note) in enumerate(tools):
        col = i % 2
        row = i // 2
        x = 20 + col * (col_w + col_gap)
        y = 55 + row * 260

        svg.rect(x, y, col_w, 240, fill="white", stroke="border")
        svg.rect(x, y, col_w, 36, fill=fill, rx=CORNER_R)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(x + col_w / 2, y + 18, title, size=FS_SMALL, bold=True, fill=tc)

        svg.text(
            x + 12, y + 54, "Запрос:", size=FS_TINY, bold=True, anchor="start", fill="text_light"
        )
        svg.rect(x + 8, y + 64, col_w - 16, 24, fill="code_bg", stroke="dark", rx=3)
        svg.mono(x + 14, y + 76, query, size=11)

        svg.text(
            x + 12,
            y + 102,
            "Результат:",
            size=FS_TINY,
            bold=True,
            anchor="start",
            fill="text_light",
        )
        rh = len(results) * 20 + 12
        svg.rect(x + 8, y + 112, col_w - 16, rh, fill="code_bg", stroke="dark", rx=3)
        for j, r in enumerate(results):
            svg.mono(x + 14, y + 128 + j * 20, r, size=10)

        svg.text(x + col_w / 2, y + 226, note, size=FS_TINY, fill="text_light")

    svg.save(os.path.join(_output_dir, "fig5-3.svg"))


# ──────────────────────── fig5-3 ────────────────────────


def fig5_4() -> None:
    """Сравнение способов редактирования файлов (пять способов и примеры кода)"""
    w, h = 900, 700
    svg = SVG(w, h)
    svg.text(w / 2, 28, "Сравнение пяти способов редактирования файлов", size=FS_TITLE, bold=True)

    approaches = [
        (
            "Diff + модель применения",
            "dark",
            [
                "LLM выводит описание diff:",
                "- def foo(x):",
                "    return x",
                "+ def foo(x, y=0):",
                "+   return x + y",
                "→ малая модель находит и применяет",
            ],
            "Плюс: разделение ответственности",
            "Минус: малейшее отклонение вызывает смещение",
        ),
        (
            "Старая строка → новая строка",
            "medium",
            [
                'old: "def foo(x):\\n',
                '       return x"',
                'new: "def foo(x, y=0):\\n',
                '       return x + y"',
                "→ точная замена строки",
            ],
            "Плюс: точно и однозначно",
            "Минус: полный вывод блока",
        ),
        (
            "По номерам строк",
            "light",
            [
                "Удалить строки 42-43, вставить:",
                "  def foo(x, y=0):",
                "    return x + y",
                "",
                "→ точный диапазон строк",
            ],
            "Плюс: высокая эффективность крупных операций",
            "Минус: в длинных файлах легко ошибиться с номерами строк",
        ),
        (
            "Команды в стиле Vim",
            "light",
            [
                "42G  (перейти к строке 42)",
                "cw   (заменить слово)",
                "dd   (удалить строку)",
                "yy/p (копировать/вставить)",
                "→ развитая семантика правок",
            ],
            "Плюс: эффективное перемещение и перестройка",
            "Минус: слабые модели часто ошибаются",
        ),
        (
            "По границам",
            "medium",
            [
                'start: "def foo(x):"',
                'end:   "    return x"',
                'new: "def foo(x, y=0):',
                '       return x + y"',
                "→ достаточно границ блока",
            ],
            "Плюс: не нужен полный блок",
            "Минус: сочетание границ должно быть уникальным",
        ),
    ]

    col_w = 168
    col_gap = 10
    total_cw = len(approaches) * col_w + (len(approaches) - 1) * col_gap
    sx = (w - total_cw) / 2

    for i, (title, fill, code_lines, pro, con) in enumerate(approaches):
        x = sx + i * (col_w + col_gap)

        svg.rect(x, 55, col_w, 38, fill=fill, rx=CORNER_R)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(x + col_w / 2, 74, title, size=FS_TINY, bold=True, fill=tc)

        code_h = len(code_lines) * 17 + 14
        svg.rect(x, 101, col_w, code_h, fill="code_bg", stroke="dark", rx=3)
        for j, line in enumerate(code_lines):
            svg.mono(x + 6, 117 + j * 17, line, size=11)

        py = 101 + code_h + 12
        svg.rect(x + 4, py, col_w - 8, 56, fill="white", stroke="dark", rx=3)
        svg.text(x + col_w / 2, py + 19, pro, size=FS_TINY, fill="text")
        svg.text(x + col_w / 2, py + 41, con, size=FS_TINY, fill="text_light")

    # Диаграмма практического применения внизу
    chart_y = 320
    svg.line(30, chart_y, w - 30, chart_y, color="dark", dash=True)
    svg.text(w / 2, chart_y + 24, "Практическое применение", size=FS_BODY, bold=True)

    adoptions = [
        ("Старая строка→новая строка", "Claude Code", 0.85, "dark"),
        ("Номера строк", "Глубокая интеграция с IDE", 0.50, "medium"),
        ("Diff + модель применения", "Cursor", 0.40, "light"),
        ("По границам", "Специализированные решения", 0.30, "light"),
        ("Команды в стиле Vim", "Экспериментальные решения", 0.15, "code_bg"),
    ]
    bar_x, bar_w_max = 250, 480
    by = chart_y + 48
    for label, products, ratio, fill in adoptions:
        svg.text(bar_x - 10, by + 14, label, size=FS_TINY, anchor="end", bold=True)
        bw = bar_w_max * ratio
        svg.rect(bar_x, by, bw, 28, fill=fill, rx=3)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(bar_x + bw / 2, by + 14, products, size=FS_TINY, fill=tc)
        by += 38

    svg.save(os.path.join(_output_dir, "fig5-4.svg"))


# ──────────────────────── fig5-4 ────────────────────────


def fig5_5() -> None:
    """Конвейер создания PPT (работа автора и рецензента с кодом Slidev)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Создание PPT: работа автора и рецензента", size=FS_TITLE, bold=True)

    # Агент-автор (слева)
    svg.rect(20, 60, 350, 280, fill="white", stroke="border", dash=True)
    svg.text(195, 82, "Агент-автор", size=FS_BODY, bold=True)

    svg.text(40, 110, "Вход: статья / исходные материалы", size=FS_SMALL, anchor="start", bold=True)
    svg.rect(30, 125, 330, 24, fill="code_bg", stroke="dark", rx=3)
    svg.mono(38, 137, "paper.pdf → разделы / тезисы / диаграммы", size=11)

    svg.text(40, 168, "Выход: Slidev Markdown", size=FS_SMALL, anchor="start", bold=True)
    code_lines = [
        "---",
        "layout: two-cols",
        "---",
        "# Архитектура Transformer",
        "::left::",
        "- Механизм самовнимания",
        "- Многоголовое внимание",
        "::right::",
        '<img src="fig3.png" />',
    ]
    svg.code_block(30, 182, 330, code_lines, font_size=10, line_h=14)

    # Агент-рецензент (справа)
    svg.rect(510, 60, 350, 280, fill="white", stroke="border", dash=True)
    svg.text(685, 82, "Агент-рецензент", size=FS_BODY, bold=True)

    svg.text(520, 110, "Шаг 1: создать снимки", size=FS_SMALL, anchor="start", bold=True)
    svg.rect(520, 125, 330, 50, fill="light")
    svg.text(685, 142, "slidev export --per-slide", size=FS_TINY, fill="text_light")
    svg.text(685, 160, "→ slide-01.png, slide-02.png ...", size=FS_TINY, fill="text_light")

    svg.text(520, 192, "Шаг 2: проверка с Vision LLM", size=FS_SMALL, anchor="start", bold=True)
    critique_lines = [
        "Критерии:",
        "  ✓ текст не выходит за границы",
        "  ✓ макет не перегружен",
        "  ✓ изображения нужного размера",
        "  ✗ Слайд 3: текст вышел за правую колонку",
        "  ✗ Слайд 7: контент расположен слишком плотно",
    ]
    svg.rect(520, 208, 330, len(critique_lines) * 16 + 12, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(critique_lines):
        svg.mono(528, 222 + j * 16, line, size=10)

    # Стрелки: автор → рецензент → автор (цикл)
    svg.arrow(370, 200, 508, 150, label="Код Slidev")
    svg.arrow(508, 300, 370, 260, label="Рекомендации", dash=True)

    # Метка итераций
    _pill(svg, 395, 220, 100, 24, "2-3 итерации", fill="dark", font_size=11, bold=True)

    # Снизу: зачем разделять агентов
    svg.line(30, 365, w - 30, 365, color="dark", dash=True)
    svg.text(w / 2, 388, "Зачем разделять автора и рецензента?", size=FS_BODY, bold=True)

    reasons = [
        (
            "Проблема одного агента",
            [
                "Снимки десятков страниц → контекст растёт",
                "Код + снимки → внимание рассеивается",
            ],
        ),
        (
            "Преимущества разделения",
            [
                "Рецензент: отдельный контекст → только снимки+код",
                "Автор сосредоточен на коде → получает только рекомендации",
            ],
        ),
        (
            "Практический эффект",
            [
                "Контекст занимает гораздо меньше места",
                "Точность исправлений заметно выше",
            ],
        ),
    ]
    rx = 30
    for title, items in reasons:
        svg.rect(rx, 405, 270, 130, fill="light")
        svg.text(rx + 135, 425, title, size=FS_SMALL, bold=True)
        for j, item in enumerate(items):
            svg.text(rx + 135, 450 + j * 24, item, size=FS_TINY, fill="text_light")
        rx += 290

    svg.save(os.path.join(_output_dir, "fig5-5.svg"))


# ──────────────────────── fig5-5 ────────────────────────


def fig5_6() -> None:
    """Эксперименты 5.6+5.7: сквозной конвейер статья→PPT→видео"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(
        w / 2, 30, "Эксперименты 5.6+5.7: статья → PPT → поясняющее видео", size=FS_TITLE, bold=True
    )

    # Верхний конвейер: статья → PPT
    stages_top = [
        (
            "Входной PDF",
            "medium",
            [
                "paper.pdf",
                "разбор структуры",
                "поиск ссылок на графику",
            ],
        ),
        (
            "Планирование",
            "light",
            [
                "структура на 10-20 страниц",
                "извлечение тезисов",
                "распределение графики",
            ],
        ),
        (
            "Создание Slidev",
            "light",
            [
                "код каждой страницы",
                "layout: two-cols",
                "компоновка кода и изображений",
            ],
        ),
        (
            "Проверка рендеринга",
            "medium",
            [
                "export --per-slide",
                "проверка Vision LLM",
                "переполнение/теснота",
            ],
        ),
        (
            "Итеративное исправление",
            "light",
            [
                "рецензент→автор",
                "правка кода Slidev",
                "повторный рендеринг и проверка",
            ],
        ),
    ]

    sw = 155
    sgap = 10
    total = len(stages_top) * sw + (len(stages_top) - 1) * sgap
    sx = (w - total) / 2

    svg.text(
        w / 2,
        60,
        "Этап 1: создание PPT (автор — рецензент)",
        size=FS_SMALL,
        bold=True,
        fill="text_light",
    )
    for i, (title, fill, details) in enumerate(stages_top):
        x = sx + i * (sw + sgap)
        svg.rect(x, 72, sw, 130, fill=fill)
        svg.text(x + sw / 2, 92, title, size=FS_SMALL, bold=True)
        svg.line(x + 8, 104, x + sw - 8, 104, color="dark")
        for j, line in enumerate(details):
            svg.mono(x + 8, 120 + j * 20, line, size=10)
        if i < len(stages_top) - 1:
            svg.arrow(x + sw + 2, 72 + 65, x + sw + sgap - 2, 72 + 65)

    # Стрелка вниз
    svg.arrow(w / 2, 202, w / 2, 240)
    svg.text(w / 2 + 60, 222, "PPT готов", size=FS_SMALL, fill="text_light")

    # Нижний конвейер: PPT → видео
    svg.text(w / 2, 255, "Этап 2: сборка видео", size=FS_SMALL, bold=True, fill="text_light")

    stages_bot = [
        (
            "Снимки страниц",
            "medium",
            [
                "slide-01.png",
                "slide-02.png",
                "...",
            ],
        ),
        (
            "Текст диктора",
            "light",
            [
                "LLM создаёт разговорный текст",
                "пояснение к странице",
                "связное повествование",
            ],
        ),
        (
            "Синтез TTS",
            "light",
            [
                "текст → речь",
                "speech-01.mp3",
                "speech-02.mp3",
            ],
        ),
        (
            "Синхронизация звука и изображения",
            "medium",
            [
                "сборка ffmpeg",
                "длительность кадра=длительность аудио",
                "эффекты переходов",
            ],
        ),
        (
            "Готовое видео",
            "dark",
            [
                "output.mp4",
                "5-15 минут",
                "два канала: изображение+звук",
            ],
        ),
    ]

    for i, (title, fill, details) in enumerate(stages_bot):
        x = sx + i * (sw + sgap)
        svg.rect(x, 268, sw, 130, fill=fill)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(x + sw / 2, 288, title, size=FS_SMALL, bold=True, fill=tc)
        svg.line(x + 8, 300, x + sw - 8, 300, color="dark")
        for j, line in enumerate(details):
            fc = "white" if fill in ("dark", "darker") else "text"
            svg.mono(x + 8, 316 + j * 20, line, size=10, fill=fc)
        if i < len(stages_bot) - 1:
            svg.arrow(x + sw + 2, 268 + 65, x + sw + sgap - 2, 268 + 65)

    # Снизу: ключевые критерии
    svg.line(30, 420, w - 30, 420, color="dark", dash=True)
    svg.text(w / 2, 440, "Критерии приёмки", size=FS_BODY, bold=True)

    criteria = [
        ("PPT", "10-20 страниц · основные результаты · ≥3 исходных иллюстраций"),
        ("Рендеринг", "текст не выходит · разумная сетка · графика по теме"),
        ("Видео", "5-15 минут · звук синхронизирован с видео · связный рассказ"),
    ]
    cx = 60
    for label, desc in criteria:
        _pill(svg, cx, 458, 60, 26, label, fill="dark", font_size=12, bold=True)
        svg.text(
            cx + 70,
            471,
            desc,
            size=FS_TINY,
            fill="text_light",
            anchor="start",
            max_width=185,
        )
        cx += 265

    svg.save(os.path.join(_output_dir, "fig5-6.svg"))


# ──────────────────────── fig5-7 ────────────────────────


def fig5_8() -> None:
    """Динамическая генерация формы (LLM→HTML→JSON→продолжение)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Динамическая форма: структурированное уточнение намерения",
        size=FS_TITLE,
        bold=True,
    )

    # Шаг 1: пользовательский запрос
    svg.rect(20, 60, 200, 60, fill="medium")
    svg.text(120, 82, "Запрос пользователя", size=FS_SMALL, bold=True)
    svg.text(120, 100, '"Хочу забронировать авиабилет в Пекин"', size=FS_TINY, fill="text_light")

    svg.arrow(220, 90, 260, 90)

    # Шаг 2: LLM анализирует запрос и создаёт форму
    svg.rect(260, 55, 260, 140, fill="white", stroke="border", dash=True)
    svg.text(390, 75, "LLM анализирует → создаёт код формы", size=FS_SMALL, bold=True)
    form_code = [
        '<form id="clarify">',
        ' <input type="text"',
        '  name="from" label="Город вылета"/>',
        ' <input type="date"',
        '  name="depart" label="Дата вылета"/>',
        ' <select name="type">',
        "  <option>В одну сторону</option>",
        "  <option>Туда и обратно</option>",
        " </select>",
        "</form>",
    ]
    svg.rect(270, 90, 240, len(form_code) * 13 + 10, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(form_code):
        svg.mono(276, 103 + j * 13, line, size=9)

    svg.arrow(520, 130, 560, 130)

    # Шаг 3: отображённая форма
    svg.rect(560, 55, 300, 200, fill="white", stroke="border")
    svg.text(710, 75, "Интерфейс готовой формы", size=FS_SMALL, bold=True)

    fields = [
        ("Город вылета", "Шанхай", 95),
        ("Дата вылета", "2025-08-15", 135),
        ("Тип поездки", "Туда-обратно ▾", 175),
        ("Дата возврата", "2025-08-22", 215),
    ]
    for label, value, fy in fields:
        svg.text(580, fy, label, size=FS_TINY, anchor="start", bold=True, max_width=70)
        svg.rect(660, fy - 12, 180, 24, fill="code_bg", stroke="dark", rx=3)
        svg.mono(668, fy, value, size=11)

    _pill(svg, 660, 238, 80, 26, "Отправить", fill="dark", font_size=FS_SMALL, bold=True)

    # Шаг 4: результат JSON
    svg.arrow(710, 268, 710, 300)
    svg.rect(560, 300, 300, 110, fill="white", stroke="border", dash=True)
    svg.text(710, 318, "Структурированный JSON", size=FS_SMALL, bold=True)
    json_lines = [
        '{"from": "Шанхай",',
        ' "depart": "2025-08-15",',
        ' "type": "Туда и обратно",',
        ' "return": "2025-08-22"}',
    ]
    svg.rect(570, 330, 280, len(json_lines) * 16 + 10, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(json_lines):
        svg.mono(578, 344 + j * 16, line, size=11)

    # Шаг 5: агент продолжает работу со структурированными данными
    svg.arrow(560, 390, 400, 440)

    svg.rect(100, 430, 500, 50, fill="medium")
    svg.text(350, 448, "Агент продолжает работу со всеми параметрами", size=FS_BODY, bold=True)
    svg.text(
        350,
        468,
        "search_flights(from='Шанхай', to='Пекин', depart='2025-08-15', ...)",
        size=FS_TINY,
        fill="text_light",
    )

    # Сравнение текста и формы
    svg.rect(20, 280, 250, 140, fill="light")
    svg.text(145, 300, "Сравнение: текст и форма", size=FS_SMALL, bold=True)
    comp = [
        "Текстовый диалог: 10 раундов",
        "  В1: Откуда? О: Шанхай",
        "  В2: Когда? О: 15 августа",
        "  В3: В одну сторону или туда и обратно? ...",
        "",
        "Динамическая форма: 1 отправка",
        "  Все данные собираются сразу",
        "  Зависимости обрабатываются сами",
    ]
    for j, line in enumerate(comp):
        svg.mono(30, 318 + j * 13, line, size=10)

    # Примечание внизу
    svg.text(
        w / 2,
        510,
        'Форму динамически создаёт LLM → при выборе "Туда и обратно" появляется дата возврата',
        size=FS_SMALL,
        fill="darker",
    )

    svg.save(os.path.join(_output_dir, "fig5-8.svg"))


# ──────────────────────── fig5-8 ────────────────────────


def fig5_9() -> None:
    """SQL-агент (режим артефактов — данные обходят LLM)"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "SQL-агент: режим артефактов и обычный режим", size=FS_TITLE, bold=True)

    # Сверху: обычный режим, данные проходят через LLM
    svg.rect(20, 55, w - 40, 200, fill="white", stroke="border", dash=True)
    svg.text(
        60,
        78,
        "Обычный режим: данные проходят через LLM (неэффективно)",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    _pill(svg, w - 110, 65, 80, 24, "✗ Неэффективно", fill="dark", font_size=12, bold=True)

    trad_steps = [
        ("Пользователь", "medium", '"Сколько людей\\nв каждом отделе?"'),
        ("LLM", "light", "создаёт\\nSQL"),
        ("DB", "medium", "выполняет\\nзапрос"),
        ("LLM", "light", "читает\\n5000 строк"),
        ("Пользователь", "medium", "текстовый\\nответ"),
    ]
    tsx = 60
    for i, (name, fill, desc) in enumerate(trad_steps):
        svg.rect(tsx, 100, 130, 60, fill=fill)
        svg.text(tsx + 65, 118, name, size=FS_SMALL, bold=True)
        for j, line in enumerate(desc.split("\\n")):
            svg.text(tsx + 65, 138 + j * 16, line, size=FS_TINY, fill="text_light")
        if i < len(trad_steps) - 1:
            svg.arrow(tsx + 130, 130, tsx + 150, 130)
        tsx += 155

    svg.rect(60, 175, w - 120, 30, fill="code_bg", stroke="dark", rx=3)
    svg.mono(
        70, 190, "Проблема: ошибки при копировании · много токенов · высокая задержка", size=12
    )

    # Разделитель
    svg.line(30, 265, w - 30, 265, color="dark", dash=True)

    # Снизу: режим артефактов, данные обходят LLM
    svg.rect(20, 275, w - 40, 280, fill="white", stroke="border", dash=True)
    svg.text(
        60,
        298,
        "Режим артефактов: данные идут прямо в интерфейс (эффективно)",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    _pill(svg, w - 110, 285, 80, 24, "✓ Эффективно", fill="medium", font_size=12, bold=True)

    # LLM создаёт код, а не данные
    svg.rect(40, 315, 250, 120, fill="light")
    svg.text(165, 335, "LLM создаёт только код", size=FS_SMALL, bold=True)
    sql_code = [
        "build_artifact(",
        '  type="sql",',
        '  code="SELECT dept,',
        "    COUNT(*) as cnt",
        "    FROM employees",
        '    GROUP BY dept")',
    ]
    svg.rect(50, 345, 230, len(sql_code) * 14 + 8, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(sql_code):
        svg.mono(58, 358 + j * 14, line, size=10)

    svg.arrow(290, 380, 340, 380)

    # Интерфейс выполняет код напрямую
    svg.rect(340, 315, 250, 120, fill="medium")
    svg.text(465, 335, "Интерфейс выполняет код", size=FS_SMALL, bold=True)
    svg.rect(350, 348, 230, 75, fill="code_bg", stroke="dark", rx=3)
    table = [
        "┌────────────┬──────┐",
        "│ dept       │ cnt  │",
        "├────────────┼──────┤",
        "│ Разработка │  42  │",
        "│ Маркетинг  │  28  │",
        "└────────────┴──────┘",
    ]
    for j, line in enumerate(table):
        svg.mono(358, 360 + j * 12, line, size=9)

    svg.arrow(590, 380, 640, 380)

    # Артефакт визуализации
    svg.rect(640, 315, 210, 120, fill="light")
    svg.text(745, 335, "Артефакт визуализации", size=FS_SMALL, bold=True)
    svg.text(745, 355, "Второй артефакт:", size=FS_TINY, fill="text_light")
    svg.rect(650, 365, 190, 60, fill="code_bg", stroke="dark", rx=3)
    svg.mono(658, 380, "build_artifact(", size=10)
    svg.mono(658, 394, '  type="chart",', size=10)
    svg.mono(658, 408, '  code="bar(data)")', size=10)

    # Схема потока данных
    svg.rect(180, 450, 520, 45, fill="dark")
    svg.text(
        440,
        465,
        "Данные: DB → интерфейс → визуализация (минуя LLM)",
        size=FS_BODY,
        fill="white",
        bold=True,
    )
    svg.text(
        440,
        483,
        "LLM создаёт только код и не участвует в передаче данных",
        size=FS_TINY,
        fill="white",
    )

    # Стрелка потока данных в обход LLM
    svg.arrow_curved(
        465,
        435,
        745,
        435,
        curve=25,
        label="Прямая передача результата SQL",
        dash=True,
        color="dark",
    )

    svg.save(os.path.join(_output_dir, "fig5-9.svg"))


# ──────────────────────── fig5-6 ────────────────────────


def fig5_7() -> None:
    "Эксперимент 5.10: конвейер интеллектуальной диагностики продукционных журналов"
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(
        w / 2, 30, "Эксперимент 5.10: диагностика продукционных журналов", size=FS_TITLE, bold=True
    )

    # Конвейер идёт слева направо, затем вниз
    # Строка 1: сбор → анализ
    svg.rect(20, 60, 250, 160, fill="white", stroke="border", dash=True)
    svg.text(145, 82, "① Сбор журналов", size=FS_BODY, bold=True)
    log_lines = [
        "trajectory_001.json:",
        '  {"role":"user","content":',
        '   "Отменить заказ #12345"}',
        '  {"role":"assistant",',
        '   "tool_call":"cancel_order"}',
        '  {"role":"tool","result":',
        '   "ERROR: нет страховки"}',
        "  → Агент не объяснил причину",
    ]
    svg.rect(30, 98, 230, len(log_lines) * 14 + 10, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(log_lines):
        svg.mono(38, 112 + j * 14, line, size=9)

    svg.arrow(270, 140, 310, 140)

    svg.rect(310, 60, 260, 160, fill="white", stroke="border", dash=True)
    svg.text(440, 82, "② Анализ с LLM", size=FS_BODY, bold=True)
    analysis = [
        "Вход: траектория + архитектурная документация + PRD",
        "",
        "Критерии анализа:",
        "  - соответствует ли процесс плану",
        "  - верны ли вызовы инструментов",
        "  - корректна ли обработка ошибок",
        "  - удобно ли пользователю",
        "",
        "→ поиск этапа и модуля сбоя",
    ]
    for j, line in enumerate(analysis):
        svg.mono(320, 100 + j * 14, line, size=10)

    svg.arrow(570, 140, 610, 140)

    svg.rect(610, 60, 250, 160, fill="white", stroke="border", dash=True)
    svg.text(735, 82, "③ Структурированный отчёт", size=FS_BODY, bold=True)
    report = [
        "Отчёт о проблеме:",
        "  Приоритет: P1 (риск оттока пользователей)",
        "  Модуль: cancellation_handler",
        "  Описание: после сбоя отмены",
        "    пользователю не объяснили причину и варианты",
        "  Совет: объяснить причину",
        "    и предложить страховку",
    ]
    svg.rect(620, 98, 230, len(report) * 14 + 10, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(report):
        svg.mono(628, 112 + j * 14, line, size=9)

    # Строка 2: создание регрессионного теста → создание задачи
    svg.arrow(w / 2, 220, w / 2, 260)

    svg.rect(60, 260, 370, 160, fill="white", stroke="border", dash=True)
    svg.text(245, 282, "④ Создание регрессионного теста", size=FS_BODY, bold=True)
    test_code = [
        "def test_cancel_no_insurance():",
        '  """Траектория #001, шаги 3-5"""',
        "  # Повтор: отмена билета экономкласса",
        "  resp = agent.run(",
        '    "Отменить заказ #12345")',
        "  # Проверка рендеринга: причина объяснена",
        '  assert "страховка" in resp.text',
        '  assert "альтернатива" in resp.text',
        "  # Проверка рендеринга: нет прямой ошибки",
        '  assert "ERROR" not in resp.text',
    ]
    svg.rect(70, 298, 350, len(test_code) * 14 + 10, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(test_code):
        svg.mono(78, 312 + j * 14, line, size=10)

    svg.arrow(430, 340, 470, 340)

    svg.rect(470, 260, 380, 160, fill="white", stroke="border", dash=True)
    svg.text(660, 282, "⑤ Автосоздание задачи GitHub", size=FS_BODY, bold=True)
    issue = [
        "gh issue create \\",
        '  --title "P1: После сбоя отмены',
        '    нет пояснения" \\',
        '  --body "**Проблема**: агент',
        "    после сбоя cancel_order",
        "    возвращает ошибку без...",
        "    **Траектория**: #001, шаги 3-5",
        '    **Тест**: test_cancel_..." \\',
        "  --assignee @backend-team",
    ]
    svg.rect(480, 298, 360, len(issue) * 14 + 10, fill="code_bg", stroke="dark", rx=3)
    for j, line in enumerate(issue):
        svg.mono(488, 312 + j * 14, line, size=10)

    # Снизу: сводка полного конвейера
    svg.rect(100, 445, w - 200, 44, fill="dark")
    svg.text(
        w / 2,
        460,
        "Сквозная автоматизация: журнал → анализ → отчёт → тест → задача",
        size=FS_BODY,
        fill="white",
        bold=True,
    )
    svg.text(
        w / 2,
        480,
        "GitHub через MCP · тестовый фреймворк сам воспроизводит и проверяет сценарий",
        size=FS_TINY,
        fill="white",
    )

    svg.text(
        w / 2,
        530,
        "Диагностика сокращается с нескольких часов до нескольких минут",
        size=FS_SMALL,
        fill="darker",
        bold=True,
    )

    svg.save(os.path.join(_output_dir, "fig5-7.svg"))


# ──────────────────────── fig5-9 ────────────────────────


def fig5_10() -> None:
    "Цикл самозагрузки агента (самовоспроизведение и эволюция)"
    w, h = 880, 555
    svg = SVG(w, h)
    svg.text(
        w / 2, 30, "Самозагрузка агента: от кода к самовоспроизведению", size=FS_TITLE, bold=True
    )

    # Шкала развития вверху
    stages = [
        ("Пыль→звезда", "Законы физики"),
        ("Звезда→планета", "Гравитационная аккреция"),
        ("Планета→жизнь", "Саморепликация DNA"),
        ("Жизнь→интеллектуальные агенты", "Самозагрузка кода"),
    ]
    sx = 60
    for i, (stage, mechanism) in enumerate(stages):
        fill = "dark" if i == 3 else ("medium" if i == 2 else "light")
        svg.rect(sx, 55, 180, 50, fill=fill)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(sx + 90, 72, stage, size=FS_SMALL, bold=True, fill=tc)
        svg.text(
            sx + 90, 92, mechanism, size=FS_TINY, fill="white" if fill == "dark" else "text_light"
        )
        if i < len(stages) - 1:
            svg.arrow(sx + 180, 80, sx + 195, 80)
        sx += 200

    # Ключевое различие
    svg.line(30, 120, w - 30, 120, color="dark", dash=True)

    svg.rect(30, 135, 400, 70, fill="light")
    svg.text(
        230,
        155,
        "Саморепликация DNA: случайные мутации + естественный отбор",
        size=FS_SMALL,
        bold=True,
    )
    svg.text(
        230,
        177,
        "Не понимает себя · не меняется целенаправленно · 3,7 млрд лет слепых проб и ошибок",
        size=FS_TINY,
        fill="text_light",
    )

    svg.rect(450, 135, 400, 70, fill="dark")
    svg.text(
        650,
        155,
        "Самозагрузка агента: понимание кода + целенаправленное проектирование",
        size=FS_SMALL,
        bold=True,
        fill="white",
    )
    svg.text(
        650,
        177,
        "Понимает устройство · создаёт целенаправленно · наследует лучшие практики",
        size=FS_TINY,
        fill="white",
    )

    # Основная схема цикла самозагрузки
    svg.rect(20, 225, 390, 295, fill="white", stroke="border", dash=True)
    svg.text(215, 248, "Исходный агент (собственный код)", size=FS_BODY, bold=True)

    svg.rect(30, 265, 175, 124, fill="light")
    svg.text(118, 285, "Системный промпт", size=FS_SMALL, bold=True)
    svg.text(40, 308, "Ты — специалист поддержки авиакомпании", size=12, anchor="start")
    svg.text(40, 326, "Правила отмены: ...", size=12, anchor="start")
    svg.text(40, 344, "Правила передачи: ...", size=12, anchor="start")
    svg.text(40, 362, "Инструмент: cancel_order", size=12, anchor="start")

    svg.rect(215, 265, 185, 124, fill="light")
    svg.text(308, 285, "Код каркаса агента", size=FS_SMALL, bold=True)
    svg.mono(225, 308, "loop:", size=12)
    svg.mono(225, 326, "  msg = llm(ctx)", size=12)
    svg.mono(225, 344, "  if tool_call:", size=12)
    svg.mono(225, 362, "    exec(tool)", size=12)

    svg.rect(30, 400, 370, 54, fill="code_bg", stroke="dark", rx=4)
    svg.text(
        215, 419, "Определения инструментов + интеграция MCP + формат сообщений", size=FS_SMALL
    )
    svg.text(215, 438, "Проверенная качественная реализация", size=FS_TINY, fill="text_light")

    # Стрелка самокопирования — подпись над заголовками пунктирных блоков
    svg.text(440, 215, "Копирование + правка", size=FS_TINY, fill="text_light", bold=True)
    svg.arrow(410, 375, 470, 375)

    # Новый агент
    svg.rect(470, 225, 390, 295, fill="white", stroke="border", dash=True)
    svg.text(665, 248, "Новый агент (после целевой правки)", size=FS_BODY, bold=True)

    svg.rect(480, 265, 180, 124, fill="medium")
    svg.text(570, 285, "Новый системный промпт", size=FS_SMALL, bold=True)
    svg.text(490, 308, "Ты — специалист поддержки интернет-магазина", size=12, anchor="start")
    svg.text(490, 326, "Правила возврата в интернет-магазине: ...", size=12, anchor="start")
    svg.text(490, 344, "Отслеживание доставки: ...", size=12, anchor="start")
    svg.text(490, 362, "Инструмент: refund_order", size=12, anchor="start")

    svg.rect(670, 265, 180, 124, fill="light")
    svg.text(760, 285, "Унаследованный каркас", size=FS_SMALL, bold=True)
    svg.mono(680, 308, "loop:", size=12)
    svg.mono(680, 326, "  msg = llm(ctx)", size=12)
    svg.mono(680, 344, "  if tool_call:", size=12)
    svg.mono(680, 362, "    exec(tool)", size=12)

    svg.rect(480, 400, 370, 54, fill="code_bg", stroke="dark", rx=4)
    svg.text(665, 419, "Новые инструменты + новая бизнес-логика", size=FS_SMALL)
    svg.text(
        665,
        438,
        "Каркас полностью унаследован → качество сохранено",
        size=FS_TINY,
        fill="text_light",
    )

    svg.save(os.path.join(_output_dir, "fig5-10.svg"))


# ──────────────────────── fig5-10 ────────────────────────


def fig5_11() -> None:
    """Эксперимент 5.14: конвейер создания нового агента метаагентом"""
    w, h = 880, 610
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Эксперимент 5.14: агент, создающий агентов", size=FS_TITLE, bold=True)

    # Вход: запрос пользователя
    svg.rect(30, 60, 280, 55, fill="medium")
    svg.text(170, 80, "Запрос пользователя", size=FS_SMALL, bold=True)
    svg.text(
        170,
        98,
        '"Создай агента службы возвратов интернет-магазина"',
        size=FS_TINY,
        fill="text_light",
    )

    svg.arrow(170, 115, 170, 145)

    # Метаагент: создатель
    svg.rect(20, 145, 840, 230, fill="white", stroke="border", dash=True)
    svg.text(440, 168, "Метаагент (агент программирования)", size=FS_BODY, bold=True)

    # Шаг 1: чтение примера
    svg.rect(35, 185, 190, 170, fill="light")
    svg.text(130, 205, "① Изучить пример кода", size=FS_SMALL, bold=True)
    svg.mono(45, 228, "read_file:", size=12)
    svg.mono(45, 248, "  agent.py", size=12)
    svg.mono(45, 268, "  tools/*.py", size=12)
    svg.mono(45, 288, "  system_prompt.md", size=12)
    svg.mono(45, 308, "  config.yaml", size=12)
    svg.text(45, 332, "→ понять архитектурный шаблон", size=12, anchor="start", fill="text_light")

    svg.arrow(225, 270, 248, 270)

    # Шаг 2: копирование каркаса
    svg.rect(248, 185, 190, 170, fill="light")
    svg.text(343, 205, "② Копировать каркас", size=FS_SMALL, bold=True)
    svg.mono(258, 228, "cp -r reference/", size=12)
    svg.mono(258, 248, "  → new_agent/", size=12)
    svg.text(258, 278, "Сохранить:", size=12, anchor="start", fill="text_light")
    svg.text(258, 298, "  Каркас цикла агента", size=12, anchor="start", fill="text_light")
    svg.text(
        258, 318, "  Формат сообщений / оптимизация KV", size=12, anchor="start", fill="text_light"
    )

    svg.arrow(438, 270, 461, 270)

    # Шаг 3: целевая правка
    svg.rect(461, 185, 190, 170, fill="medium")
    svg.text(556, 205, "③ Целевая правка", size=FS_SMALL, bold=True)
    svg.mono(471, 228, "edit_file:", size=12)
    svg.mono(471, 248, "  system_prompt.md", size=12)
    svg.text(471, 268, "  → правила возврата", size=12, anchor="start", fill="text_light")
    svg.mono(471, 290, "  tools/refund.py", size=12)
    svg.text(
        471, 310, "  → добавить инструмент возврата", size=12, anchor="start", fill="text_light"
    )
    svg.mono(471, 332, "  config.yaml", size=12)

    svg.arrow(651, 270, 674, 270)

    # Шаг 4: проверка
    svg.rect(674, 185, 175, 170, fill="light")
    svg.text(761, 205, "④ Проверка тестами", size=FS_SMALL, bold=True)
    svg.mono(684, 228, "bash:", size=12)
    svg.mono(684, 248, "  python agent.py", size=12)
    svg.text(684, 270, "  → запустить агента", size=12, anchor="start", fill="text_light")
    svg.text(
        684, 290, "  → отправить тестовое сообщение", size=12, anchor="start", fill="text_light"
    )
    svg.text(
        684, 310, "  → проверить вызовы инструментов", size=12, anchor="start", fill="text_light"
    )
    svg.text(684, 330, "  → проверить диалог", size=12, anchor="start", fill="text_light")

    # Выход: новый агент
    svg.arrow(w / 2, 375, w / 2, 410)

    svg.rect(115, 410, 700, 90, fill="white", stroke="border", dash=True)
    svg.text(465, 432, "Созданный агент", size=FS_BODY, bold=True)

    outputs = [
        ("system_prompt.md", "Правила возврата в интернет-магазине"),
        ("tools/refund.py", "Инструменты возврата / поиска"),
        ("agent.py", "Унаследованный каркас"),
        ("config.yaml", "Конфигурация модели / параметров"),
    ]
    ox = 135
    for fname, desc in outputs:
        svg.rect(ox, 448, 170, 42, fill="light")
        svg.mono(ox + 85, 462, fname, size=10, anchor="middle")
        svg.text(ox + 85, 480, desc, size=FS_TINY, fill="text_light")
        ox += 178

    # Сравнение внизу
    svg.line(30, 515, w - 30, 515, color="dark", dash=True)
    svg.rect(60, 530, 350, 54, fill="light")
    svg.text(235, 549, "Создание с нуля: без лучших практик", size=FS_SMALL, bold=True)
    svg.text(
        235,
        571,
        "Бессистемное управление контекстом · нестандартный дизайн инструментов · устаревшие API",
        size=FS_TINY,
        fill="text_light",
    )

    svg.rect(470, 530, 350, 54, fill="dark")
    svg.text(
        645, 549, "Правка примера: наследование практик", size=FS_SMALL, bold=True, fill="white"
    )
    svg.text(
        645,
        571,
        "Стандартный формат сообщений · стандартный дизайн инструментов · современные API",
        size=FS_TINY,
        fill="white",
    )

    svg.save(os.path.join(_output_dir, "fig5-11.svg"))


# ──────────────────────── запуск ────────────────────────


def main(output_dir: str) -> None:
    global _output_dir
    _output_dir = output_dir
    os.makedirs(_output_dir, exist_ok=True)
    figs = [
        fig5_1,
        fig5_2,
        fig5_3,
        fig5_4,
        fig5_5,
        fig5_6,
        fig5_7,
        fig5_8,
        fig5_9,
        fig5_10,
        fig5_11,
    ]
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nСоздано иллюстраций: {len(figs)}. Каталог: {_output_dir}/")


if __name__ == "__main__":
    main(parse_output_dir(_output_dir))
