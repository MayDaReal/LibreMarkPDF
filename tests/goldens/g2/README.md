# Reviewed G2 visual baseline

`expected.json` and its 34 PNGs are the approved, compact expected data for
the 31-fixture Gate G2 corpus.  The PNGs are required reference rasters for
the frozen 144-DPI visual thresholds; no generated PDF is committed.

The baseline was generated from the complete Linux evidence for candidate
commit `90d7dafd282dfbac4cf1692e523f9410cb8a588d`, approved by `maydareal`,
and recorded by the signed local tag `g2-golden-initial-2026-07-14`.
`expected.json` retains the review identity and source-evidence SHA-256.

Normal harness execution never modifies these files.  Replacement requires
the separate `tools/update_g2_goldens.py` command, complete reviewed evidence,
and a named human review record.
