# План реализации русского издания книги об AI-агентах

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Цель:** Выпустить воспроизводимое русское community-издание книги Bojie Li версии `v1.2` с 12 переведёнными Markdown-файлами, локализованными схемами, проверками качества и PDF.

**Архитектура:** Китайский upstream зафиксирован коммитом `97de455e9aa44cf9f93441ce0c771c9aa9643d92` и существует только в `.tmp/upstream/`. В Git хранятся русские тексты, контрольный manifest, глоссарий, детерминированные проверки, локализованные генераторы и проверенный PDF. Перевод выполняет только `gpt-5.6-sol`; `claude-opus-4-8` независимо проверяет смысл. Массовый перевод заблокирован до пользовательского решения по blind benchmark.

**Стек:** Git, Python 3.12, `uv`, PyYAML, JSON Schema, pytest, Ruff, Pyright/LSP, Codex CLI, Claude Code, Pandoc, XeLaTeX, ElegantBook, Lua, `rsvg-convert`, Poppler.

**Дизайн:** `docs/superpowers/specs/2026-07-20-russian-translation-design.md`

---

## Общие ограничения выполнения

- Источником перевода служит только китайский каталог `book/` указанного коммита. `book-en/` используется только как технический образец PDF-сборки.
- Китайские Markdown-файлы и полные китайские фрагменты не добавляются в Git. Они допустимы только под `.tmp/`.
- Model IDs неизменны: `gpt-5.6-sol` и `claude-opus-4-8`. Alias, fallback и автоматическая замена модели запрещены.
- Все текстовые правки в отслеживаемых файлах выполняются через `apply_patch`. Копирование неизменённых бинарных изображений и продвижение проверенных сгенерированных SVG/PDF считаются механическими операциями.
- Python меняется по TDD: сначала наблюдать ожидаемое падение узкого теста, затем минимальная реализация, полный тест и статическая проверка.
- Для навигации по Python использовать Pyright/LSP: определения, ссылки и типы. `rg` допустим только для инвентаризации текста и файлов.
- Перед benchmark-batch, генерацией 77 схем и PDF-сборкой выполнять:

  ~~~bash
  free -h
  ps -eo pid,pcpu,pmem,rss,cmd --sort=-rss | head -20
  ~~~

- Ничего не устанавливать в ОС без отдельного явного разрешения пользователя.
- После каждого зелёного этапа делать explanatory commit. Не выполнять `push`, не создавать tag и release без отдельной команды пользователя.
- Если тест падает неожиданно, применить `superpowers:systematic-debugging`; перед заявлением о готовности — `superpowers:verification-before-completion`.

## Задача 1: Воспроизводимый каркас и pinned upstream

**Файлы:**

- Создать: `.gitignore`
- Создать: `.python-version`
- Создать: `pyproject.toml`
- Создать: `README.md`
- Создать: `LICENSE`
- Создать: `NOTICE`
- Создать: `upstream.json`
- Создать: `glossary.yml`
- Создать: `scripts/__init__.py`
- Создать: `tests/test_project_metadata.py`
- Создать: `uv.lock`

- [ ] **Шаг 1: Добавить падающие metadata-тесты**

`tests/test_project_metadata.py` должен проверять:

1. `upstream.json` содержит URL, commit, `v1.2`, `book` и ровно 12 Markdown-записей.
2. Пути и Git blob SHA-1 совпадают с таблицей ниже.
3. `book/images` имеет tree SHA-1 `b0d9cbe7700caa4a8d5eff9fe9cc929d03756cfd`, ожидаемое число файлов `133`, а manifest содержит path, Git blob SHA-1 и size каждого asset.
4. `.tmp/probe` игнорируется Git.
5. `git ls-files .tmp` возвращает пустой список.
6. `README.md`, `NOTICE` и `glossary.yml` содержат строку `Русский перевод: community edition`.
7. `LICENSE` имеет Git blob SHA-1 `bd3e071f150cf46f86c91d3341d36644f16e11cb`.

Manifest Markdown:

| Path | Git blob SHA-1 | Bytes |
|---|---|---:|
| `book/introduction.md` | `edfd6ed34b3d14760cac5114cfb3622745a30969` | 20731 |
| `book/chapter1.md` | `fc40590687d38b2b330bd3035a3ea1cba30ea037` | 66344 |
| `book/chapter2.md` | `50db6e6945cb54a40de703795491f1a58eebaa12` | 134173 |
| `book/chapter3.md` | `8472fef633914e90be30b9b67b4dcdc15c576efc` | 106898 |
| `book/chapter4.md` | `d145d863e9106cd0ad69b543d64849eda50ef7ca` | 92542 |
| `book/chapter5.md` | `fe2c17b954d8165b1d490b0fde35d7ea76f1b6ed` | 113297 |
| `book/chapter6.md` | `2ea2974b75b8430e83a6b947ca59da111604b3c6` | 100135 |
| `book/chapter7.md` | `5e8421aec0a98672991dc693b0cc2ee604a65c43` | 136396 |
| `book/chapter8.md` | `0aa3a04b24ef65bfc3082ddb0e12ecadfcb4f104` | 67878 |
| `book/chapter9.md` | `9109acb6ac1a240e9a25fdb5ecf989f8bfbd02c2` | 91363 |
| `book/chapter10.md` | `0f608bcfcd12a6a73d392a0b44fe89acdae2c03b` | 98472 |
| `book/afterword.md` | `90dafce3240e7b1a6f1e2fefbc59bd54efe2c34f` | 11121 |

Запустить:

~~~bash
uv run --with 'pytest>=8.4,<9' pytest -q tests/test_project_metadata.py
~~~

Ожидается: падение из-за отсутствующих metadata-файлов проекта, а не из-за отсутствия pytest.

- [ ] **Шаг 2: Создать Python-конфигурацию**

Установить в `.python-version` значение `3.12`. В `pyproject.toml` определить:

- package name `ai-agent-book-ru-tools`, version `0.1.0`, `requires-python = ">=3.12,<3.13"`;
- runtime dependencies `PyYAML>=6.0.2,<7` and `jsonschema>=4.25,<5`;
- dev dependencies `pytest>=8.4,<9` and `ruff>=0.12,<1`;
- pytest `pythonpath = ["."]`;
- Ruff target `py312`, line length `100`, rules `E,F,I,UP,B,ANN`;
- Pyright `typeCheckingMode = "strict"`, includes `scripts`, `tests`, `book/gen_*_figs.py`, `book/gen_cover.py`, `book/svg_lib.py`.

Запустить:

~~~bash
uv lock
uv sync --dev
~~~

- [ ] **Шаг 3: Зафиксировать игнорируемые артефакты**

`.gitignore` должен включать `.tmp/`, `.venv/`, Python caches, pytest/Ruff caches и вспомогательные файлы XeLaTeX/Pandoc. `dist/*.pdf` игнорировать нельзя.

- [ ] **Шаг 4: Загрузить и проверить upstream snapshot**

~~~bash
mkdir -p .tmp
git clone --filter=blob:none --no-checkout https://github.com/bojieli/ai-agent-book.git .tmp/upstream
git -C .tmp/upstream fetch --depth=1 origin 97de455e9aa44cf9f93441ce0c771c9aa9643d92
git -C .tmp/upstream checkout --detach 97de455e9aa44cf9f93441ce0c771c9aa9643d92
test "$(git -C .tmp/upstream rev-parse HEAD)" = "97de455e9aa44cf9f93441ce0c771c9aa9643d92"
git -C .tmp/upstream fsck --no-dangling
~~~

Проверить все manifest blobs командой `git -C .tmp/upstream rev-parse HEAD:<path>`, а размеры — `git -C .tmp/upstream cat-file -s HEAD:<path>`. Любое расхождение останавливает задачу.

