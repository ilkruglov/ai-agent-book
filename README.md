# AI-агенты изнутри: принципы проектирования и инженерная практика

Русский перевод: community edition.

Независимый русский перевод книги Bojie Li «深入理解 AI Agent：设计原理与工程实践». Перевод выполняется напрямую с китайского оригинала и не является официальным изданием автора.

## Зафиксированный источник

- Репозиторий: <https://github.com/bojieli/ai-agent-book>
- Версия: `v2.0`
- Коммит: `c3352738f4b6fe42fe34e3cf6a79bcb424a133b8`
- Исходный каталог: `book/`
- Лицензия: Apache License 2.0

Китайские Markdown-исходники не хранятся в Git этого репозитория. Для сверки они загружаются в игнорируемый каталог `.tmp/upstream/`.

## Статус

Готово издание `v2.0-ru.1`: [PDF, 543 страницы](dist/AI-Agents-in-Depth-RU-v2.0.pdf).

Переведены и сверены введение, 10 глав, послесловие и справочные ответы на вопросы для размышления: 13 файлов, 111 фрагментов. В книге 114 иллюстраций; 39 изменённых SVG заново подготовлены для вёрстки. Проверены ссылки, 34 таблицы и границы текста на всех страницах PDF. Проверенные тексты и сведения об их происхождении находятся в [updates/v2.0/](updates/v2.0/), результаты проверок — в [status.json](updates/v2.0/status.json).

Предыдущее издание сохранено: [PDF 1.2](dist/AI-Agents-in-Depth-RU-v1.2.pdf). Его иллюстрации и манифесты находятся в [updates/v1.2/](updates/v1.2/); исходное состояние русского перевода — в коммите `ed2ae516d45dfe26e934cb390b80f105ca780b1f`.

При обновлении прежний русский перевод используется как редакционная опора, а новый китайский оригинал остаётся источником содержания. Каждый фрагмент переводится и затем сверяется с китайским оригиналом двумя последовательными вызовами exact-модели `gpt-5.6-sol` через Codex app-server. Provider fallback и автоматическая замена модели запрещены.

## Локальная подготовка

~~~bash
uv sync --frozen --dev
mkdir -p .tmp
git clone --filter=blob:none --no-checkout https://github.com/bojieli/ai-agent-book.git .tmp/upstream
git -C .tmp/upstream fetch --depth=1 origin c3352738f4b6fe42fe34e3cf6a79bcb424a133b8
git -C .tmp/upstream checkout --detach c3352738f4b6fe42fe34e3cf6a79bcb424a133b8
~~~

## Проверки

~~~bash
uv run pytest -q
uv run ruff format --check scripts tests
uv run ruff check scripts tests
pyright scripts tests
~~~

Проверки структуры, ссылок, терминологии и извлечённого PDF-текста находятся в `scripts/`.

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json
uv run python scripts/check_links.py book
bash book/build_pdf.sh
# После проверки PDF из .tmp/pdf-build-v2.0/:
bash book/build_pdf.sh --promote
~~~

Сборка проверяет наличие Pandoc, XeLaTeX, Chrome, Poppler и необходимых TeX-пакетов, включая `xurl` для переноса длинных ссылок. Команда `--promote` сверяет контрольные суммы исходников и PDF перед копированием в `dist/`.

Генераторы `book/gen_*_figs.py` сохранены для версии 1.2. Не запускайте их поверх иллюстраций 2.0: новая сборка использует локализованные SVG из `book/images/`, зафиксированные в `asset-translation-manifest.json`.

## Атрибуция и лицензия

Оригинальная работа принадлежит Bojie Li. Русские файлы являются изменённым производным произведением. Условия распространения приведены в [LICENSE](LICENSE), сведения об изменениях — в [NOTICE](NOTICE).
