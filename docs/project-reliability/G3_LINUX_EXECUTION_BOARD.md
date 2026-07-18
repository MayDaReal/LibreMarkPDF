# Gate G3 Linux execution board

Status: **automated Ubuntu row complete — human and physical-offline review open**
Integration owner: **G3 integration owner**
Starting commit: `779ada2930e862e89b29789f49aa09cdf846ec46`

This board covers only `LNX-001` through `LNX-005`. It does not change the
mandatory Windows x64 decision, start macOS or Lot 4 work, advertise Linux, or
alter the independent open G2 PDFium `23-unicode` limitation.

| Task | Owner | Owned files | Dependencies | Before / after observable behavior | Focused command | Required evidence | State | Residual risk | Next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `LNX-001` | Linux packaging owner | Linux validation guide, lock and gate records | ADR-003, exact native host inventory | no declared candidate matrix or library floor / one explicit Ubuntu 24.04.4 x86_64 G3 row, CPython 3.9 baseline and observed GLIBC 2.38 symbol ceiling | `tools/run_g3_linux_candidate.sh --inspect-only ...` | OS/kernel/architecture/glibc/Python/lock identities and matrix status | evidence complete for declared G3 row | not a support promise; older glibc and other distributions remain unverified | G4 support decision before advertising |
| `LNX-002` | Linux packaging owner | Linux validation guide, build and evidence scripts | `LNX-001` | AppImage and tarball trade-offs unrecorded / onedir tarball selected; FUSE-free behavior, size and startup retained; AppImage explicitly not selected | `python -m unittest tests.test_linux_packaging -v` | format decision, tool/FUSE probes, size/startup observations | complete for selected format | AppImage behavior remains unverified and unclaimed | none for tarball candidate |
| `LNX-003` | Linux packaging owner | portable spec, Linux build script, lock, notices and packaging tests | Lots 3A–3C, pinned renderer resources | legacy build downloads and requests sudo / no-download onedir tarball with GUI, CLI, diagnostic entry paths and frozen resources | `./build_linux_portable.sh` | artifact inventory, dependency scan, browser/font/theme/licence hashes | complete for exact candidate `973469e` | system compatibility beyond the declared host remains unverified | G4 support matrix |
| `LNX-004` | native Linux matrix owner and named GUI reviewer | external evidence archive and Linux harness | `LNX-001`–`LNX-003` | no exact Linux evidence / Unicode-space external path passes no-Python, empty-cache, isolated-network, GUI smoke, CLI contracts and 31-fixture canonical comparison | `tools/run_g3_linux_candidate.sh --evidence-root ... --require-offline` | transcript, exact exits, manual screenshots/checklist, canonical report, artifact/SBOM hashes | automated portion complete; human review and physical-offline runner open | Xvfb smoke cannot prove real focus, scaling, contrast, DnD or desktop integration | named GUI review and physical-disconnection run |
| `LNX-005` | Linux packaging owner | Linux validation guide and evidence archive | exact candidate from `LNX-003` | generic dependency warning only / retained FUSE, user namespace, no `chrome-sandbox`, Playwright `--no-sandbox`, 153-ELF/zero-unresolved results | `tools/run_g3_linux_candidate.sh --evidence-root ...` | `/dev/fuse`, helpers, user namespace, sandbox disclosure, `ldd` and launch results | complete for exact candidate and host | process sandbox posture and host policy must be reconsidered before advertising | G4 security/support review |

## Gate rule

Linux G3 is evaluated independently and never blocks the mandatory Windows
lane. It may pass only after every advertised distribution/version and
architecture has reproducible native evidence for the exact candidate. Until
then the conclusion is:

`LINUX G3 NOT YET PASSED`

The declared Ubuntu automated row is complete, but named real-desktop GUI
review and the runner's physical-disconnection evidence remain open.
