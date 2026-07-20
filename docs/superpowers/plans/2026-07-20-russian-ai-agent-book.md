# GPT-only Russian AI Agent Book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Выпустить воспроизводимое русское community-издание книги Bojie Li `v1.2`, переведённое и сверенное только exact-моделью `gpt-5.6-sol`, с 12 Markdown-файлами, локализованными схемами и проверенным PDF.

**Architecture:** Pinned китайский source существует только в `.tmp/upstream/`. Codex app-server запускает два последовательных GPT-прохода для каждого lossless Markdown chunk: перевод и source-сверку; `thread/start` подтверждает effective model и запрещает provider fallback. В Git входят только проверенный русский текст, provenance manifest без китайского source, локализованные assets, deterministic validators и release PDF.

**Tech Stack:** Git, Python 3.12, `uv`, PyYAML, JSON Schema, pytest, Ruff, Pyright/LSP, Codex app-server stdio JSON-RPC, Pandoc, XeLaTeX, ElegantBook, Lua, `rsvg-convert`, Poppler.

**Design:** `docs/superpowers/specs/2026-07-20-russian-translation-design.md`

## Global Constraints

- Source repository: `https://github.com/bojieli/ai-agent-book`, commit `97de455e9aa44cf9f93441ce0c771c9aa9643d92`, version `v1.2`, directory `book/`.
- Единственная model ID: `gpt-5.6-sol`. Alias, provider fallback и автоматическая замена запрещены.
- `thread/start` обязан вернуть `model = gpt-5.6-sol`, `modelProvider = openai`, `thread.ephemeral = true` и read-only sandbox.
- Китайские Markdown-файлы, prompts и model responses существуют только под `.tmp/`; в tracked manifest попадают paths, hashes и runtime evidence без китайского текста.
- Каждый chunk проходит перевод и второй GPT-проход source-сверки; второй проход не называется независимым.
- Все текстовые правки выполняются через `apply_patch`; неизменённые бинарные assets и проверенные generated/PDF artifacts допускают механическое копирование.
- Python меняется по TDD: failing test → минимальная реализация → узкий green → полный green.
- Python требует type hints, `ruff format`, `ruff check` и strict Pyright.
- Перед model batches, генерацией схем и PDF-сборкой выполнять `free -h` и `ps -eo pid,pcpu,pmem,rss,cmd --sort=-rss | head -20`.
- Ничего не устанавливать в ОС без отдельного явного разрешения пользователя.
- Никаких `push`, tags или GitHub release без отдельной команды пользователя.
- Не перезаписывать частичные runtime artifacts: hash mismatch или неполная пара response/evidence останавливают продолжение.

## Current Baseline

Уже завершены и не повторяются:

- `4b33756`: pinned metadata, `upstream.json`, `glossary.yml`, Python project.
- `1888860`: structural, terminology, CJK и PDF-text validator.
- `40fdec3`: local links, images и Unicode anchors validator.
- `247a86a`: lossless Markdown chunks и первоначальный model orchestration.
- `d556bb0`: утверждённый GPT-only design spec.

Работа выполняется inline в worktree `/home/ikruglov/ai-agent-book-ru/.worktrees/russian-v1.2` на ветке `feature/russian-v1.2`.

---

### Task 1: Replace the dual-model runner with exact GPT app-server transport

**Files:**

- Modify: `scripts/model_runner.py:1`
- Modify: `tests/test_model_runner.py:1`
- Modify: `README.md:19`
- Delete: `scripts/review_file.py`
- Delete: `tests/test_review_file.py`
- Delete: `prompts/review.txt`
- Delete: `prompts/review.schema.json`
- Delete untracked: `scripts/benchmark.py`
- Delete untracked: `tests/test_benchmark.py`
- Delete untracked: `prompts/benchmark_review.txt`
- Delete untracked: `prompts/benchmark_review.schema.json`

**Interfaces:**

- Produces: `ModelName = Literal["gpt-5.6-sol"]`.
- Produces: `RuntimeEvidence(requested_model, reported_model, provider, thread_id, turn_id, ephemeral, fallback_allowed, sandbox_type, completion_observed, usage_observed, command_sha256)`.
- Produces: `run_model(model: ModelName, prompt: str, repo_root: Path, output_path: Path, timeout_seconds: int) -> ModelResult`.
- Produces: CLI `python scripts/model_runner.py smoke --output .tmp/model-smoke.json`.

- [ ] **Step 1: Write failing app-server protocol tests**

Replace dual-model command tests with exact assertions:

```python
def test_builds_exact_app_server_command() -> None:
    assert build_command() == (
        "codex",
        "app-server",
        "--stdio",
        "-c",
        "mcp_servers={}",
    )


def test_thread_start_disables_fallback_and_is_ephemeral(tmp_path: Path) -> None:
    request = build_thread_start_request(tmp_path)
    assert request["method"] == "thread/start"
    assert request["params"]["model"] == "gpt-5.6-sol"
    assert request["params"]["allowProviderModelFallback"] is False
    assert request["params"]["ephemeral"] is True
    assert request["params"]["permissions"] == ":read-only"


def test_rejects_effective_model_mismatch(fake_stream: FakeJsonRpcStream) -> None:
    fake_stream.thread_start_result["model"] = "other-model"
    with pytest.raises(ModelRunError, match="effective model"):
        run_model("gpt-5.6-sol", "nonce", ROOT, ROOT / ".tmp/out.txt", 60)
```

Add independent failures for provider mismatch, `ephemeral=false`, non-read-only sandbox, missing token usage, missing final agent message, turn error, timeout and output outside repo `.tmp/`.

- [ ] **Step 2: Run the focused tests and observe RED**

Run:

```bash
uv run pytest -q tests/test_model_runner.py
```

Expected: failures reference the old `codex exec` command and unsupported app-server request/parser interfaces.

- [ ] **Step 3: Implement the stdio JSON-RPC lifecycle**

Implement these request shapes in `scripts/model_runner.py`:

```python
THREAD_START_PARAMS: dict[str, object] = {
    "model": "gpt-5.6-sol",
    "allowProviderModelFallback": False,
    "ephemeral": True,
    "permissions": ":read-only",
    "approvalPolicy": "never",
    "baseInstructions": (
        "Perform the requested text transformation without tools. "
        "Return only the requested final payload."
    ),
    "dynamicTools": [],
}

TURN_INPUT = [{"type": "text", "text": prompt, "text_elements": []}]
```

The transport must send `initialize`, `initialized`, `thread/start`, then `turn/start`; correlate JSON-RPC IDs; collect only the final-phase `agentMessage`; require `thread/tokenUsage/updated` and `turn/completed`; drain stderr concurrently; terminate the app-server only after completion or typed failure. Never infer model identity from the requested value.

- [ ] **Step 4: Add fail-closed smoke CLI**

`model_runner.py smoke` sends a random nonce, requires exact echo, and writes this JSON only under `.tmp/`:

```json
{
  "schema_version": 1,
  "model_id": "gpt-5.6-sol",
  "nonce_sha256": "<64 lowercase hex>",
  "runtime": {
    "reported_model": "gpt-5.6-sol",
    "provider": "openai",
    "ephemeral": true,
    "fallback_allowed": false,
    "completion_observed": true,
    "usage_observed": true
  }
}
```

- [ ] **Step 5: Remove all external-editor and comparison tooling**

Delete the listed files through `apply_patch`. Update `README.md` to say the book uses two exact GPT passes and no model-comparison gate. Remove the temporary `.tmp/benchmark/` state created by this branch only after resolving its exact path and confirming it is ignored by Git.

- [ ] **Step 6: Verify and commit the transport migration**

Run:

```bash
uv run pytest -q tests/test_model_runner.py
uv run pytest -q
uv run ruff format scripts tests
uv run ruff check scripts tests
pyright scripts tests
git diff --check
! rg -n -i 'claude-opus|claude code|blind benchmark|translation-benchmark' README.md scripts tests prompts
```

Expected: all checks pass and forbidden pipeline references are absent.

Commit:

```bash
git add README.md scripts/model_runner.py tests/test_model_runner.py scripts/translate_file.py
git add -u scripts tests prompts
git commit -m "refactor: use an exact GPT-only runtime" -m "Replace the dual-model CLI pipeline with fail-closed Codex app-server evidence and remove external review and comparison tooling."
```

### Task 2: Build the two-pass GPT translation and provenance pipeline

**Files:**

- Modify: `scripts/translate_file.py:1`
- Modify: `tests/test_translate_file.py:1`
- Create: `scripts/verify_translation.py`
- Create: `tests/test_verify_translation.py`
- Create: `prompts/verify_translation.txt`
- Create: `prompts/verify_translation.schema.json`
- Modify: `scripts/check_translation.py:1`
- Modify: `tests/test_check_translation.py:1`
- Modify: `tests/test_project_metadata.py:1`
- Create: `translation-manifest.json`

**Interfaces:**

- Consumes: `run_model("gpt-5.6-sol", prompt, repo_root, output_path, timeout_seconds)` from Task 1.
- Produces: `translate_file(..., evidence_path: Path) -> TranslationManifest` without a comparison gate.
- Produces: `verify_file(source_path, draft_path, translation_evidence_path, output_path, evidence_path, manifest_fragment_path, glossary_path, repo_root, timeout_seconds) -> VerificationManifest`.
- Extends: `validate_translation(..., manifest_path: Path | None = None)` and CLI `--manifest`.

