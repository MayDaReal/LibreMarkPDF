# ADR-002: Visual and structural equivalence contract

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**
Threshold amendment date: **2026-07-14**
Threshold amendment approval: **explicitly approved by the owner after review
of the exact flagged Windows/Linux pair**

## Context

Native Windows, Linux, and macOS artifacts cannot be expected to produce
byte-identical PDF serialization. The product nevertheless requires strict,
repeatable equivalence for every user-visible and structural result generated
from the same versioned inputs and render profile.

## Decision

Given identical Markdown bytes, theme, render profile, options, and local
resources, every advertised platform must produce output with:

- identical page count and dimensions;
- identical extracted text and reading order;
- identical headings, links, images, headers, and footers;
- identical margins, line breaks, pagination, table geometry, and image
  placement;
- identical canonical pre-render HTML and render-profile fingerprint.

Canonical pages are rasterized with the pinned inspection tool at 144 DPI and
must satisfy all of these frozen thresholds:

- SSIM greater than or equal to `0.70`;
- no more than `4.20%` of pixels exceeding an RGB-channel delta of `16`;
- no contiguous changed region larger than `0.05%` of a page.

Any semantic, missing-resource, geometry, or pagination difference fails the
contract regardless of raster metrics.

PDF byte identity is not required. Volatile metadata, document identifiers,
compression, and object serialization may differ when they do not change the
structural or rendered result.

## Threshold freeze policy

The renderer feasibility spike must test these thresholds on native Windows
x64 and at least one second operating system. The thresholds may be amended
once if measured antialiasing variance produces false failures. Any amendment
requires recorded evidence, owner approval, and an explicit update to this ADR
before Gate G1. Thresholds must not be relaxed merely to pass a failing build.

The one permitted review was completed on 2026-07-14. The exact selected
Windows/Linux profile had equal canonical HTML, profile fingerprints, page
count, page dimensions, and extracted text. Its two pages measured SSIM
`0.71837`/`0.70820`, changed pixels `3.1196%`/`4.0963%`, and largest changed
regions `0.01732%`/`0.02224%`. Retained diffs showed distributed glyph-edge
antialiasing rather than geometry movement. Both platforms repeated exactly
within-platform.

The amended limits accept that measured cross-OS antialiasing envelope while
tightening the contiguous-region limit. They still reject the earlier
geometry failures independently through exact structural checks, SSIM below
`0.70`, and changed regions above `0.05%`. The owner approved the candidate
appearance and this amendment explicitly. The thresholds are now frozen for
the release program; later changes require a superseding ADR and explicit
golden review.

## Required evidence

Every release comparison report must record:

- fixture, theme, font, and render-profile hashes;
- renderer revision and inspection-tool version;
- operating system and architecture;
- page-level structural results and raster metrics;
- retained visual diff artifacts for every failure.
