"""Characterization tests for deterministic document preparation."""

import hashlib
import unittest
from pathlib import Path

from libremark_pdf import core
from libremark_pdf.engine import document


class TestDocumentDomain(unittest.TestCase):
    def test_core_reexports_the_canonical_document_functions(self):
        for name in (
            "markdown_to_html", "extract_title", "resolve_render_date",
            "build_header_template", "build_footer_template", "build_full_html",
            "render_profile_for_options", "prepare_render_document",
        ):
            self.assertIs(getattr(core, name), getattr(document, name), name)
        self.assertNotIn(
            "libremark_pdf.core", Path(document.__file__).read_text(encoding="utf-8")
        )

    def test_fixed_templates_profile_and_html_remain_exact(self):
        cfg = core.HeaderFooterConfig(
            top_left="Fixed {title}", bottom_center="Page {page} / {total}"
        )
        prepared = core.prepare_render_document(
            "# Canonical\n\nBody with **bold**.",
            render_date="2026-07-14", header_footer=cfg,
        )
        self.assertEqual(
            hashlib.sha256(
                core.build_header_template(cfg, "2026-07-14").encode("utf-8")
            ).hexdigest(),
            "5f31dd6ecc2f7eece80e23938bb144e18c8576c80733927068640074f5168f9d",
        )
        self.assertEqual(
            hashlib.sha256(
                core.build_footer_template(cfg, "2026-07-14").encode("utf-8")
            ).hexdigest(),
            "f7869cc42a46365ece66451cfc2733174361fb0fc9f00c620cbc50c0c7a6003e",
        )
        self.assertEqual(
            prepared.profile.fingerprint,
            "a39b293f471e820e9afb87c46267de0776fa15c7ab68b69c9dae403af78c6805",
        )
        self.assertEqual(
            hashlib.sha256(prepared.full_html.encode("utf-8")).hexdigest(),
            "484685c815fe500442ce13bf7dd7b54a8124dc730e9b2895d6742dfa7d22d5af",
        )


if __name__ == "__main__":
    unittest.main()
