# Platform support

Windows x64 is the only platform in the initial `v0.1.0` support scope. A Windows artifact must
be built and validated on native Windows, outside the checkout, with its
embedded browser and without Python or a Playwright cache available at runtime.

Linux x86_64 is a separate candidate lane. The portable tarball is tested
against an explicitly declared matrix; no general Linux compatibility is
promised until that matrix has been validated — aucune compatibilité Linux générale
n’est annoncée avant cette validation. macOS remains out of scope.

Playwright payloads are also platform-native. A shared checkout therefore keeps
generated Windows resources in `browser-win/` and Linux resources in
`browser-linux/`. Git ignores both directories.

Artifacts from different platforms are not interchangeable. Canonical
comparison verifies structural and visual equivalence; it does not promise
byte-identical PDFs.

Native canonical evidence retains exact text and PDFium geometry hashes per
reviewed platform. This does not conceal cross-platform semantic differences:
Linux support still requires an explicit native matrix and a separate
cross-platform review before it can be advertised.
