# G1 renderer probes

This directory contains feasibility code only. It is not imported by
`libremark_pdf` and does not change production rendering.

`renderer_probe.py` checks deterministic logical fingerprints, literal
neutralization of an untrusted HTML fragment, JavaScript/service-worker browser
controls, a local data-only fixture, and deny-all routing for an attempted
remote image. Write generated JSON outside the repository:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/libremark-playwright-1223 \
  /tmp/libremark-g1-venv/bin/python spikes/g1/renderer_probe.py \
  --output /tmp/libremark-g1-renderer-probe.json
```

The probe is not the Lot 2 implementation. In particular, it does not parse and
embed arbitrary Markdown resources, sanitize trusted HTML, select final fonts,
or establish cross-platform visual equivalence.