- [ ] **Шаг 5: Создать attribution, license, manifest и исходный глоссарий**

- Скопировать exact Apache-2.0 `LICENSE` из pinned snapshot.
- В `NOTICE` указать Bojie Li, upstream URL и commit, а также факт изменения русских файлов при переводе.
- В `README.md` указать русское название, `Русский перевод: community edition`, source/version, текущий статус, локальные команды проверки/сборки и license notice.
- `upstream.json` хранит таблицу Markdown, license blob, images tree/count, path/blob/size всех 133 assets, generator blob IDs и `book-en` build-support blob IDs. Эти данные позволяют проверять clean clone без `.tmp/upstream/`.
- `glossary.yml` использует schema version `1`. Каждая запись содержит `id`, список `source`, `preferred`, `rule` и список `forbidden`. Начальный набор включает согласованное правило `AI-агент`, а также общие термины: `LLM`, `prompt`, `token`, `context`, `context window`, `tool`, `tool call`, `memory`, `RAG`, `MCP`, `agent loop`, `inference`, `fine-tuning`, `reinforcement learning`, `reward`, `benchmark`, `latency`, `throughput`, `KV cache`, `prompt injection`.

Не объявлять русский вариант предпочтительным, пока он не проверен по pinned source. Такую запись помечать `status: candidate` и не применять её запреты до принятия при review benchmark.

- [ ] **Шаг 6: Получить зелёный baseline**

~~~bash
uv run pytest -q tests/test_project_metadata.py
uv run ruff format --check tests scripts
uv run ruff check tests scripts
pyright tests scripts
git diff --check
~~~

Ожидается: все проверки проходят.

- [ ] **Шаг 7: Коммит**

~~~bash
git add .gitignore .python-version pyproject.toml uv.lock README.md LICENSE NOTICE upstream.json glossary.yml scripts/__init__.py tests/test_project_metadata.py
git commit -m "chore: bootstrap pinned Russian translation project" -m "Record the exact v1.2 Chinese source, attribution, tooling, and glossary contract without tracking upstream prose."
~~~

## Задача 2: Структурный и терминологический валидатор

**Файлы:**

- Создать: `scripts/check_translation.py`
- Создать: `tests/test_check_translation.py`

- [ ] **Шаг 1: Написать падающие unit tests**

Использовать fixtures `tmp_path` с короткими парами source/target Markdown. Покрыть каждый случай независимо:

- совпадающая последовательность уровней заголовков проходит, хотя их текст различается;
- отсутствующий или лишний заголовок приводит к ошибке;
- несовпадение количества code fences, marker либо info-string приводит к ошибке;
- несовпадение последовательности image destinations приводит к ошибке, а переведённый alt text допустим;
- несовпадение числа разделителей таблиц приводит к ошибке;
- отсутствие точного уведомления о переводе приводит к ошибке;
- CJK в prose приводит к ошибке;
- CJK внутри `<!-- cjk-allow: reason="..." -->` / `<!-- /cjk-allow -->` разрешён;
- пустой allow reason приводит к ошибке;
- запрещённое написание из accepted glossary приводит к ошибке;
- запись `status: candidate` не применяется принудительно;
- `--only chapter2.md` проверяет только эту пару;
- PDF text без русского названия, любого H1 книги либо с `U+FFFD` приводит к ошибке.

Запустить:

~~~bash
uv run pytest -q tests/test_check_translation.py
~~~

Ожидается: ошибка импорта, потому что `scripts.check_translation` ещё не существует.

- [ ] **Шаг 2: Реализовать typed parser and validator**

Реализовать следующие публичные интерфейсы с явными типами:

- `MarkdownShape`: frozen dataclass с уровнями/текстом заголовков, fences, числом таблиц и image destinations;
- `ValidationIssue`: frozen dataclass с `path`, `line`, `code`, `message`;
- `CjkOccurrence`: frozen dataclass с `line`, `text`;
- `find_cjk(text: str) -> list[CjkOccurrence]`;
- `parse_markdown(text: str) -> MarkdownShape`;
- `load_glossary(path: Path) -> tuple[GlossaryTerm, ...]`;
- `validate_translation(source_path: Path, target_path: Path, terms: tuple[GlossaryTerm, ...]) -> list[ValidationIssue]`;
- `validate_pdf_text(pdf_text: str, expected_h1: tuple[str, ...]) -> list[ValidationIssue]`;
- `main(argv: Sequence[str] | None = None) -> int`.

Использовать диапазоны CJK `U+3400–U+4DBF`, `U+4E00–U+9FFF`, `U+F900–U+FAFF`. Разбирать fences до заголовков, изображений и таблиц, чтобы Markdown-подобный код не влиял на структуру. Требовать точное уведомление:

~~~html
<!-- Русский перевод: community edition. Источник: https://github.com/bojieli/ai-agent-book; файл изменён относительно upstream. -->
~~~

CLI contract:

~~~text
python scripts/check_translation.py --source SOURCE_DIR --target TARGET_DIR --glossary FILE [--only FILE]... [--pdf-text FILE]
~~~

При отсутствующем source, target или glossary возвращать код `2`; при findings — `1`; при успехе — `0`. Не продолжать структурную проверку без source.

- [ ] **Шаг 3: Проверка**

~~~bash
uv run pytest -q tests/test_check_translation.py
uv run ruff format scripts/check_translation.py tests/test_check_translation.py
uv run ruff check scripts/check_translation.py tests/test_check_translation.py
pyright scripts/check_translation.py tests/test_check_translation.py
git diff --check
~~~

Ожидается: все проверки проходят.

- [ ] **Шаг 4: Коммит**

~~~bash
git add scripts/check_translation.py tests/test_check_translation.py
git commit -m "feat: validate translation structure and terminology" -m "Fail closed on source drift, Markdown shape changes, undocumented CJK, glossary violations, and damaged PDF text."
~~~

## Задача 3: Локальные ссылки, изображения и якоря

**Файлы:**

- Создать: `scripts/check_links.py`
- Создать: `tests/test_check_links.py`

- [ ] **Шаг 1: Написать падающие tests**

Покрыть локальные `.md` links, image paths, anchors того же файла и других файлов, суффиксы повторяющихся GitHub-style anchors, percent-decoding, кириллические заголовки и ссылки внутри code fences. Проверить, что HTTP(S), `mailto:` и внешние URL без fragment пропускаются без network request. Любая ссылка на `.tmp/upstream`, `book-zh` либо абсолютный filesystem path должна приводить к ошибке.

Add two modes:

- строгий режим по умолчанию: каждый локальный destination и anchor должен существовать;
- `--partial-manifest upstream.json`: links на один из 12 заявленных, но ещё не переведённых Markdown-файлов выводятся как информационные и не приводят к ошибке; images и anchors существующих файлов остаются строгими.

Запустить:

~~~bash
uv run pytest -q tests/test_check_links.py
~~~

Ожидается: ошибка импорта.

- [ ] **Шаг 2: Реализовать checker**

Публичные интерфейсы:

- `LinkIssue`: frozen dataclass с `path`, `line`, `code`, `target`;
- `github_anchor(text: str, occurrence: int) -> str` preserving Unicode letters and numbers;
- `collect_anchors(markdown: str) -> set[str]`;
- `check_book(root: Path, only: tuple[Path, ...], partial_manifest: Path | None) -> list[LinkIssue]`;
- `main(argv: Sequence[str] | None = None) -> int`.

CLI:

~~~text
python scripts/check_links.py BOOK_DIR [--only FILE]... [--partial-manifest FILE]
~~~

- [ ] **Шаг 3: Проверка и коммит**

