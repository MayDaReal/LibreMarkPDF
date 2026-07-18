# Local theme package contract

LibreMark PDF community themes are local, versioned, offline directories.
Installing a theme never downloads content. The built-in `default@1` theme is
an exact alias of the frozen root `style.css` and cannot be replaced or
removed.

## Manifest schema 1

Every package contains `theme.json` at its root. Paths use relative POSIX
syntax, even on Windows. All package files other than `theme.json` must appear
exactly once in `files` with a lowercase SHA-256 digest.

```json
{
  "schema": 1,
  "id": "example-theme",
  "version": "1",
  "name": {
    "en": "Example theme",
    "fr": "Thème d’exemple"
  },
  "render_profiles": ["default@1"],
  "css": "style.css",
  "licenses": ["LICENSE.txt"],
  "preview": {
    "markdown": "preview.md",
    "image": "preview.png"
  },
  "files": {
    "LICENSE.txt": "<sha256>",
    "preview.md": "<sha256>",
    "preview.png": "<sha256>",
    "style.css": "<sha256>"
  }
}
```

`preview.markdown` and `preview.image` are optional roles, but contribution
review requires a lightweight Markdown fixture and an explicitly reviewed
preview image before a new theme can be distributed. Tests and ordinary
conversion never regenerate or approve a golden preview.

IDs use lowercase ASCII letters, numbers, dots, underscores, or hyphens and
remain stable across updates. Versions use ASCII letters, numbers, dots,
underscores, or hyphens. The bilingual names are display text, not identifiers.
Schema 1 themes must declare compatibility with render profile `default@1`.

## Security and licence rules

The validator rejects:

- absolute paths, `..`, backslashes, symbolic links, and undeclared files;
- unsupported file types and missing or empty licence files;
- missing files, malformed digests, and hash mismatches;
- CSS `@import`, `url(...)`, scripts, `javascript:`, remote URLs, and `file:`
  URLs;
- remote/script content in preview Markdown and active or externally referenced
  SVG or image assets, whether or not they are selected as the preview;
- packages exceeding the core resource limits;
- the reserved `default` identifier and incompatible render profiles.

Theme CSS is inserted only by the shared core and receives the same embedded
fonts, deny-network browser policy, and deterministic A4 settings as the
default. A theme cannot introduce a second renderer or relax the Markdown trust
policy.

## Validate and test locally

```bash
python -m libremark_pdf theme show default@1 --json
python -m libremark_pdf theme install path/to/theme --json
python -m libremark_pdf theme list --json
python -m libremark_pdf convert sample.md --theme example-theme@1 --json
python -m libremark_pdf theme remove example-theme@1 --json
python -m unittest tests.test_themes -v
```

Installation validates into a sibling temporary directory and publishes the
complete directory atomically. Replacing an existing ID requires explicit
`--replace`. Removal first renames the installed directory, then deletes it.
The implementation restores the previous directory when replacement fails
before publication. If Windows temporarily locks a file after an atomic update
or removal, the selected registry state remains complete and a hidden cleanup
directory may remain for later housekeeping.

For a contribution, include the package, focused validator tests, the preview
fixture, before/after preview images, licence provenance, exact hashes, the
render-profile identity, and a named human visual review. Never update a
golden as a normal test side effect.
