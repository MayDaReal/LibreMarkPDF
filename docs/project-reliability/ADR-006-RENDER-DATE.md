# ADR-006: Render date semantics

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

## Context

The `{date}` token must remain useful in normal conversions while producing a
single explainable value across a batch and a reproducible value in tests and
golden comparisons.

## Decision

- By default, the application resolves the local calendar date once when a
  conversion job starts.
- Every item in that job uses the same resolved date, including work that
  crosses midnight.
- The CLI provides an explicit `--date YYYY-MM-DD` option.
- The GUI provides an equivalent optional date control with idiomatic English
  and French labels and validation messages.
- The resolved date is included in the render profile, its diagnostics, and
  the structured JSON result.
- Automated tests, canonical fixtures, and golden comparisons must provide an
  explicit fixed date.
- File timestamps and document metadata are not implicit sources for `{date}`.

The render-profile fingerprint includes the resolved date when date expansion
can affect output. Two conversions using different resolved dates are not
considered identical render inputs.

## Validation

Invalid explicit dates fail before rendering with a stable actionable error.
The accepted format is the calendar form `YYYY-MM-DD`; locale-specific parsing
is not used.

Tests must cover default resolution, explicit resolution, invalid dates, one
date across a batch, midnight boundaries through an injected clock, CLI JSON,
and EN/FR GUI validation.
