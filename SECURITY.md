# Security policy

## Supported versions

LibreMark PDF is currently a pre-release prototype. No released version is
receiving a formal security-support guarantee yet. Security fixes target the
current `main` branch until the first supported release policy is published.

The current renderer does not yet enforce the target network, raw-HTML, local
resource, custom-CSS, or overwrite protections. Convert only trusted Markdown
and CSS and avoid remote resources. These known limitations are tracked in
`docs/project-reliability/BACKLOG.md` and must not be reported as newly
discovered vulnerabilities without additional impact.

## Report a vulnerability privately

Use the repository's **Security** tab and select **Report a vulnerability** to
open a private GitHub security advisory. Include the affected commit/version,
operating system and architecture, reproduction steps, impact, and whether the
issue requires untrusted Markdown, CSS, HTML, or a built artifact.

If private vulnerability reporting is not enabled, open a public issue that
asks maintainers to establish a private contact channel. Do not include exploit
details, secrets, private documents, or a proof of concept in that issue.

Maintainers should acknowledge a private report within seven calendar days,
then provide a triage update or request for more information. Timelines for a
fix and disclosure depend on severity, affected releases, and coordination;
they will be agreed with the reporter rather than promised in advance.

Do not test against systems or documents you do not own, access third-party
data, degrade services, or publish an unresolved exploit. Good-faith local
testing and coordinated disclosure are welcome.
