"""PyInstaller dispatcher for authoritative GUI, CLI, and diagnostic binaries."""

import sys
from pathlib import Path

from libremark_pdf.__main__ import main


def frozen_main() -> int:
    """Dispatch by frozen executable identity while retaining source fallback."""
    executable = Path(sys.argv[0]).stem.lower()
    if executable == "libremarkpdf-cli":
        from libremark_pdf.cli import main as cli_main
        return cli_main(sys.argv[1:])
    if executable in ("libremarkpdf", "libremarkpdf-debug"):
        from libremark_pdf.gui import launch
        launch()
        return 0
    return main()


if __name__ == "__main__":
    raise SystemExit(frozen_main())
