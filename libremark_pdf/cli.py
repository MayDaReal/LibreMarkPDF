"""Non-interactive command-line front end for LibreMark PDF."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from . import core
from . import __version__


class CliUsageError(ValueError):
    """Command-line validation failure rendered by the selected output mode."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


class _VersionAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS,
                 help=None):
        super().__init__(
            option_strings=option_strings, dest=dest, default=default,
            nargs=0, help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        parser._print_message(version_text() + "\n", sys.stdout)
        parser.exit()


def _json_text(payload: dict) -> str:
    return json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    )


def _error_payload(message: str, code: str = "INVALID_ARGUMENT") -> dict:
    return {
        "error": message,
        "error_code": code,
        "input": None,
        "output": None,
        "status": "error",
    }


def version_payload() -> dict:
    """Return application and pinned renderer identities."""
    return dict({"application": "LibreMark PDF", "version": __version__},
                **core.renderer_identity())


def version_text() -> str:
    identity = version_payload()
    return (
        "{application} {version}; render-profile {render_profile}; "
        "Playwright {playwright_version}; Chromium {chromium_version} "
        "(revision {chromium_revision})"
    ).format(**identity)


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
        "--theme",
        metavar="ID[@VERSION]",
        default=None,
        help="Select a validated installed theme. Cannot be combined with --css.",
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
        "--date",
        "--render-date",
        dest="render_date",
        metavar="YYYY-MM-DD",
        default=None,
        help=(
            "Fixed date used for {date} header/footer tokens. "
            "--render-date is retained as a legacy alias."
        ),
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
    message = None
    if args.css and args.theme:
        message = "--css and --theme cannot be used together."
    elif args.output and args.out_dir:
        message = "--output and --out-dir cannot be used together."
    elif args.output and len(args.inputs) > 1:
        message = "--output can only be used with a single input file; use --out-dir for batches."
    if message is not None:
        if args.json:
            print(_json_text(_error_payload(message)))
        else:
            print(f"ERROR {message}", file=sys.stderr)
        return 1

    header_footer = _build_header_footer(args)

    profile = None
    try:
        profile = core.render_profile_for_options(
            css_path=args.css,
            header_footer=header_footer,
            render_date=args.render_date,
            trusted_html=args.trusted_html,
            theme=args.theme,
        )
    except Exception as exc:
        results = [
            {
                "input": item,
                "output": None,
                "status": "error",
                "error": str(exc),
                "error_code": core.error_code(exc),
            }
            for item in args.inputs
        ]
    else:
        args.render_date = profile.render_date

    if profile is not None and len(args.inputs) == 1 and args.output:
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
                theme=args.theme,
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
    elif profile is not None:
        results = core.convert_batch(
            args.inputs, output_dir=args.out_dir, css_path=args.css, header_footer=header_footer,
            render_date=args.render_date, trusted_html=args.trusted_html,
            overwrite=args.overwrite, theme=args.theme,
        )

    if profile is not None:
        identity = core.renderer_identity()
        diagnostics = {
            "chromium_revision": identity["chromium_revision"],
            "chromium_version": identity["chromium_version"],
            "playwright_version": identity["playwright_version"],
            "render_date": profile.render_date,
            "render_profile": profile.profile_version,
            "renderer_fingerprint": profile.fingerprint,
            "theme": args.theme or core.DEFAULT_THEME_ID,
        }
        for result in results:
            result.update(diagnostics)

    failed = any(result["status"] != "ok" for result in results)

    if args.json:
        payload = results[0] if len(results) == 1 else {"results": results}
        print(_json_text(payload))
    else:
        _print_human(results)

    return 1 if failed else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Inspect bundled identities and resources without launching Chromium."""
    identity = version_payload()
    required = {
        "css": core.DEFAULT_CSS_PATH.is_file(),
        "fonts": core.FONTS_DIR.is_dir() and all(
            (core.FONTS_DIR / item[0]).is_file() for item in core._FONT_FILES
        ),
        "icons": core.ICONS_DIR.is_dir(),
        "license": core.resource_path("LICENSE").is_file(),
        "default_theme": core.show_theme(core.DEFAULT_THEME_ID).css_path.is_file(),
        "browser": bool(identity["browser_executables"]),
    }
    payload = dict(identity, resources=required)
    payload["status"] = "ok" if all(required.values()) else "error"
    payload["error"] = None if payload["status"] == "ok" else "One or more bundled resources are missing."
    payload["error_code"] = None if payload["status"] == "ok" else "RESOURCE_MISSING"
    if args.json:
        print(_json_text(payload))
    else:
        print(version_text())
        for name in sorted(required):
            print("{0}: {1}".format(name, "ok" if required[name] else "missing"))
        if payload["error"]:
            print("ERROR " + payload["error"], file=sys.stderr)
    return 0 if payload["status"] == "ok" else 1


def _theme_result(action, args: argparse.Namespace) -> int:
    try:
        payload = action()
        status = 0
    except Exception as exc:
        payload = _error_payload(str(exc), core.error_code(exc))
        status = 1
    if args.json:
        print(_json_text(payload))
    elif status == 0:
        if isinstance(payload, list):
            for item in payload:
                print(item["reference"] + "  " + item["name"]["en"])
        else:
            print(payload["reference"])
    else:
        print("ERROR " + payload["error"], file=sys.stderr)
    return status


def cmd_theme_list(args: argparse.Namespace) -> int:
    return _theme_result(
        lambda: [item.as_dict() for item in core.list_themes()], args
    )


def cmd_theme_show(args: argparse.Namespace) -> int:
    return _theme_result(lambda: core.show_theme(args.reference).as_dict(), args)


def cmd_theme_install(args: argparse.Namespace) -> int:
    return _theme_result(
        lambda: core.install_theme(args.package, replace=args.replace).as_dict(),
        args,
    )


def cmd_theme_remove(args: argparse.Namespace) -> int:
    return _theme_result(lambda: core.remove_theme(args.reference).as_dict(), args)


def build_parser() -> argparse.ArgumentParser:
    """Create the complete non-interactive CLI parser."""
    parser = _ArgumentParser(
        prog="libremark-pdf",
        description="Convert Markdown files to styled PDF documents.",
    )
    parser.add_argument(
        "--version",
        action=_VersionAction,
        help="Show application and renderer identities, then exit.",
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=_ArgumentParser
    )

    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert one or more Markdown files to PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    _add_common_arguments(convert_parser)
    convert_parser.set_defaults(func=cmd_convert)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Inspect bundled resources without launching or downloading a browser.",
    )
    doctor_parser.add_argument(
        "--json", action="store_true", help="Print a machine-readable diagnostic."
    )
    doctor_parser.set_defaults(func=cmd_doctor)

    theme_parser = subparsers.add_parser(
        "theme", help="Manage validated local community themes."
    )
    theme_commands = theme_parser.add_subparsers(
        dest="theme_command", required=True, parser_class=_ArgumentParser
    )
    theme_list = theme_commands.add_parser("list", help="List available themes.")
    theme_list.add_argument("--json", action="store_true")
    theme_list.set_defaults(func=cmd_theme_list)
    theme_show = theme_commands.add_parser("show", help="Show one theme.")
    theme_show.add_argument("reference", metavar="ID[@VERSION]")
    theme_show.add_argument("--json", action="store_true")
    theme_show.set_defaults(func=cmd_theme_show)
    theme_install = theme_commands.add_parser(
        "install", help="Validate and install a local theme package."
    )
    theme_install.add_argument("package", metavar="DIRECTORY")
    theme_install.add_argument(
        "--replace", action="store_true", help="Atomically replace an installed id."
    )
    theme_install.add_argument("--json", action="store_true")
    theme_install.set_defaults(func=cmd_theme_install)
    theme_remove = theme_commands.add_parser(
        "remove", help="Atomically remove an installed local theme."
    )
    theme_remove.add_argument("reference", metavar="ID[@VERSION]")
    theme_remove.add_argument("--json", action="store_true")
    theme_remove.set_defaults(func=cmd_theme_remove)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse `argv`, run the selected command, and return an exit status."""
    arguments = list(argv) if argv is not None else sys.argv[1:]
    parser = build_parser()
    try:
        args = parser.parse_args(arguments)
        return args.func(args)
    except CliUsageError as exc:
        if "--json" in arguments:
            print(_json_text(_error_payload(str(exc))))
        else:
            print("ERROR {0}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
