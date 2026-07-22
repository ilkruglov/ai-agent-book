#!/usr/bin/env python3
"Создаёт все SVG-иллюстрации для главы 4 (Инструменты).\n\nРисунки (всего 12):\n  fig4-1:  Диаграмма последовательности протокола MCP (конкретное содержимое сообщений)\n  fig4-2:  Подготовка контекста субагента (4 стратегии с примерами)\n  fig4-3:  Событийная архитектура (реальные источники событий и данные)\n  fig4-4:  Асинхронная обработка событий (сравнение отмены, очереди и параллельной обработки во времени)\n  fig4-5:  Эксп. 4.4 — событийная архитектура AI-агента\n  fig4-6:  Противоречие синхронного обучения и асинхронного развёртывания\n  fig4-7:  Эксп. 4.5 — асинхронный агент с прерыванием\n  fig4-8:  Иерархия обнаружения инструментов (сервер→инструмент)\n  fig4-9:  Оптимизация KV-кэша (стабильность системного промпта)\n  fig4-10: Конвейер самоэволюции инструментов (несколько этапов)\n  fig4-11: Эксп. 4.7 — конвейер самоэволюции агента\n  fig4-12: Цикл обучения Voyager (учебный план + библиотека навыков)\n"

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


# ──────────────────────── fig4-1 ────────────────────────


def fig4_1() -> None:
    "Диаграмма последовательности протокола MCP с конкретным содержимым сообщений"
    w, h = 880, 620
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Последовательность взаимодействия по MCP", size=FS_TITLE, bold=True)

    cl_x, sv_x = 200, 680
    svg.box(cl_x - 80, 50, 160, 44, "Клиент MCP", fill="medium", bold=True)
    svg.box(sv_x - 80, 50, 160, 44, "Сервер MCP", fill="medium", bold=True)
    svg.line(cl_x, 94, cl_x, 600, color="dark", dash=True)
    svg.line(sv_x, 94, sv_x, 600, color="dark", dash=True)

    # 1 Запрос initialize
    y = 130
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "initialize", size=FS_BODY, bold=True)
    svg.code_block(
        cl_x + 30,
        y + 6,
        350,
        [
            '{"method": "initialize",',
            ' "capabilities": {"tools": true}}',
        ],
        font_size=FS_TINY,
        line_h=18,
    )

    # 2 Ответ initialize
    y = 215
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "ответ initialize", size=FS_BODY, bold=True)
    svg.code_block(
        cl_x + 30,
        y + 6,
        350,
        [
            '{"serverInfo": {"name": "weather-server"},',
            ' "capabilities": {"tools": {"listChanged":true}}}',
        ],
        font_size=FS_TINY,
        line_h=18,
    )

    # 3 tools/list
    y = 295
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/list", size=FS_BODY, bold=True)
    svg.code_block(
        cl_x + 30,
        y + 6,
        350,
        [
            '{"method": "tools/list"}',
        ],
        font_size=FS_TINY,
        line_h=18,
    )

    # 4 Ответ tools/list
    y = 365
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "ответ tools/list", size=FS_BODY, bold=True)
    svg.code_block(
        cl_x + 10,
        y + 6,
        400,
        [
            '{"tools": [{"name": "get_weather",',
            '  "inputSchema": {"city": "string"}}]}',
        ],
        font_size=FS_TINY,
        line_h=18,
    )

    # 5 tools/call
    y = 450
    svg.arrow(cl_x + 4, y, sv_x - 4, y)
    svg.text((cl_x + sv_x) / 2, y - 14, "tools/call", size=FS_BODY, bold=True)
    svg.code_block(
        cl_x + 30,
        y + 6,
        350,
        [
            '{"method": "tools/call",',
            ' "params": {"name": "get_weather",',
            '  "arguments": {"city": "Пекин"}}}',
        ],
        font_size=FS_TINY,
        line_h=18,
    )

    # 6 Результат tools/call
    y = 550
    svg.arrow(sv_x - 4, y, cl_x + 4, y, dash=True)
    svg.text((cl_x + sv_x) / 2, y - 14, "результат tools/call", size=FS_BODY, bold=True)
    svg.code_block(
        cl_x + 30,
        y + 6,
        350,
        [
            '{"content": [{"type": "text",',
            '  "text": "Пекин: 22°C, ясно"}]}',
        ],
        font_size=FS_TINY,
        line_h=18,
    )

    # Названия этапов слева
    svg.text(50, 165, "① Согласование", size=FS_SMALL, bold=True, fill="text_light")
    svg.text(50, 310, "② Обнаружение", size=FS_SMALL, bold=True, fill="text_light")
    svg.text(50, 500, "③ Вызов", size=FS_SMALL, bold=True, fill="text_light")

    svg.save(os.path.join(_output_dir, "fig4-1.svg"))


# ──────────────────────── fig4-2 ────────────────────────


