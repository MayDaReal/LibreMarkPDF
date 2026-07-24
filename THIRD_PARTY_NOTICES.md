# Third-party notices for candidate validation

The repository's MIT license covers LibreMark PDF source. It does not replace
the licenses of Python dependencies, Chromium, PDFium, fonts, icons, themes, or
other bundled resources.

The native validation workflows generate SPDX 2.3 JSON inventories from the exact
hashed Windows or Linux dependency lock and every file in the corresponding
packaged candidate. Those inventories are candidate evidence, not a claim that
an official release notice review is complete.

The current locked Python components and declared licence expressions are:

| Components | Licence expression |
| --- | --- |
| CustomTkinter | MIT |
| darkdetect | BSD-3-Clause |
| Markdown | BSD-3-Clause |
| Playwright, importlib-metadata, coverage, PyInstaller hooks | Apache-2.0 |
| pyee, altgraph, pefile, setuptools, Ruff, zipp | MIT |
| greenlet | MIT AND PSF-2.0 |
| Pillow | MIT-CMU |
| packaging | Apache-2.0 OR BSD-2-Clause |
| pypdfium2 | BSD-3-Clause AND Apache-2.0, with bundled PDFium third-party terms |
| pywin32-ctypes | BSD-3-Clause |
| PyInstaller | GPL-2.0-or-later WITH Bootloader-exception |
| tkinterdnd2 | MIT |
| typing-extensions | PSF-2.0 |

The application also includes a selected local subset of Bootstrap Icons
1.11.1 under MIT. Its source SVG files, generated runtime PNG variants and
origin manifest are under `assets/ui-icons/`; its complete licence is retained
as `licenses/Bootstrap-Icons-LICENSE.txt`. CustomTkinter's complete bundled MIT
licence is retained as `licenses/CustomTkinter-LICENSE.txt`.

CustomTkinter 6.0.0's wheel contains that MIT licence and an MIT classifier,
but its legacy `License` metadata field incorrectly says
`Creative Commons Zero v1.0 Universal`. Upstream confirmation and correction
are tracked in https://github.com/TomSchimansky/CustomTkinter/issues/2857.

The exact versions and platform-specific archive SHA-256 values are in
`requirements/locks/windows-x64-py39.txt` and
`requirements/locks/linux-x86_64-py39.txt`; the applicable records are copied
into each generated SBOM. Chromium/headless shell `148.0.7778.96` revision
`1223` carries its packaged `LICENSE.headless_shell`; the evidence inventory
hashes that file and the complete browser payload.

The seven bundled Noto faces are licensed under OFL-1.1. Their retained texts
are:

- `licenses/NotoDistribution-OFL.txt`;
- `licenses/NotoCJK-OFL.txt`;
- `licenses/NotoEmoji-OFL.txt`;
- `licenses/NotoSansSymbols2-OFL.txt`.

The built-in `default@1` theme is an exact alias of the project `style.css` and
is covered by the root MIT licence. Every community theme package must provide
and hash its own licence files. Project icons and brand assets ship with the
root MIT licence.

Before publication, the release owner must still retain for every component:

- name, version/revision, source URL, archive or file SHA-256;
- SPDX identifier and complete license/copyright text;
- whether it is used at build time, runtime, or bundled in the artifact;
- notices or source-offer obligations; and
- the native artifact(s) containing it.

The release owner must compare the generated inventory with the PyInstaller
manifest, browser payload, fonts, themes, icons, and assets. Unknown, missing,
or incompatible licences block publication. Automated validation does not
replace the publication licence review.
