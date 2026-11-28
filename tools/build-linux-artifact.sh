#!/usr/bin/env bash
# Build the Linux x86_64 onedir candidate and normalized tar.gz archive.
#
# This script never installs dependencies, downloads Chromium, invokes sudo,
# or changes host configuration. Prepare the locked CPython 3.14 environment
# and exact Playwright browser payload before running it.

set -euo pipefail
cd "$(dirname "$0")/.."

python_bin="${LIBREMARK_PDF_PYTHON:-python}"
browser_source="${LIBREMARK_PDF_BROWSER_SOURCE:-browser-linux}"
dist_path="${LIBREMARK_PDF_DISTPATH:-$PWD/dist}"
work_path="${LIBREMARK_PDF_WORKPATH:-$PWD/build}"
manual_source="$work_path/manual-pdfs"
lock_path="$PWD/requirements/locks/linux-x86_64-py314.txt"
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
  'import sys, sysconfig; raise SystemExit(not (sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 14) and not sysconfig.get_config_var("Py_GIL_DISABLED")))'
then
  echo "[FAILED] This candidate build requires CPython 3.14." >&2
  exit 1
fi
"$python_bin" tools/verify_locked_environment.py --lock "$lock_path"

browser_source="$(realpath "$browser_source")"
revisions="$("$python_bin" -c 'from libremark_pdf import core; print(core.CHROMIUM_REVISION, core.FFMPEG_REVISION)')"
read -r chromium_revision ffmpeg_revision <<< "$revisions"
shell_directory="chromium_headless_shell-$chromium_revision"
shell_relative="$shell_directory/chrome-headless-shell-linux64/chrome-headless-shell"
browser_executable="$browser_source/$shell_relative"
if [[ ! -x "$browser_executable" ]]; then
  echo "[FAILED] Exact Chromium headless shell revision $chromium_revision is unavailable." >&2
  exit 1
fi
if [[ ! -d "$browser_source/ffmpeg-$ffmpeg_revision" ]]; then
  echo "[FAILED] FFmpeg revision $ffmpeg_revision is unavailable." >&2
  exit 1
fi
if find "$browser_source" -mindepth 1 -maxdepth 1 \
  \( -name 'chromium*' -o -name 'ffmpeg-*' \) \
  ! -name "$shell_directory" ! -name "ffmpeg-$ffmpeg_revision" -print -quit | grep -q .
then
  echo "[FAILED] Browser source contains an unapproved Chromium payload." >&2
  exit 1
fi

mkdir -p "$dist_path" "$work_path"
PLAYWRIGHT_BROWSERS_PATH="$browser_source" \
  "$python_bin" tools/stage_manual_pdfs.py --output-dir "$manual_source"
export LIBREMARK_PDF_BROWSER_SOURCE="$browser_source"
export LIBREMARK_PDF_MANUAL_SOURCE="$manual_source"
"$python_bin" -m PyInstaller --noconfirm --clean \
  --distpath "$dist_path" \
  --workpath "$work_path" \
  LibreMarkPDF.spec

candidate="$dist_path/LibreMarkPDF"
for entry in LibreMarkPDF LibreMarkPDF-cli LibreMarkPDF-debug; do
  if [[ ! -x "$candidate/$entry" ]]; then
    echo "[FAILED] Expected entry path is missing: $candidate/$entry" >&2
    exit 1
  fi
done
if [[ ! -x "$candidate/_internal/browsers/$shell_relative" ]]; then
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
