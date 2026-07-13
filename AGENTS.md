# AGENTS.md — LibreMark PDF contributor guide

## Product contract

LibreMark PDF converts UTF-8 Markdown to styled A4 PDF locally through
Playwright/Chromium. Preserve all three public access paths:

- desktop GUI: batch selection, preview, custom CSS, EN/FR;
- non-interactive CLI: stable stdout/stderr, JSON, nonzero on any failure;
- agent skill: the command contract in `SKILL.md`.

Reusable conversion behavior belongs only in `libremark_pdf/core.py`. GUI and
CLI modules translate user input and present results; they must not implement a
second rendering path.

## Read before editing

Read only the material needed for the active task, but read each selected file
completely:

| Task | Required files |
| --- | --- |
| Any user-visible change | `README.md`, both user manuals, affected front end |
| Conversion/rendering | `libremark_pdf/core.py`, `tests/test_core.py`, approved rendering ADRs |
| CLI or skill | `libremark_pdf/cli.py`, `libremark_pdf/__main__.py`, `SKILL.md` |
| GUI or translations | `libremark_pdf/gui.py`, `libremark_pdf/i18n.py` |
| Packaging/release | build scripts, both specs, `requirements.txt`, Windows validation guide |
| Reliability work | `TARGET_ARCHITECTURE.md`, `BACKLOG.md`, relevant ADRs |

The local `docs/project-reliability/BASELINE_AUDIT.md` is an immutable historical
input and is intentionally excluded from Git. If present, read it for
reliability work; never edit, stage, or publish it. If a required document and
the implementation disagree, report the discrepancy instead of silently
choosing one.

## Repository boundaries

- `libremark_pdf/core.py`: Markdown, templates, resources, Chromium, PDF, preview.
- `libremark_pdf/cli.py`: arguments, JSON/human output, process status.
- `libremark_pdf/gui.py`: Tk widgets and background-work orchestration.
- `libremark_pdf/i18n.py`: matching EN/FR tables and language persistence.
- `style.css`, `icons/`, `assets/`, `browsers/`: frozen runtime resources.
- `tests/`: `unittest` regression and integration checks.

Do not search or edit generated `venv/`, `build/`, `dist/`, caches, PDFs, or
downloaded browser contents unless the task explicitly targets an artifact.
Never commit those files.

## Invariants

- Python 3.9 remains supported. Avoid `X | None`, `match`, and APIs introduced
  after 3.9.
- Runtime conversion must not require an account, upload, telemetry, or network.
- `resource_path()` must resolve the same data from source and `sys._MEIPASS`.
- A bundled browser must be selected through `PLAYWRIGHT_BROWSERS_PATH`.
- Default rendering, CSS, fonts, margins, pagination, and status icons are
  compatibility-sensitive. Do not alter them without an approved ADR and
  reviewed golden evidence.
- Promise structural and strict visual equivalence, not byte-identical PDFs.
- Default footer: `Page {page} / {total}`. `HeaderFooterConfig.none()` disables
  all six fields.
- Supported header/footer tokens: `{titre}`, `{title}`, `{date}`, `{page}`,
  `{total}`. Escape literal user text before inserting it into HTML.
- Batch conversion returns one result per input and continues after an item
  fails.
- All Tk calls run on the main thread. Workers communicate through the queue.
- Drag-and-drop is optional; importing and launching the GUI must still work
  without `tkinterdnd2`.
- New GUI text must be idiomatic in both EN and FR with matching placeholders.
- Build and validate a native artifact for every advertised OS/architecture.
  Windows x64 is the first mandatory official lane.

## Clean-code rules

- Make the smallest coherent change; do not mix renderer, packaging, visual identity,
  and unrelated cleanup.
- Prefer focused functions, explicit data flow, early validation, and names that
  reveal intent. Avoid speculative abstractions and hidden side effects.
- Use `pathlib.Path`, UTF-8 for text files, context managers, and narrow
  exceptions. Broad exceptions are allowed only at user-facing or per-item
  isolation boundaries and must retain an actionable message.
- Add type hints to new or materially changed boundaries. Use Python 3.9 syntax.
- Comments explain constraints, decisions, or non-obvious failure handling;
  they do not narrate straightforward code. Keep public docstrings concise.
- Do not add a dependency when the standard library or an existing dependency
  is sufficient. Dependency changes also require packaging, lock, license,
  documentation, and frozen-artifact review.
- Keep CLI output deterministic: JSON has no stray stdout; human errors go to
  stderr; exit `0` means every requested conversion succeeded.
- Never weaken an error or a test merely to make a check pass.

No formatter, linter, or type checker is currently authoritative. Do not run a
repository-wide rewrite under a new tool. `unittest` is the mandatory baseline.

## Change workflow

1. Inspect `git status` and preserve unrelated work.
2. State observable acceptance criteria and identify the owning module.
3. Reproduce defects with the smallest relevant command.
4. Implement the smallest evidence-backed change.
5. Add a regression test for changed public behavior.
6. Run focused checks, then the active backlog gate or full suite.
7. Review the diff for generated files, secrets, unsafe resources, rendering
   drift, EN/FR mismatch, and documentation drift.
8. Record exact commands, exit codes, environment, and anything not verified.

Use separate worktrees for concurrent writers. In a shared directory, allow
only one writer at a time. No two agents may concurrently own `core.py`, shared
tests, packaging manifests, or the same documentation.

## Verification commands

```bash
python3 -m unittest discover -s tests -v
python3 -m libremark_pdf convert --help
python3 -m libremark_pdf convert README.md --json
```

```powershell
python -m unittest discover -s tests -v
python -m libremark_pdf convert --help
build.bat
```

Browser tests require the compatible Chromium payload. If it is unavailable,
report the limitation; do not skip or rewrite tests to hide it.

For a Windows release candidate, a successful build is insufficient. Exercise
GUI startup, preview, CLI JSON conversion, offline operation, empty user cache,
and an external path containing spaces using the exact candidate artifact.

## Documentation and delivery

Use English for code, technical files, filenames, and commits. Keep
`README.md`, `docs/MANUAL_EN.md`, `docs/MANUEL_FR.md`, CLI help, and `SKILL.md`
synchronized when their contract changes. Commit subjects are concise,
imperative English and contain no agent attribution unless the owner requests
it.

A handoff states: files changed, behavior affected, commands and exit codes,
evidence, risks, and unverified platforms. Backlog work is complete only when
its acceptance evidence exists; code presence alone earns no completion.
