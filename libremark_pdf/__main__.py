"""Dispatch arguments to the CLI and no-argument launches to the GUI."""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) > 1:
        from .cli import main as cli_main
        return cli_main(sys.argv[1:])

    from .gui import launch
    launch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