def fig4_2() -> None:
    """Подготовка контекста субагента: сравнение четырёх стратегий"""
    w, h = 880, 530
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Стратегии передачи контекста субагенту", size=FS_TITLE, bold=True)

    strategies = [
        (
            "Минимальный контекст",
            "dark",
            '"Запросить статус заказа 12345"',
            "Без контекста → конфиденциальность защищена",
        ),
        (
            "Ручной отбор",
            "medium",
            '"Регион пользователя: США\\nКратко: запрос на возврат"',
            "Явный выбор → контроль",
        ),
        (
            "Автосокращение",
            "light",
            '"Данные пользователя + 3 последних хода\\n+ релевантные результаты инструментов"',
            "По правилам → баланс",
        ),
        (
            "Контекст от LLM",
            "code_bg",
            '"LLM анализирует траекторию\\n→ структурированный объект контекста"',
            "Самый интеллектуальный → +1 вызов",
        ),
    ]

    col_w = 190
    gap = 18
    start_x = (w - 4 * col_w - 3 * gap) / 2

    # Основной агент сверху
    svg.box(w / 2 - 100, 55, 200, 44, "Основной агент", fill="medium", bold=True)
    svg.text(
        w / 2, 118, "Как подготовить контекст для субагента?", size=FS_SMALL, fill="text_light"
    )

    for i, (title, fill, example, note) in enumerate(strategies):
        x = start_x + i * (col_w + gap)
        top_y = 145

        svg.arrow(w / 2, 99, x + col_w / 2, top_y - 2)

        svg.rect(x, top_y, col_w, 36, fill=fill)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(x + col_w / 2, top_y + 18, title, size=FS_SMALL, bold=True, fill=tc)

        svg.rect(x, top_y + 46, col_w, 80, fill="code_bg", stroke="dark", rx=4)
        for j, line in enumerate(example.split("\\n")):
            svg.mono(x + 8, top_y + 70 + j * 20, line, size=FS_TINY)

        svg.text(x + col_w / 2, top_y + 150, note, size=FS_TINY, fill="text_light")

        svg.box(x + 15, top_y + 175, col_w - 30, 36, "Субагент", fill="light", font_size=FS_SMALL)

    # Внизу: рекомендации по выбору
    svg.line(30, 395, w - 30, 395, color="dark", dash=True)
    svg.text(w / 2, 418, "Рекомендации", size=FS_BODY, bold=True)

    guides = [
        ("Простые частые вызовы", "Погода, калькулятор", "→ Минимум"),
        ("Средняя сложность", "Данные, обработка файлов", "→ Автосокращение"),
        ("Сложные задачи", "Отчёты, поддержка", "→ Контекст от LLM"),
    ]
    gx = 80
    for label, example, rec in guides:
        svg.rect(gx, 438, 230, 70, fill="light")
        svg.text(gx + 115, 458, label, size=FS_SMALL, bold=True)
        svg.text(gx + 115, 478, example, size=FS_TINY, fill="text_light")
        svg.text(gx + 115, 498, rec, size=FS_SMALL, bold=True, fill="darker")
        gx += 260

    svg.save(os.path.join(_output_dir, "fig4-2.svg"))


# ──────────────────────── fig4-3 ────────────────────────


def fig4_3() -> None:
    "Событийная архитектура с конкретными источниками и данными событий"
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Событийная архитектура асинхронного AI-агента", size=FS_TITLE, bold=True)

    # Слева: источники событий
    sources = [
        ("Почта", "on_email_reply", '{"from":"alice@...",\n "subject":"Re: совещание"}'),
        ("Таймер", "on_timer_expire", '{"task_id":"daily_report",\n "scheduled":"09:00"}'),
        ("Webhook", "on_webhook", '{"repo":"agent-lib",\n "event":"pr_merged"}'),
        ("Пользователь", "on_user_message", '{"text":"Проверь\n погоду на завтра"}'),
    ]

    src_x, src_w = 20, 155
    svg.text(src_x + src_w / 2, 65, "Источники событий", size=FS_BODY, bold=True)
    for i, (name, event_type, payload) in enumerate(sources):
        y = 85 + i * 110
        svg.box(src_x, y, src_w, 40, name, fill="medium", bold=True, font_size=FS_SMALL)
        svg.mono(src_x + 5, y + 56, event_type, size=FS_TINY)
        for j, pl in enumerate(payload.split("\n")):
            svg.mono(src_x + 5, y + 74 + j * 16, pl, size=11)

    # В центре: очередь событий
    q_x, q_w = 215, 190
    svg.text(q_x + q_w / 2, 65, "Очередь событий", size=FS_BODY, bold=True)
    svg.rect(q_x, 85, q_w, 390, fill="white", stroke="border", dash=True)

    queue_events = [
        ("user.input", "Приоритет: обычный", "light"),
        ("email.reply", "Приоритет: обычный", "light"),
        ("user.interrupt", "Приоритет: срочный!", "dark"),
        ("timer.trigger", "Приоритет: обычный", "light"),
    ]
    for i, (evt, pri, fill) in enumerate(queue_events):
        ey = 105 + i * 85
        svg.rect(q_x + 10, ey, q_w - 20, 60, fill=fill, rx=4)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(q_x + q_w / 2, ey + 22, evt, size=FS_SMALL, bold=True, fill=tc)
        svg.text(
            q_x + q_w / 2,
            ey + 44,
            pri,
            size=FS_TINY,
            fill="white" if fill == "dark" else "text_light",
        )

    # Стрелки от источников к очереди
    for i in range(4):
        sy = 105 + i * 110
        svg.arrow(src_x + src_w + 2, sy, q_x - 2, 120 + i * 85)

    # Справа: обработка агентом
    ag_x = 450
    svg.text(ag_x + 200, 65, "Обработка агентом", size=FS_BODY, bold=True)

    svg.arrow(q_x + q_w + 2, 280, ag_x - 2, 280, label="Получить событие")

    steps = [
        ("Маршрутизатор событий", "LLM оценивает срочность", "medium"),
        ("Добавление в траекторию", "Структурированный формат события", "light"),
        ("Инференс LLM", "Наблюдение→мысль→действие", "light"),
        ("Инструменты выполнения инструмента", "Асинхр./синхр. запуск", "light"),
        ("Обработка результата", "Уведомление/ответ/запись", "medium"),
    ]

    step_w, step_h = 360, 50
    for i, (title, desc, fill) in enumerate(steps):
        sy = 110 + i * 80
        svg.rect(ag_x, sy, step_w, step_h, fill=fill)
        svg.text(
            ag_x + 10,
            sy + step_h / 2,
            title,
            size=FS_SMALL,
            bold=True,
            anchor="start",
            max_width=190,
        )
        svg.text(
            ag_x + step_w - 10,
            sy + step_h / 2,
            desc,
            size=FS_TINY,
            fill="text_light",
            anchor="end",
            max_width=145,
        )
        if i < len(steps) - 1:
            svg.arrow(ag_x + step_w / 2, sy + step_h + 2, ag_x + step_w / 2, sy + 78)

    # Обратная связь
    svg.arrow_curved(
        ag_x + step_w, 450, ag_x + step_w, 130, curve=-50, label="Цикл", dash=True, color="dark"
    )

    svg.save(os.path.join(_output_dir, "fig4-3.svg"))


# ──────────────────────── fig4-4 ────────────────────────


