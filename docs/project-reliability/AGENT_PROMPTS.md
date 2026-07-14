# Active agent assignment template

This file supplies the small amount of context that is specific to an assigned
reliability task. It does not restate the repository contract: `AGENTS.md`, the
active [`BACKLOG.md`](BACKLOG.md), the target architecture, and accepted ADRs
remain authoritative.

The complete prompts used through G1 are frozen in
[`archive/g1/AGENT_PROMPTS.md`](archive/g1/AGENT_PROMPTS.md). Do not copy them
into a new assignment; they contain closed-gate status and historical facts.

## Integrator bootstrap

```text
You are the LibreMark PDF integration owner for the current active gate.

Read AGENTS.md completely, inspect git status, then read the active backlog,
target architecture, relevant ADRs, and every AGENTS.md-required file for the
tasks you assign. Treat the local BASELINE_AUDIT.md as immutable historical
input and never edit, stage, or publish it.

Identify the first incomplete gate. Create an execution board containing task
IDs, owners, file boundaries, dependencies, acceptance evidence, and exact test
commands. Use separate worktrees for concurrent writers; in one shared
directory allow one writer at a time. The integrator alone changes task state.

Review evidence before acceptance. Do not infer production behavior from a
spike, official support from a successful build, or visual compatibility from
PDF byte equality. Stop for required human decisions. Record exact commands,
exit codes, environment, renderer/lock revision, artifact or report path and
hash, limitations, risk, and next dependency.
```

## Specialist assignment

Fill every bracket; omit no field. Add task-specific acceptance details from
the backlog or ADR instead of reproducing general repository rules.

```text
ROLE
You own [TASK IDS] for [GATE/LOT].

SCOPE
- Owned files: [EXACT FILES OR DIRECTORIES]
- Read first: AGENTS.md, [RELEVANT ADRS], [REQUIRED IMPLEMENTATION/TEST/DOCS]
- Dependencies/input evidence: [COMMITS, LOCKS, REPORTS, API CONTRACTS]
- Out of scope: [EXPLICIT NEIGHBORING OWNERSHIP]

OBSERVABLE ACCEPTANCE
- [BEFORE/AFTER BEHAVIOR]
- [FOCUSED REGRESSION TEST]
- [GATE-SPECIFIC EVIDENCE]

VERIFICATION
- [EXACT FOCUSED COMMAND]
- [EXACT GATE OR FULL-SUITE COMMAND]
- [NATIVE/ARTIFACT CHECK WHEN APPLICABLE]

HANDOFF
Return task state; owned files; before/after behavior; commands and exit codes;
OS/architecture; dependency lock and renderer revision where relevant;
evidence/artifact paths and SHA-256; limitations; risks; unverified items;
cross-owner requests; and next gate dependency.
```

## Review checklist

The integrator verifies that:

- shared conversion behavior remains in `libremark_pdf/core.py`;
- Python 3.9, local-first runtime, GUI/CLI/skill paths, and EN/FR parity remain;
- errors and tests were not weakened;
- renderer/default-style changes have accepted ADR and golden evidence;
- packaging and platform claims belong to the exact native artifact tested;
- generated browsers, builds, distributions, caches, PDFs, and secrets are not
  committed;
- public documentation is synchronized where the contract changed;
- evidence distinguishes observed, inferred, failed, and unverified results.

Use the smallest specialist team consistent with file ownership. A single
accountable core owner integrates security, resources, fonts, output planning,
and browser lifecycle changes; independent review may remain read-only.
