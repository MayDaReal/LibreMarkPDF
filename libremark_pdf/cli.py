"""Non-interactive command-line front end for LibreMark PDF."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from . import core


def _value_or_empty(value: Optional[str]) -> str:
    return value if value is not None else ""


def _build_header_footer(
    args: argparse.Namespace,
) -> Optional[core.HeaderFooterConfig]:
    fields = [
        args.header_left,
        args.header_center,
        args.header_right,
        args.footer_left,
        args.footer_center,
        args.footer_right,
    ]
    if all(f is None for f in fields):
        return None

    cfg = core.HeaderFooterConfig(
        top_left=_value_or_empty(args.header_left),
        top_center=_value_or_empty(args.header_center),
        top_right=_value_or_empty(args.header_right),
        bottom_left=_value_or_empty(args.footer_left),
        bottom_center=(
            args.footer_center if args.footer_center is not None
            else "Page {page} / {total}"
        ),
        bottom_right=_value_or_empty(args.footer_right),
    )
    return cfg


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT.md",
        help="One or more Markdown files to convert.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT.pdf",
        default=None,
        help="Output PDF path. Only valid with a single INPUT file.",
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        default=None,
        help="Output folder (used for batch conversion, or to redirect a single file "
        "while keeping its base name). Defaults to next to each source file.",
    )
    parser.add_argument(
        "--css",
        metavar="PATH",
        default=None,
        help="Path to a CSS file. Defaults to the bundled style.css.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output only after a successful conversion.",
    )
    parser.add_argument(
        "--trusted-html",
        action="store_true",
        help="Allow the approved static raw-HTML subset; active and network content remains blocked.",
    )
    parser.add_argument(
        "--render-date",
        metavar="YYYY-MM-DD",
        default=None,
        help="Fixed date used for {date} header/footer tokens.",
    )
    parser.add_argument("--header-left", default=None, metavar="TEXT")
    parser.add_argument("--header-center", default=None, metavar="TEXT")
    parser.add_argument("--header-right", default=None, metavar="TEXT")
    parser.add_argument("--footer-left", default=None, metavar="TEXT")
    parser.add_argument(
        "--footer-center",
        default=None,
        metavar="TEXT",
        help=(
            "Defaults to 'Page {page} / {total}'. Pass an empty value to "
            "remove it."
        ),
    )
    parser.add_argument("--footer-right", default=None, metavar="TEXT")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON result instead of human-readable text.",
    )


def _print_human(results: list[dict]) -> None:
    for r in results:
        if r["status"] == "ok":
            print(f"OK    {r['input']} -> {r['output']}")
        else:
            print(f"ERROR {r['input']}: {r['error']}", file=sys.stderr)


def cmd_convert(args: argparse.Namespace) -> int:
    """Execute a conversion request and return its process exit status."""
    if args.output and len(args.inputs) > 1:
        message = (
            "--output can only be used with a single input file; "
            "use --out-dir for batches."
        )
        if args.json:
            print(json.dumps({"status": "error", "error": message}))
        else:
            print(f"ERROR {message}", file=sys.stderr)
        return 1

    header_footer = _build_header_footer(args)

    if len(args.inputs) == 1 and args.output:
        results = []
        try:
            output_path = core.convert_markdown_to_pdf(
                args.inputs[0],
                args.output,
                css_path=args.css,
                header_footer=header_footer,
                render_date=args.render_date,
                trusted_html=args.trusted_html,
                overwrite=args.overwrite,
            )
            results.append(
                {
                    "input": args.inputs[0],
                    "output": str(output_path),
                    "status": "ok",
                    "error": None,
                    "error_code": None,
                }
            )
        except Exception as exc:
            # This is the CLI's user-facing boundary; core retains the cause in
            # the message and JSON must still be emitted for failures.
            results.append(
                {
                    "input": args.inputs[0],
                    "output": None,
                    "status": "error",
                    "error": str(exc),
                    "error_code": core.error_code(exc),
                }
            )
    else:
        results = core.convert_batch(
            args.inputs, output_dir=args.out_dir, css_path=args.css, header_footer=header_footer,
            render_date=args.render_date, trusted_html=args.trusted_html,
            overwrite=args.overwrite,
        )

    failed = any(result["status"] != "ok" for result in results)

    if args.json:
        payload = results[0] if len(results) == 1 else {"results": results}
        print(json.dumps(payload, indent=2))
    else:
        _print_human(results)

    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    """Create the complete non-interactive CLI parser."""
    parser = argparse.ArgumentParser(
        prog="libremark-pdf",
        description="Convert Markdown files to styled PDF documents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert one or more Markdown files to PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    _add_common_arguments(convert_parser)
    convert_parser.set_defaults(func=cmd_convert)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse `argv`, run the selected command, and return an exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
