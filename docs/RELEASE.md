# Release

The root `VERSION` file is the single version source for the application, CLI,
and candidates. It follows PEP 440: `0.1.0.dev1` for development, `0.1.0b1`
for beta, `0.1.0rc1` for a release candidate, and `0.1.0` for a stable release.

Each candidate is built natively under `dist/<version>/<platform>/`. It
contains the candidate, checksums, SBOM, manifest, automated reports, and human
checklist. The candidate packages localized PDF guides generated during the
build from the tracked Markdown manuals through LibreMark PDF's own CLI and the
tracked root stylesheet; the generated PDFs are not versioned.

A public beta requires complete automated validation on its platform. A stable
release also requires a completed human checklist, a valid canonical corpus
comparison, and applicable signatures. A successful build alone never makes a
release official.

The initial `v0.1.0` release scope is Windows x64. A Linux candidate validated
after an immutable `v0.1.0` publication is released under a later version; it
does not retroactively expand the platform promise of the published release.

Large archives, browsers, virtual environments, and generated PDFs are not
versioned. Concise reports, manifests, and checksums for a published release
may be versioned.
