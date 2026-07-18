#!/usr/bin/env bash
# Build the Linux x86_64 onedir candidate and normalized tar.gz archive.
#
# This script never installs dependencies, downloads Chromium, invokes sudo,
# or changes host configuration. Prepare the locked CPython 3.9 environment
# and exact Playwright browser payload before running it.

set -euo pipefail
cd "$(dirname "$0")"

python_bin="${LIBREMARK_PDF_PYTHON:-python}"
browser_source="${LIBREMARK_PDF_BROWSER_SOURCE:-browsers}"
dist_path="${LIBREMARK_PDF_DISTPATH:-$PWD/dist}"
work_path="${LIBREMARK_PDF_WORKPATH:-$PWD/build}"
lock_path="$PWD/requirements/locks/linux-x86_64-py39.txt"
archive_name="LibreMarkPDF-linux-x86_64-candidate.tar.gz"

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "[FAILED] This candidate build requires native Linux x86_64." >&2
  exit 1
fi
if [[ ! -x "$python_bin" ]] && ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "[FAILED] CPython executable is unavailable: $python_bin" >&2
  exit 1
fi
if ! "$python_bin" -c \
  "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)"
then
  echo "[FAILED] This candidate build requires CPython 3.9." >&2
  exit 1
fi
if ! "$python_bin" -c \
  "import PyInstaller; raise SystemExit(0 if PyInstaller.__version__ == '6.21.0' else 1)"
then
  echo "[FAILED] PyInstaller 6.21.0 is required." >&2
  exit 1
fi
"$python_bin" tools/verify_locked_environment.py --lock "$lock_path"

browser_source="$(realpath "$browser_source")"
browser_executable="$browser_source/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell"
if [[ ! -x "$browser_executable" ]]; then
  echo "[FAILED] Exact Chromium headless shell revision 1223 is unavailable." >&2
  exit 1
fi
if find "$browser_source" -maxdepth 1 -type d -name 'chromium*' \
  ! -name 'chromium_headless_shell-1223' -print -quit | grep -q .
then
  echo "[FAILED] Browser source contains an unapproved Chromium payload." >&2
  exit 1
fi

mkdir -p "$dist_path" "$work_path"
export LIBREMARK_PDF_BROWSER_SOURCE="$browser_source"
"$python_bin" -m PyInstaller --noconfirm --clean \
  --distpath "$dist_path" \
  --workpath "$work_path" \
  LibreMarkPDF-portable.spec

candidate="$dist_path/LibreMarkPDF"
for entry in LibreMarkPDF LibreMarkPDF-cli LibreMarkPDF-debug; do
  if [[ ! -x "$candidate/$entry" ]]; then
    echo "[FAILED] Expected entry path is missing: $candidate/$entry" >&2
    exit 1
  fi
done
if [[ ! -x "$candidate/_internal/browsers/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell" ]]; then
  echo "[FAILED] The exact browser was not frozen into the candidate." >&2
  exit 1
fi

source_date_epoch="${SOURCE_DATE_EPOCH:-$(git show -s --format=%ct HEAD)}"
archive_path="$dist_path/$archive_name"
tar --sort=name --mtime="@$source_date_epoch" --owner=0 --group=0 \
  --numeric-owner -C "$dist_path" -cf - LibreMarkPDF | gzip -n > "$archive_path"
sha256sum "$archive_path" > "$archive_path.sha256"

echo "Linux x86_64 candidate built without installation or download."
echo "Directory: $candidate"
echo "GUI: $candidate/LibreMarkPDF"
echo "CLI: $candidate/LibreMarkPDF-cli"
echo "Diagnostic GUI: $candidate/LibreMarkPDF-debug"
echo "Archive: $archive_path"
echo "This native candidate is not an advertised or published release."