- [ ] **Step 1: Write failing first-pass and second-pass tests**

Tests must prove:

```python
def test_translation_starts_after_exact_smoke_without_eval_file(...) -> None:
    manifest = translate_file(source, draft, glossary, evidence, repo)
    assert manifest.model == "gpt-5.6-sol"
    assert not (repo / "evals/translation-benchmark.json").exists()


def test_verifier_binds_source_and_draft_hashes(...) -> None:
    result = verify_file(source, draft, translation_evidence, verified, evidence, fragment, glossary, repo, 60)
    assert result.source_sha256 == sha256(source.read_bytes()).hexdigest()
    assert result.draft_sha256 == sha256(draft.read_bytes()).hexdigest()
    assert verified.read_text().startswith("<!-- Русский перевод: community edition.")


def test_manifest_rejects_missing_second_pass_evidence(...) -> None:
    issues = validate_translation(source, target, load_glossary(glossary), manifest_path=manifest)
    assert {issue.code for issue in issues} == {"manifest-second-pass"}
```

Add failures for unknown JSON fields, wrong hashes, non-GPT model ID, outer Markdown fence, changed heading/fence/table/image shape, CJK outside allowlist, partial artifacts and output outside `.tmp/verified/`.

- [ ] **Step 2: Run focused tests and observe RED**

```bash
uv run pytest -q tests/test_translate_file.py tests/test_verify_translation.py tests/test_check_translation.py
```

Expected: missing verifier imports and the old translation gate cause failures.

- [ ] **Step 3: Define the strict second-pass schema and prompt**

The JSON Schema root has `additionalProperties: false` and exactly:

```json
{
  "source_sha256": "<64 lowercase hex>",
  "draft_sha256": "<64 lowercase hex>",
  "model_id": "gpt-5.6-sol",
  "issues": [
    {
      "category": "semantic",
      "severity": "major",
      "source_start_line": 1,
      "source_end_line": 1,
      "draft_start_line": 1,
      "draft_end_line": 1,
      "evidence": "Проверяемое описание ошибки без длинной цитаты source",
      "correction": "Краткое описание исправления"
    }
  ],
  "corrected_translation": "<full corrected Markdown chunk>"
}
```

Allowed categories: `semantic`, `omission`, `addition`, `russian`, `terminology`, `markdown`. Allowed severities: `critical`, `major`, `minor`. The prompt forbids unrelated rewriting and requires every change to correspond to source-backed evidence.

- [ ] **Step 4: Implement two-pass orchestration and evidence files**

Remove `_load_benchmark_gate`. First-pass outputs stay in `.tmp/drafts/`; corrected outputs stay in `.tmp/verified/`; runtime responses and evidence are paired and hash-validated. Each manifest fragment contains source path/blob/hash, final hash and both runtime evidence records, but no source, prompt, issue evidence or model response text.

- [ ] **Step 5: Add tracked manifest validation**

Initialize `translation-manifest.json`:

```json
{
  "schema_version": 1,
  "upstream_commit": "97de455e9aa44cf9f93441ce0c771c9aa9643d92",
  "model_id": "gpt-5.6-sol",
  "transport": {
    "name": "codex-app-server",
    "provider_fallback": false,
    "sandbox": "read-only",
    "ephemeral": true
  },
  "files": []
}
```

`check_translation.py --manifest` must require one manifest entry per `--only` file, match upstream blob/hash and tracked final SHA-256, and require exact evidence for pass names `translation` and `source_verification`.

- [ ] **Step 6: Verify and commit the two-pass pipeline**

```bash
uv run pytest -q tests/test_translate_file.py tests/test_verify_translation.py tests/test_check_translation.py
uv run pytest -q
uv run ruff format scripts tests
uv run ruff check scripts tests
pyright scripts tests
git diff --check
git add scripts/translate_file.py scripts/verify_translation.py scripts/check_translation.py tests/test_translate_file.py tests/test_verify_translation.py tests/test_check_translation.py tests/test_project_metadata.py prompts/verify_translation.txt prompts/verify_translation.schema.json translation-manifest.json docs/superpowers/plans/2026-07-20-russian-ai-agent-book.md
git commit -m "feat: verify translations with a second GPT pass" -m "Bind corrected Markdown to pinned source and draft hashes, preserve runtime provenance, and validate the tracked translation manifest."
```

### Task 3: Verify the real exact GPT runtime

**Files:**

