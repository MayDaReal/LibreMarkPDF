# Gate G3 Windows report

Status: **active — no decision**  
Starting commit: `7b147a027e18a93d15000ac5d43cb810eb03d9a2`  
Scope: mandatory Windows x64 Lots 3A, 3B, 3C, and 3D

## Initial custody

- `git status --short --branch` returned `## main` and the pre-existing deletion
  ` D docs/project-reliability/G2_WINDOWS_EXECUTION_PROMPT.md`.
- `git rev-parse HEAD` returned
  `7b147a027e18a93d15000ac5d43cb810eb03d9a2`.
- `git log -1 --show-signature` verified a good ED25519 signature for
  `maydareality@gmail.com`, key
  `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`, on commit
  `7b147a027e18a93d15000ac5d43cb810eb03d9a2` (`Record Unicode extraction
  limitation`).
- The local immutable `BASELINE_AUDIT.md` was read and was not modified,
  staged, or published.
- `docs/project-reliability/archive/g1/` is immutable and will not be changed.
- The pre-existing G2 prompt deletion is unrelated owner work and will not be
  edited, staged, restored, moved, or published.

## Authorization and exclusions

The owner explicitly authorized G3 implementation and evaluation while G2 is
open. This report does not reopen, alter, weaken, or claim closure of G2. macOS
tasks `MAC-001` through `MAC-005`, optional Linux distribution tasks `LNX-001`
through `LNX-005`, Lot 4, release publication, hosted settings, credentials,
signing setup, release upload, spending, pushing, and baseline/G1 changes are
excluded.

## Known cross-gate limitation

G2 retains fixture `23-unicode` and the pinned PDFium 5.11.0 extraction
difference: Linux reports `हि न्दी`, while retained native Windows evidence
reports `हिन्दी`. The owner directed that it not be normalized, ignored,
thresholded, removed, or treated as accepted. It remains a separate G2 blocker
and regression target. It does not block Lot 3 implementation or the recording
of native Windows G3 candidate evidence.

## Contract discrepancy found before implementation

ADR-006 names the canonical explicit render-date option `--date YYYY-MM-DD`.
The current CLI, README, both manuals, and `SKILL.md` expose
`--render-date YYYY-MM-DD`. G3 will preserve the shipped spelling as a legacy
alias while aligning the approved public contract; no renderer behavior or
date semantics will be changed silently.

## Environment

The integration workspace is Linux, not native Windows. Native Windows edition,
build, x64 architecture, exact artifact behavior, disconnected-network state,
AV observations, Authenticode status, GUI screenshots, and Windows performance
must come from a clean native Windows x64 execution of the exact candidate.
Until that evidence is returned and verified, Windows G3 cannot pass.

## Command log

| Command | Exit | Result |
| --- | ---: | --- |
| `git status --short --branch && git rev-parse HEAD && git log -1 --show-signature` | 0 | Initial custody recorded as above. |
| `rg --files` with generated/build/browser exclusions | 0 | Repository inputs inventoried; no generated artifacts searched. |
| Complete reads required by the owner and `AGENTS.md` | 0 | Contracts, reliability records, implementation, relevant tests, packaging inputs, locks, and Windows validation guide read before code changes. |

Detailed implementation, failed experiments, command outputs, hashes, native
environment data, evidence paths, limitations, and final decision will be
appended as work proceeds. Task state is maintained in
[`G3_EXECUTION_BOARD.md`](G3_EXECUTION_BOARD.md).

## Current decision

**WINDOWS G3 NOT YET PASSED**

Reason: implementation and exact native Windows x64 candidate evidence are not
yet complete. This is a G3 status, separate from the known G2 blocker.
