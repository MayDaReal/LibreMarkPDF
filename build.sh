#!/bin/bash
# build.sh — builds a standalone LibreMark PDF executable for Linux.
#
# Run this once on each Linux machine/distribution you want to support —
# PyInstaller builds are not reliably portable across distros with
# different glibc versions, so building locally is the safest approach.
#
# Usage:
#   chmod +x build.sh
#   ./build.sh

set -e
cd "$(dirname "$0")"

echo "=== LibreMark PDF build (Linux) ==="

if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "ERROR: the 'tkinter' module is missing."
  echo "Install it first, e.g. on Debian/Ubuntu: sudo apt install python3-tk"
  exit 1
fi

echo "--- Creating virtual environment ---"
python3 -m venv venv
source venv/bin/activate

echo "--- Installing Python dependencies ---"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "--- Downloading Chromium (bundled, local copy) ---"
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/browsers"
python -m playwright install chromium

echo "--- Installing Chromium's system dependencies (needs sudo) ---"
python -m playwright install-deps chromium || \
  echo "WARNING: could not install system dependencies automatically. \
See https://playwright.dev/python/docs/browsers#install-system-dependencies"

echo "--- Building the executable with PyInstaller ---"
python -m PyInstaller --noconfirm --clean LibreMarkPDF.spec

echo ""
echo "=== Build complete ==="
echo "Executable: dist/LibreMarkPDF"
echo ""
echo "To create a double-clickable launcher, run: ./make_desktop_launcher.sh"
