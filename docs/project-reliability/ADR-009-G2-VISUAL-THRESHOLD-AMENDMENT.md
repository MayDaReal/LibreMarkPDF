# ADR-009: G2 cross-platform visual-threshold amendment

Status: **accepted**
Decision date: **2026-07-18**
Owner approval: **maydareal, explicitly recorded during the G2 integration
session**

## Context

ADR-002 froze a `0.05%` maximum connected changed region after the G1 renderer
spike.  The exact G2 candidate commit
`1822a7c538558622a088ef464f15ddee408eef1d` has identical canonical HTML,
render-profile fingerprint, resources, page count, dimensions, extracted text,
links, and images on fresh Linux and native Windows evidence.  The only raster
failure is page 1 of fixture `09-inline-code`: SSIM `0.7036`, changed pixels
`0.3705%`, and largest connected changed region `0.0608%`.

The failed metric is narrowly above the previous ceiling; every other frozen
metric and every strict structural check passes.  The retained page diff is
part of the Linux/Windows comparison evidence.

## Decision

For Gate G2 canonical comparisons only, this ADR supersedes ADR-002's largest
connected changed-region ceiling from `0.05%` to `0.10%` of a page.  The other
limits remain unchanged:

- SSIM at least `0.70`;
- changed pixels at most `4.20%` at RGB-channel delta `16`;
- strict semantic, resource, geometry, and pagination equality.

This is not permission to weaken structural checks, change renderer inputs, or
accept any other visual difference.  The G1 archive and its historical `0.05%`
spike evidence remain immutable.  A further threshold change requires a new
superseding ADR and explicit owner golden review.

## Required evidence

- a signed local tag for the reviewed candidate commit;
- regenerated expected manifest and raster set from complete candidate evidence;
- a same-commit Linux comparison and native Windows comparison using the new
  ceiling;
- retained diff/report for `09-inline-code` and any other failure.