- Temporary only: `.tmp/model-smoke.json`

**Interfaces:**

- Consumes: Task 1 smoke CLI.
- Produces: verified local runtime state required by all translation tasks.

- [ ] **Step 1: Check host resources**

```bash
free -h
ps -eo pid,pcpu,pmem,rss,cmd --sort=-rss | head -20
```

Stop if available RAM is below 4 GiB or another process is saturating the host.

- [ ] **Step 2: Run exact nonce smoke**

```bash
uv run python scripts/model_runner.py smoke --output .tmp/model-smoke.json --timeout-seconds 600
uv run python -m json.tool .tmp/model-smoke.json
```

Expected: exact `gpt-5.6-sol`, provider `openai`, `ephemeral=true`, `fallback_allowed=false`, completion and usage true. Any other result blocks Task 4 onward.

### Task 4: Import pinned assets and PDF build support

**Files:**

- Create: `book/images/*` (133 pinned files)
- Create: `book/gen_ch1_figs.py`, `book/gen_ch2_figs.py`, `book/gen_ch3_figs.py`, `book/gen_ch4_figs.py`, `book/gen_ch5_figs.py`, `book/gen_ch8_figs.py`, `book/gen_ch9_figs.py`
- Create: `book/gen_cover.py`, `book/svg_lib.py`
- Create: `book/build_pdf.sh`, `book/preamble.tex`, `book/cover.tex`, `book/crossref.lua`, `book/experiment_box.lua`
- Create: `tests/test_pinned_assets.py`

**Interfaces:**

- Consumes: exact paths and blob IDs from `upstream.json`.
- Produces: complete local assets and build plumbing without translated prose.

- [ ] **Step 1: Write the failing pinned-asset test**

Test exact 133 image blobs, nine generator/support blobs, five PDF support blobs and absence of copied upstream `.md` files.

- [ ] **Step 2: Observe RED**

```bash
uv run pytest -q tests/test_pinned_assets.py
```

Expected: imported files are absent.

- [ ] **Step 3: Mechanically copy exact pinned files**

Copy `book/images/`, generators and `svg_lib.py` from `.tmp/upstream/book/`; copy only the five declared build-support files from `.tmp/upstream/book-en/`. Do not execute or localize them in this task.

- [ ] **Step 4: Verify and commit assets**

```bash
uv run pytest -q tests/test_pinned_assets.py
test "$(find book/images -type f | wc -l)" -eq 133
test -z "$(find book -maxdepth 1 -name '*.md' -print)"
git diff --check
git add book tests/test_pinned_assets.py
git commit -m "assets: import pinned v1.2 book resources" -m "Import exact source images, generators, and PDF build support without copying Chinese prose."
```

## Translation Task Template

Tasks 5–16 use the same executable contract but each names its own source, outputs, terminology and verification commands explicitly:

1. Accept glossary entries only after checking all pinned-source uses.
2. Run pass 1 to `.tmp/drafts/<file>` and pass 2 to `.tmp/verified/<file>`.
3. Run structural validation against `.tmp/verified/`.
4. Add the complete verified Russian file and its manifest fragment via `apply_patch`.
5. Run tracked structure/manifest and partial/full link checks.
6. Commit one completed book file.

### Task 5: Translate and verify `introduction.md`

**Files:** Create `book/introduction.md`; modify `glossary.yml`, `translation-manifest.json`; temporary `.tmp/drafts/introduction.md`, `.tmp/verified/introduction.md`, `.tmp/evidence/introduction.*.json`.

**Focus:** title, edition boundaries, author claims, introductory definitions and every image/table position.

- [ ] **Step 1: Prepare accepted introduction terminology**

Check every relevant candidate against `.tmp/upstream/book/introduction.md`; edit only confirmed `status: accepted` entries.

- [ ] **Step 2: Run both exact GPT passes**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/introduction.md --output .tmp/drafts/introduction.md --evidence .tmp/evidence/introduction.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/introduction.md --draft .tmp/drafts/introduction.md --translation-evidence .tmp/evidence/introduction.translation.json --output .tmp/verified/introduction.md --evidence .tmp/evidence/introduction.verification.json --manifest-fragment .tmp/evidence/introduction.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only introduction.md
```

- [ ] **Step 3: Promote verified content and provenance**

Inspect the corrected Markdown and fragment; add `book/introduction.md` and the `introduction.md` manifest entry through `apply_patch` without copying Chinese text or issue evidence.

- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only introduction.md
uv run python scripts/check_links.py book --only introduction.md --partial-manifest upstream.json
git diff --check
git add book/introduction.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate the introduction into Russian" -m "Translate and source-verify the introduction with two exact GPT passes and recorded runtime provenance."
```

