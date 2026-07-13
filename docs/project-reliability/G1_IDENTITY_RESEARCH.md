# Gate G1 identity availability research

Status: **research only; ADR-008 remains authoritative**
Research date: 2026-07-13
Legal status: **preliminary search, not legal advice or trademark clearance**

## Candidate comparison

Scores are 1–5 for distinction, purpose clarity, EN/FR speech, CLI suitability,
search intent, and community fit.

| Candidate | D | C | EN/FR | CLI | Search | Community | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LibreMark PDF | 4 | 5 | 5 | 5 | 3 | 5 | 27 |
| FolioDown PDF | 4 | 3 | 4 | 5 | 3 | 4 | 23 |
| SlateLeaf PDF | 4 | 3 | 4 | 5 | 2 | 4 | 22 |
| PageForge MD | 2 | 5 | 5 | 5 | 1 | 4 | 22 |
| MarkLeaf PDF | 2 | 4 | 5 | 5 | 1 | 4 | 21 |
| OpenQuill PDF | 2 | 3 | 5 | 5 | 1 | 4 | 20 |
| Markdown Foundry | 2 | 5 | 4 | 4 | 1 | 4 | 20 |
| Mardocelle PDF | 5 | 1 | 2 | 4 | 5 | 2 | 19 |

The historical shortlist is LibreMark PDF, FolioDown PDF, and SlateLeaf PDF.
It did not automatically approve LibreMark PDF; the repository owner's separate
approval is recorded in accepted ADR-008 and is not reopened here.

## Collision findings

Exact-name web and registry queries found no reproducible authoritative proof
that any shortlist name is available. Material adjacent or exact uses include:

- `LibreMark.org`, documented as a LibreMark policy since 2015:
  <https://libreplanet.org/wiki/Group%3ALibreMark>;
- the Folio Markdown application: <https://flathub.org/apps/com.toolstack.Folio>;
- Slate and Siteleaf Markdown products: <https://www.slatemd.app/> and
  <https://www.siteleaf.com/>;
- Markleaf Markdown/PDF products: <https://markleaf.app/> and
  <https://f-droid.org/en/packages/com.markleaf.notes/>;
- PageForge PDF products and PyPI package: <https://pageforge.dev/> and
  <https://pypi.org/project/pageforge/>;
- OpenQuill uses: <https://openquill.net/terms> and
  <https://www.openquill.app/>;
- Markdown Foundry extension:
  <https://marketplace.visualstudio.com/items?itemName=dvlprlife.mdfoundry>.

GitHub, PyPI, winget, Scoop, Homebrew, Debian, Fedora, Arch, and Flathub searches
did not surface an exact indexed shortlist package. Negative indexed searches
are not proof of availability. Recheck authenticated/current sources before any
reservation: <https://github.com/search>, <https://pypi.org/search/>,
<https://github.com/microsoft/winget-pkgs>,
<https://github.com/ScoopInstaller/Main>,
<https://github.com/ScoopInstaller/Extras>, <https://formulae.brew.sh/>,
<https://packages.debian.org/>, <https://packages.fedoraproject.org/>, and
<https://archlinux.org/packages/>. AUR, Snapcraft, openSUSE, Ubuntu PPAs,
registrar domain records, and authenticated social handles remain unverified.

Preliminary official trademark sources are INPI DATA INPI
(<https://www.inpi.fr/ressources/propriete-intellectuelle/rechercher-une-marque-base-marques>),
EUIPO/TMview (<https://www.euipo.europa.eu/en/search-ip>), USPTO
(<https://www.uspto.gov/trademarks/search>), and WIPO
(<https://www.wipo.int/en/web/global-brand-database>). Their interactive
portals did not yield a retained, reproducible result set here. A trained human
or counsel must search exact, phonetic, visual, related-goods, territory, owner,
and common-law variants. Existing LibreMark.org use is a material lead.

## Icon-direction research

The accepted master is
`tools/svg-asset-forge/sources/libremark-pdf-logo.svg`, SHA-256
`d25fdc3f8ca0d2306dae07340b55f68b09fef5689ccf37b2ea9573128a59883c`.
Three assessed directions are:

1. the adopted conversion bridge (current master), retaining page/hash/arrow at
   16 px and full detail at 128/512;
2. a responsive simplified `# -> PDF` family, which would improve small-size
   legibility but require a new owner/rights review;
3. a local-document seal emphasizing offline privacy, which weakens the direct
   Markdown-to-PDF story and would also require a new approval.

Only direction 1 is governance-compatible today. The small `CSS` label is not
legible at 16 px, no 512-pixel PNG exists, and directions 2/3 were not generated.
No asset or identity change is authorized by this research.

## Backlog recommendation

- BRD-001 and BRD-002: research evidence complete.
- BRD-003: in progress; authoritative package/domain/handle availability absent.
- BRD-004: in progress; official-source method recorded but no legal clearance.
- BRD-005: research concepts complete, literal multi-size alternative asset
  evidence incomplete.
