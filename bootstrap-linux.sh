#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")" && pwd)"
python_bin="${PYTHON:-python3.9}"
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
  [[ "$requested" -eq 1 ]] && return 0
  [[ "$offline" -eq 1 || "$non_interactive" -eq 1 || ! -t 0 ]] && return 1
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

python_ready=0
if command -v "$python_bin" >/dev/null 2>&1 &&
  "$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)'
then
  python_ready=1
fi
if [[ "$python_ready" -eq 0 ]] && command -v pyenv >/dev/null 2>&1; then
  pyenv_version="$(pyenv versions --bare 2>/dev/null | awk '$1 ~ /^3\.9([.]|$)/ { print $1; exit }')"
  if [[ -n "$pyenv_version" ]]; then
    python_bin="$(PYENV_VERSION="$pyenv_version" pyenv prefix 2>/dev/null)/bin/python"
    if "$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)' 2>/dev/null; then
      python_ready=1
    fi
  fi
fi
if [[ "$python_ready" -eq 0 ]] && confirm_install "CPython 3.9" "$install_python"; then
  if command -v apt-get >/dev/null 2>&1; then
    install_linux_packages python3.9 python3.9-venv
  elif command -v dnf >/dev/null 2>&1; then
    install_linux_packages python3.9
  elif command -v zypper >/dev/null 2>&1; then
    install_linux_packages python39
  fi
  if command -v "$python_bin" >/dev/null 2>&1 &&
    "$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)'
  then
    python_ready=1
  fi
fi
[[ "$python_ready" -eq 1 ]] || {
  echo "CPython 3.9 is required. Install it manually (for example with pyenv) or rerun with --install-python." >&2
  exit 1
}

if ! command -v make >/dev/null 2>&1 &&
  confirm_install "GNU Make" "$install_make"
then
  install_linux_packages make
fi
venv="$repo_root/.venv-linux-py39"
lock="$repo_root/requirements/locks/linux-x86_64-py39.txt"
browser_root="$repo_root/browser-linux"
if [[ ! -d "$venv" ]]; then
  "$python_bin" -m venv "$venv"
fi
venv_python="$venv/bin/python"
if [[ $offline -eq 1 ]]; then
  "$venv_python" -m pip install --no-index --require-hashes -r "$lock"
else
  "$venv_python" -m pip install --require-hashes -r "$lock"
fi
"$venv_python" -m pip check
if [[ $offline -eq 1 ]]; then
  [[ -d "$browser_root" ]] || { echo "Offline mode requires browser-linux/." >&2; exit 1; }
else
  PLAYWRIGHT_BROWSERS_PATH="$browser_root" "$venv_python" -m playwright install --only-shell chromium
fi
[[ -d "$browser_root/chromium_headless_shell-1223" ]] || {
  echo "The required Chromium headless-shell revision 1223 is missing." >&2
  exit 1
}
PLAYWRIGHT_BROWSERS_PATH="$browser_root" "$venv_python" tools/verify_locked_environment.py --lock "$lock"
PLAYWRIGHT_BROWSERS_PATH="$browser_root" "$venv_python" -m libremark_pdf doctor --json
echo "Ready: $venv_python"
if command -v make >/dev/null 2>&1; then
  echo "Next: make test"
else
  echo "GNU Make is optional and unavailable. Rerun with --install-make."
fi