def fig4_4() -> None:
    "Сравнение трёх стратегий асинхронной обработки событий во времени"
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Три стратегии обработки событий", size=FS_TITLE, bold=True)

    lane_x = 130
    lane_w = 720
    tl_x0 = lane_x + 10
    tl_w = lane_w - 20

    def time_bar(
        y: float,
        x_start_pct: float,
        x_end_pct: float,
        fill: str,
        label: str,
        h_bar: float = 28,
    ) -> None:
        xs = tl_x0 + tl_w * x_start_pct
        xe = tl_x0 + tl_w * x_end_pct
        svg.rect(xs, y, xe - xs, h_bar, fill=fill, rx=4)
        svg.text(
            (xs + xe) / 2,
            y + h_bar / 2,
            label,
            size=FS_TINY,
            fill="white" if fill in ("dark", "darker") else "text",
        )

    # Заголовок временной шкалы
    svg.text(tl_x0 + tl_w * 0.25, 55, "t₁", size=FS_SMALL, fill="text_light")
    svg.text(tl_x0 + tl_w * 0.50, 55, "t₂", size=FS_SMALL, fill="text_light")
    svg.text(tl_x0 + tl_w * 0.75, 55, "t₃", size=FS_SMALL, fill="text_light")

    # ── Полоса 1: отмена ──
    y1 = 80
    svg.rect(lane_x, y1, lane_w, 140, fill="white", stroke="border", dash=True)
    svg.text(lane_x / 2, y1 + 70, "С отменой", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y1 + 95, "(срочные)", size=FS_SMALL, fill="text_light")

    time_bar(y1 + 15, 0.0, 0.40, "medium", "Идёт инференс LLM...")
    svg.line(tl_x0 + tl_w * 0.40, y1 + 10, tl_x0 + tl_w * 0.40, y1 + 130, color="border", dash=True)
    svg.text(tl_x0 + tl_w * 0.40, y1 + 10, '⚡ user.interrupt: "Стоп!"', size=FS_TINY, bold=True)
    time_bar(y1 + 15, 0.40, 0.45, "dark", "×", h_bar=28)

    time_bar(y1 + 55, 0.0, 0.35, "light", "Выполняется инструмент...")
    time_bar(y1 + 55, 0.40, 0.45, "dark", "×", h_bar=28)

    time_bar(y1 + 95, 0.47, 1.0, "medium", "Новый инференс LLM (прерывание + очистка очереди)")

    # ── Полоса 2: очередь ──
    y2 = 240
    svg.rect(lane_x, y2, lane_w, 140, fill="white", stroke="border", dash=True)
    svg.text(lane_x / 2, y2 + 70, "С очередью", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y2 + 95, "(обычные)", size=FS_SMALL, fill="text_light")

    time_bar(y2 + 15, 0.0, 0.15, "medium", "LLM", h_bar=24)
    time_bar(y2 + 15, 0.18, 0.60, "light", "Инструменты выполнения инструмента (search_web)")
    time_bar(y2 + 15, 0.63, 0.90, "medium", "LLM обобщает")

    svg.line(tl_x0 + tl_w * 0.35, y2 + 46, tl_x0 + tl_w * 0.35, y2 + 130, color="dark", dash=True)
    svg.text(
        tl_x0 + tl_w * 0.35,
        y2 + 46,
        'user: "Только за последний месяц"',
        size=FS_TINY,
        fill="text_light",
    )

    _pill(
        svg,
        tl_x0 + tl_w * 0.30,
        y2 + 65,
        150,
        24,
        "Ожидание в очереди",
        fill="light",
        font_size=FS_TINY,
    )

    time_bar(y2 + 100, 0.63, 0.68, "dark", "", h_bar=20)
    svg.text(
        tl_x0 + tl_w * 0.72,
        y2 + 110,
        "Пакетное добавление: tool.result + уточнение пользователя",
        size=FS_TINY,
        fill="text_light",
    )

    # ── Полоса 3: параллельная обработка ──
    y3 = 400
    svg.rect(lane_x, y3, lane_w, 140, fill="white", stroke="border", dash=True)
    svg.text(lane_x / 2, y3 + 70, "Параллельно", size=FS_BODY, bold=True)
    svg.text(lane_x / 2, y3 + 95, "(независимые)", size=FS_SMALL, fill="text_light")

    time_bar(y3 + 15, 0.0, 0.80, "light", "Основная задача: анализ данных (долгая)")

    svg.line(tl_x0 + tl_w * 0.30, y3 + 50, tl_x0 + tl_w * 0.30, y3 + 130, color="dark", dash=True)
    svg.text(
        tl_x0 + tl_w * 0.30,
        y3 + 50,
        'user: "Какая сегодня погода?"',
        size=FS_TINY,
        fill="text_light",
    )

    time_bar(y3 + 70, 0.32, 0.50, "medium", "Параллельный LLM", h_bar=24)
    time_bar(y3 + 70, 0.52, 0.62, "dark", "Погода", h_bar=24)

    svg.text(
        tl_x0 + tl_w * 0.64,
        y3 + 82,
        "→ Сразу ответить",
        size=FS_TINY,
        fill="text_light",
        anchor="start",
        max_width=tl_w * 0.30,
    )
    svg.text(
        tl_x0 + tl_w * 0.50,
        y3 + 115,
        "Метка: [параллельно основной задаче]",
        size=FS_TINY,
        fill="text_light",
    )

    svg.save(os.path.join(_output_dir, "fig4-4.svg"))


# ──────────────────────── fig4-5 ────────────────────────


