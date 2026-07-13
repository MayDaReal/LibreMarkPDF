# Project reliability program

This directory contains the frozen audit reference and the execution package
for evolving LibreMark PDF into a high-reliability, local-first Markdown-to-PDF
product.

Read in this order:

1. [`BASELINE_AUDIT.md`](BASELINE_AUDIT.md) — immutable score and evidence
   captured on 2026-07-13 (**43/100**).
2. [`TARGET_ARCHITECTURE.md`](TARGET_ARCHITECTURE.md) — renderer,
   deterministic-output, and native-distribution decision.
3. [`BACKLOG.md`](BACKLOG.md) — task IDs, parallel waves, dependencies, gates,
   and acceptance criteria.
4. [`AGENT_PROMPTS.md`](AGENT_PROMPTS.md) — optimized orchestrator bootstrap and
   specialist prompts.

The baseline document must not be edited to reflect future work. At the end of
the backlog, an independent auditor creates a separate dated final report using
the unchanged scoring breakdown.
