#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")" && pwd)"
python_bin="${PYTHON:-python3.14}"
cd "$repo_root"
offline=0
install_python=0
install_make=0
non_interactive=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline) offline=1 ;;
    --install-python) install_python=1 ;;
    --install-make) install_make=1 ;;
    --non-interactive) non_interactive=1 ;;
    *)
      echo "Usage: $0 [--offline] [--install-python] [--install-make] [--non-interactive]" >&2
      exit 2
      ;;
  esac
  shift
done
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "bootstrap-linux.sh requires native Linux x86_64." >&2
  exit 1
fi

confirm_install() {
  local purpose="$1"
  local requested="$2"
  [[ "$offline" -eq 1 ]] && return 1
  [[ "$requested" -eq 1 ]] && return 0
  [[ "$non_interactive" -eq 1 || ! -t 0 ]] && return 1
  read -r -p "$purpose is missing. Install it now? [y/N] " answer
  [[ "$answer" =~ ^([yY]|[yY][eE][sS]|[oO]|[oO][uU][iI])$ ]]
}

install_linux_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y "$@"
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y "$@"
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper --non-interactive install "$@"
  else
    echo "No supported package manager found (apt, dnf, zypper)." >&2
    return 1
  fi
}

is_supported_python() {
  command -v "$1" >/dev/null 2>&1 && "$1" -c \
    'import sys, sysconfig; raise SystemExit(not (sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 14) and not sysconfig.get_config_var("Py_GIL_DISABLED")))'
}

if ! is_supported_python "$python_bin" && [[ -z "${PYTHON:-}" ]] &&
  command -v pyenv >/dev/null 2>&1
then
  while IFS= read -r pyenv_version; do
    prefix="$(PYENV_VERSION="$pyenv_version" pyenv prefix)"
    if is_supported_python "$prefix/bin/python"; then
      python_bin="$prefix/bin/python"
      break
    fi
  done < <(pyenv versions --bare | awk '/^3\.14\.[0-9]+$/' | sort -Vr)
fi
if ! is_supported_python "$python_bin" && [[ -z "${PYTHON:-}" ]] &&
  command -v apt-cache >/dev/null 2>&1 &&
  apt-cache show python3.14 python3.14-venv 2>/dev/null |
    awk '/^Package: python3.14$/ { p=1 } /^Package: python3.14-venv$/ { v=1 } END { exit !(p && v) }' &&
  confirm_install "CPython 3.14" "$install_python"
then
  install_linux_packages python3.14 python3.14-venv
fi
is_supported_python "$python_bin" || {
  echo "Standard CPython 3.14 is required. Install it with pyenv or set PYTHON to a matching executable." >&2
  exit 1
}

if ! command -v make >/dev/null 2>&1 &&
  confirm_install "GNU Make" "$install_make"
then
  install_linux_packages make
fi
venv="${LIBREMARK_PDF_VENV:-$repo_root/.venv-linux-py314}"
lock="$repo_root/requirements/locks/linux-x86_64-py314.txt"
browser_root="${LIBREMARK_PDF_BROWSER_SOURCE:-$repo_root/browser-linux}"
if [[ ! -d "$venv" ]]; then
  "$python_bin" -m venv "$venv"
fi
venv_python="$venv/bin/python"
is_supported_python "$venv_python" || {
  echo "The environment at $venv must use standard CPython 3.14." >&2
  exit 1
}
browser_root="$(realpath -m "$browser_root")"
if [[ $offline -eq 1 ]]; then
  "$venv_python" -m pip install --no-index --only-binary=:all: --require-hashes -r "$lock"
else
  "$venv_python" -m pip install --only-binary=:all: --require-hashes -r "$lock"
fi
"$venv_python" -m pip check
if [[ $offline -eq 1 ]]; then
  [[ -d "$browser_root" ]] || { echo "Offline mode requires a staged browser payload at $browser_root." >&2; exit 1; }
else
  PLAYWRIGHT_BROWSERS_PATH="$browser_root" "$venv_python" -m playwright install --only-shell chromium
fi
PLAYWRIGHT_BROWSERS_PATH="$browser_root" "$venv_python" tools/verify_locked_environment.py --lock "$lock"
PLAYWRIGHT_BROWSERS_PATH="$browser_root" "$venv_python" -m libremark_pdf doctor --json
echo "Ready: $venv_python"
if command -v make >/dev/null 2>&1; then
  echo "Next: make test"
else
  echo "GNU Make is optional and unavailable. Rerun with --install-make."
fi