def fig4_5() -> None:
    """Эксперимент 4.4: событийная архитектура AI-агента"""
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(
        w / 2, 30, "Эксперимент 4.4: событийная архитектура AI-агента", size=FS_TITLE, bold=True
    )

    # Источники событий слева
    src_data = [
        ("on_user_message", "Web/приложение"),
        ("on_email_reply", "Почта"),
        ("on_github_pr_update", "GitHub"),
        ("on_timer_expire", "Таймер"),
        ("on_webhook_received", "Webhook"),
        ("on_resource_alert", "Системные оповещения"),
    ]
    svg.text(85, 65, "Внешние источники событий", size=FS_BODY, bold=True)
    for i, (evt, src) in enumerate(src_data):
        y = 82 + i * 58
        svg.rect(10, y, 150, 44, fill="light")
        svg.text(85, y + 16, src, size=FS_SMALL, bold=True)
        svg.mono(15, y + 36, evt, size=11)

    # Сервер FastAPI в центре
    svg.rect(200, 80, 200, 390, fill="white", stroke="border", dash=True)
    svg.text(300, 100, "Сервер FastAPI", size=FS_BODY, bold=True)

    svg.rect(215, 120, 170, 50, fill="medium")
    svg.text(300, 137, "HTTP-эндпоинт", size=FS_SMALL, bold=True)
    svg.text(300, 157, "POST /events/{type}", size=FS_TINY, fill="text_light")

    svg.rect(215, 190, 170, 50, fill="light")
    svg.text(300, 207, "Маршрутизатор событий", size=FS_SMALL, bold=True)
    svg.text(300, 227, "LLM оценивает срочность", size=FS_TINY, fill="text_light")

    svg.rect(215, 260, 170, 50, fill="light")
    svg.text(300, 277, "Очередь событий", size=FS_SMALL, bold=True)
    svg.text(300, 297, "Сортировка по приоритету", size=FS_TINY, fill="text_light")

    svg.rect(215, 330, 170, 50, fill="light")
    svg.text(300, 347, "Цикл агента", size=FS_SMALL, bold=True)
    svg.text(300, 367, "Получить→решить→выполнить", size=FS_TINY, fill="text_light")

    svg.rect(215, 400, 170, 50, fill="medium")
    svg.text(300, 417, "Управление сеансами", size=FS_SMALL, bold=True)
    svg.text(300, 437, "Контекст нескольких потоков", size=FS_TINY, fill="text_light")

    for i in range(4):
        svg.arrow(300, 170 + i * 70, 300, 190 + i * 70)

    for i in range(6):
        svg.arrow(160, 104 + i * 58, 213, 145)

    # Серверы инструментов MCP справа
    svg.text(610, 65, "Серверы инструментов MCP", size=FS_BODY, bold=True)

    tools = [
        ("Инструменты восприятия", "search_web, read_file\nread_webpage, parse_image"),
        ("Инструменты выполнения", "code_interpreter\nvirtual_terminal, write_file"),
        ("Инструменты совместной работы", "browser_use\nrequest_human_approval"),
        ("Инструменты уведомлений", "send_email, send_slack\nsend_im_notification"),
    ]
    for i, (name, desc) in enumerate(tools):
        y = 82 + i * 100
        svg.rect(460, y, 250, 80, fill="light")
        svg.text(585, y + 22, name, size=FS_SMALL, bold=True)
        for j, line in enumerate(desc.split("\n")):
            svg.mono(470, y + 48 + j * 18, line, size=12)

    svg.arrow(400, 355, 458, 180)
    svg.arrow(458, 260, 400, 355)

    # Постоянное хранилище
    svg.rect(740, 82, 130, 380, fill="code_bg", stroke="dark", rx=4)
    svg.text(805, 115, "Хранилище", size=FS_SMALL, bold=True)
    items = [
        "История диалогов",
        "Журнал событий",
        "Задачи по расписанию",
        "Состояние инструментов",
        "Аудиторский журнал",
    ]
    for i, item in enumerate(items):
        svg.text(805, 160 + i * 55, item, size=FS_SMALL)

    svg.save(os.path.join(_output_dir, "fig4-5.svg"))


# ──────────────────────── fig4-6 ────────────────────────


