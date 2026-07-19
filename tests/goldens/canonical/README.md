# Reviewed canonical visual baseline

`expected.json` and its 34 PNGs are the approved, compact expected data for
the 31-fixture canonical corpus. The PNGs are required reference rasters for
the frozen 144-DPI visual thresholds; no generated PDF is committed.

The baseline is regenerated from complete Linux evidence for candidate commit
`1822a7c538558622a088ef464f15ddee408eef1d`, approved by `maydareal`, and
recorded by the signed local tag `g2-golden-regeneration-2026-07-18`.
`expected.json` retains the review identity and source-evidence SHA-256.

Normal harness execution never modifies these files.  Replacement requires
the separate `tools/update_visual_goldens.py` command, complete reviewed evidence,
and a named human review record.