~~~bash
uv run pytest -q tests/test_check_links.py
uv run ruff format scripts/check_links.py tests/test_check_links.py
uv run ruff check scripts/check_links.py tests/test_check_links.py
pyright scripts/check_links.py tests/test_check_links.py
git diff --check
git add scripts/check_links.py tests/test_check_links.py
git commit -m "feat: validate Russian book links and assets" -m "Check local Markdown targets, Unicode anchors, and image paths without relying on network access."
~~~

## Задача 4: Безопасные model runners и chunking

**Файлы:**

- Создать: `scripts/markdown_chunks.py`
- Создать: `scripts/model_runner.py`
- Создать: `scripts/translate_file.py`
- Создать: `scripts/review_file.py`
- Создать: `prompts/translate.txt`
- Создать: `prompts/review.txt`
- Создать: `prompts/review.schema.json`
- Создать: `tests/test_markdown_chunks.py`
- Создать: `tests/test_model_runner.py`
- Создать: `tests/test_translate_file.py`
- Создать: `tests/test_review_file.py`

- [ ] **Шаг 1: TDD для lossless chunking**

Тесты должны доказать, что `split_markdown(text: str, max_chars: int) -> tuple[MarkdownChunk, ...]`:

- повторное объединение byte-for-byte совпадает с исходным текстом;
- сначала предпочитаются границы H2, затем H3;
- разбиение не происходит внутри fenced block, Markdown table или HTML comment;
- назначаются устойчивые zero-padded indices и source line ranges;
- при превышении `max_chars` одним неделимым блоком возникает typed error.

Запустить тест и зафиксировать ошибку импорта, затем реализовать frozen `MarkdownChunk(index, start_line, end_line, text, sha256)` и получить зелёный прогон.

- [ ] **Шаг 2: TDD для exact model commands**

Тесты должны сверять точные массивы аргументов и отклонять незаявленную модель либо output вне `.tmp/` репозитория.

Codex command:

~~~text
codex exec -m gpt-5.6-sol -s read-only -C /home/ikruglov/ai-agent-book-ru --ephemeral --ignore-user-config --json -o OUTPUT -
~~~

Claude command:

~~~text
claude -p --model claude-opus-4-8 --safe-mode --no-session-persistence --tools "" --permission-mode dontAsk --output-format json
~~~

Implement:

- `ModelName = Literal["gpt-5.6-sol", "claude-opus-4-8"]`;
- frozen `ModelSpec`, `RuntimeEvidence`, `ModelResult` dataclasses;
- `build_command(model: ModelName, repo_root: Path, output_path: Path) -> tuple[str, ...]`;
- `run_model(model: ModelName, prompt: str, repo_root: Path, output_path: Path, timeout_seconds: int) -> ModelResult`.

`run_model` передаёт prompt только через stdin, захватывает stderr/stdout, сохраняет SHA-256 и runtime completion evidence и никогда не повторяет запрос другой моделью. Ненулевой exit, timeout, отсутствующий response, отсутствие completion/usage evidence либо model metadata, не согласующиеся с запрошенным exact ID, считаются фатальными.

- [ ] **Шаг 3: TDD для translation orchestration**

Тесты с mock `run_model` должны доказать:

- source читается только из `.tmp/upstream/book/`;
- translation собирается только под `.tmp/drafts/`;
- каждый chunk получает одинаковый accepted glossary, а также собственные path/hash/line range;
- model output с лишним внешним code fence отклоняется;
- собранный draft должен пройти shape-сравнение `parse_markdown` до успешного завершения;
- full-book translation не запускается, пока `evals/translation-benchmark.json` не содержит `decision.approved_primary = true` и primary model `gpt-5.6-sol`.

Использовать по умолчанию `max_chars=40000`, не разрывать блоки кода, таблиц и комментариев, а в тестах разрешить явное меньшее значение.

- [ ] **Шаг 4: TDD для независимого review**

`tests/test_review_file.py` с mock runtime проверяет, что `review_file.py` принимает только `claude-opus-4-8`, выравнивает source/translation chunks по структуре, пишет только в `.tmp/reviews/`, проверяет ответ по `prompts/review.schema.json` и отклоняет неизвестные поля, неверные hashes и line ranges вне chunk.

- [ ] **Шаг 5: Создать translation/review prompts**

`prompts/translate.txt` требует прямой перевод с китайского на естественный технический русский, точную Markdown-структуру, неизменные code/machine identifiers, соблюдение glossary, отсутствие пропусков/добавлений, русские подписи и output только с переведённым chunk.

`prompts/review.txt` явно запрещает переписывать главу целиком. Он требует issues, подтверждённые source, с категориями `semantic`, `omission`, `addition`, `russian`, `terminology`, `markdown`; severities `critical`, `major`, `minor`; source/target line ranges; кратким evidence и предложенной русской заменой.

`prompts/review.schema.json` is strict JSON Schema: no additional properties, all fields required, and top-level fields `source_sha256`, `translation_sha256`, `model_id`, `issues`.

- [ ] **Шаг 6: Проверка**

~~~bash
uv run pytest -q tests/test_markdown_chunks.py tests/test_model_runner.py tests/test_translate_file.py tests/test_review_file.py
uv run ruff format scripts tests
uv run ruff check scripts tests
pyright scripts tests
git diff --check
~~~

Ожидается: все проверки проходят. Prompt-файлы в plain text/JSON не передаются Ruff.

- [ ] **Шаг 7: Коммит**

~~~bash
git add scripts/markdown_chunks.py scripts/model_runner.py scripts/translate_file.py scripts/review_file.py prompts/translate.txt prompts/review.txt prompts/review.schema.json tests/test_markdown_chunks.py tests/test_model_runner.py tests/test_translate_file.py tests/test_review_file.py
git commit -m "feat: pin translation and review model runners" -m "Use lossless Markdown chunks, exact model IDs, read-only runtimes, and fail-closed output validation with no fallback."
~~~

## Задача 5: Blind benchmark и блокирующий user gate

**Файлы:**

- Создать: `scripts/benchmark.py`
- Создать: `tests/test_benchmark.py`
- Создать: `prompts/benchmark_review.txt`
- Создать: `prompts/benchmark_review.schema.json`
- Создать после согласования: `evals/translation-benchmark.json`

- [ ] **Шаг 1: Зафиксировать 20 sample specifications в тесте и runner**

| ID | Source range |
|---|---|
| `B01` | `book/introduction.md:1-20` |
| `B02` | `book/chapter1.md:11-40` |
| `B03` | `book/chapter1.md:227-268` |
| `B04` | `book/chapter2.md:32-83` |
| `B05` | `book/chapter2.md:486-537` |
| `B06` | `book/chapter2.md:653-686` |
| `B07` | `book/chapter3.md:90-119` |
| `B08` | `book/chapter3.md:417-456` |
| `B09` | `book/chapter4.md:39-87` |
| `B10` | `book/chapter4.md:345-396` |
| `B11` | `book/chapter5.md:90-143` |
| `B12` | `book/chapter5.md:333-370` |
| `B13` | `book/chapter6.md:280-330` |
| `B14` | `book/chapter6.md:516-529` |
| `B15` | `book/chapter7.md:70-100` |
| `B16` | `book/chapter7.md:480-543` |
| `B17` | `book/chapter8.md:234-280` |
| `B18` | `book/chapter9.md:190-225` |
| `B19` | `book/chapter9.md:448-493` |
| `B20` | `book/chapter10.md:235-284` |

Тесты проверяют точные диапазоны, parent blob IDs из `upstream.json`, hashes извлечений, отсутствие китайского текста в tracked output, устойчивую A/B-анонимизацию, пять критериев только со значениями `0/1/2` и все три условия gate.

- [ ] **Шаг 2: Реализовать benchmark state machine**

Команды:

~~~text
python scripts/benchmark.py prepare --upstream .tmp/upstream --work .tmp/benchmark
python scripts/benchmark.py smoke --work .tmp/benchmark
python scripts/benchmark.py run --work .tmp/benchmark --batch-size 5
python scripts/benchmark.py report --work .tmp/benchmark --output .tmp/benchmark/report.md
python scripts/benchmark.py finalize --work .tmp/benchmark --decision .tmp/benchmark/decision.json --output .tmp/translation-benchmark.json
~~~

Правила состояний:

1. `prepare` извлекает source в `.tmp/benchmark/source/`, записывает SHA-256 и создаёт secret A/B mapping под `.tmp/`; повторный `prepare` не должен незаметно заменять существующие результаты.
2. `smoke` отправляет nonce-запрос каждой exact model. Он записывает команду, requested ID, runtime completion evidence и возвращённые model metadata. Отсутствующий либо противоречивый evidence приводит к ошибке.
3. `run` переводит каждый фрагмент обеими моделями, затем просит обе модели независимо оценить анонимные варианты A/B. Prompts содержат одинаковые source и accepted glossary.
4. Scores покрывают смысловую точность, пропуски/добавления, естественность русского языка, glossary и Markdown-структуру. Каждый критерий — целое число `0`, `1` либо `2`.
5. При расхождении двух judges по критерию final score остаётся unresolved; `decision.json` должен содержать итоговую целочисленную оценку пользователя. Максимум варианта остаётся `200`.
6. `report` показывает русские тексты A/B, deterministic shape findings, оценки обоих judges, расхождения и critical-error evidence, но не раскрывает личности до финального раздела сравнения.
7. `finalize` отклоняет unresolved scores и записывает source path/range/hash, русские варианты, exact model IDs/settings/evidence, final scores, critical flags, gate evaluation и user decision. Китайский source text не записывается.

Gate блокирует primary при любом условии:

- варианту `gpt-5.6-sol` назначена хотя бы одна critical error;
- `gpt_total <= opus_total - 10`;
- `gpt-5.6-sol` имеет более низкую semantic score минимум на пяти samples.

- [ ] **Шаг 3: Проверить реализацию без вызовов моделей**

~~~bash
uv run pytest -q tests/test_benchmark.py
uv run ruff format scripts/benchmark.py tests/test_benchmark.py
uv run ruff check scripts/benchmark.py tests/test_benchmark.py
pyright scripts/benchmark.py tests/test_benchmark.py
git diff --check
~~~

- [ ] **Шаг 4: Выполнить реальный benchmark ограниченными batches**

Сначала проверить load и RAM общими командами. Затем:

~~~bash
uv run python scripts/benchmark.py prepare --upstream .tmp/upstream --work .tmp/benchmark
uv run python scripts/benchmark.py smoke --work .tmp/benchmark
uv run python scripts/benchmark.py run --work .tmp/benchmark --batch-size 5
uv run python scripts/benchmark.py report --work .tmp/benchmark --output .tmp/benchmark/report.md
~~~

После каждого batch сообщать число завершённых samples, failures и остаток. Немедленно остановиться, если любая exact model недоступна либо runtime identity evidence недостаточен.

- [ ] **Шаг 5: СТОП — передать report пользователю**

Не создавать `evals/translation-benchmark.json`, не коммитить benchmark и не начинать Задачу 7. Передать пользователю расхождения оценок и запросить явное принятие либо отклонение `gpt-5.6-sol` как primary. Записать ответ в `.tmp/benchmark/decision.json`: `approved_primary`, итоговые оценки критериев, время решения и краткое обоснование.

- [ ] **Шаг 6: Финализировать только после явного согласования**

~~~bash
uv run python scripts/benchmark.py finalize --work .tmp/benchmark --decision .tmp/benchmark/decision.json --output .tmp/translation-benchmark.json
uv run python -c 'from pathlib import Path; from scripts.check_translation import find_cjk; text=Path(".tmp/translation-benchmark.json").read_text(); assert not find_cjk(text)'
~~~

Полностью проверить JSON, затем добавить его проверенное содержимое в `evals/translation-benchmark.json` через `apply_patch`.

- [ ] **Шаг 7: Закоммитить benchmark tooling и принятый результат**

~~~bash
git add scripts/benchmark.py tests/test_benchmark.py prompts/benchmark_review.txt prompts/benchmark_review.schema.json evals/translation-benchmark.json glossary.yml
git commit -m "test: gate translation with a blind model benchmark" -m "Record source hashes, exact runtime evidence, anonymous comparisons, conservative scores, and the user's primary-model decision."
~~~

Если gate отклоняет primary, остановиться с незакоммиченными benchmark files до согласования пользователем новых настроек либо нового дизайна.

## Задача 6: Импорт pinned assets и технической PDF-базы

**Файлы:**

- Создать: `book/images/*` (133 pinned upstream assets)
- Создать: `book/gen_ch1_figs.py`
- Создать: `book/gen_ch2_figs.py`
- Создать: `book/gen_ch3_figs.py`
- Создать: `book/gen_ch4_figs.py`
- Создать: `book/gen_ch5_figs.py`
- Создать: `book/gen_ch8_figs.py`
- Создать: `book/gen_ch9_figs.py`
- Создать: `book/gen_cover.py`
- Создать: `book/svg_lib.py`
- Создать: `book/build_pdf.sh`
- Создать: `book/preamble.tex`
- Создать: `book/cover.tex`
- Создать: `book/crossref.lua`
- Создать: `book/experiment_box.lua`
- Создать: `tests/test_pinned_assets.py`

- [ ] **Шаг 1: Добавить падающий asset-manifest test**

Тест проверяет 133 файла и их source hashes из `upstream.json`, семь генераторов глав, `gen_cover.py`, `svg_lib.py` и пять PDF support files из `book-en`. Проверка работает без `.tmp/upstream/`: для imported paths она вычисляет текущий Git blob SHA-1. Она также подтверждает, что upstream `.md` не скопированы.

- [ ] **Шаг 2: Механически скопировать exact pinned files**

Механически скопировать `book/images/`, generators и `svg_lib.py` из `.tmp/upstream/book/`. Из `.tmp/upstream/book-en/` скопировать только `build_pdf.sh`, `preamble.tex`, `cover.tex`, `crossref.lua`, `experiment_box.lua`. `gen_cover.py` взять из pinned Chinese tree `book/`. В этой задаче ничего не исполнять и не локализовать.

- [ ] **Шаг 3: Проверить provenance**

~~~bash
uv run pytest -q tests/test_pinned_assets.py
test "$(find book/images -type f | wc -l)" -eq 133
test -z "$(find book -maxdepth 1 -name '*.md' -print)"
git diff --check
~~~

- [ ] **Шаг 4: Коммит**

~~~bash
git add book tests/test_pinned_assets.py
git commit -m "assets: import pinned v1.2 book resources" -m "Bring in the exact upstream images and generators plus the English build plumbing, without copying translated prose."
~~~

## Задача 7: Перевод `introduction.md`

**Файлы:**

- Создать: `book/introduction.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/introduction.md`, `.tmp/reviews/introduction.json`

- [ ] **Шаг 1: Проверить benchmark gate и подготовить термины**

Убедиться, что `evals/translation-benchmark.json` содержит `approved_primary: true`, exact primary `gpt-5.6-sol` и отсутствие blocking gate. Сверить каждый glossary candidate введения со всеми вхождениями в pinned source; переводить из `candidate` в `accepted` только через `apply_patch`.

- [ ] **Шаг 2: Получить GPT draft и наблюдать ожидаемое отсутствие tracked target**

~~~bash
test ! -e book/introduction.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/introduction.md --output .tmp/draft-book/introduction.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only introduction.md
~~~

Ожидается: model run и структурная проверка проходят; `book/introduction.md` всё ещё отсутствует.

- [ ] **Шаг 3: Проверить и добавить reviewed draft**