def fig4_6() -> None:
    "Противоречие синхронного обучения и асинхронного развёртывания"
    w, h = 880, 570
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Парадигма синхронного обучения против реалий асинхронного развёртывания",
        size=FS_TITLE,
        bold=True,
    )

    # Вверху: модель обучения
    svg.rect(20, 55, w - 40, 195, fill="white", stroke="border", dash=True)
    svg.text(
        60,
        78,
        "Обучение: строгая синхронная последовательность",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    _pill(svg, w - 200, 64, 160, 28, "Ограничение API", fill="dark", font_size=FS_SMALL)

    steps_train = [
        ("Наблюдение", "medium", "Пользователь: погода в Пекине"),
        ("Размышление", "light", "Нужно вызвать инструмент погоды"),
        ("Действие", "medium", "get_weather(Beijing)"),
        ("Наблюдение", "light", "22°C, ясно"),
    ]
    bw, bh, gap = 180, 55, 22
    sx = (w - (4 * bw + 3 * gap)) / 2
    for i, (phase, fill, content) in enumerate(steps_train):
        x = sx + i * (bw + gap)
        svg.rect(x, 100, bw, bh, fill=fill)
        svg.text(x + bw / 2, 120, phase, size=FS_SMALL, bold=True)
        svg.text(x + bw / 2, 142, content, size=FS_TINY, fill="text_light")
        if i < 3:
            svg.arrow(x + bw + 2, 128, x + bw + gap - 2, 128)

    svg.rect(sx, 170, 4 * bw + 3 * gap, 30, fill="code_bg", stroke="dark", rx=4)
    svg.mono(
        sx + 10,
        185,
        "tool_call → следующей записью должен быть tool_result, иначе ошибка API",
        size=FS_TINY,
    )

    # Разделитель
    svg.line(20, 262, w - 20, 262, color="dark", dash=True)
    svg.text(w / 2, 280, "Противоречие", size=FS_BODY, bold=True, fill="darker")

    # Внизу: асинхронная среда
    svg.rect(20, 295, w - 40, 210, fill="white", stroke="border", dash=True)
    svg.text(
        60,
        318,
        "Развёртывание: чередование асинхронных событий",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )
    _pill(svg, w - 200, 304, 160, 28, "Конфликт формата!", fill="dark", font_size=FS_SMALL)

    # Асинхронная временная шкала
    items = [
        ("Ассистент", "medium", "tool_call:\nget_weather(Beijing)", 0.0, 0.20),
        ("Ожидание...", "code_bg", "Инструмент работает ~5 с", 0.22, 0.50),
        ("Прерывание пользователем", "dark", '"Не надо,\nпроверь Шанхай"', 0.40, 0.55),
        ("???", "code_bg", "Когда придёт tool_result?\nКак сохранить формат?", 0.57, 0.78),
        (
            "Заполнитель",
            "light",
            "[инструмент ещё работает,\nсначала обработать прерывание]",
            0.80,
            1.0,
        ),
    ]

    tl_x0, tl_w = 50, w - 100
    for role, fill, txt, t0, t1 in items:
        x0 = tl_x0 + tl_w * t0
        x1 = tl_x0 + tl_w * t1
        bar_y = 395 if role == "Прерывание пользователем" else 340
        svg.rect(x0, bar_y, x1 - x0, 50, fill=fill, rx=4)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text((x0 + x1) / 2, bar_y + 15, role, size=FS_TINY, bold=True, fill=tc)
        for j, tl in enumerate(txt.split("\n")):
            svg.text((x0 + x1) / 2, bar_y + 32 + j * 14, tl, size=11, fill=tc)

    svg.rect(50, 455, w - 100, 40, fill="code_bg", stroke="dark", rx=4)
    svg.mono(
        60,
        475,
        "Решение: заполнитель восстанавливает формат + несрочные события ставятся в очередь + прерывание только для действительно срочных событий",
        size=FS_TINY,
    )

    # Главный вывод
    svg.rect(140, 510, w - 280, 40, fill="dark")
    svg.text(
        w / 2,
        530,
        "Фундаментальное решение: модели следующего поколения необходимо обучать с подкреплением (RL) в асинхронной среде",
        size=FS_SMALL,
        fill="white",
        bold=True,
    )

    svg.save(os.path.join(_output_dir, "fig4-6.svg"))


# ──────────────────────── fig4-7 ────────────────────────


def fig4_7() -> None:
    """Эксперимент 4.5: асинхронный AI-агент с прерыванием"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Эксперимент 4.5: прерывание и возобновление асинхронного AI-агента",
        size=FS_TITLE,
        bold=True,
    )

    # Временная шкала
    tl_x0, tl_w = 120, 740

    # Полосы
    lanes = [
        ("Агент", 80),
        ("Инструмент A", 180),
        ("Инструмент B", 260),
        ("Инструмент C", 340),
        ("Траектория", 420),
    ]
    for name, y in lanes:
        svg.text(55, y, name, size=FS_SMALL, bold=True)
        svg.line(tl_x0, y, tl_x0 + tl_w, y, color="dark", dash=True)

    def tbar(
        y: float,
        t0: float,
        t1: float,
        fill: str,
        label: str,
        h_bar: float = 22,
    ) -> None:
        xs = tl_x0 + tl_w * t0
        xe = tl_x0 + tl_w * t1
        svg.rect(xs, y - h_bar / 2, xe - xs, h_bar, fill=fill, rx=3)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text((xs + xe) / 2, y, label, size=11, fill=tc)

    # Этап 1: агент запускает 3 инструмента
    tbar(80, 0.0, 0.12, "medium", "LLM: запуск 3 инструментов")

    # Инструменты выполняются
    tbar(180, 0.13, 0.45, "light", "Скрипт A: 3%/с → готово за 33 с")
    tbar(260, 0.13, 0.70, "light", "Скрипт B: 2%/с → 50 с...")
    tbar(340, 0.13, 0.90, "code_bg", "Скрипт C: 1%/с → 100 с...")

    # Событие: инструмент A завершён
    t_done = 0.45
    svg.line(tl_x0 + tl_w * t_done, 70, tl_x0 + tl_w * t_done, 450, color="border", dash=True)
    svg.text(tl_x0 + tl_w * t_done, 62, "A завершён", size=FS_TINY, bold=True)

    # Агент проверяет остальные инструменты
    tbar(80, 0.46, 0.58, "medium", "Проверка прогресса B, C")
    tbar(420, 0.46, 0.58, "light", "B≈66% C≈33%")

    # Отмена C (< 50%)
    t_cancel = 0.60
    svg.line(tl_x0 + tl_w * t_cancel, 70, tl_x0 + tl_w * t_cancel, 450, color="dark", dash=True)
    svg.text(tl_x0 + tl_w * t_cancel, 62, "Отмена C", size=FS_TINY, bold=True, fill="darker")

    tbar(340, 0.60, 0.65, "dark", "×")

    # B завершён
    t_b_done = 0.70
    svg.line(tl_x0 + tl_w * t_b_done, 70, tl_x0 + tl_w * t_b_done, 450, color="border", dash=True)
    svg.text(tl_x0 + tl_w * t_b_done, 62, "B завершён", size=FS_TINY, bold=True)

    # Агент формирует отчёт
    tbar(80, 0.72, 0.95, "medium", "LLM: отчёт по результатам A+B")
    tbar(420, 0.72, 0.95, "light", "Результат A + результат B + отмена C")

    # Пояснения
    svg.rect(tl_x0, 460, tl_w, 40, fill="code_bg", stroke="dark", rx=4)
    svg.mono(
        tl_x0 + 10,
        480,
        "Важно: вставка заполнителя + события асинхронного завершения + API cancel_tool(task_id)",
        size=FS_TINY,
    )

    svg.save(os.path.join(_output_dir, "fig4-7.svg"))


# ──────────────────────── fig4-8 ────────────────────────


def fig4_8() -> None:
    "Иерархия обнаружения инструментов (сопоставление сервер→инструмент)"
    w, h = 880, 540
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Иерархический подбор инструментов", size=FS_TITLE, bold=True)

    # Запрос сверху
    svg.rect(250, 55, 380, 44, fill="medium")
    svg.text(
        440, 77, 'AI-агент: "Статистика участников репозитория GitHub"', size=FS_SMALL, bold=True
    )

    svg.arrow(440, 99, 440, 130)

    # discover_tools
    svg.rect(300, 132, 280, 44, fill="dark")
    svg.text(
        440,
        154,
        "discover_tools(запрос на естественном языке)",
        size=FS_SMALL,
        fill="white",
        bold=True,
    )

    svg.arrow(440, 176, 440, 210)

    # Уровень 1: подбор сервера
    svg.rect(20, 210, w - 40, 110, fill="white", stroke="border", dash=True)
    svg.text(
        55,
        233,
        "Уровень 1: выбор сервера (семантическое сходство)",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )

    servers = [
        ("GitHub", 0.92, "dark"),
        ("Погода", 0.15, "light"),
        ("Финансы", 0.23, "light"),
        ("ArXiv", 0.18, "light"),
        ("Файловая система", 0.31, "light"),
    ]
    sx = 50
    for name, score, fill in servers:
        svg.rect(sx, 255, 145, 50, fill=fill)
        tc = "white" if fill in ("dark", "darker") else "text"
        svg.text(sx + 72, 272, name, size=FS_SMALL, bold=True, fill=tc)
        svg.text(
            sx + 72,
            292,
            f"Сходство: {score:.2f}",
            size=FS_TINY,
            fill="white" if fill == "dark" else "text_light",
        )
        sx += 165

    # Стрелка к уровню 2
    svg.arrow(123, 305, 123, 345)
    svg.text(175, 330, "Сервер Top-1", size=FS_SMALL, fill="text_light")

    # Уровень 2: подбор инструмента на сервере
    svg.rect(20, 345, w - 40, 160, fill="white", stroke="border", dash=True)
    svg.text(
        55,
        368,
        "Уровень 2: выбор среди 26 инструментов сервера GitHub",
        size=FS_BODY,
        bold=True,
        anchor="start",
    )

    tools = [
        ("search_repositories", 0.41, "Поиск репозиториев"),
        ("list_contributors", 0.89, "Список участников"),
        ("get_repo_stats", 0.85, "Статистика репозитория"),
        ("create_issue", 0.12, "Создать Issue"),
        ("get_commit_history", 0.67, "История коммитов"),
    ]
    tx = 30
    for name, score, desc in tools:
        is_top = score > 0.80
        fill = "dark" if is_top else "light"
        svg.rect(tx, 388, 155, 55, fill=fill)
        tc = "white" if is_top else "text"
        svg.mono(tx + 5, 406, name, size=11, fill=tc)
        svg.text(
            tx + 78, 428, f"{score:.2f} | {desc}", size=11, fill="white" if is_top else "text_light"
        )
        tx += 170

    # Внизу: результат
    svg.rect(180, 468, 520, 30, fill="code_bg", stroke="dark", rx=4)
    svg.mono(190, 483, "Top-3: list_contributors, get_repo_stats, get_commit_history", size=12)

    svg.save(os.path.join(_output_dir, "fig4-8.svg"))


# ──────────────────────── fig4-9 ────────────────────────


def fig4_9() -> None:
    """Оптимизация KV-кэша за счёт стабильности системного промпта"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Оптимизация KV-кэша при динамической загрузке инструментов",
        size=FS_TITLE,
        bold=True,
    )

    # Слева: базовый подход
    left_x = 30
    svg.text(220, 65, "Базовая схема: кэш сбрасывается", size=FS_BODY, bold=True)

    blocks_naive = [
        (
            "Системный промпт",
            120,
            "medium",
            "Вы — AI-помощник...\n+ схемы всех инструментов",
            "~50K токенов",
        ),
        ("Сообщение пользователя", 100, "light", "Цена акций NVDA", ""),
        ("Ассистент", 80, "light", "tool_call: ...", ""),
    ]
    ny = 85
    for label, bh, fill, content, note in blocks_naive:
        svg.rect(left_x, ny, 380, bh, fill=fill, rx=4)
        svg.text(left_x + 190, ny + 22, label, size=FS_SMALL, bold=True)
        for j, line in enumerate(content.split("\n")):
            svg.text(left_x + 190, ny + 44 + j * 20, line, size=FS_TINY, fill="text_light")
        if note:
            svg.text(left_x + 360, ny + 22, note, size=FS_TINY, fill="darker", anchor="end")
        ny += bh + 8

    svg.rect(left_x, ny + 5, 380, 40, fill="dark")
    svg.text(
        left_x + 190,
        ny + 25,
        "Новый инструмент → весь кэш сбрасывается!",
        size=FS_SMALL,
        fill="white",
        bold=True,
    )

    # Справа: оптимизированный подход
    right_x = 460
    svg.text(660, 65, "Оптимизация: стабильный кэш", size=FS_BODY, bold=True)

    blocks_opt = [
        (
            "Системный промпт (фикс.)",
            75,
            "medium",
            "Вы — AI-помощник...\nРоль + правила + базовые инструменты",
            "~2K токенов | KV-кэш",
        ),
        (
            "Строка состояния агента (облегчённая)",
            45,
            "code_bg",
            "Доступные инструменты: web_search, get_weather...",
            "~200 токенов",
        ),
        ("Пользователь: discover_tools", 40, "light", '"Нужна цена акций"', ""),
        ("Результат инструмента", 55, "light", "Схема get_stock_quote", "Определение инструмента"),
        ("Сообщение пользователя", 40, "light", "Цена акций NVDA", ""),
        (
            "Строка состояния агента (обновлена)",
            45,
            "code_bg",
            "+get_stock_quote добавлен",
            "~220 токенов",
        ),
    ]
    oy = 85
    for label, bh, fill, content, note in blocks_opt:
        svg.rect(right_x, oy, 400, bh, fill=fill, rx=4)
        svg.text(
            right_x + 10,
            oy + 16,
            label,
            size=FS_SMALL,
            bold=True,
            anchor="start",
            max_width=270,
        )
        for j, line in enumerate(content.split("\n")):
            svg.text(right_x + 200, oy + 32 + j * 16, line, size=FS_TINY, fill="text_light")
        if note:
            svg.text(
                right_x + 390,
                oy + 16,
                note,
                size=11,
                fill="darker",
                anchor="end",
                max_width=105,
            )
        oy += bh + 5

    svg.rect(right_x, oy + 5, 400, 40, fill="medium")
    svg.text(
        right_x + 200,
        oy + 25,
        "Системный промпт неизменен → KV-кэш используется повторно",
        size=FS_SMALL,
        bold=True,
    )

    # Сравнение внизу
    svg.line(30, 475, w - 30, 475, color="dark", dash=True)
    comps = [
        (
            "Доля попаданий в кэш",
            "~0% (сброс при смене инструмента)",
            "~95% (меняется лишь подсказка)",
        ),
        (
            "Задержка первого токена",
            "Высокая (пересчёт 50K токенов)",
            "Низкая (инкрементный расчёт ~200 токенов)",
        ),
    ]
    cy = 495
    svg.text(250, cy, "Показатель", size=FS_SMALL, bold=True)
    svg.text(500, cy, "Базовая схема", size=FS_SMALL, bold=True)
    svg.text(740, cy, "Оптимизация", size=FS_SMALL, bold=True)
    for metric, naive, opt in comps:
        cy += 28
        svg.text(250, cy, metric, size=FS_TINY)
        svg.text(500, cy, naive, size=FS_TINY, fill="text_light")
        svg.text(740, cy, opt, size=FS_TINY, fill="text_light")

    svg.save(os.path.join(_output_dir, "fig4-9.svg"))


