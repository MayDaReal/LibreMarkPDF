"""PyInstaller entry point that preserves the ``libremark_pdf`` package context."""

from libremark_pdf.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
