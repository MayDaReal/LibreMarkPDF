# Third-party notices plan

The repository's MIT license covers LibreMark PDF source. It does not replace
the licenses of Python dependencies, Chromium, PDFium, fonts, icons, themes, or
other bundled resources.

No official binary notice bundle is claimed complete yet. Before a candidate
can pass the release gate, automation must derive an inventory from the exact
hashed dependency lock and packaged payload, then retain for every component:

- name, version/revision, source URL, archive or file SHA-256;
- SPDX identifier and complete license/copyright text;
- whether it is used at build time, runtime, or bundled in the artifact;
- notices or source-offer obligations; and
- the native artifact(s) containing it.

The release owner must compare the generated inventory with the PyInstaller
manifest, browser payload, fonts, themes, icons, and assets. Unknown, missing,
or incompatible licenses block publication. Font candidates and their current
research status are recorded separately in the G1 renderer spike report.
