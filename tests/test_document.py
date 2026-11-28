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
            "5552d4415fad58535d226f5c901ad9d060bfadc0abe62265e354cce84175dcd4",
        )
        self.assertEqual(
            hashlib.sha256(prepared.full_html.encode("utf-8")).hexdigest(),
            "a4bfd28eb2319dee66ce754ec96854ee977d6d857df662170058240cdccac04c",
        )


if __name__ == "__main__":
    unittest.main()
