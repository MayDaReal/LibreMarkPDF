# Documentation synchronization checklist

Use this checklist for every public-contract change.

- [ ] `README.md` describes the same supported behavior and limitations.
- [ ] `docs/MANUAL_EN.md` contains the complete English user workflow.
- [ ] `docs/MANUEL_FR.md` contains an idiomatic French equivalent with unchanged
      flags, tokens, paths, and identifiers.
- [ ] `python -m libremark_pdf convert --help` matches both manuals.
- [ ] `SKILL.md` uses the same command, JSON, verification, and safety contract.
- [ ] GUI text exists in both `libremark_pdf/i18n.py` tables with matching
      formatting placeholders.
- [ ] Build and platform validation guides make only evidence-backed claims.
- [ ] Version, renderer/profile identifiers, dependency locks, and known
      limitations are synchronized where relevant.
- [ ] Examples were exercised and their exit codes recorded.

Documentation-only editorial changes may mark non-applicable items explicitly.