### Task 6: Translate and verify `chapter1.md`

**Files:** Create `book/chapter1.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/drafts`, `.tmp/verified`, `.tmp/evidence`.

**Focus:** `AI Agent`, agent paradigm, agent harness, model/training/inference components and `fig1-1`–`fig1-10`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter1.md --output .tmp/drafts/chapter1.md --evidence .tmp/evidence/chapter1.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter1.md --draft .tmp/drafts/chapter1.md --translation-evidence .tmp/evidence/chapter1.translation.json --output .tmp/verified/chapter1.md --evidence .tmp/evidence/chapter1.verification.json --manifest-fragment .tmp/evidence/chapter1.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter1.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter1.md
uv run python scripts/check_links.py book --only chapter1.md --partial-manifest upstream.json
git diff --check
git add book/chapter1.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 1 into Russian" -m "Preserve agent-system definitions, code, structure, and figure references through two exact GPT passes."
```

### Task 7: Translate and verify `chapter2.md`

**Files:** Create `book/chapter2.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** LLM API/context, `prefill`, `decode`, `KV cache`, latency, throughput, context window, prompt injection, formulas, security negations and `fig2-1`–`fig2-11`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter2.md --output .tmp/drafts/chapter2.md --evidence .tmp/evidence/chapter2.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter2.md --draft .tmp/drafts/chapter2.md --translation-evidence .tmp/evidence/chapter2.translation.json --output .tmp/verified/chapter2.md --evidence .tmp/evidence/chapter2.verification.json --manifest-fragment .tmp/evidence/chapter2.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter2.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter2.md
uv run python scripts/check_links.py book --only chapter2.md --partial-manifest upstream.json
git diff --check
git add book/chapter2.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 2 into Russian" -m "Preserve LLM runtime, cache, context, formula, and prompt-security semantics with source-bound verification."
```

### Task 8: Translate and verify `chapter3.md`

**Files:** Create `book/chapter3.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** short-/long-term memory, retrieval, embedding, vector database, chunking, RAG, ranking, formulas and `fig3-1`–`fig3-14`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter3.md --output .tmp/drafts/chapter3.md --evidence .tmp/evidence/chapter3.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter3.md --draft .tmp/drafts/chapter3.md --translation-evidence .tmp/evidence/chapter3.translation.json --output .tmp/verified/chapter3.md --evidence .tmp/evidence/chapter3.verification.json --manifest-fragment .tmp/evidence/chapter3.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter3.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter3.md
uv run python scripts/check_links.py book --only chapter3.md --partial-manifest upstream.json
git diff --check
git add book/chapter3.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 3 into Russian" -m "Preserve memory, retrieval, ranking, tables, and formulas with two-pass source verification."
```

### Task 9: Translate and verify `chapter4.md`

**Files:** Create `book/chapter4.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** tool definition/call/result, schemas, orchestration, concurrency, async ordering, timeout, retry, idempotency and `fig4-1`–`fig4-12`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter4.md --output .tmp/drafts/chapter4.md --evidence .tmp/evidence/chapter4.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter4.md --draft .tmp/drafts/chapter4.md --translation-evidence .tmp/evidence/chapter4.translation.json --output .tmp/verified/chapter4.md --evidence .tmp/evidence/chapter4.verification.json --manifest-fragment .tmp/evidence/chapter4.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter4.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter4.md
uv run python scripts/check_links.py book --only chapter4.md --partial-manifest upstream.json
git diff --check
git add book/chapter4.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 4 into Russian" -m "Preserve tool schemas, asynchronous execution, and error semantics through GPT source verification."
```

### Task 10: Translate and verify `chapter5.md`

**Files:** Create `book/chapter5.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** sandbox, permission, trust boundary, prompt injection, file edits, patches, coding agents, security modal verbs and `fig5-1`–`fig5-11`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter5.md --output .tmp/drafts/chapter5.md --evidence .tmp/evidence/chapter5.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter5.md --draft .tmp/drafts/chapter5.md --translation-evidence .tmp/evidence/chapter5.translation.json --output .tmp/verified/chapter5.md --evidence .tmp/evidence/chapter5.verification.json --manifest-fragment .tmp/evidence/chapter5.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter5.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter5.md
uv run python scripts/check_links.py book --only chapter5.md --partial-manifest upstream.json
git diff --check
git add book/chapter5.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 5 into Russian" -m "Preserve coding-agent workflows, executable examples, permissions, and security boundaries."
```

### Task 11: Translate and verify `chapter6.md`

**Files:** Create `book/chapter6.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** evaluation datasets, metrics, judges, rubrics, variance, confidence intervals, statistical significance, pass rate, contamination, formulas and exact comparison directions.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter6.md --output .tmp/drafts/chapter6.md --evidence .tmp/evidence/chapter6.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter6.md --draft .tmp/drafts/chapter6.md --translation-evidence .tmp/evidence/chapter6.translation.json --output .tmp/verified/chapter6.md --evidence .tmp/evidence/chapter6.verification.json --manifest-fragment .tmp/evidence/chapter6.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter6.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter6.md
uv run python scripts/check_links.py book --only chapter6.md --partial-manifest upstream.json
git diff --check
git add book/chapter6.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 6 into Russian" -m "Preserve evaluation metrics, formulas, statistical qualifiers, and comparison directions."
```

### Task 12: Translate and verify `chapter7.md`

**Files:** Create `book/chapter7.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** SFT, RL, policy, reward, trajectory, rollout, verifier, tool creation, training data, objectives and mathematical notation.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter7.md --output .tmp/drafts/chapter7.md --evidence .tmp/evidence/chapter7.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter7.md --draft .tmp/drafts/chapter7.md --translation-evidence .tmp/evidence/chapter7.translation.json --output .tmp/verified/chapter7.md --evidence .tmp/evidence/chapter7.verification.json --manifest-fragment .tmp/evidence/chapter7.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter7.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter7.md
uv run python scripts/check_links.py book --only chapter7.md --partial-manifest upstream.json
git diff --check
git add book/chapter7.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 7 into Russian" -m "Preserve training objectives, rewards, algorithms, notation, and tool-learning examples."
```

### Task 13: Translate and verify `chapter8.md`

**Files:** Create `book/chapter8.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** realtime, streaming, interruption, turn-taking, STT/TTS, endpointing, latency, multimodal events and `fig8-1`–`fig8-7`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter8.md --output .tmp/drafts/chapter8.md --evidence .tmp/evidence/chapter8.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter8.md --draft .tmp/drafts/chapter8.md --translation-evidence .tmp/evidence/chapter8.translation.json --output .tmp/verified/chapter8.md --evidence .tmp/evidence/chapter8.verification.json --manifest-fragment .tmp/evidence/chapter8.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter8.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter8.md
uv run python scripts/check_links.py book --only chapter8.md --partial-manifest upstream.json
git diff --check
git add book/chapter8.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 8 into Russian" -m "Preserve realtime interaction, latency budgets, multimodal states, and API event semantics."
```

### Task 14: Translate and verify `chapter9.md`

**Files:** Create `book/chapter9.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** embodied agents, perception, planning, control, actuators, sensors, world models, simulation, physical units, safety and `fig9-1`–`fig9-12`.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter9.md --output .tmp/drafts/chapter9.md --evidence .tmp/evidence/chapter9.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter9.md --draft .tmp/drafts/chapter9.md --translation-evidence .tmp/evidence/chapter9.translation.json --output .tmp/verified/chapter9.md --evidence .tmp/evidence/chapter9.verification.json --manifest-fragment .tmp/evidence/chapter9.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter9.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter9.md
uv run python scripts/check_links.py book --only chapter9.md --partial-manifest upstream.json
git diff --check
git add book/chapter9.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 9 into Russian" -m "Preserve embodied-agent control, robotics terminology, physical units, and safety constraints."
```

### Task 15: Translate and verify `chapter10.md`

**Files:** Create `book/chapter10.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** multi-agent coordination, communication, protocol, role, delegation, consensus, competition, topology, shared state and failure modes.

