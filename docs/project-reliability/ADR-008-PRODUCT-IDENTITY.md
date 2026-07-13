# ADR-008: Product identity and future compatibility policy

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

## Context

The project needs one consistent product identity across its application,
package, command, executable, configuration, documentation, and visual assets.
Future public identity changes also need a predictable compatibility policy.

## Decision

- Use **LibreMark PDF** as the product name.
- Use `libremark-pdf` for the repository, distribution, and command.
- Use `libremark_pdf` for the Python package and keep reusable conversion
  behavior in `libremark_pdf/core.py`.
- Use `LibreMarkPDF` for native executable names.
- Store local configuration in `~/.libremark-pdf/config.json`.
- Use
  `tools/svg-asset-forge/sources/libremark-pdf-logo.svg` as the canonical
  vector master.
- Keep identifiers synchronized across the GUI, CLI, skill, documentation,
  tests, packaging, resources, and release metadata.
- Review product-identity changes separately from renderer, security,
  default-style, and packaging-behavior changes.

## Future compatibility policy

After the first public release, an approved rename must preserve documented
commands, configuration, and automation aliases for at least 12 months and at
least two minor releases. Both minimums apply. Removal requires advance
deprecation notices, synchronized documentation, migration tests, and a
separate owner-approved ADR.

## Acceptance evidence

- synchronized source package, GUI, CLI, skill, EN/FR documentation, tests,
  build scripts, specifications, launchers, assets, license, and contributor
  guidance;
- focused source and packaging tests using the canonical public identifiers;
- reviewed vector master and reproducibly generated application assets;
- staged-manifest review before the initial application commit.
