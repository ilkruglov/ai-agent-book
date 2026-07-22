"""Создание всех иллюстраций главы 1."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import FS_BODY, FS_SMALL, FS_TINY, FS_TITLE, SVG, parse_output_dir

_output_dir = os.path.join(os.path.dirname(__file__), "images")


def fig1_4() -> None:
    """Архитектура нативного AI-агента Kimi K3 / GPT-5.6 — подпись к рис. 1-4."""
    s = SVG(820, 520)

    # Заголовок
    s.text(
        410, 30, "«Модель и есть AI-агент»: нативные вызовы инструментов", size=FS_TITLE, bold=True
    )

    # Центральный блок модели
    s.rect(260, 70, 300, 100, fill="medium")
    s.text(410, 100, "LLM (Kimi K3 / GPT-5.6)", size=FS_BODY, bold=True)
    s.text(410, 130, "Агент после обучения с подкреплением (RL)", size=FS_SMALL, fill="text_light")

    # Нативные инструменты справа
    s.group_box(620, 70, 180, 210, "Нативные инструменты")
    s.box(635, 105, 150, 50, "$web_search", fill="light", font_size=FS_SMALL)
    s.box(635, 170, 150, 50, "code_interpreter", fill="light", font_size=FS_SMALL)
    s.box(635, 235, 150, 50, "Другие инструменты...", fill="white", font_size=FS_SMALL)

    s.arrow(560, 120, 633, 130)
    s.arrow(633, 195, 560, 145)

    # Цикл ReAct ниже
    s.group_box(100, 210, 460, 280, "Цикл ReAct (автономно внутри модели)")

    # Шаг 1: ввод пользователя
    s.box(
        120,
        250,
        200,
        55,
        "Пользователь: найди динамику\nBitcoin за последний месяц",
        fill="light",
        font_size=FS_SMALL,
    )

    # Шаг 2: рассуждение
    s.box(
        120,
        325,
        200,
        55,
        "Рассуждение: нужны актуальные\nданные и анализ в коде",
        fill="#e8e8e8",
        font_size=FS_SMALL,
    )
    s.arrow(220, 307, 220, 323)

    # Шаг 3: вызов инструмента
    s.box(
        340,
        250,
        200,
        55,
        "Вызов $web_search\n«Цена BTC за месяц»",
        fill="light",
        font_size=FS_SMALL,
    )
    s.arrow(322, 277, 338, 277)

    # Шаг 4: результат инструмента
    s.box(
        340,
        325,
        200,
        55,
        "Результат: [данные о ценах]\n$67,230 → $71,450",
        fill="#e8e8e8",
        font_size=FS_SMALL,
    )
    s.arrow(440, 307, 440, 323)

    # Шаг 5: код
    s.box(
        120,
        400,
        200,
        55,
        "Вызов code_interpreter\nКод расчёта RSI, MACD",
        fill="light",
        font_size=FS_SMALL,
    )
    s.arrow(340, 377, 220, 398, color="dark")

    # Шаг 6: итог
    s.box(
        340, 400, 200, 55, "Итог: отчёт по теханализу\n+ графики", fill="medium", font_size=FS_SMALL
    )
    s.arrow(322, 427, 338, 427)

    # Сигнал RL-обучения проходит в зазоре между ReAct и инструментами, не перекрывая содержимое
    s.arrow_curved(565, 480, 410, 172, curve=40, dash=True, color="dark")
    s.text(
        605, 330, "Сигнал RL-обучения", size=FS_TINY, fill="text_light", bold=True, anchor="start"
    )

    # Слева: отличия от традиционных схем
    s.group_box(15, 70, 230, 120, "Отличия от традиционных фреймворков")
    s.text(130, 110, "✗ Внешняя оркестрация не нужна", size=FS_SMALL, anchor="middle")
    s.text(130, 135, "✗ Не нужен ручной цикл ReAct", size=FS_SMALL, anchor="middle")
    s.text(130, 160, "✓ Агент сам ведёт весь процесс", size=FS_SMALL, anchor="middle")

    s.save(f"{_output_dir}/fig1-3.svg")  # Процесс ReAct → рис. 1-3


def fig1_1() -> None:
    """Три парадигмы обучения — подпись к рис. 1-1."""
    s = SVG(820, 480)

    s.text(410, 30, "Три парадигмы обучения AI-агента", size=FS_TITLE, bold=True)

    col_w = 240
    gap = 20
    x_start = (820 - 3 * col_w - 2 * gap) / 2

    for i, (title, subtitle, time_label, items, example) in enumerate(
        [
            (
                "Постобучение",
                "После основного обучения",
                "При обучении",
                [
                    "Изменяет веса модели",
                    "Постоянно · универсально",
                    "Дорого · медленно обновлять",
                ],
                "Пример: когда вызывать инструмент",
            ),
            (
                "Контекстное обучение",
                "Обучение в контексте",
                "При инференсе",
                [
                    "Мягкая адаптация через внимание",
                    "Временно · быстрая адаптация",
                    "Ограничено контекстным окном",
                ],
                "Пример: новый формат по 3 образцам",
            ),
            (
                "Экстернализированное обучение",
                "Обучение с вынесением знаний",
                "При работе",
                [
                    "База знаний + генерация инструментов",
                    "Постоянно · обновляемо",
                    "Надёжно · проверяемо",
                ],
                "Пример: процесс как инструмент",
            ),
        ]
    ):
        x = x_start + i * (col_w + gap)

        # Заголовок
        s.box(x, 65, col_w, 65, f"{title}\n{subtitle}", fill="medium", bold=True, font_size=FS_BODY)

        # Метка этапа
        s.badge(x + col_w / 2 - 40, 140, 80, 28, time_label, fill="darker")

        # Пункты
        for j, item in enumerate(items):
            y = 185 + j * 45
            s.box(x, y, col_w, 38, item, fill="light", font_size=FS_SMALL)

        # Пример
        s.rect(x, 330, col_w, 45, fill="code_bg", stroke="dark", rx=4)
        s.text(x + col_w / 2, 352, example, size=FS_SMALL, fill="text_light")

    # Шкала времени внизу
    s.arrow(60, 430, 760, 430, color="dark")
    s.text(60, 455, "Медленно (недели)", size=FS_SMALL, fill="text_light", anchor="start")
    s.text(410, 455, "Скорость обучения", size=FS_SMALL, fill="text_light")
    s.text(760, 455, "Быстро (миллисекунды)", size=FS_SMALL, fill="text_light", anchor="end")

    s.save(f"{_output_dir}/fig1-4.svg")  # Три парадигмы обучения → рис. 1-4


def fig1_2() -> None:
    """Схема абляционного эксперимента с контекстом — подпись к рис. 1-2."""
    W = 980
    s = SVG(W, 500)

    s.text(W / 2, 30, "Схема эксперимента по абляции контекста", size=FS_TITLE, bold=True)

    # Заголовки столбцов в порядке удаления компонентов в эксперименте 1-1
    components = [
        "Системный промпт",
        "Описания инструментов",
        "Вывод инструмента",
        "Ход рассуждений",
        "История сообщений",
    ]
    comp_w = 105
    comp_gap = 10
    # Слева оставлено 110 для подписей строк, справа — 170 для результатов
    comp_x = 130

    for i, comp in enumerate(components):
        x = comp_x + i * (comp_w + comp_gap)
        s.text(x + comp_w / 2, 65, comp, size=FS_SMALL, bold=True, max_width=comp_w - 8)

    # Заголовок столбца результатов
    result_x = comp_x + len(components) * (comp_w + comp_gap) + 10  # = 705
    s.text(result_x + 80, 65, "Результат", size=FS_SMALL, bold=True)

    # Строки эксперимента
    conditions = [
        ("Базовый вариант", [True, True, True, True, True], "✓ Работает"),
        ("Без описаний", [True, False, True, True, True], "✗ Нельзя вызвать инструмент"),
        ("Без вывода", [True, True, False, True, True], "✗ Слепой цикл"),
        ("Без рассуждений", [True, True, True, False, True], "△ Решения несвязны"),
        ("Без истории", [True, True, True, True, False], "△ Повтор действий"),
    ]

    for j, (label, flags, result) in enumerate(conditions):
        y = 95 + j * 72

        # Подпись строки
        s.text(115, y + 28, label, size=FS_SMALL, bold=True, anchor="end")

        for i, present in enumerate(flags):
            x = comp_x + i * (comp_w + comp_gap)
            fill = "light" if present else "white"
            stroke = "border" if present else "dark"
            s.rect(x, y, comp_w, 55, fill=fill, stroke=stroke, dash=not present)
            if present:
                s.text(x + comp_w / 2, y + 28, "✓", size=FS_BODY)
            else:
                s.text(x + comp_w / 2, y + 28, "✗", size=FS_BODY, fill="dark")

        # Результат в отдельном столбце справа от сетки
        s.text(
            result_x + 80,
            y + 28,
            result,
            size=FS_SMALL,
            fill="text" if "✓" in result else ("text_light" if "△" in result else "dark"),
        )

    s.save(f"{_output_dir}/fig1-1.svg")  # Абляция контекста → рис. 1-1


def fig1_3() -> None:
    """Траектория AI-агента — подпись к рис. 1-3."""
    s = SVG(820, 680)

    s.text(
        410, 30, "Траектория AI-агента: цикл ReAct для сводки по валютам", size=FS_TITLE, bold=True
    )

    lx = 40  # левое поле
    rw = 480  # ширина блока

    y = 60

    # Раунд 1
    s.badge(lx, y, 80, 26, "Раунд 1", fill="darker")
    y += 36

    # Сообщение пользователя
    s.rect(lx, y, rw, 50, fill="light")
    s.text(lx + 10, y + 16, "user", size=FS_SMALL, bold=True, anchor="start")
    s.text(
        lx + 10,
        y + 38,
        "«Рассчитай годовой доход: Q1 $2.5M, Q2 €2.1M, Q3 £1.8M»",
        size=FS_TINY,
        anchor="start",
    )
    y += 60

    # Рассуждение ассистента
    s.rect(lx, y, rw, 45, fill="#e8e8e8")
    s.text(
        lx + 10,
        y + 14,
        "assistant.reasoning",
        size=FS_SMALL,
        bold=True,
        anchor="start",
        fill="darker",
    )
    s.text(
        lx + 10,
        y + 34,
        "«Нужно конвертировать EUR и GBP в USD, затем сложить»",
        size=FS_TINY,
        anchor="start",
    )
    y += 55

    # Вызовы инструментов
    s.rect(lx, y, rw, 70, fill="code_bg", stroke="dark", rx=4)
    s.text(
        lx + 10,
        y + 14,
        "assistant.tool_calls",
        size=FS_SMALL,
        bold=True,
        anchor="start",
        fill="darker",
    )
    s.mono(lx + 10, y + 36, 'convert_currency(2100000, "EUR", "USD")', size=FS_TINY)
    s.mono(lx + 10, y + 54, 'convert_currency(1800000, "GBP", "USD")', size=FS_TINY)
    y += 80

    # Результаты инструментов
    s.rect(lx, y, rw, 55, fill="light")
    s.text(
        lx + 10, y + 14, "tool (результат)", size=FS_SMALL, bold=True, anchor="start", fill="darker"
    )
    s.mono(lx + 10, y + 36, "EUR→USD: 2,282,608.70", size=FS_TINY)
    s.mono(lx + 250, y + 36, "GBP→USD: 2,278,481.01", size=FS_TINY)
    y += 65

    # Раунд 2
    s.badge(lx, y, 80, 26, "Раунд 2", fill="darker")
    y += 36

    # Рассуждение ассистента 2
    s.rect(lx, y, rw, 45, fill="#e8e8e8")
    s.text(
        lx + 10,
        y + 14,
        "assistant.reasoning",
        size=FS_SMALL,
        bold=True,
        anchor="start",
        fill="darker",
    )
    s.text(
        lx + 10,
        y + 34,
        "«Курсы получены; вызываю интерпретатор кода для итогового расчёта»",
        size=FS_TINY,
        anchor="start",
    )
    y += 55

    # Вызов интерпретатора кода
    s.rect(lx, y, rw, 50, fill="code_bg", stroke="dark", rx=4)
    s.text(
        lx + 10,
        y + 14,
        "assistant.tool_calls",
        size=FS_SMALL,
        bold=True,
        anchor="start",
        fill="darker",
    )
    s.mono(lx + 10, y + 36, 'code_interpreter("total = 2.5M + 2.28M + 2.28M")', size=FS_TINY)
    y += 60

    # Раунд 3
    s.badge(lx, y, 80, 26, "Раунд 3", fill="darker")
    y += 36

    # Итоговый ответ
    s.rect(lx, y, rw, 45, fill="medium")
    s.text(
        lx + 10,
        y + 14,
        "assistant.content (итоговый ответ)",
        size=FS_SMALL,
        bold=True,
        anchor="start",
    )
    s.text(
        lx + 10,
        y + 36,
        "«За год: $7,061,089.71; среднее за квартал: $2,353,696.57»",
        size=FS_TINY,
        anchor="start",
    )
    y += 55

    # Справа: фигурная скобка и пояснение
    bx = 540
    s.brace_right(bx, 60, y - 10, "")
    s.text(600, 250, "Траектория", size=FS_BODY, bold=True, anchor="start")
    s.text(600, 280, "=", size=FS_BODY, anchor="start")
    s.text(600, 310, "Полный ввод,", size=FS_BODY, anchor="start")
    s.text(600, 340, "который LLM видит", size=FS_BODY, anchor="start")
    s.text(600, 370, "при каждом вызове", size=FS_BODY, anchor="start")

    # Блок ключевых свойств справа
    s.group_box(570, 410, 230, 140, "Ключевые свойства")
    s.text(685, 445, "Накопление контекста", size=FS_SMALL, bold=True)
    s.text(685, 470, "Вся история видна в каждом раунде", size=FS_TINY, fill="text_light")
    s.text(685, 500, "Структурированная траектория", size=FS_SMALL, bold=True)
    s.text(685, 525, "user / assistant / tool", size=FS_TINY, fill="text_light")

    s.save(f"{_output_dir}/fig1-2.svg")  # Траектория агента → рис. 1-2


def fig1_wf_chaining() -> None:
    """Цепочка промптов — паттерн рабочего процесса из раздела главы 1 об оркестрации."""
    s = SVG(820, 300)

    s.text(410, 28, "Цепочка промптов: пошаговое создание контента", size=FS_TITLE, bold=True)

    # Узлы с конкретными описаниями
    nodes = [
        ("Документ\nтребований", "light", FS_SMALL),
        ("LLM: создаёт план", "#e8e8e8", FS_SMALL),
        ("LLM: пишет текст", "#e8e8e8", FS_SMALL),
        ("LLM: переводит", "#e8e8e8", FS_SMALL),
        ("Многоязычный\nдокумент", "medium", FS_SMALL),
    ]

    node_w = 130
    node_h = 55
    gap = 15
    total = len(nodes) * node_w + (len(nodes) - 1) * gap
    x_start = (820 - total) / 2
    y = 65

    for i, (label, fill, fs) in enumerate(nodes):
        x = x_start + i * (node_w + gap)
        s.box(x, y, node_w, node_h, label, fill=fill, font_size=fs)
        if i > 0:
            px = x_start + (i - 1) * (node_w + gap) + node_w
            s.arrow(px + 2, y + node_h / 2, x - 2, y + node_h / 2)

    # Контрольные ромбы между этапами
    gate_y = y + node_h + 15
    for i in [1, 2]:
        gx = x_start + i * (node_w + gap) + node_w / 2
        s.diamond(gx, gate_y + 22, 60, 40, fill="white", label="Проверка", font_size=FS_TINY)
        s.line(gx, y + node_h, gx, gate_y + 2, dash=True, color="dark")

    # Примеры содержимого внизу
    snippet_y = gate_y + 60
    snippets = [
        (x_start + 15, "«Примечания к релизу»"),
        (x_start + node_w + gap + 15, "→ План из 5 разделов"),
        (x_start + 2 * (node_w + gap) + 15, "→ Документ на 3000 знаков"),
        (x_start + 3 * (node_w + gap) + 15, "→ EN / JP / KR"),
    ]
    for sx, txt in snippets:
        s.text(
            sx,
            snippet_y,
            txt,
            size=FS_TINY,
            fill="text_light",
            anchor="start",
            max_width=node_w - 20,
        )

    s.save(f"{_output_dir}/fig1-5.svg")


def fig1_wf_routing() -> None:
    """Маршрутизация — паттерн рабочего процесса из раздела главы 1 об оркестрации."""
    s = SVG(820, 440)

    s.text(410, 28, "Маршрутизация: классификация обращений клиентов", size=FS_TITLE, bold=True)

    # Вход
    s.box(30, 130, 150, 55, "Запрос пользователя", fill="medium", font_size=FS_BODY)

    # Маршрутизатор
    s.diamond(300, 157, 140, 80, fill="#e8e8e8", label="Классификатор", font_size=FS_SMALL)
    s.arrow(182, 157, 230, 157)

    # Ветви
    branches = [
        (55, "Запрос возврата", "Промпт политики возврата\n+ API заказов", "light"),
        (155, "Техподдержка", "Промпт диагностики\n+ инструмент анализа логов", "light"),
        (255, "Частый вопрос", "Промпт для FAQ\n+ база знаний", "light"),
        (355, "Другое", "Haiku (экономия)\n+ общий промпт", "white"),
    ]

    bx = 490
    bw = 160
    for _i, (by_offset, label, desc, fill) in enumerate(branches):
        by = by_offset
        s.box(bx, by, bw, 50, label, fill=fill, bold=True, font_size=FS_SMALL)
        s.box(bx + bw + 10, by, 140, 50, desc, fill="code_bg", font_size=FS_TINY)
        s.arrow(370, 157, bx - 2, by + 25)

    # Примечание
    s.text(
        410,
        425,
        "Ключ: LLM или обычный классификатор; простые и частые запросы — малой модели",
        size=FS_SMALL,
        fill="text_light",
    )

    s.save(f"{_output_dir}/fig1-6.svg")


def fig1_wf_parallel() -> None:
    """Параллелизация — паттерн рабочего процесса из раздела главы 1 об оркестрации."""
    s = SVG(820, 360)

    s.text(410, 28, "Параллелизация: ревью кода с разных сторон", size=FS_TITLE, bold=True)

    # Вход
    s.box(30, 130, 150, 55, "Код из\nпул-реквеста", fill="medium", font_size=FS_SMALL)

    # Разделение
    s.text(220, 157, "Разделение", size=FS_SMALL, bold=True)

    # Параллельные исполнители
    workers = [
        (70, "LLM₁: безопасность", "SQL-инъекции\nXSS\nУтечки прав доступа"),
        (155, "LLM₂: стиль", "Именование\nДублирование кода\nСложность"),
        (240, "LLM₃: логика", "Граничные случаи\nНулевые указатели\nПроблемы конкурентности"),
    ]

    wx = 290
    ww = 155
    for _i, (wy, title, items) in enumerate(workers):
        s.box(wx, wy, ww, 55, title, fill="light", bold=True, font_size=FS_SMALL)
        s.box(wx + ww + 5, wy, 130, 55, items, fill="code_bg", font_size=FS_TINY)
        s.arrow(180, 157, wx - 2, wy + 28)

    # Сведение результатов
    s.box(
        640, 130, 150, 55, "Сводка результатов\nИтоговый отчёт", fill="medium", font_size=FS_SMALL
    )
    for _i, (wy, _, _) in enumerate(workers):
        s.arrow(wx + ww + 135 + 2, wy + 28, 638, 157)

    s.save(f"{_output_dir}/fig1-7.svg")


def fig1_wf_orchestrator() -> None:
    """Оркестратор и исполнители — паттерн рабочего процесса из раздела главы 1 об оркестрации."""
    s = SVG(820, 440)

    s.text(
        410, 28, "Оркестратор и исполнители: правки в нескольких файлах", size=FS_TITLE, bold=True
    )

    # Оркестратор сверху: заголовок и внутренняя подпись разнесены по вертикали
    s.rect(260, 60, 300, 95, fill="medium")
    s.text(410, 82, "Оркестратор LLM", size=FS_BODY, bold=True)
    s.rect(270, 105, 280, 38, fill="#e8e8e8", rx=4)
    s.text(410, 124, "«Анализ Issue → поиск файлов → распределение подзадач»", size=FS_TINY)

    # Исполнители
    workers = [
        (
            40,
            "Исполнитель 1",
            "Изменить auth.py\nДобавить поддержку OAuth2",
            "Инструменты\nчтения/правки",
        ),
        (
            290,
            "Исполнитель 2",
            "Изменить api.py\nДобавить новый эндпоинт",
            "Инструменты\nчтения/правки",
        ),
        (
            540,
            "Исполнитель 3",
            "Написать test_auth.py\nДобавить тесты",
            "Инструмент\nзапуска тестов",
        ),
    ]

    wy = 220
    ww = 230
    wh = 55
    for wx, title, task, tools in workers:
        s.box(wx, wy, ww, wh, f"{title}: {task}", fill="light", font_size=FS_SMALL)
        s.box(wx + 20, wy + wh + 10, ww - 40, 40, tools, fill="code_bg", font_size=FS_TINY)
        s.arrow(410, 157, wx + ww / 2, wy - 2)

    # Сведение
    s.box(
        260,
        370,
        300,
        55,
        "Оркестратор: слияние → проверка согласованности",
        fill="medium",
        font_size=FS_SMALL,
    )
    for wx, _, _, _ in workers:
        s.arrow(wx + ww / 2, wy + wh + 52, 410, 368)

    s.save(f"{_output_dir}/fig1-8.svg")


def fig1_wf_evaluator() -> None:
    """Оценщик и оптимизатор — паттерн рабочего процесса из раздела главы 1 об оркестрации."""
    s = SVG(820, 380)

    s.text(
        410, 28, "Оценщик и оптимизатор: итерации литературного перевода", size=FS_TITLE, bold=True
    )

    # Генератор
    s.box(50, 100, 200, 65, "LLM-генератор\nПервичный перевод", fill="light", font_size=FS_SMALL)

    # Вывод
    s.rect(50, 185, 200, 45, fill="code_bg", stroke="dark", rx=4)
    s.text(150, 208, "Китайский оригинал → перевод v1", size=FS_TINY)
    s.arrow(150, 167, 150, 183)

    # Оценщик
    s.box(330, 100, 200, 65, "LLM-оценщик\nОценка по критериям", fill="#e8e8e8", font_size=FS_SMALL)
    s.arrow(252, 207, 330, 160)

    # Критерии оценки
    s.rect(330, 185, 200, 80, fill="code_bg", stroke="dark", rx=4)
    s.text(340, 205, "Точность: 4/5", size=FS_TINY, anchor="start")
    s.text(340, 225, "Беглость: 3/5 ← улучшить", size=FS_TINY, anchor="start")
    s.text(340, 245, "Культурная адаптация: 4/5", size=FS_TINY, anchor="start")
    s.arrow(430, 167, 430, 183)

    # Метка обратной связи над дугой, чтобы не перекрывать содержимое оценщика
    s.arrow_curved(430, 267, 150, 98, curve=80, dash=True, color="dark")
    s.text(290, 90, "Обратная связь + советы", size=FS_TINY, fill="text_light", bold=True)

    # Счётчик итераций
    s.box(610, 100, 170, 55, "Число итераций: n", fill="white", font_size=FS_SMALL)
    s.text(695, 170, "Условия выхода:", size=FS_SMALL, bold=True, anchor="start")
    s.text(695, 195, "① Все оценки ≥ 4/5", size=FS_TINY, anchor="start", fill="text_light")
    s.text(695, 218, "② Лимит итераций", size=FS_TINY, anchor="start", fill="text_light")

    # Итоговый результат
    s.box(
        220,
        310,
        380,
        55,
        "Итог: качественный перевод после 3 итераций",
        fill="medium",
        font_size=FS_SMALL,
    )

    s.save(f"{_output_dir}/fig1-9.svg")


def fig1_5() -> None:
    """Цикл автономного AI-агента — подпись к рис. 1-5."""
    s = SVG(820, 500)

    s.text(410, 28, "Цикл выполнения автономного AI-агента", size=FS_TITLE, bold=True)

    # Структура цикла while
    s.rect(80, 60, 500, 380, fill="white", stroke="border", rx=8, dash=True)
    s.text(330, 82, "while not done:", size=FS_BODY, bold=True)

    # Шаг 1: рассуждение — заголовок над кодом
    s.rect(120, 100, 420, 60, fill="#e8e8e8")
    s.text(130, 115, "① Рассуждение", size=FS_SMALL, bold=True, anchor="start")
    s.rect(130, 125, 400, 28, fill="code_bg", rx=4)
    s.mono(140, 140, "«Анализ результатов поиска... данных мало, нужен ещё поиск»", size=FS_TINY)

    # Шаг 2: действие
    s.rect(120, 175, 420, 60, fill="light")
    s.text(130, 190, "② Действие", size=FS_SMALL, bold=True, anchor="start")
    s.rect(130, 200, 400, 28, fill="code_bg", rx=4)
    s.mono(140, 215, 'web_search("методы RL-обучения AI-агентов 2025")', size=FS_TINY)
    s.arrow(330, 162, 330, 173)

    # Шаг 3: наблюдение
    s.rect(120, 250, 420, 60, fill="light")
    s.text(130, 265, "③ Наблюдение", size=FS_SMALL, bold=True, anchor="start")
    s.rect(130, 275, 400, 28, fill="code_bg", rx=4)
    s.mono(140, 290, 'tool_result: "Найдены 3 релевантные статьи..."', size=FS_TINY)
    s.arrow(330, 237, 330, 248)

    # Обратная стрелка цикла
    s.arrow_curved(540, 280, 540, 120, curve=-40, label="Продолжить цикл", color="dark")

    # Условия выхода справа
    s.group_box(610, 60, 190, 190, "Условия выхода")
    exits = [
        "① Задача выполнена",
        "② Вызван final_answer",
        "③ Ответ без вызова инструмента",
        "④ Достигнут лимит итераций",
        "⑤ Превышен лимит ошибок",
    ]
    for i, ex in enumerate(exits):
        s.text(620, 100 + i * 32, ex, size=FS_SMALL, anchor="start")

    # Внизу: конкретный пример выполнения
    s.rect(80, 360, 500, 70, fill="medium", rx=6)
    s.text(330, 380, "Пример выполнения: исправление кода в SWE-bench", size=FS_SMALL, bold=True)
    s.text(
        330,
        405,
        "Поиск в коде → баг → правка → тесты: сбой → новая правка → тесты: успех → готово",
        size=FS_TINY,
    )
    s.text(330, 425, "(5 итераций, 12 вызовов инструментов)", size=FS_TINY, fill="text_light")

    # Стрелка завершения
    s.arrow(330, 312, 330, 358, label="done = True")

    s.save(f"{_output_dir}/fig1-10.svg")


def main(output_dir: str) -> None:
    global _output_dir
    _output_dir = output_dir
    os.makedirs(_output_dir, exist_ok=True)
    # Основные иллюстрации главы, обозначенные как рис. 1-1 — рис. 1-5
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_4()
    fig1_5()
    # Иллюстрации паттернов рабочих процессов, пока не используемые в chapter1.md;
    # сохранены для возможного использования в будущем
    fig1_wf_chaining()
    fig1_wf_routing()
    fig1_wf_parallel()
    fig1_wf_orchestrator()
    fig1_wf_evaluator()
    print("Глава 1: создано 5 основных иллюстраций и 5 схем рабочих процессов.")


if __name__ == "__main__":
    main(parse_output_dir(_output_dir))