Сравнить draft и source по разделам, особенно название, границы издания, утверждения автора и вводные определения. Добавить полный русский файл через `apply_patch`; сохранить точное уведомление и позиции всех изображений, блоков кода и таблиц.

- [ ] **Шаг 4: Независимый Opus review и подтверждённые source исправления**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/introduction.md --translation book/introduction.md --glossary glossary.yml --output .tmp/reviews/introduction.json --model claude-opus-4-8
~~~

Для каждого finding заново открыть соответствующий диапазон китайского source, принять через `apply_patch` только подтверждённые исправления и повторить review изменённых chunks. Неразрешённых issues `critical` или `major` остаться не должно.

- [ ] **Шаг 5: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only introduction.md
uv run python scripts/check_links.py book --only introduction.md --partial-manifest upstream.json
git diff --check
git add book/introduction.md glossary.yml
git commit -m "docs(book): translate the introduction into Russian" -m "Translate directly from the pinned Chinese v1.2 source and apply source-verified independent review findings."
~~~

## Задача 8: Перевод `chapter1.md`

**Файлы:**

- Создать: `book/chapter1.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter1.md`, `.tmp/reviews/chapter1.json`

- [ ] **Шаг 1: Подготовить терминологию главы**

Проверить во всей главе употребление `AI Agent`, agent paradigm, agent harness, понятий model/training/inference и системных компонентов. До генерации принять один русский вариант для каждого понятия; неопределённые candidates принудительно не применять.

- [ ] **Шаг 2: Получить draft и выполнить структурную red/green-проверку**

~~~bash
test ! -e book/chapter1.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter1.md --output .tmp/draft-book/chapter1.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter1.md
~~~

Добавить полный проверенный draft в `book/chapter1.md` через `apply_patch`. Сверить по source определения, причинно-следственные утверждения и каждую ссылку на `fig1-1`–`fig1-10`.

- [ ] **Шаг 3: Независимый review и исправления**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter1.md --translation book/chapter1.md --glossary glossary.yml --output .tmp/reviews/chapter1.json --model claude-opus-4-8
~~~

Устранять findings только после проверки указанных китайских строк. Повторять review каждого изменённого chunk до отсутствия unresolved issues `critical` и `major`.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter1.md
uv run python scripts/check_links.py book --only chapter1.md --partial-manifest upstream.json
git diff --check
git add book/chapter1.md glossary.yml
git commit -m "docs(book): translate chapter 1 into Russian" -m "Preserve the chapter structure, agent-system definitions, code, and figure references from the pinned Chinese source."
~~~

## Задача 9: Перевод `chapter2.md`

**Файлы:**

- Создать: `book/chapter2.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter2.md`, `.tmp/reviews/chapter2.json`

- [ ] **Шаг 1: Подготовить терминологию главы**

Проверить и принять единообразные варианты для понятий LLM API/context, `prefill`, `decode`, `KV cache`, latency/throughput, context window и prompt injection. Имена API и protocol tokens сохранить без изменений.

- [ ] **Шаг 2: Получить draft и выполнить структурную проверку**

~~~bash
test ! -e book/chapter2.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter2.md --output .tmp/draft-book/chapter2.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter2.md
~~~

Добавить проверенный draft через `apply_patch`. Вручную сравнить формулы, числовые примеры, таблицы, security negations и ссылки `fig2-1`–`fig2-11`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter2.md --translation book/chapter2.md --glossary glossary.yml --output .tmp/reviews/chapter2.json --model claude-opus-4-8
~~~

Каждое предложенное исправление сверить с source и повторно проверить изменённые chunks. Critical смысловые инверсии, потерянные ограничения и изменённые machine strings блокируют commit.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter2.md
uv run python scripts/check_links.py book --only chapter2.md --partial-manifest upstream.json
git diff --check
git add book/chapter2.md glossary.yml
git commit -m "docs(book): translate chapter 2 into Russian" -m "Translate the LLM runtime, context, cache, and prompt-security material with source-verified terminology."
~~~

## Задача 10: Перевод `chapter3.md`

**Файлы:**

- Создать: `book/chapter3.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter3.md`, `.tmp/reviews/chapter3.json`

- [ ] **Шаг 1: Подготовить терминологию memory и retrieval**

Проверить во всей source-главе термины short-/long-term memory, retrieval, embedding, vector database, chunking и RAG. Product/API identifiers сохранить.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter3.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter3.md --output .tmp/draft-book/chapter3.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter3.md
~~~

Сравнить алгоритмы retrieval, утверждения о ranking, формулы, ячейки таблиц и `fig3-1`–`fig3-14`; затем добавить полный файл через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter3.md --translation book/chapter3.md --glossary glossary.yml --output .tmp/reviews/chapter3.json --model claude-opus-4-8
~~~

Исправлять только подтверждённые source findings и повторять review изменённых chunks до устранения unresolved high-severity issues.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter3.md
uv run python scripts/check_links.py book --only chapter3.md --partial-manifest upstream.json
git diff --check
git add book/chapter3.md glossary.yml
git commit -m "docs(book): translate chapter 3 into Russian" -m "Preserve memory and retrieval semantics, examples, tables, and all source figure references."
~~~

## Задача 11: Перевод `chapter4.md`

**Файлы:**

- Создать: `book/chapter4.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter4.md`, `.tmp/reviews/chapter4.json`

- [ ] **Шаг 1: Подготовить tool-runtime терминологию**

Check tool definition/call/result, schema, orchestration, concurrency, asynchronous execution, timeout, retry and idempotency terminology. Do not translate JSON keys, function names or status values.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter4.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter4.md --output .tmp/draft-book/chapter4.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter4.md
~~~

Проверить async ordering, error branches, code comments, schemas и `fig4-1`–`fig4-12`; добавить полный русский файл через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter4.md --translation book/chapter4.md --glossary glossary.yml --output .tmp/reviews/chapter4.json --model claude-opus-4-8
~~~

Проверить все принятые правки по китайским source line ranges и повторить review изменённых chunks.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter4.md
uv run python scripts/check_links.py book --only chapter4.md --partial-manifest upstream.json
git diff --check
git add book/chapter4.md glossary.yml
git commit -m "docs(book): translate chapter 4 into Russian" -m "Translate tool design and asynchronous execution while preserving schemas, code, and error semantics."
~~~

## Задача 12: Перевод `chapter5.md`

**Файлы:**

- Создать: `book/chapter5.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter5.md`, `.tmp/reviews/chapter5.json`

- [ ] **Шаг 1: Подготовить терминологию security и coding agents**

Проверить термины sandbox, permission, trust boundary, prompt injection, file edit, patch, repository и coding agent. Точно сохранить смысл путей, команд, identifiers и security modal verbs.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter5.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter5.md --output .tmp/draft-book/chapter5.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter5.md
~~~

Сравнить каждое security-ограничение, пример файловой операции, code block и `fig5-1`–`fig5-11`; добавить полный файл через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter5.md --translation book/chapter5.md --glossary glossary.yml --output .tmp/reviews/chapter5.json --model claude-opus-4-8
~~~

Treat negation, permission scope, attack preconditions and command changes as critical review points. Recheck and re-review all corrected chunks.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter5.md
uv run python scripts/check_links.py book --only chapter5.md --partial-manifest upstream.json
git diff --check
git add book/chapter5.md glossary.yml
git commit -m "docs(book): translate chapter 5 into Russian" -m "Preserve coding-agent workflows and security boundaries without changing executable examples."
~~~

## Задача 13: Перевод `chapter6.md`

**Файлы:**

- Создать: `book/chapter6.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter6.md`, `.tmp/reviews/chapter6.json`

- [ ] **Шаг 1: Подготовить терминологию evaluation**

