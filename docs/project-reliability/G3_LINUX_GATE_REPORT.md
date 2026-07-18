# Gate G3 Linux report

Status: **LINUX G3 NOT YET PASSED — automated Ubuntu row complete**
Starting commit: `779ada2930e862e89b29789f49aa09cdf846ec46`
Scope: optional Linux tasks `LNX-001` through `LNX-005`

## Initial custody

- `git status --short --branch` returned `## main` and the pre-existing
  unrelated deletion
  ` D docs/project-reliability/G2_WINDOWS_EXECUTION_PROMPT.md`.
- `git rev-parse HEAD` returned
  `779ada2930e862e89b29789f49aa09cdf846ec46`.
- `git log -1 --show-signature` verified a good ED25519 signature for
  `maydareality@gmail.com`, key
  `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`.
- The immutable local `BASELINE_AUDIT.md` was read and will not be modified,
  staged or published. `docs/project-reliability/archive/g1/` remains
  immutable.
- The unrelated G2 prompt deletion will not be edited, staged, restored,
  moved or published.

## Authorization and boundaries

On 2026-07-18 the owner separately authorized the Linux part of G3 that can be
completed before returning to native Windows. This activates `LNX-001` through
`LNX-005` only. macOS, Lot 4, publication, upload, hosted settings,
credentials, signing, spending and pushing remain excluded. Linux must not be
advertised before its independent native gate passes.

The open G2 PDFium `23-unicode` extraction limitation remains a known,
independent cross-gate blocker. This work does not reopen, alter, weaken or
claim closure of G2.

## Initial host observation

- Ubuntu 24.04.4 LTS, kernel `6.17.0-35-generic`, x86_64;
- glibc 2.39;
- CPython 3.12.3 development environment and available CPython 3.9.23;
- Playwright 1.60.0 with Chromium headless shell revision 1223 staged in the
  user cache;
- `Xvfb` and `xvfb-run` available;
- the initial sandbox view hid `/dev/fuse`; the native evidence run found
  `/dev/fuse` mode `0666` and both `fusermount` helpers;
- unprivileged user namespaces enabled;
- no `appimagetool` found.

These observations describe one implementation host only. They do not define
or prove a supported distribution matrix.

## Acceptance direction

The owning module is native packaging and evidence tooling. The observable
target is a no-download Linux x86_64 onedir tarball with distinct GUI, CLI and
diagnostic entries, exact bundled renderer resources, and a repeatable runner
that tests the copied artifact outside the repository without Python or user
cache. The runner must retain host-library, Chromium sandbox, FUSE, offline,
canonical comparison, SBOM and artifact-integrity evidence.

## Exact candidate

- source commit:
  `973469e3e3076be1d2f91bbf01024566afae1379`;
- commit signature: good ED25519 signature for `maydareality@gmail.com`, key
  `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`;
- host: Ubuntu 24.04.4 LTS, kernel `6.17.0-35-generic`, native x86_64,
  glibc 2.39;
- build: CPython 3.9.23, PyInstaller 6.21.0, 15 exact hash-locked packages;
- renderer: Playwright 1.60.0, Chromium headless shell
  148.0.7778.96 revision 1223;
- artifact:
  `artifacts/LibreMarkPDF-linux-x86_64-candidate.tar.gz`, 214,791,795
  bytes, SHA-256
  `33dfdd7e2ee610c3ba21f57c16df1971373d49ff9c2e308616b1f6bf67b8aa19`;
- SPDX 2.3 SBOM: 16 packages and 921 files, 656,936 bytes, SHA-256
  `bc8f4ddd3726c8898e2e2c86e89d9e407c76884e8d40366a96da5db86f75177f`.

The candidate is unadvertised and unpublished. No release, upload, push,
credential, signing configuration or spending occurred.

## Commands and observable evidence

The authoritative runner command was:

```bash
tools/run_g3_linux_candidate.sh \
  --evidence-root "/tmp/G3 Evidence/LibreMark PDF – Linux x86_64" \
  --python /tmp/libremark-g3-linux-venv/bin/python \
  --browser-source /home/maydareal/.cache/ms-playwright
```

It exited `0`. Its final source suite ran 168 tests in 102.921 seconds and
passed. The build performed no dependency installation, browser download,
elevation or system change.

From the copied candidate path
`candidate external/LibreMark PDF – Linux x86_64`, with an empty home/cache and
a `PATH` directory containing no Python:

- candidate `doctor --json`: exit `0`, clean JSON, all resources present, and
  the bundled Linux Chromium executable reported;
- Unicode-and-space conversion: exit `0`;
- missing input: exit `1`, clean JSON;
- partial batch: exit `1`, one successful result plus one
  `INPUT_NOT_FOUND`, proving continuation;
- input/output collision: exit `1`, `INPUT_OUTPUT_COLLISION`;
- unwritable destination: exit `1`, `OUTPUT_UNAVAILABLE`;
- `default@1` theme conversion: exit `0`;
- GUI and diagnostic GUI Xvfb smoke: each remained responsive for five
  seconds and was intentionally ended by `timeout` (`124`);
- 153 ELF files inspected, maximum referenced GLIBC symbol 2.38, zero
  unresolved libraries, and no `chrome-sandbox` helper.

An ephemeral user/network namespace had a distinct namespace identity and its
real `ip`/`/proc/net/dev` view contained only a disabled loopback interface.
The exact candidate converted the Unicode-and-space input there with exit `0`.
The host Ethernet interface remained up outside the namespace, so the runner
was deliberately invoked without `--require-offline`.

Performance observation on this host:

- extracted onedir: 528,251,592 bytes;
- `doctor`: 0.07 seconds wall time, 22,160 KiB maximum RSS;
- one conversion: 12.72 seconds wall time, 893,140 KiB maximum RSS.

