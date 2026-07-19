# Platform support

Windows x64 is the first mandatory candidate platform. A Windows artifact must
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