Check benchmark, dataset, metric, judge, rubric, variance, confidence interval, statistical significance, pass rate and contamination terms. Keep formula symbols and metric names unchanged.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter6.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter6.md --output .tmp/draft-book/chapter6.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter6.md
~~~

Сверить с source все знаменатели, проценты, статистические qualifiers, обозначения формул и таблицы; добавить проверенный файл через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter6.md --translation book/chapter6.md --glossary glossary.yml --output .tmp/reviews/chapter6.json --model claude-opus-4-8
~~~

Любое изменённое число, направление сравнения или утверждение о неопределённости считать critical до проверки по source. Повторить review изменённых chunks.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter6.md
uv run python scripts/check_links.py book --only chapter6.md --partial-manifest upstream.json
git diff --check
git add book/chapter6.md glossary.yml
git commit -m "docs(book): translate chapter 6 into Russian" -m "Translate agent evaluation and statistical guidance with exact metrics, formulas, and qualifications."
~~~

## Задача 14: Перевод `chapter7.md`

**Файлы:**

- Создать: `book/chapter7.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter7.md`, `.tmp/reviews/chapter7.json`

- [ ] **Шаг 1: Подготовить терминологию training**

Проверить терминологию SFT, RL, policy, reward, trajectory, rollout, verifier, tool creation и training data. Сохранить algorithm/model/dataset identifiers и математические обозначения.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter7.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter7.md --output .tmp/draft-book/chapter7.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter7.md
~~~

Построчно проверить сравнение SFT/RL, направление reward, таблицы, алгоритмы и code blocks; добавить полный target через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter7.md --translation book/chapter7.md --glossary glossary.yml --output .tmp/reviews/chapter7.json --model claude-opus-4-8
~~~

Проверить каждое исправление по source; повторять review изменённых chunks до устранения high-severity findings.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter7.md
uv run python scripts/check_links.py book --only chapter7.md --partial-manifest upstream.json
git diff --check
git add book/chapter7.md glossary.yml
git commit -m "docs(book): translate chapter 7 into Russian" -m "Preserve training objectives, reward semantics, algorithms, and tool-learning examples from the source."
~~~

## Задача 15: Перевод `chapter8.md`

**Файлы:**

- Создать: `book/chapter8.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter8.md`, `.tmp/reviews/chapter8.json`

- [ ] **Шаг 1: Подготовить терминологию realtime agents**

Check realtime, streaming, interruption, turn-taking, speech-to-text, text-to-speech, endpointing, latency and multimodal terms. Keep API events and field names unchanged.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter8.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter8.md --output .tmp/draft-book/chapter8.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter8.md
~~~

Проверить event order, latency budgets, состояния голосового взаимодействия и `fig8-1`–`fig8-7`; добавить файл через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter8.md --translation book/chapter8.md --glossary glossary.yml --output .tmp/reviews/chapter8.json --model claude-opus-4-8
~~~

Resolve issues by source comparison and re-review all changed chunks.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter8.md
uv run python scripts/check_links.py book --only chapter8.md --partial-manifest upstream.json
git diff --check
git add book/chapter8.md glossary.yml
git commit -m "docs(book): translate chapter 8 into Russian" -m "Translate realtime interaction and multimodal pipelines while preserving event and API semantics."
~~~

## Задача 16: Перевод `chapter9.md`

**Файлы:**

- Создать: `book/chapter9.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter9.md`, `.tmp/reviews/chapter9.json`

- [ ] **Шаг 1: Подготовить терминологию embodied agents и robotics**

Проверить термины embodied agent, perception, planning, control, actuator, sensor, world model, simulation, policy и safety. Сохранить hardware/model identifiers и единицы измерения.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter9.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter9.md --output .tmp/draft-book/chapter9.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter9.md
~~~

Проверить причинность control loop, физические единицы, safety constraints и `fig9-1`–`fig9-12`; добавить полный файл через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter9.md --translation book/chapter9.md --glossary glossary.yml --output .tmp/reviews/chapter9.json --model claude-opus-4-8
~~~

Каждый исправленный chunk сверить с source и повторно проверить; изменения физического направления, единиц или safety считаются critical.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter9.md
uv run python scripts/check_links.py book --only chapter9.md --partial-manifest upstream.json
git diff --check
git add book/chapter9.md glossary.yml
git commit -m "docs(book): translate chapter 9 into Russian" -m "Preserve embodied-agent control, robotics terminology, units, and safety constraints."
~~~

## Задача 17: Перевод `chapter10.md`

**Файлы:**

- Создать: `book/chapter10.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/chapter10.md`, `.tmp/reviews/chapter10.json`

- [ ] **Шаг 1: Подготовить multi-agent терминологию**

Проверить термины multi-agent system, coordination, communication, protocol, role, delegation, consensus, competition, topology и shared state. Сохранить protocol messages, identifiers и названия упомянутых систем.

- [ ] **Шаг 2: Получить, проверить и добавить draft**

~~~bash
test ! -e book/chapter10.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter10.md --output .tmp/draft-book/chapter10.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only chapter10.md
~~~

Проверить роли agents, направления сообщений, coordination failure modes, код и таблицы; добавить проверенный target через `apply_patch`.

- [ ] **Шаг 3: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/chapter10.md --translation book/chapter10.md --glossary glossary.yml --output .tmp/reviews/chapter10.json --model claude-opus-4-8
~~~

Устранять только подтверждённые source issues и повторять review изменённых chunks до отсутствия high-severity findings.

- [ ] **Шаг 4: Проверка и коммит**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --only chapter10.md
uv run python scripts/check_links.py book --only chapter10.md --partial-manifest upstream.json
git diff --check
git add book/chapter10.md glossary.yml
git commit -m "docs(book): translate chapter 10 into Russian" -m "Translate multi-agent coordination and communication without changing protocol or system semantics."
~~~

## Задача 18: Перевод `afterword.md` и строгая проверка всех 12 файлов

**Файлы:**

- Создать: `book/afterword.md`
- Изменять при необходимости: `glossary.yml`
- Только временно: `.tmp/draft-book/afterword.md`, `.tmp/reviews/afterword.json`

- [ ] **Шаг 1: Получить и добавить draft послесловия**

~~~bash
test ! -e book/afterword.md
uv run python scripts/translate_file.py --source .tmp/upstream/book/afterword.md --output .tmp/draft-book/afterword.md --glossary glossary.yml --model gpt-5.6-sol
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/draft-book --glossary glossary.yml --only afterword.md
~~~

Проверить благодарности, имена, даты, ссылки и утверждения автора; добавить полный файл через `apply_patch`.

- [ ] **Шаг 2: Независимый review**

~~~bash
uv run python scripts/review_file.py --source .tmp/upstream/book/afterword.md --translation book/afterword.md --glossary glossary.yml --output .tmp/reviews/afterword.json --model claude-opus-4-8
~~~

Применять только подтверждённые source исправления и устранить каждую unresolved issue `critical` или `major`.

- [ ] **Шаг 3: Выполнить строгие проверки всей книги**

~~~bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml
uv run python scripts/check_links.py book
uv run pytest -q
git diff --check
~~~

Ожидается: все 12 файлов существуют; проверки структуры, CJK, терминологии, ссылок, anchors и изображений проходят без partial mode.

- [ ] **Шаг 4: Коммит**

~~~bash
git add book/afterword.md glossary.yml
git commit -m "docs(book): translate the afterword into Russian" -m "Complete the twelve-file Russian manuscript and pass strict whole-book structure and link validation."
~~~

## Задача 19: Локализация генераторов, 77 SVG и русской обложки

**Файлы:**

