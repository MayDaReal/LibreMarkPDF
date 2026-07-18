# Gate G3 Linux report

Status: **LINUX G3 NOT YET PASSED — implementation and native evidence active**
Starting commit: `779ada2930e862e89b29789f49aa09cdf846ec46`
Scope: optional Linux tasks `LNX-001` through `LNX-005`

## Initial custody

- `git status --short --branch` returned `## main` and the pre-existing
  unrelated deletion
  ` D docs/project-reliability/G2_WINDOWS_EXECUTION_PROMPT.md`.
- `git rev-parse HEAD` returned
  `779ada2930e862e89b29789f49aa09cdf846ec46`.
- `git log -1 --show-signature` verified a good ED25519 signature for
  `maydareality@gmail.com`, key
  `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`.
- The immutable local `BASELINE_AUDIT.md` was read and will not be modified,
  staged or published. `docs/project-reliability/archive/g1/` remains
  immutable.
- The unrelated G2 prompt deletion will not be edited, staged, restored,
  moved or published.

## Authorization and boundaries

On 2026-07-18 the owner separately authorized the Linux part of G3 that can be
completed before returning to native Windows. This activates `LNX-001` through
`LNX-005` only. macOS, Lot 4, publication, upload, hosted settings,
credentials, signing, spending and pushing remain excluded. Linux must not be
advertised before its independent native gate passes.

The open G2 PDFium `23-unicode` extraction limitation remains a known,
independent cross-gate blocker. This work does not reopen, alter, weaken or
claim closure of G2.

## Initial host observation

- Ubuntu 24.04.4 LTS, kernel `6.17.0-35-generic`, x86_64;
- glibc 2.39;
- CPython 3.12.3 development environment and available CPython 3.9.23;
- Playwright 1.60.0 with Chromium headless shell revision 1223 staged in the
  user cache;
- `Xvfb` and `xvfb-run` available;
- `fusermount` and `fusermount3` available, but `/dev/fuse` absent;
- unprivileged user namespaces enabled;
- no `appimagetool` found.

These observations describe one implementation host only. They do not define
or prove a supported distribution matrix.

## Acceptance direction

The owning module is native packaging and evidence tooling. The observable
target is a no-download Linux x86_64 onedir tarball with distinct GUI, CLI and
diagnostic entries, exact bundled renderer resources, and a repeatable runner
that tests the copied artifact outside the repository without Python or user
cache. The runner must retain host-library, Chromium sandbox, FUSE, offline,
canonical comparison, SBOM and artifact-integrity evidence.

Detailed commands, exit codes, hashes, failures and limitations will be added
as work proceeds. Task state is maintained in
[`G3_LINUX_EXECUTION_BOARD.md`](G3_LINUX_EXECUTION_BOARD.md).

## Current decision

**LINUX G3 NOT YET PASSED**

Reason: no exact Linux G3 candidate or declared multi-distribution native
matrix evidence exists yet.
