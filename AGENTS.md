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
| Reliability work | `docs/VALIDATION.md`, `docs/RELEASE.md`, `docs/PLATFORM_SUPPORT.md` |

If a required document and the implementation disagree, report the discrepancy
instead of silently choosing one.

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

## Repository hygiene

The main branch contains only material needed to understand, develop, test,
package, or support the current product. Before adding a file, identify its
owner, current consumer, maintenance trigger, and deletion condition. If none
is concrete, do not add the file.

- Prefer updating an existing authoritative file over creating a new document,
  script, fixture, helper, or configuration layer.
- Keep one source of truth per fact. Reference it from consumers instead of
  copying versions, commands, requirements, checklists, or support statements.
- Do not commit plans, prompts, agent transcripts, execution boards, scratch
  notes, intermediate reports, local inventories, or reproducible evidence.
  Use issues, pull requests, release assets, and Git history for that context.
- Keep generated artifacts, logs, screenshots, reports, downloaded tools,
  virtual environments, caches, and temporary data outside version control.
  Add an ignore rule when a new tool creates a repeatable local output.
- Commit a fixture, golden, binary, or sample only when an active automated
  test or runtime path consumes it. Keep the smallest representative case and
  document its update command in `docs/VALIDATION.md`.
- Organize tests by lasting product behavior, not by incident, milestone,
  development batch, gate, or agent task. Merge overlapping coverage and avoid
  rerunning the same test through multiple default targets.
- Keep tools platform-neutral when their behavior is shared. Use a thin
  platform wrapper only for genuinely native setup, build, or validation.
- Remove obsolete compatibility paths, completed-work documents, and replaced
  scripts in the same change that makes them obsolete. Confirm references with
  `rg` and rely on Git history instead of retaining an in-tree archive.
- Temporary migration code must name its removal condition in a concise
  comment or tracked issue. It must not silently become a second permanent path.
- Do not track `archive`, `old`, `backup`, `tmp`, `.work`, gate-named, or
  date-named repository areas. Material required only for a published release
  belongs with that release, not on the main branch.

At each release boundary, audit tracked files, ignored generated directories,
dependencies, test overlap, stale documentation, and unreferenced fixtures or
tools. Deletion is preferred when Git history or reproducible automation already
preserves the information.

## Backlog branches and local work

Start a substantial backlog on a dedicated branch named
`backlog/<short-topic>`. Keep product changes in that branch and use the ignored
`.work/<short-topic>/` directory only when cross-session local context or
supervisor-requested working output is useful.

- Keep rolling context concise. Prefer `STATE.md`, `DECISIONS.md`, and `NEXT.md`;
  add `reports/` or `artifacts/` only when the supervisor requests them.
- At the start of a resumed session, read only the active backlog state files.
  Open detailed reports only when the current task requires them.
- `.work/` is local, non-authoritative, excluded from builds and tests, and must
  contain no secrets, personal data, required source, or sole copy of a decision.
- Promote durable behavior to code and tests, contributor rules to `AGENTS.md`,
  validation rules to active documentation, and shared backlog state to the
  issue or pull request.
- An ignored work directory is available only to sessions sharing the same
  checkout. Use the issue or pull request when separate clones need the context.
- Before merging, run `make repository-check`, promote any durable information,
  delete `.work/<short-topic>/`, and confirm `git ls-files .work` prints nothing.
- Delete the local backlog branch after its reviewed changes are integrated.

For this shared checkout, read `.work/shared-memory-session.md` when resuming
work that depends on recurring local execution constraints. Keep that file
short, factual, and limited to observations that can save repeated diagnosis;
it is local context, not product documentation or a source of truth.

## Invariants

- Source development targets standard GIL-enabled CPython 3.14. The
  supported range is `>=3.14,<3.15`. Validate each native release lane.
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
- Add type hints to new or materially changed boundaries. Use Python 3.14 syntax.
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

## Context and execution efficiency

Use the smallest context that can safely support the change. Token and runtime
efficiency must not weaken correctness, required evidence, or the complete
reading of a file selected as necessary.

- Search with `rg` or `rg --files` before opening files. Read only the files
  required by the task and avoid generated directories and unrelated history.
- Find definitions and references before reading a large module. Do not reread
  unchanged content during the same task.
- Prefer concise diagnostic excerpts over complete logs. Preserve the command,
  exit code, first actionable error, root cause, and only the context needed to
  understand them.
- Do not place complete test output, reports, diffs, or conversation history in
  agent context when a structured summary is sufficient.
- Resume work from a compact state summary: objective, decisions, changed
  files, verification results, remaining risks, and next action.
- Validate progressively: reproduce with the smallest command, run the focused
  test, then its functional group, and run the full required gate only when the
  change scope or delivery stage requires it.
- Group independent searches and read-only checks when practical. Do not run a
  test again merely because multiple Make targets include the same coverage.
- Keep progress updates limited to material assumptions, completed checks,
  useful partial results, and blockers. Do not repeat commentary in the final
  handoff.
- Keep the final handoff factual and compact: outcome, changed files, commands
  and exit codes, evidence, risks, and unverified platforms.

Never save tokens by partially reading a required file, hiding an error,
skipping required browser or release validation, replacing a relevant test with
inspection, or omitting an uncertainty that affects the result.

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
make build-windows
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
