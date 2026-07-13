# SVG Asset Forge contributor guide

## Scope

This guide applies only to `tools/svg-asset-forge/`. The repository root guide
also applies.

## Contract

- `sources/libremark-pdf-logo.svg` is the canonical editable master.
- `generate_assets.py` writes the six PNG sizes and the multi-size ICO to the
  repository-level `assets/` directory.
- Generation dependencies remain exactly pinned and build-only.
- Every output is replaced atomically and reported with its SHA-256 hash.
- Do not hand-edit generated PNG or ICO files.
- Do not change the master or its rendered appearance without explicit owner
  approval and visual review of representative sizes.

## Verification

Run the generator in an isolated environment using the commands in `README.md`.
Confirm that all expected files exist, the ICO contains every documented size,
transparent corners remain transparent, and no unrelated files change.
