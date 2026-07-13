# SVG Asset Forge

SVG Asset Forge produces the PNG and Windows ICO files used by LibreMark PDF.
It is a build-time tool and is not included in the application's runtime
dependencies.

`sources/libremark-pdf-logo.svg` is the canonical vector master approved by
the repository owner on 2026-07-13. It is original project artwork distributed
under the repository's MIT license.

The small `CSS` label is stored as vector paths, so the master does not depend
on an installed font. Those three glyph outlines were derived from Liberation
Sans Bold, distributed under the SIL Open Font License 1.1. The source font
used during outlining had SHA-256:

```text
3973aa5054fb467dd5627245d3dc82e37bf16fe075756156a570455871351582
```

## Set up and run

Use Python 3.10 or newer in a temporary build environment:

```bash
python3 -m pip install -r tools/svg-asset-forge/requirements.txt
python3 tools/svg-asset-forge/generate_assets.py
```

The script creates the six application PNG sizes and the multi-size Windows
ICO under `assets/`. It prints SHA-256 hashes for the source and every output.
The generation tools are build-only and are not runtime dependencies.

The generated files are application resources and remain under `assets/`.
Do not edit them manually. Any visual change to the master requires explicit
owner review before regeneration.

The owner visually approved the transparent-background derivatives at 16, 32,
and 256 pixels on 2026-07-13. Automated inspection also confirmed transparent
corner pixels and the expected six embedded ICO sizes from 16 through 256
pixels.