## Canonical comparison

All 31 immutable G2 fixtures were generated only through the exact frozen CLI
candidate. The final report is `pass` with no failures. Fixture `23-unicode`
also passes structurally and visually on this Linux host with SSIM 1.0 and
zero changed pixels. This Linux observation does not alter or close the
separate Windows PDFium G2 limitation.

The first long single-process attempt was externally terminated during
fixture 09 with child exit `-15`. Fixture 09 passed alone, and bounded recovery
batches completed 8, 16, 24 and finally all 31 fixtures. Expected data was
never written or updated.

Canonical hashes:

- report:
  `9e4207be6b8fe8dc5cd68b8177324168cb415fa854297e189013b1c257e61ab5`;
- actual evidence:
  `7b11575dceeecb37796f2e9cd7298348a297a4910aa4a8498ab94911ac46e137`;
- fixture manifest:
  `3118048f16c6d047efaf4bfe779c808fccac17ffbfade1192498b07b7434ecdb`;
- immutable expected data:
  `dd32efe4bb7728f80a4e9d7c47d77d7f136c3b54e6de37ddaa8184c08c277464`.

## Resource and evidence hashes

- Linux lock:
  `437f764fb28a462a00a50eb50ed41801bad9da059a570f37e39d7e8a746c9e04`;
- `style.css` / `default@1`:
  `abd57a32108e78e204706eb8d437d8c0b94c333245d3e5ce83cc31aec4d550a9`;
- evidence manifest:
  `2a561ecae44094eed55a3847b31427b34051ac7dffcfa661ac4dd4083dd727d3`;
- consolidated evidence archive: 215,559,687 bytes, SHA-256
  `8414de50b54fbb0f36212532ec568992af32e44c8e66407aa87af5c974de7626`.

The retained local handoff copies are under `dist/g3-linux/`, which is ignored
by Git: the candidate tarball, its checksum, the SPDX document, the complete
evidence archive and its checksum.

Exact font, icon, community-theme and input hashes are retained in
`logs/source-input-hashes.sha256`. Exact commands and output are retained in
`logs/g3-linux-transcript.txt`; the recovery and every failed experiment are
in `logs/canonical-recovery.txt` and `logs/failed-experiments.txt`.

## Format and host-policy decision

The portable onedir tarball is selected for G3. It has no FUSE dependency and
preserves separate GUI, CLI and diagnostic entries. `appimagetool` was absent;
`/dev/fuse`, `fusermount` and `fusermount3` were present. No AppImage was built
or claimed.

The bundled headless shell has no setuid sandbox helper and Playwright uses its
default `--no-sandbox` launch. Runtime document/network policy remains active,
but it is not a process sandbox. This is disclosed and must be reconsidered
before Linux is advertised.

## Failed experiments and limitations

- Three earlier runner revisions failed respectively because the Python venv
  symlink was resolved to its base interpreter, because a shell-function
  prefix did not export browser staging, and because source `doctor` selected
  the repository's Windows browser tree.
- Initial ELF inspection produced 12 false missing-sibling reports until it
  reproduced the PyInstaller runtime library path. The corrected exact scan
  reports zero unresolved libraries.
- The first archive attempt wrote inside its active source tree and tar
  detected a changing transcript. The corrected runner stages the archive
  outside the tree.
- The first offline namespace assertion used a host-mounted sysfs view. The
  corrected proof uses the namespace identity, `ip` and `/proc/net/dev`.
- Native AppImage behavior, other distributions/architectures, older glibc,
  Wayland, high-DPI scaling, real keyboard/focus/contrast behavior,
  drag-and-drop integration and desktop open actions remain unverified.
- The physical Ethernet adapter was up. The isolated namespace proves
  no-network execution, but `--require-offline` physical-adapter evidence is
  still open.
- `manual-linux-gui-review.md` remains explicitly incomplete.

## Task state

| Task | Result | Remaining dependency |
| --- | --- | --- |
| `LNX-001` | evidence complete for the declared Ubuntu 24.04.4 x86_64 G3 row | later G4 support matrix before advertising |
| `LNX-002` | complete for selected onedir tarball | AppImage remains unselected and unclaimed |
| `LNX-003` | complete for exact candidate `973469e` | other hosts remain unverified |
| `LNX-004` | automated portion complete | named real-desktop review and physical-offline runner |
| `LNX-005` | complete for exact host/candidate | later process-sandbox policy decision |

## Exact remaining work

| Remaining work | Owner | Exact command or decision | Classification |
| --- | --- | --- | --- |
| Real-desktop EN/FR accessibility and integration review | named Linux GUI reviewer | extract the candidate, then complete `manual-linux-gui-review.md` with retained screenshots/video for keyboard focus, contrast, scaling, DnD/fallback, preview, cancellation, collisions, open actions and themes | G3 blocker (`LNX-004`) |
| Physical-disconnection runner evidence | native Ubuntu owner | disconnect every non-loopback interface, then run the authoritative command above with `--require-offline` and archive the result | G3 blocker (`LNX-004`) |
| Decide any future advertised Linux support matrix | release owner at G4 | explicitly name distributions/versions/architectures and obtain exact native evidence for each | not a blocker for this unadvertised G3 implementation candidate |
| Resolve Windows PDFium `23-unicode` | separate G2 owner | retain the independent G2 command and decision | known separate G2 blocker; not a Linux G3 implementation blocker |

## Current decision

**LINUX G3 NOT YET PASSED**

Reason: the exact automated Ubuntu candidate evidence passes, but the named
real-desktop GUI review and physical-disconnection runner evidence are still
required.
