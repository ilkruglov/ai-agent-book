# AI-агенты изнутри: принципы проектирования и инженерная практика

Русский перевод: community edition.

Независимый русский перевод книги Bojie Li «深入理解 AI Agent：设计原理与工程实践». Перевод выполняется напрямую с китайского оригинала и не является официальным изданием автора.

## Зафиксированный источник

- Репозиторий: <https://github.com/bojieli/ai-agent-book>
- Версия: `v1.2`
- Коммит: `97de455e9aa44cf9f93441ce0c771c9aa9643d92`
- Исходный каталог: `book/`
- Лицензия: Apache License 2.0

Китайские Markdown-исходники не хранятся в Git этого репозитория. Для сверки они загружаются в игнорируемый каталог `.tmp/upstream/`.

## Статус

Идёт подготовка перевода `v1.2-ru.1`. Каждый фрагмент переводится и затем сверяется с китайским оригиналом двумя последовательными вызовами exact-модели `gpt-5.6-sol` через Codex app-server. Provider fallback и автоматическая замена модели запрещены.

## Локальная подготовка

~~~bash
uv sync --frozen --dev
mkdir -p .tmp
git clone --filter=blob:none --no-checkout https://github.com/bojieli/ai-agent-book.git .tmp/upstream
git -C .tmp/upstream fetch --depth=1 origin 97de455e9aa44cf9f93441ce0c771c9aa9643d92
git -C .tmp/upstream checkout --detach 97de455e9aa44cf9f93441ce0c771c9aa9643d92
~~~

## Проверки

~~~bash
uv run pytest -q
uv run ruff format --check scripts tests
uv run ruff check scripts tests
pyright scripts tests
~~~

После появления рукописи и PDF добавятся строгие проверки структуры, ссылок, терминологии и извлечённого PDF-текста. Итоговый артефакт будет находиться по пути `dist/AI-Agents-in-Depth-RU-v1.2.pdf`.

## Атрибуция и лицензия

Оригинальная работа принадлежит Bojie Li. Русские файлы являются изменённым производным произведением. Условия распространения приведены в [LICENSE](LICENSE), сведения об изменениях — в [NOTICE](NOTICE).
