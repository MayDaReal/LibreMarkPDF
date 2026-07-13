# ADR-003: Supported platform and architecture policy

Status: **accepted**
Decision date: **2026-07-13**
Owner approval: **recorded explicitly during the reliability-program session**

## Context

A standalone desktop artifact is native to an operating system and processor
architecture. Build success on one platform is not evidence that another
platform is supported.

## Decision

Windows x64 is the first mandatory official release lane and the only initial
platform that may be advertised after passing its native Gate G4.

Linux and macOS are independent, optional release lanes. Neither may be listed
as supported or included in general portability claims until its own native
end-to-end Gate G4 passes on every advertised architecture.

The project will:

- build and validate a distinct native artifact for every advertised
  operating system and architecture;
- make no claim that one executable is universal across Windows, Linux, and
  macOS;
- require the exact candidate artifact to pass GUI, CLI, preview, batch,
  offline, external-path, integrity, and visual-equivalence checks;
- decide and document minimum OS versions during each native packaging spike,
  before making a support promise;
- treat a platform expansion as a separately gated release decision rather
  than a blocker for the first Windows x64 release.

Source compatibility with Python 3.9 does not constitute a supported native
artifact or an advertised platform.

## Consequences

- Windows x64 release work and evidence take priority.
- Linux distribution and architecture claims remain absent until the Linux
  lane passes.
- macOS architecture, signing, notarization, and hardware evidence remain
  future gated work.
- Documentation and repository metadata must distinguish source development
  environments from officially supported standalone artifacts.