- Изменить: `book/gen_ch1_figs.py`
- Изменить: `book/gen_ch2_figs.py`
- Изменить: `book/gen_ch3_figs.py`
- Изменить: `book/gen_ch4_figs.py`
- Изменить: `book/gen_ch5_figs.py`
- Изменить: `book/gen_ch8_figs.py`
- Изменить: `book/gen_ch9_figs.py`
- Изменить: `book/gen_cover.py`
- Изменить: `book/svg_lib.py`
- Механически изменить после проверки: `book/images/fig1-*.svg`, `book/images/fig2-*.svg`, `book/images/fig3-*.svg`, `book/images/fig4-*.svg`, `book/images/fig5-*.svg`, `book/images/fig8-*.svg`, `book/images/fig9-*.svg`
- Создать: `derived-files.json`
- Изменить: `tests/test_pinned_assets.py`
- Создать: `tests/test_figure_generators.py`

- [ ] **Шаг 1: Добавить падающие generator-contract tests**

Тесты должны определить точный expected output set:

- глава 1: `fig1-1.svg`–`fig1-10.svg`;
- глава 2: `fig2-1.svg`–`fig2-11.svg`;
- глава 3: `fig3-1.svg`–`fig3-14.svg`;
- глава 4: `fig4-1.svg`–`fig4-12.svg`;
- глава 5: `fig5-1.svg`–`fig5-11.svg`;
- глава 8: `fig8-1.svg`–`fig8-7.svg`;
- глава 9: `fig9-1.svg`–`fig9-12.svg`.

Suite требует ровно 77 outputs, CLI `--output-dir` в каждом генераторе, typed `generate_all(output_dir: Path) -> tuple[Path, ...]`, одинаковые bytes в двух запусках, корректные XML/SVG roots и отсутствие недокументированного CJK. `derived-files.json` для каждого рисунка фиксирует, должен ли он содержать кириллицу: английские identifiers и формулы не переводятся искусственно. Также тест проверяет, что `gen_cover.py` не зависит от сети/API и детерминированно создаёт русскую vector cover.

Запустить:

~~~bash
uv run pytest -q tests/test_figure_generators.py
~~~

Ожидается: падения, потому что импортированные генераторы пишут в фиксированные каталоги, не имеют typed contract и содержат source labels.

- [ ] **Шаг 2: Проверить symbols через LSP и локализовать generators**

Через Pyright/LSP найти определения и call sites в `svg_lib.py` и всех генераторах. Изменить shared API один раз, затем обновить каждую ссылку. Видимые labels переводить непосредственно по соответствующим source-подписям и абзацам; сохранить layout, цвета, размеры, нумерацию, стрелки и имена outputs. Перевести comments/docstrings. Добавить явные type annotations во все изменённые функции.

Заменить upstream cover API script детерминированным локальным SVG generator. Он должен выводить:

- `AI-агенты изнутри`;
- `Принципы проектирования и инженерная практика`;
- `Bojie Li`;
- `Русский перевод: community edition`;
- `v1.2-ru.1`.

Не сохранять вызов image model, fallback branch, поиск API key или network access.

- [ ] **Шаг 3: Форматировать и проверить типы до генерации**

~~~bash
uv run ruff format book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py tests/test_figure_generators.py
uv run ruff check book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py tests/test_figure_generators.py
pyright book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py tests/test_figure_generators.py
~~~

- [ ] **Шаг 4: Проверить нагрузку хоста и сгенерировать в `.tmp/`**

Выполнить общие проверки RAM/load. При memory pressure либо постороннем CPU-heavy process остановиться и сообщить об этом. Иначе:

~~~bash
mkdir -p .tmp/generated-images
uv run python book/gen_ch1_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch2_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch3_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch4_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch5_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch8_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch9_figs.py --output-dir .tmp/generated-images
uv run python book/gen_cover.py --output-dir .tmp/generated-images
uv run pytest -q tests/test_figure_generators.py
~~~

Ожидается: 77 chapter SVG и cover; все тесты проходят.

- [ ] **Шаг 5: Проверить и продвинуть сгенерированные файлы**

Проверить contact sheet либо representative SVG каждой главы в исходном разрешении. Подтвердить отсутствие clipping, overlap и потерянных glyphs. Механически скопировать из `.tmp/generated-images/` в `book/images/` только 77 проверенных рисунков и русскую cover; не копировать каталог целиком.

Создать `derived-files.json` через `apply_patch`. Для каждого изменённого asset, generator и `svg_lib.py` указать path, исходный Git blob SHA-1, SHA-256 производного файла, reason и producing task; для рисунков добавить generator и `expected_cyrillic`. Для новой `cover-ru.svg` использовать `source_blob_sha1: null` и указать `generated_by: book/gen_cover.py`. Изменить `tests/test_pinned_assets.py`: неизменённые upstream files обязаны совпадать с `upstream.json`, а осознанно изменённые — с `derived-files.json`. Так provenance-тест остаётся строгим после локализации.

- [ ] **Шаг 6: Полная проверка изображений и коммит**

~~~bash
uv run pytest -q tests/test_figure_generators.py
uv run pytest -q tests/test_pinned_assets.py
uv run python scripts/check_links.py book
uv run ruff check --select ANN book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py
git diff --check
git add book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py book/images derived-files.json tests/test_figure_generators.py tests/test_pinned_assets.py
git commit -m "assets: localize generated diagrams for Russian readers" -m "Translate all 77 generated SVGs and replace the network cover path with a deterministic typed vector generator."
~~~

## Задача 20: Кириллическая PDF-сборка и smoke checks

**Файлы:**

- Создать: `scripts/prepare_pdf.py`
- Создать: `tests/test_prepare_pdf.py`
- Создать: `tests/test_pdf_config.py`
- Изменить: `book/build_pdf.sh`
- Изменить: `book/preamble.tex`
- Изменить: `book/cover.tex`
- Изменить: `book/crossref.lua`
- Изменить: `book/experiment_box.lua`
- Изменить: `derived-files.json`
- Создать после успешных проверок: `dist/AI-Agents-in-Depth-RU-v1.2.pdf`

- [ ] **Шаг 1: TDD для изолированного PDF workspace**

`tests/test_prepare_pdf.py` должен доказать для `prepare_pdf(source_book: Path, work_dir: Path) -> PreparedBook`:

- требуются 12 точных имён Markdown в source order;
- source files копируются только в переданный вызывающей стороной work directory под `.tmp/`;
- Markdown image destinations меняются с `.svg` на `.pdf` без изменения code fences или inline code;
- возвращается typed manifest Markdown, скопированных raster images и SVG conversion jobs;
- destinations вне work directory и отсутствующие локальные изображения отклоняются.

Зафиксировать ошибку импорта, реализовать `scripts/prepare_pdf.py` со strict types, затем выполнить pytest, Ruff и Pyright.

- [ ] **Шаг 2: Добавить падающие статические build-config tests**

`tests/test_pdf_config.py` проверяет:

- точные title, author, translator attribution и version `v1.2-ru.1`;
- точный source order: introduction, главы 1–10, afterword;
- `set -euo pipefail` и вычисление путей относительно repository;
- preflight обязательных команд `pandoc`, `xelatex`, `rsvg-convert`, `kpsewhich`, `pdfinfo`, `pdftotext`;
- preflight обязательных файлов и локальных изображений;
- уникальный build directory под `.tmp/` репозитория без `rm -rf`;
- отсутствие установки dependencies и использования текста `book-en`;
- финальное продвижение только после успеха `pdfinfo`, `pdftotext` и `check_translation.py --pdf-text`.

Запустить и зафиксировать падения на импортированных upstream build files.

- [ ] **Шаг 3: Адаптировать build files**

