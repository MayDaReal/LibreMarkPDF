# ADR-007: Windows artifact format selection criteria

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

## Context

A PyInstaller one-file executable is convenient to download but extracts at
runtime and may increase startup time, temporary-disk usage, and antivirus
false positives. A zipped portable directory is less compact conceptually but
keeps runtime files explicit. The official format must be chosen from native
Windows evidence rather than appearance or build success.

## Decision

The portable zipped directory is the guaranteed fallback candidate. A one-file
artifact becomes the primary Windows x64 format only when it passes the same
functional and release gates and all additional criteria below.

Both candidates must be exercised on a clean native Windows x64 environment,
outside the repository, from paths containing spaces and Unicode, without
Python, an installed browser, Playwright cache, or runtime network access.

The one-file candidate must additionally demonstrate:

- no detection by the current Microsoft Defender definitions used for the
  recorded release test;
- median cold GUI startup no more than two seconds and no more than 25 percent
  slower than the portable-directory candidate on the reference system;
- end-to-end conversion no more than 10 percent slower under the recorded
  representative workload;
- complete temporary extraction cleanup after normal exit and failure;
- safe concurrent launches;
- actionable failure and cleanup under insufficient temporary disk space;
- correct behavior from Unicode and long supported paths.

Download size, extracted size, warm startup, preview time, conversion time,
temporary-disk peak, antivirus observations, and user steps must be recorded
for both candidates.

If the one-file candidate fails any mandatory criterion, the zipped portable
directory becomes the official primary format. Both formats may be published
only when each is independently validated and clearly distinguished.

## Measurement policy

Performance comparisons use the same immutable source, dependency lock,
renderer payload, resources, machine, power state, and fixture corpus. Reports
record individual runs, medians, warm-up policy, artifact hashes, Defender
version and definitions, and observed variance.

Passing PyInstaller alone is not acceptance evidence. The exact candidate must
pass GUI, CLI, preview, batch, offline, integrity, and visual-equivalence gates.
