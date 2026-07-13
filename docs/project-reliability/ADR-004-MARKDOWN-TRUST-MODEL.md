# ADR-004: Markdown trust and resource policy

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

## Context

Markdown, embedded HTML, custom CSS, and referenced resources are untrusted
inputs. The current permissive browser path can execute active content or make
network requests. That behavior is incompatible with a private, local-first
converter.

## Decision

The default conversion mode is safe and offline:

- all external network access is denied;
- JavaScript and service workers are disabled;
- raw HTML in Markdown is neutralized and rendered as literal text;
- remote URLs, `file:` URLs, CSS `@import`, and network-capable CSS references
  are rejected with actionable errors;
- local resources are restricted to the Markdown file's resolved base
  directory and cannot escape it through traversal or symbolic links;
- supported local images are validated for type and size, then embedded as
  data URIs before Chromium receives the document;
- renderer inputs have documented size, count, and timeout limits.

An explicit `--trusted-html` compatibility option may enable static raw HTML
for locally trusted documents. This option does not enable scripts, event
handlers, service workers, frames, embedded objects, external resources, or
network access. Active and network-capable content remains forbidden in every
official mode.

The GUI must describe the compatibility option clearly in idiomatic English
and French. The CLI, agent skill, manuals, and JSON diagnostics must use the
same policy and terminology.

## Compatibility consequence

Safe mode deliberately changes the prototype's permissive raw-HTML behavior.
The compatibility option preserves legitimate static-HTML use only through an
explicit trust decision. This is an approved security change, not an implicit
renderer modification.

Implementation must include focused security tests and an explicit golden
review for fixtures whose output changes because raw HTML is neutralized.

## Required evidence

- zero observed runtime network requests in default and trusted-HTML modes;
- tests for scripts, handlers, service workers, frames, objects, remote URLs,
  CSS imports, traversal, symbolic-link escape, malformed resources, and size
  limits;
- proof that accepted local resources render after embedding;
- synchronized EN/FR GUI text, CLI help, skill, and manuals.