Использовать файлы `book-en` только как переносимый технический baseline. Настроить XeLaTeX с кириллическими шрифтами и явным CJK fallback для разрешённых оригинальных примеров. Сохранить поведение upstream Lua, но перевести видимые labels блоков. `cover.tex` должен использовать русский текст cover из Задачи 19.

`book/build_pdf.sh` должен:

1. вычислить repo root относительно собственного пути;
2. падать с точным именем отсутствующей команды/файла;
3. создавать уникальный `.tmp/pdf-build.XXXXXX` и сохранять его при ошибке;
4. вызывать `scripts/prepare_pdf.py`;
5. преобразовывать запланированные SVG через `rsvg-convert -f pdf`;
6. вызывать Pandoc/XeLaTeX с 12 файлами в manifest order и metadata выше;
7. писать candidate PDF только в уникальный work directory;
8. выполнять `pdfinfo`, извлекать текст через `pdftotext` и запускать PDF-text validator;
9. создавать `dist/` и продвигать проверенный candidate в `dist/AI-Agents-in-Depth-RU-v1.2.pdf`.

Через `apply_patch` дополнить `derived-files.json` source blob IDs и SHA-256 изменённых `build_pdf.sh`, TeX и Lua files. `tests/test_pinned_assets.py` должен отклонять изменение любого imported support file без такой записи.

- [ ] **Шаг 4: Проверить Python и статическую конфигурацию**

~~~bash
uv run pytest -q tests/test_prepare_pdf.py tests/test_pdf_config.py tests/test_pinned_assets.py
uv run ruff format scripts/prepare_pdf.py tests/test_prepare_pdf.py tests/test_pdf_config.py
uv run ruff check scripts/prepare_pdf.py tests/test_prepare_pdf.py tests/test_pdf_config.py
pyright scripts/prepare_pdf.py tests/test_prepare_pdf.py tests/test_pdf_config.py
bash -n book/build_pdf.sh
git diff --check
~~~

- [ ] **Шаг 5: Повторно проверить реальные системные зависимости**

~~~bash
command -v pandoc
command -v xelatex
command -v rsvg-convert
command -v kpsewhich
command -v pdfinfo
command -v pdftotext
kpsewhich elegantbook.cls
fc-match "TeX Gyre Pagella"
fc-match "DejaVu Sans"
fc-match "Noto Sans CJK SC"
~~~

На момент планирования `pandoc`, `xelatex`, `rsvg-convert` и `kpsewhich` отсутствовали. Если чего-либо всё ещё нет, **ОСТАНОВИТЬСЯ и запросить явное разрешение** до изменения хоста. Предлагаемый набор Debian/Ubuntu packages:

~~~text
pandoc texlive-xetex texlive-latex-extra texlive-fonts-recommended texlive-lang-cyrillic texlive-lang-chinese fonts-texgyre fonts-dejavu fonts-noto-cjk librsvg2-bin poppler-utils
~~~

Только после явного разрешения пользователя установить подтверждённо отсутствующие packages и повторить все preflight-команды. Не устанавливать ненужные packages и не продолжать, если `elegantbook.cls` либо обязательные fonts не разрешаются.

- [ ] **Шаг 6: Проверить нагрузку, собрать и проверить PDF**

Выполнить общие проверки RAM/load, затем:

~~~bash
bash book/build_pdf.sh
pdfinfo dist/AI-Agents-in-Depth-RU-v1.2.pdf
pdftotext dist/AI-Agents-in-Depth-RU-v1.2.pdf .tmp/book.txt
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --pdf-text .tmp/book.txt
~~~

Проверить title page, оглавление, минимум одну насыщенную текстом страницу, одну таблицу, один code block и один локализованный SVG из каждой главы с генератором. Проверить выделение/копирование кириллицы из PDF и отсутствие обрезанных glyphs.

- [ ] **Шаг 7: Коммит**

~~~bash
git add scripts/prepare_pdf.py tests/test_prepare_pdf.py tests/test_pdf_config.py book/build_pdf.sh book/preamble.tex book/cover.tex book/crossref.lua book/experiment_box.lua derived-files.json dist/AI-Agents-in-Depth-RU-v1.2.pdf
git commit -m "build: add reproducible Russian PDF edition" -m "Build the twelve-file Cyrillic manuscript in an isolated workspace and publish only after metadata and extracted-text smoke checks."
~~~

## Задача 21: Release verification and handoff for `v1.2-ru.1`

**Файлы:**

- Изменить: `README.md`
- Изменять только при подтверждённой по source проблеме: translated Markdown, glossary, generators, checks or PDF build files

- [ ] **Шаг 1: Обновить release-facing README через `apply_patch`**

Установить статус завершённого `v1.2-ru.1`. Указать exact upstream commit, прямой перевод с китайского, model IDs, benchmark gate, независимый review, verification commands, PDF path, build dependencies, attribution, license и сохранение оригинальных screenshots с русскими подписями. Не заявлять об официальном одобрении автора.

- [ ] **Шаг 2: Выполнить полную чистую verification matrix**

Сначала применить `superpowers:verification-before-completion`. Затем выполнить из repository root:

~~~bash
uv sync --frozen --dev
uv run pytest -q
uv run ruff format --check scripts tests book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py
uv run ruff check scripts tests book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py
uv run ruff check --select ANN scripts tests book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py
pyright scripts tests book/gen_ch1_figs.py book/gen_ch2_figs.py book/gen_ch3_figs.py book/gen_ch4_figs.py book/gen_ch5_figs.py book/gen_ch8_figs.py book/gen_ch9_figs.py book/gen_cover.py book/svg_lib.py
uv run python scripts/check_links.py book
bash book/build_pdf.sh
pdfinfo dist/AI-Agents-in-Depth-RU-v1.2.pdf
pdftotext dist/AI-Agents-in-Depth-RU-v1.2.pdf .tmp/book-final.txt
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --pdf-text .tmp/book-final.txt
test "$(git hash-object LICENSE)" = "bd3e071f150cf46f86c91d3341d36644f16e11cb"
test -z "$(git ls-files '.tmp/*')"
git diff --check
~~~

Любое падение отменяет утверждение о готовности release. Провести диагностику, при применимости добавить падающий regression test, исправить через `apply_patch`, заново выполнить всю matrix и пересобрать PDF.

- [ ] **Шаг 3: Проверить tracked scope**

~~~bash
git status --short
git ls-files
git count-objects -vH
~~~

Подтвердить ровно 12 русских Markdown-файлов книги, 133 original/localized image paths плюс русскую cover, один принятый benchmark result, отсутствие `.tmp/`, китайского source snapshot, экспериментальных upstream chapter directories, credentials и runtime logs.

- [ ] **Шаг 4: Финальный release commit**

~~~bash
git add README.md
git commit -m "release: prepare Russian community edition v1.2-ru.1" -m "Document the completed direct translation, pinned provenance, benchmark gate, independent review, reproducible checks, and verified PDF artifact."
~~~

- [ ] **Шаг 5: Свежие post-commit evidence**

~~~bash
git status --short
git show --check --stat --oneline HEAD
pdfinfo dist/AI-Agents-in-Depth-RU-v1.2.pdf
~~~

Ожидается: пустой status, чистая commit check и корректные русские PDF metadata. Сообщить commit hashes, число тестов, количество страниц/размер PDF и границы покрытия. Остановиться до tag, создания remote, push или GitHub release.

## Контрольные точки выполнения

1. Задачи 1–4 создают только детерминированную инфраструктуру.
2. Задача 5 останавливается для пользовательского решения по benchmark.
3. Задача 6 импортирует pinned assets; Задачи 7–18 переводят по одному source file на commit.
4. Задача 19 выполняет ограниченную локальную генерацию после проверки load/RAM.
5. Задача 20 запрашивает явное разрешение на host packages, если dependencies отсутствуют.
6. Задача 21 объявляет завершение только по свежим evidence полной matrix.