- [ ] **Step 1: Accept source-checked chapter terminology**
- [ ] **Step 2: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/chapter10.md --output .tmp/drafts/chapter10.md --evidence .tmp/evidence/chapter10.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/chapter10.md --draft .tmp/drafts/chapter10.md --translation-evidence .tmp/evidence/chapter10.translation.json --output .tmp/verified/chapter10.md --evidence .tmp/evidence/chapter10.verification.json --manifest-fragment .tmp/evidence/chapter10.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only chapter10.md
```

- [ ] **Step 3: Add verified chapter and manifest entry through `apply_patch`**
- [ ] **Step 4: Verify and commit**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --only chapter10.md
uv run python scripts/check_links.py book --only chapter10.md --partial-manifest upstream.json
git diff --check
git add book/chapter10.md glossary.yml translation-manifest.json
git commit -m "docs(book): translate chapter 10 into Russian" -m "Preserve multi-agent roles, message directions, protocols, shared state, and coordination failures."
```

### Task 16: Translate `afterword.md` and validate the complete manuscript

**Files:** Create `book/afterword.md`; modify `glossary.yml`, `translation-manifest.json`; temporary matching files under `.tmp/`.

**Focus:** acknowledgements, names, dates, links and author claims.

- [ ] **Step 1: Run both passes and temporary validation**

