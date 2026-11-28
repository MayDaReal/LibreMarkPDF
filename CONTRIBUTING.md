# Contributing to LibreMark PDF

LibreMark PDF is a pre-release, local-first Markdown-to-PDF application. Read
`AGENTS.md` before changing code: it defines module ownership, compatibility
constraints, required documents, and validation rules.

## Where to start

Use the smallest path that matches your change. The product README and the two
user manuals are the public behavior reference; this file is the contributor
workflow; `AGENTS.md` contains repository-wide constraints. Use the focused
validation, release, and platform documents only when the change needs them.

| Change | Read first |
| --- | --- |
| Core conversion or rendering | `libremark_pdf/core.py`, relevant tests, and `docs/VALIDATION.md` |
| CLI or agent contract | `libremark_pdf/cli.py`, `libremark_pdf/__main__.py`, `SKILL.md` |
| GUI or translations | `libremark_pdf/gui.py`, `libremark_pdf/i18n.py`, both manuals |
| Packaging or release validation | `Makefile`, native tools, requirements, and `docs/RELEASE.md` |
| Validation or platform policy | `docs/VALIDATION.md` and `docs/PLATFORM_SUPPORT.md` |

When a change crosses more than one row, read each affected canonical source;
avoid copying the same contract into a new document.

## Development setup

Use standard CPython 3.14. The reproducible dependency workflow and pure-test
command are in [`requirements/README.md`](requirements/README.md). Browser
installation is a development/build step and may use the network; conversion
must not download anything at runtime.

Before opening a pull request, run the smallest focused test for your change,
then:

```bash
python -m unittest discover -s tests -v
python tools/check_source_hygiene.py
python -m libremark_pdf convert --help
```

Browser-backed tests require the Playwright revision recorded in the active
lock. If the compatible browser is unavailable, report the limitation; do not
skip or weaken the test.

## Change boundaries

- Put reusable conversion behavior only in `libremark_pdf/core.py`.
- Keep GUI Tk calls on the main thread and preserve optional drag-and-drop.
- Keep CLI stdout/stderr, JSON, and exit status deterministic.
- Target Python 3.14 without unrelated syntax rewrites.
- Do not combine renderer, packaging, visual identity, or unrelated cleanup.
- Do not commit browsers, virtual environments, builds, PDFs, caches, secrets,
  or local configuration.

Renderer, default CSS, font, margin, pagination, and status-icon changes need
an approved ADR and reviewed before/after golden evidence. Dependency changes
need updated constraints/locks, licenses, packaging review, and an explanation
of the renderer revision when relevant.

## Documentation and translations

User-visible contracts must remain synchronized across `README.md`, the English
and French manuals, CLI help, and `SKILL.md`. New GUI strings require idiomatic
English and French entries with identical formatting placeholders. Use
[`docs/DOCUMENTATION_SYNC.md`](docs/DOCUMENTATION_SYNC.md) during review.

## Themes

Theme packages must follow `docs/THEME_CONTRIBUTING.md`. Include purpose,
license/SPDX identifier, local assets and their licenses, a representative
Markdown fixture, and reviewed visual evidence. Remote URLs, `@import`,
scripts, and path traversal are rejected. The approved default stylesheet must
remain unchanged.

## Pull requests

Use one coherent change per pull request. Complete the template with observable
before/after behavior, exact commands and exit codes, environment, evidence,
risks, and unverified platforms. Maintainers review against
`docs/VALIDATION.md` and the relevant release criteria. Code presence alone
does not establish successful validation.

By contributing, you agree that your contribution is licensed under the
repository's MIT License and that you have the right to submit it.