# ──────────────────────── fig4-10 ────────────────────────


def fig4_10() -> None:
    """Многоэтапный конвейер самоэволюции инструментов"""
    w, h = 880, 500
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Самоэволюция AI-агента: от задачи к инструменту", size=FS_TITLE, bold=True)

    # Этапы конвейера
    stages = [
        (
            "① Выявление потребности",
            "medium",
            [
                "Задача: извлечь субтитры YouTube",
                "Агент: нужного инструмента нет",
                "→ запуск самоэволюции",
            ],
        ),
        (
            "② Web-поиск",
            "light",
            [
                "поиск: субтитры YouTube",
                "библиотека Python",
                "→ найдены 3 библиотеки",
            ],
        ),
        (
            "③ Изучение GitHub",
            "light",
            [
                "Открыть jdepoix/youtube-",
                "transcript-api",
                "→ прочитать README + примеры",
            ],
        ),
        (
            "④ Изучение и тест",
            "light",
            [
                "Тест в code_interpreter:",
                "from youtube_transcript",
                "  _api import ...",
            ],
        ),
        (
            "⑤ Упаковка инструмента",
            "medium",
            [
                "Создание MCP-инструмента:",
                "get_youtube_transcript",
                "(video_id) → text",
            ],
        ),
    ]

    stage_w, stage_h = 155, 145
    gap = 12
    total_w = len(stages) * stage_w + (len(stages) - 1) * gap
    sx = (w - total_w) / 2

    for i, (title, fill, details) in enumerate(stages):
        x = sx + i * (stage_w + gap)
        svg.rect(x, 60, stage_w, stage_h, fill=fill)
        svg.text(x + stage_w / 2, 82, title, size=FS_SMALL, bold=True)
        svg.line(x + 10, 94, x + stage_w - 10, 94, color="dark")
        for j, line in enumerate(details):
            svg.mono(x + 8, 114 + j * 20, line, size=11)
        if i < len(stages) - 1:
            svg.arrow(x + stage_w + 2, 60 + stage_h / 2, x + stage_w + gap - 2, 60 + stage_h / 2)

    # Библиотека инструментов внизу
    svg.arrow(w / 2, 205, w / 2, 240)

    svg.rect(120, 240, w - 240, 50, fill="dark")
    svg.text(
        w / 2,
        265,
        "⑥ Регистрация в библиотеке инструментов → прямое повторное использование в будущем",
        size=FS_BODY,
        fill="white",
        bold=True,
    )

    # Сценарий повторного использования
    svg.arrow(w / 2, 290, w / 2, 320)
    svg.rect(60, 320, w - 120, 160, fill="white", stroke="border", dash=True)
    svg.text(w / 2, 345, "Повторное использование: похожая задача", size=FS_BODY, bold=True)

    svg.rect(80, 365, 340, 50, fill="code_bg", stroke="dark", rx=4)
    svg.mono(90, 382, 'Агент: "Нужно извлечь субтитры YouTube"', size=FS_TINY)
    svg.mono(90, 400, '→ search_tools("субтитры YouTube")', size=FS_TINY)

    svg.arrow(420, 390, 460, 390)

    svg.rect(460, 365, 330, 50, fill="light")
    svg.text(625, 382, "Найден! get_youtube_transcript", size=FS_SMALL, bold=True)
    svg.text(625, 402, "Без поиска и создания — сразу вызов", size=FS_TINY, fill="text_light")

    svg.rect(200, 430, 480, 35, fill="medium")
    svg.text(
        w / 2,
        448,
        "Инструменты + знания + стратегии → навыки растут с практикой",
        size=FS_SMALL,
        bold=True,
    )

    svg.save(os.path.join(_output_dir, "fig4-10.svg"))