```bash
uv run python scripts/translate_file.py --source .tmp/upstream/book/afterword.md --output .tmp/drafts/afterword.md --evidence .tmp/evidence/afterword.translation.json --glossary glossary.yml
uv run python scripts/verify_translation.py --source .tmp/upstream/book/afterword.md --draft .tmp/drafts/afterword.md --translation-evidence .tmp/evidence/afterword.translation.json --output .tmp/verified/afterword.md --evidence .tmp/evidence/afterword.verification.json --manifest-fragment .tmp/evidence/afterword.manifest.json --glossary glossary.yml
uv run python scripts/check_translation.py --source .tmp/upstream/book --target .tmp/verified --glossary glossary.yml --only afterword.md
```

- [ ] **Step 2: Add verified afterword and manifest entry through `apply_patch`**

- [ ] **Step 3: Run strict whole-book verification**

```bash
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json
uv run python scripts/check_links.py book
uv run pytest -q
git diff --check
```

Expected: exactly 12 translated files, one manifest entry per file, no unresolved structure/CJK/glossary/link findings.

- [ ] **Step 4: Commit the completed manuscript**

```bash
git add book/afterword.md glossary.yml translation-manifest.json
git commit -m "docs(book): complete the Russian manuscript" -m "Translate and source-verify the afterword, complete all twelve manifest entries, and pass strict whole-book validation."
```

### Task 17: Localize generated figures and the Russian cover

**Files:**

- Modify: `book/gen_ch1_figs.py`, `book/gen_ch2_figs.py`, `book/gen_ch3_figs.py`, `book/gen_ch4_figs.py`, `book/gen_ch5_figs.py`, `book/gen_ch8_figs.py`, `book/gen_ch9_figs.py`, `book/gen_cover.py`, `book/svg_lib.py`
- Update mechanically after verification: generated `book/images/fig{1,2,3,4,5,8,9}-*.svg`
- Create: `derived-files.json`, `tests/test_figure_generators.py`
- Modify: `tests/test_pinned_assets.py`

**Interfaces:**

- Produces: deterministic 77 localized SVG outputs and Russian cover metadata.
- Records: generator source hash, command, output path/hash and generation status in `derived-files.json`.

- [ ] **Step 1: Write failing generator inventory and localization tests**

Tests require exact output filenames, no tracked output path under `.tmp/`, Russian labels in declared SVG text nodes, no unexpected CJK and deterministic rerun hashes.

- [ ] **Step 2: Observe RED**

```bash
uv run pytest -q tests/test_figure_generators.py tests/test_pinned_assets.py
```

- [ ] **Step 3: Localize generator strings with type-safe edits**

Translate only human-visible labels; preserve geometry, colors, IDs, filenames, dimensions, formulas and code identifiers. All new/changed Python signatures require explicit annotations.

- [ ] **Step 4: Check resources and generate into `.tmp/`**

```bash
free -h
ps -eo pid,pcpu,pmem,rss,cmd --sort=-rss | head -20
uv run python book/gen_ch1_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch2_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch3_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch4_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch5_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch8_figs.py --output-dir .tmp/generated-images
uv run python book/gen_ch9_figs.py --output-dir .tmp/generated-images
uv run python book/gen_cover.py --output-dir .tmp/generated-images
```

- [ ] **Step 5: Verify, promote and commit generated files**

```bash
uv run pytest -q tests/test_figure_generators.py tests/test_pinned_assets.py
uv run ruff format book/gen_*_figs.py book/gen_cover.py book/svg_lib.py tests
uv run ruff check book/gen_*_figs.py book/gen_cover.py book/svg_lib.py tests
pyright book/gen_*_figs.py book/gen_cover.py book/svg_lib.py tests
git diff --check
git add book derived-files.json tests/test_figure_generators.py tests/test_pinned_assets.py
git commit -m "assets: localize generated figures and cover" -m "Translate human-visible diagram labels while preserving pinned geometry, filenames, and reproducible output provenance."
```

### Task 18: Build and verify the Cyrillic PDF

**Files:**

- Modify: `book/build_pdf.sh`, `book/preamble.tex`, `book/cover.tex`, `book/crossref.lua`, `book/experiment_box.lua`
- Create after verification: `dist/AI-Agents-in-Depth-RU-v1.2.pdf`
- Create: `tests/test_pdf_build.py`

**Interfaces:**

