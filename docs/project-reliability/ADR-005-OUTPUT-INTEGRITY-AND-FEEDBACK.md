# ADR-005: Output integrity, overwrite, and failure feedback

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

## Context

Conversion must never silently overwrite an existing file, let two batch
inputs target the same output, or leave a partial PDF. Users also need an
immediate result summary and enough optional detail to understand and report a
failure without exposing private documents automatically.

## Output decision

- Existing outputs are never overwritten by default.
- The non-interactive CLI overwrites only with an explicit `--overwrite`
  option.
- The GUI presents the complete overwrite decision before conversion starts.
- The core preflights every planned destination before rendering.
- Two inputs targeting the same output are rejected even when overwrite is
  enabled.
- Input/output identity is always rejected.
- Entries with invalid or colliding plans fail before writing; independent
  valid entries continue and still produce one result per input.
- Every PDF is written to a uniquely named temporary file in the destination
  directory and committed atomically only after successful rendering and
  validation.
- Failure removes temporary output and preserves any previous destination.
- The CLI exits nonzero when any requested entry fails.

## Immediate feedback

Every front end must show a concise result as soon as the batch completes:

- total, successful, failed, and cancelled counts;
- one visible status per input;
- the final output path for success;
- a short actionable message and stable error code for failure;
- access to expanded technical details without obscuring the summary.

CLI human output uses stderr for failures. JSON output remains valid and
contains one structured result per input with no stray stdout text. The GUI
uses an expandable or separate details view and provides direct access to
successful outputs where supported.

## User-controlled diagnostic report

On explicit request, the application creates a local Markdown or JSON support
report containing the application version, render-profile fingerprint,
renderer revision, operating system, architecture, sanitized options, result
summary, stable error codes, and sanitized technical details.

The default report excludes:

- Markdown, HTML, CSS, and document contents;
- environment variables, credentials, tokens, and browser profile data;
- full home-directory paths and unrelated filesystem information;
- input files or generated PDFs.

The user can review, copy, or save the report before sharing it. An explicit
action may open the repository's GitHub issue form in the system browser and
prepare the report for manual submission. The application never uploads or
submits a report automatically, never requires a GitHub account for conversion,
and continues to work fully offline.

All related GUI text must exist in idiomatic English and French. Issue forms
must remind users to review diagnostic content before publication.

## Required evidence

- focused tests for overwrite, collisions, input/output equality, atomic
  commit, cleanup, partial batch results, and exit codes;
- GUI and CLI tests for concise summaries and expanded failure details;
- report-redaction tests using paths, secrets, document content, and nested
  exceptions;
- an offline test proving conversion and local report generation make no
  network request;
- a manual GitHub issue workflow check that uses only explicit user action.