# ──────────────────────── fig4-11 ────────────────────────


def fig4_11() -> None:
    "Эксперимент 4.7: AI-агент находит инструменты в сети и самоэволюционирует"
    w, h = 880, 480
    svg = SVG(w, h)
    svg.text(
        w / 2, 30, "Эксперимент 4.7: конвейер самоэволюции AI-агента", size=FS_TITLE, bold=True
    )

    # Минимальный набор базовых инструментов сверху
    svg.rect(30, 60, w - 60, 48, fill="medium")
    svg.text(w / 2, 76, "Базовые инструменты (минимум)", size=FS_SMALL, bold=True)
    base_tools = ["web_search", "read_webpage", "code_interpreter", "create_tool", "search_tools"]
    btx = 65
    for t in base_tools:
        tw = len(t) * 8 + 20
        _pill(svg, btx, 82, tw, 22, t, fill="dark", font_size=11, bold=True)
        btx += tw + 10

    # Входная задача
    svg.arrow(w / 2, 108, w / 2, 135)
    svg.rect(100, 135, w - 200, 45, fill="code_bg", stroke="dark", rx=4)
    svg.mono(
        110,
        150,
        'Задача: "Последняя цена акций NVDA и изменение в процентах относительно недели назад?" → Агент: нет финансового инструмента!',
        size=FS_TINY,
    )
    svg.mono(110, 168, "→ выявить пробел → запустить самоэволюцию", size=FS_TINY)

    # Конвейер самоэволюции
    svg.arrow(w / 2, 180, w / 2, 210)

    pipe_y = 210
    pipe_stages = [
        (
            "web_search",
            "Поиск вариантов",
            "light",
            ['"API цен акций для Python"', "→ yfinance, Alpha Vantage..."],
        ),
        (
            "read_webpage",
            "Оценка вариантов",
            "light",
            ["yfinance: бесплатно, без ключа API", "Alpha Vantage: нужна регистрация..."],
        ),
        (
            "code_interpreter",
            "Тестирование",
            "light",
            ["import yfinance as yf", "yf.Ticker('NVDA').history()"],
        ),
        (
            "create_tool",
            "Упаковка и регистрация",
            "medium",
            ["name: get_stock_data", "schema: {ticker, period}"],
        ),
    ]

    pw = 190
    pgap = 15
    total_pw = len(pipe_stages) * pw + (len(pipe_stages) - 1) * pgap
    px = (w - total_pw) / 2
    for i, (tool, desc, fill, details) in enumerate(pipe_stages):
        svg.rect(px, pipe_y, pw, 120, fill=fill)
        _pill(svg, px + 10, pipe_y + 8, pw - 20, 22, tool, fill="dark", font_size=11, bold=True)
        svg.text(px + pw / 2, pipe_y + 48, desc, size=FS_SMALL, bold=True)
        for j, line in enumerate(details):
            svg.mono(px + 8, pipe_y + 70 + j * 18, line, size=11)
        if i < len(pipe_stages) - 1:
            svg.arrow(px + pw + 2, pipe_y + 60, px + pw + pgap - 2, pipe_y + 60)
        px += pw + pgap

    # Библиотека инструментов
    svg.arrow(w / 2, 330, w / 2, 360)
    svg.rect(200, 360, w - 400, 44, fill="dark")
    svg.text(
        w / 2,
        382,
        "Библиотека инструментов: get_stock_data зарегистрирован",
        size=FS_BODY,
        fill="white",
        bold=True,
    )

    # Повторное использование
    svg.arrow(w / 2, 404, w / 2, 430)
    svg.rect(100, 430, w - 200, 40, fill="code_bg", stroke="dark", rx=4)
    svg.mono(
        110,
        442,
        'Проверка повторного использования: "Цена TSLA" → search_tools находит совпадение → прямой вызов get_stock_data',
        size=FS_TINY,
    )
    svg.mono(110, 458, "Без поиска/оценки/теста → затраты ниже на 90%+", size=FS_TINY)

    svg.save(os.path.join(_output_dir, "fig4-11.svg"))


