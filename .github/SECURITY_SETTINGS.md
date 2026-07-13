# Repository security settings

An administrator must enable GitHub private vulnerability reporting, secret
scanning with push protection, Dependabot alerts, and branch protection for the
`quality` and `security` workflows. These hosted settings cannot be proven by
files in a checkout; record the enablement date and repository URL in release
evidence.

Playwright, Python-Markdown, and PDFium updates are intentionally excluded from
ordinary dependency automation. Their update pull requests must change the
platform lock, record the browser/inspection revision, and include renderer and
golden-review evidence.
