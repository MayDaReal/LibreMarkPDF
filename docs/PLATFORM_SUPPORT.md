# Platform support

The initial `v0.1.0` support scope contains two independently validated lanes:
Windows x64 and Ubuntu 24.04 x86_64. A Windows artifact must be built and
validated on native Windows, outside the checkout, with its embedded browser
and without Python or a Playwright cache available at runtime.

The Linux portable tarball must be built and validated natively on Ubuntu
24.04 x86_64. Its release evidence records the desktop environment, display
server, glibc requirements, offline behavior, and GUI/CLI checks. This narrow
matrix makes no general Linux compatibility claim (aucune compatibilité Linux générale):
other distributions, versions, architectures, desktop environments, and
display servers are not supported unless separately validated. macOS remains
out of scope.

Playwright payloads are also platform-native. A shared checkout therefore keeps
generated Windows resources in `browser-win/` and Linux resources in
`browser-linux/`. Git ignores both directories.

Artifacts from different platforms are not interchangeable. Canonical
comparison verifies structural and visual equivalence; it does not promise
byte-identical PDFs.

Native canonical evidence retains exact text and PDFium geometry hashes per
reviewed platform. This does not conceal cross-platform semantic differences:
every advertised native matrix requires its own evidence and cross-platform
review.
