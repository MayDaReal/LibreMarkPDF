# Contributing to LibreMark PDF

LibreMark PDF is a pre-release, local-first Markdown-to-PDF application. Read
`AGENTS.md` before changing code: it defines module ownership, compatibility
constraints, required documents, and verification gates.

## Development setup

Use Python 3.9 or newer. The reproducible dependency workflow and pure-test
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
- Preserve Python 3.9 syntax.
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

The community theme package format is not implemented yet. Do not present an
arbitrary CSS file as a validated theme. For proposals, include purpose,
license/SPDX identifier, local assets and their licenses, a representative
Markdown fixture, screenshots or PDFs as review artifacts (not source files),
and confirm that the CSS contains no remote URLs, `@import`, scripts, or path
traversal. The approved default stylesheet must remain unchanged.

## Pull requests

Use one coherent change per pull request. Complete the template with observable
before/after behavior, exact commands and exit codes, environment, evidence,
risks, and unverified platforms. Maintainers review against the current gate in
`docs/project-reliability/BACKLOG.md`. Code presence alone does not complete a
backlog item.

By contributing, you agree that your contribution is licensed under the
repository's MIT License and that you have the right to submit it.
