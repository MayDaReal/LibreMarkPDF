# ADR-010: PDFium visible-text geometry tolerance

Status: **accepted**
Decision date: **2026-07-18**
Owner approval: **maydareal, explicitly recorded during the G2 integration
session**

## Context

ADR-002 required exact PDFium character-box hashes. That makes the comparison
dependent on the inspection library's platform-specific interpretation of PDF
font metrics rather than only on the rendered document contract.

For the exact candidate commit
`1822a7c538558622a088ef464f15ddee408eef1d`, Linux and native Windows have
identical canonical HTML, render-profile fingerprint, resources, page count,
page dimensions, links, image counts, and pagination. The regenerated
comparison shows different `text_geometry_sha256` values on all fixtures.

The retained Linux/Windows PDFs were measured directly with pinned PDFium
5.11.0. On every page whose extracted character sequence is exactly equal, the
maximum absolute difference of any coordinate of any **visible** character box
is `1.8553619385 pt` (fixture `09-inline-code`, emoji `✅`). Whitespace boxes
vary more because PDFium represents advance space rather than a painted glyph;
carriage-return and line-feed boxes are control artifacts and can span the
page. The prior observed `5.0367 pt` maximum is a whitespace-box coordinate,
not movement of visible text.

One fixture, `23-unicode`, has an extracted-text difference between platforms:
Linux reports `हि न्दी`; Windows reports `हिन्दी`. It is a semantic failure and
is deliberately outside this tolerance.

## Decision

For Gate G2 cross-platform comparison, this ADR supersedes only the exact
PDFium character-box hash requirement in ADR-002 and the target architecture.
The harness must instead require all of the following:

- exact extracted Unicode text and reading order, including character count;
- exact page count and page dimensions;
- exact canonical HTML, render-profile, resource, link, and image inventory;
- for each non-whitespace, non-control extracted character, an absolute
  difference of at most `2.00 pt` in each PDFium character-box coordinate;
- unchanged ADR-009 raster thresholds and the strict semantic, resource,
  geometry, and pagination checks.

The tolerance applies only to the inspector's per-character box coordinates.
It does not permit changed line breaks, altered text, moved visible layout,
different margins, pages, links, images, or a failed visual metric. It must be
reported page by page, including the largest observed visible-character delta.

## Rationale and limits

`2.00 pt` is the smallest rounded ceiling above the measured `1.8554 pt`
envelope. It is not derived from the earlier whitespace/control-box outliers.
The independent 144-DPI visual thresholds, strict pagination checks, and exact
text/order check continue to detect user-visible layout changes. This decision
does not close the `23-unicode` text-extraction discrepancy.

Any increase, change in which characters are excluded, renderer/PDFium update,
or use beyond G2 requires a new superseding ADR and explicit owner review.

## Required evidence

- harness implementation and focused boundary tests for `2.00 pt`, control,
  whitespace, and text-order behavior;
- regenerated Linux and native Windows reports for the exact same candidate;
- a retained per-page maximum-delta report;
- a separate resolution of the `23-unicode` extracted-text mismatch before G2
  may pass.