- Consumes: 12 verified Markdown files, localized assets and `translation-manifest.json`.
- Produces: reproducible Russian PDF with title, author, attribution and version metadata.

- [ ] **Step 1: Write failing PDF preflight tests**

Test dependency reporting, ordered 12-file input list, Russian metadata, `.tmp/` build target and refusal to replace `dist/` before smoke checks.

- [ ] **Step 2: Observe RED**

```bash
uv run pytest -q tests/test_pdf_build.py
```

- [ ] **Step 3: Adapt build support for Cyrillic**

Use XeLaTeX and fonts with Cyrillic coverage; keep CJK fallback only for allowlisted examples. Build in `.tmp/pdf-build/`; require successful `pdfinfo`, `pdftotext`, title/chapter checks and no U+FFFD before promotion.

- [ ] **Step 4: Check dependencies without installing them**

```bash
free -h
ps -eo pid,pcpu,pmem,rss,cmd --sort=-rss | head -20
bash book/build_pdf.sh --check-deps
```

If any dependency is absent, stop and request explicit permission before system installation.

- [ ] **Step 5: Build, smoke-test and promote PDF**

```bash
bash book/build_pdf.sh
pdfinfo .tmp/pdf-build/AI-Agents-in-Depth-RU-v1.2.pdf
pdftotext .tmp/pdf-build/AI-Agents-in-Depth-RU-v1.2.pdf .tmp/book.txt
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --pdf-text .tmp/book.txt
uv run pytest -q tests/test_pdf_build.py
```

Only after all commands pass, mechanically promote the exact checked PDF to `dist/`.

- [ ] **Step 6: Commit PDF support and artifact**

```bash
git add book/build_pdf.sh book/preamble.tex book/cover.tex book/crossref.lua book/experiment_box.lua tests/test_pdf_build.py dist/AI-Agents-in-Depth-RU-v1.2.pdf
git commit -m "build: produce the Russian v1.2 PDF" -m "Build with Cyrillic-capable XeLaTeX settings and promote only the PDF that passed metadata and extracted-text checks."
```

### Task 19: Release verification and handoff

**Files:**

- Modify: `README.md`, `NOTICE`, `translation-manifest.json`
- Verify: all tracked project files and `dist/AI-Agents-in-Depth-RU-v1.2.pdf`

**Interfaces:**

- Produces: release-ready `v1.2-ru.1` checkout; does not create tag, push or publish.

- [ ] **Step 1: Update release metadata**

README and NOTICE must state exact upstream commit, direct Chinese-to-Russian translation, two exact GPT passes, app-server identity evidence, deterministic validation, Apache-2.0 attribution and absence of official author endorsement.

- [ ] **Step 2: Run complete verification from a clean logical state**

```bash
uv run pytest -q
uv run ruff format --check scripts tests book/gen_*_figs.py book/gen_cover.py book/svg_lib.py
uv run ruff check scripts tests book/gen_*_figs.py book/gen_cover.py book/svg_lib.py
pyright scripts tests book/gen_*_figs.py book/gen_cover.py book/svg_lib.py
uv run python scripts/check_links.py book
uv run python scripts/check_translation.py --source .tmp/upstream/book --target book --glossary glossary.yml --manifest translation-manifest.json --pdf-text .tmp/book.txt
pdfinfo dist/AI-Agents-in-Depth-RU-v1.2.pdf
git diff --check
test "$(find book -maxdepth 1 -name '*.md' | wc -l)" -eq 12
test "$(find book/images -type f | wc -l)" -eq 133
test -z "$(git ls-files .tmp)"
```

- [ ] **Step 3: Audit tracked contents**

Confirm no credentials, runtime logs, Chinese source snapshot, temporary responses, partial PDF artifacts or undeclared experimental directories are tracked. `translation-manifest.json` must contain exactly 12 file entries and no CJK.

- [ ] **Step 4: Commit release state**

```bash
git add README.md NOTICE translation-manifest.json
git commit -m "release: prepare Russian community edition v1.2-ru.1" -m "Record exact GPT-only provenance, complete verification, attribution, and the checked Russian PDF artifact."
```

- [ ] **Step 5: Stop before external publication**

Report branch, commits, verification evidence and PDF path. Do not push, tag or create a release without a new explicit user command.

## Execution Checkpoints

1. After Task 2: GPT-only codebase, no comparison/editor tooling, all tests green.
2. After Task 3: real app-server smoke proves exact model; otherwise stop.
3. After each Task 5–16: one complete source-verified book file and manifest entry committed.
4. Before Task 18 dependency installation: stop for user permission if any package is missing.
5. After Task 19: release-ready local branch only; external publication remains unauthorized.
