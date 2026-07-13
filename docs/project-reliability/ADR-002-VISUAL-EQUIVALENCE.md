# ADR-002: Visual and structural equivalence contract

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

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
must satisfy all of these initial thresholds:

- SSIM greater than or equal to `0.995`;
- no more than `0.10%` of pixels exceeding an RGB-channel delta of `16`;
- no contiguous changed region larger than `0.50%` of a page.

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

After that review, the thresholds are frozen for the release program. Later
changes require a new superseding ADR and explicit golden review.

## Required evidence

Every release comparison report must record:

- fixture, theme, font, and render-profile hashes;
- renderer revision and inspection-tool version;
- operating system and architecture;
- page-level structural results and raster metrics;
- retained visual diff artifacts for every failure.