# ──────────────────────── fig4-12 (Voyager, ранее fig4_voyager) ────────


def fig4_12() -> None:
    """Цикл обучения Voyager: учебный план, библиотека навыков и итеративные промпты"""
    w, h = 880, 520
    svg = SVG(w, h)
    svg.text(
        w / 2,
        30,
        "Voyager: архитектура непрерывно обучающегося AI-агента",
        size=FS_TITLE,
        bold=True,
    )

    svg.rect(20, 65, 260, 180, fill="white", stroke="border", dash=True)
    svg.text(150, 88, "Автоматический генератор учебного плана", size=FS_BODY, bold=True)
    curriculum = [
        "Вход: состояние + освоенные навыки",
        "Выход: следующая цель исследования",
        "",
        "Пример целей:",
        "  срубить дерево → сделать доски",
        "  → сделать деревянную кирку → добыть камень",
        "  → построить печь → выплавить железный слиток",
    ]
    for i, line in enumerate(curriculum):
        svg.mono(32, 112 + i * 20, line, size=12)

    svg.rect(600, 65, 260, 180, fill="white", stroke="border", dash=True)
    svg.text(730, 88, "Итеративные промпты", size=FS_BODY, bold=True)
    iterative = [
        "При сбое собрать обратную связь:",
        "  - наблюдение среды (ошибка)",
        "  - результат самопроверки",
        "",
        "Добавить в промпт LLM",
        "→ улучшать код",
        "→ повторять до успеха",
    ]
    for i, line in enumerate(iterative):
        svg.mono(612, 112 + i * 20, line, size=12)

    svg.arrow(280, 155, 370, 155, label="Цель")
    svg.arrow(560, 155, 600, 155)

    svg.rect(370, 110, 190, 80, fill="medium")
    svg.text(465, 140, "Работа агента", size=FS_BODY, bold=True)
    svg.text(465, 165, "Генерация кода GPT-4", size=FS_SMALL, fill="text_light")

    svg.arrow(465, 190, 465, 260)
    svg.text(510, 230, "Успех → обобщить", size=FS_SMALL, fill="text_light")

    svg.rect(120, 260, 640, 240, fill="white", stroke="border", dash=True)
    svg.text(440, 283, "Библиотека навыков — ядро внешнего обучения", size=FS_BODY, bold=True)

    skills = [
        (
            "chopTree()",
            "Срубить дерево\nБазовый навык",
            "function chopTree() {\n  bot.dig(nearest('log'));\n}",
        ),
        (
            "craftPlanks()",
            "Сделать доски\nВызов chopTree",
            "function craftPlanks() {\n  chopTree(); craft('planks');\n}",
        ),
        (
            "craftPickaxe()",
            "Сделать деревянную кирку\nКомпозиция навыков",
            "function craftPickaxe() {\n  craftPlanks(); craft('stick');\n  craft('wooden_pickaxe');\n}",
        ),
    ]
    skx = 140
    for name, desc, code in skills:
        svg.rect(skx, 305, 190, 175, fill="light")
        svg.text(skx + 95, 325, name, size=FS_SMALL, bold=True)
        for j, dl in enumerate(desc.split("\n")):
            svg.text(skx + 95, 347 + j * 18, dl, size=FS_TINY, fill="text_light")

        svg.rect(skx + 10, 385, 170, 80, fill="code_bg", stroke="dark", rx=4)
        for j, cl in enumerate(code.split("\n")):
            svg.mono(skx + 18, 400 + j * 18, cl, size=11)
        skx += 215

    svg.arrow_curved(
        120, 380, 150, 245, curve=60, label="Освоенные навыки", dash=True, color="dark"
    )

    svg.save(os.path.join(_output_dir, "fig4-12.svg"))


# ──────────────────────── main ────────────────────────


def main(output_dir: str) -> None:
    global _output_dir
    _output_dir = output_dir
    os.makedirs(_output_dir, exist_ok=True)
    figs = [
        fig4_1,
        fig4_2,
        fig4_3,
        fig4_4,
        fig4_5,
        fig4_6,
        fig4_7,
        fig4_8,
        fig4_9,
        fig4_10,
        fig4_11,
        fig4_12,
    ]
    # Примечание: fig4_11 = эксперимент 4.7 с самоэволюцией агента,
    # fig4_12 = Voyager (в порядке появления в главе)
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nСоздано {len(figs)} иллюстраций в {_output_dir}/")


if __name__ == "__main__":
    main(parse_output_dir(_output_dir))
