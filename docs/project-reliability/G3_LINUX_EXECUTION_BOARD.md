# Gate G3 Linux execution board

Status: **active — optional Linux x86_64 lane explicitly authorized**
Integration owner: **G3 integration owner**
Starting commit: `779ada2930e862e89b29789f49aa09cdf846ec46`

This board covers only `LNX-001` through `LNX-005`. It does not change the
mandatory Windows x64 decision, start macOS or Lot 4 work, advertise Linux, or
alter the independent open G2 PDFium `23-unicode` limitation.

| Task | Owner | Owned files | Dependencies | Before / after observable behavior | Focused command | Required evidence | State | Residual risk | Next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `LNX-001` | Linux packaging owner | Linux validation guide, lock and gate records | ADR-003, exact native host inventory | no declared candidate matrix or library floor / explicit x86_64 candidate baseline, glibc floor and unadvertised test matrix | `tools/run_g3_linux_candidate.sh --inspect-only ...` | OS/kernel/architecture/glibc/Python/lock identities and matrix status | open | one host cannot establish distribution compatibility | native matrix execution |
| `LNX-002` | Linux packaging owner | Linux validation guide, build and evidence scripts | `LNX-001` | AppImage and tarball trade-offs unrecorded / reproducible comparison with one selected candidate format and accurate FUSE limits | `python -m unittest tests.test_linux_packaging -v` | format decision, tool/FUSE probes, size/startup observations | open | AppImage runtime and extraction vary by host | exact candidate build |
| `LNX-003` | Linux packaging owner | portable spec, Linux build script, lock, notices and packaging tests | Lots 3A–3C, pinned renderer resources | legacy build downloads and requests sudo / no-download onedir tarball build with GUI, CLI, diagnostic entry paths and frozen resources | `./build_linux_portable.sh` | artifact inventory, dependency scan, browser/font/theme/licence hashes | open | host glibc and Chromium shared libraries remain external | native matrix execution |
| `LNX-004` | native Linux matrix owner | external evidence archives and Linux harness | `LNX-001`–`LNX-003` | no exact Linux G3 artifact evidence / external Unicode-space path passes no-Python, empty-cache, offline, GUI/CLI and canonical tests | `tools/run_g3_linux_candidate.sh --evidence-root ... --require-offline` | transcripts, exit codes, screenshots/checklist, canonical report/diffs, artifact/SBOM hashes | open | current workspace represents only one Ubuntu host | remaining declared hosts and human GUI review |
| `LNX-005` | Linux packaging owner | Linux validation guide and evidence archive | exact candidate from `LNX-003` | generic dependency warning only / retained FUSE availability, AppImage fallback, Chromium sandbox and unresolved-library observations | `tools/run_g3_linux_candidate.sh --evidence-root ...` | `/dev/fuse`, fusermount, user namespace, sandbox permissions, `ldd` and launch results | open | container/desktop security policy differs from end-user systems | Linux G3 decision |

## Gate rule

Linux G3 is evaluated independently and never blocks the mandatory Windows
lane. It may pass only after every advertised distribution/version and
architecture has reproducible native evidence for the exact candidate. Until
then the conclusion is:

`LINUX G3 NOT YET PASSED`

