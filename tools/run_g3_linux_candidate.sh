#!/usr/bin/env bash
# Build and exercise one exact Linux x86_64 G3 candidate without elevation.

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
evidence_root=""
python_bin=""
browser_source=""
require_offline=0
inspect_only=0
xvfb_pid=""

usage() {
  echo "Usage: $0 --evidence-root DIR --python PYTHON --browser-source DIR [--require-offline] [--inspect-only]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --evidence-root)
      evidence_root="$2"
      shift 2
      ;;
    --python)
      python_bin="$2"
      shift 2
      ;;
    --browser-source)
      browser_source="$2"
      shift 2
      ;;
    --require-offline)
      require_offline=1
      shift
      ;;
    --inspect-only)
      inspect_only=1
      shift
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$evidence_root" || -z "$python_bin" || -z "$browser_source" ]]; then
  usage >&2
  exit 2
fi
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "This evidence runner requires native Linux x86_64." >&2
  exit 1
fi
if [[ "$(id -u)" == "0" ]]; then
  echo "Run the Linux candidate evidence as an unprivileged user." >&2
  exit 1
fi

mkdir -p "$evidence_root"
evidence_root="$(realpath "$evidence_root")"
repo_root="$(realpath "$repo_root")"
python_bin="$(realpath "$python_bin")"
browser_source="$(realpath "$browser_source")"
case "$evidence_root/" in
  "$repo_root/"*)
    echo "Evidence root must be outside the repository." >&2
    exit 1
    ;;
esac

logs="$evidence_root/logs"
artifacts="$evidence_root/artifacts"
runtime="$evidence_root/runtime"
work="$evidence_root/build-work"
mkdir -p "$logs" "$artifacts" "$runtime" "$work"
transcript="$logs/g3-linux-transcript.txt"
exec > >(tee -a "$transcript") 2>&1

cleanup() {
  if [[ -n "$xvfb_pid" ]] && kill -0 "$xvfb_pid" 2>/dev/null; then
    kill "$xvfb_pid" 2>/dev/null || true
    wait "$xvfb_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

run() {
  echo "> $*"
  set +e
  "$@"
  local code=$?
  set -e
  echo "exit=$code"
  if [[ $code -ne 0 ]]; then
    return "$code"
  fi
}

network_state() {
  local output="$1"
  : > "$output"
  for state in /sys/class/net/*/operstate; do
    [[ -e "$state" ]] || continue
    local interface
    interface="$(basename "$(dirname "$state")")"
    [[ "$interface" == "lo" ]] && continue
    printf '%s %s\n' "$interface" "$(cat "$state")" >> "$output"
  done
}

assert_offline() {
  local state_file="$1"
  if [[ $require_offline -eq 1 ]] && grep -Eq ' (up|unknown)$' "$state_file"; then
    echo "Physical network interfaces are not all down:" >&2
    cat "$state_file" >&2
    return 1
  fi
}

cd "$repo_root"
git status --short --branch | tee "$logs/git-status-before.txt"
git rev-parse HEAD | tee "$logs/commit.txt"
git log -1 --show-signature | tee "$logs/git-signature.txt"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "The native candidate checkout must be clean." >&2
  exit 1
fi

{
  uname -a
  uname -m
  getconf GNU_LIBC_VERSION
  ldd --version | sed -n '1p'
  cat /etc/os-release
} > "$logs/linux-environment.txt"
cat "$logs/linux-environment.txt"
{
  echo "appimagetool=$(command -v appimagetool || true)"
  echo "fusermount=$(command -v fusermount || true)"
  echo "fusermount3=$(command -v fusermount3 || true)"
  if [[ -e /dev/fuse ]]; then
    stat -c 'dev_fuse=%A %a %U:%G' /dev/fuse
  else
    echo "dev_fuse=absent"
  fi
  sysctl kernel.unprivileged_userns_clone 2>&1 || true
} > "$logs/fuse-sandbox-host.txt"
cat "$logs/fuse-sandbox-host.txt"
network_state "$logs/network-before.txt"
assert_offline "$logs/network-before.txt"

if [[ $inspect_only -eq 1 ]]; then
  echo "Host inspection complete; no build or runtime action requested."
  exit 0
fi

run "$python_bin" --version
run "$python_bin" -c \
  "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)"
run "$python_bin" tools/verify_locked_environment.py \
  --lock requirements/locks/linux-x86_64-py39.txt
run "$python_bin" -m pip check
"$python_bin" -m pip freeze --all | sort > "$logs/python-freeze.txt"
run "$python_bin" -m libremark_pdf --version
run "$python_bin" -m libremark_pdf doctor --json

{
  sha256sum requirements/locks/linux-x86_64-py39.txt
  sha256sum style.css tests/fixtures/g2/manifest.json
  sha256sum tests/goldens/g2/expected.json
  find fonts icons tests/fixtures/themes/community-blue -type f -print0 |
    sort -z | xargs -0 sha256sum
} > "$logs/source-input-hashes.sha256"

PLAYWRIGHT_BROWSERS_PATH="$browser_source" \
  run "$python_bin" -m unittest discover -s tests -v

LIBREMARK_PDF_PYTHON="$python_bin" \
LIBREMARK_PDF_BROWSER_SOURCE="$browser_source" \
LIBREMARK_PDF_DISTPATH="$artifacts" \
LIBREMARK_PDF_WORKPATH="$work" \
  run ./build_linux_portable.sh

candidate="$artifacts/LibreMarkPDF"
external_parent="$evidence_root/candidate external"
external_candidate="$external_parent/LibreMark PDF – Linux x86_64"
mkdir -p "$external_parent"
cp -a "$candidate" "$external_candidate"
cli="$external_candidate/LibreMarkPDF-cli"
gui="$external_candidate/LibreMarkPDF"
debug_gui="$external_candidate/LibreMarkPDF-debug"
empty_home="$runtime/empty-home"
empty_path="$runtime/empty-path"
mkdir -p "$empty_home" "$empty_path"
if find "$empty_home" -mindepth 1 -print -quit | grep -q .; then
  echo "The isolated home was not empty before candidate execution." >&2
  exit 1
fi

run_cli_case() {
  local name="$1"
  local expected_exit="$2"
  shift 2
  local stdout_file="$logs/$name.stdout.json"
  local stderr_file="$logs/$name.stderr.txt"
  set +e
  env -i HOME="$empty_home" XDG_CACHE_HOME="$empty_home/.cache" \
    XDG_CONFIG_HOME="$empty_home/.config" PATH="$empty_path" LANG=C.UTF-8 \
    "$cli" "$@" > "$stdout_file" 2> "$stderr_file"
  local code=$?
  set -e
  echo "CLI $name exit=$code expected=$expected_exit"
  if [[ $code -ne $expected_exit ]]; then
    return 1
  fi
  if [[ -s "$stderr_file" ]]; then
    echo "CLI $name emitted unexpected stderr." >&2
    return 1
  fi
  "$python_bin" -m json.tool "$stdout_file" >/dev/null
}

source_dir="$runtime/source"
output_dir="$runtime/output"
mkdir -p "$source_dir" "$output_dir"
printf '# Linux candidate\n\nUnicode path: épreuve.\n' > "$source_dir/épreuve test.md"
printf '# Batch continuation\n' > "$source_dir/good.md"
run_cli_case doctor 0 doctor --json
run_cli_case success 0 convert "$source_dir/épreuve test.md" \
  --output "$output_dir/résultat final.pdf" --date 2026-07-14 --json
run_cli_case missing 1 convert "$source_dir/missing.md" --json
run_cli_case partial-batch 1 convert "$source_dir/good.md" \
  "$source_dir/missing.md" --out-dir "$output_dir/batch" --json
run_cli_case collision 1 convert "$source_dir/good.md" \
  --output "$source_dir/good.md" --json
run_cli_case theme 0 convert "$source_dir/good.md" \
  --output "$output_dir/theme.pdf" --theme default@1 \
  --date 2026-07-14 --json

permission_dir="$runtime/no-write"
mkdir -p "$permission_dir"
chmod 500 "$permission_dir"
set +e
run_cli_case permission 1 convert "$source_dir/good.md" \
  --output "$permission_dir/denied.pdf" --json
permission_exit=$?
set -e
chmod 700 "$permission_dir"
if [[ $permission_exit -ne 0 ]]; then
  echo "Permission-denied candidate case failed to produce the expected contract." >&2
  exit 1
fi

display_number=$((90 + ($$ % 100)))
display=":$display_number"
Xvfb "$display" -screen 0 1280x900x24 -nolisten tcp > "$logs/xvfb.txt" 2>&1 &
xvfb_pid=$!
sleep 1
if ! kill -0 "$xvfb_pid" 2>/dev/null; then
  echo "Xvfb did not start; GUI smoke evidence is unavailable." >&2
  exit 1
fi
for entry in "$gui" "$debug_gui"; do
  name="$(basename "$entry")"
  set +e
  timeout 5s env -i HOME="$empty_home" XDG_CACHE_HOME="$empty_home/.cache" \
    XDG_CONFIG_HOME="$empty_home/.config" PATH="$empty_path" LANG=C.UTF-8 \
    DISPLAY="$display" "$entry" > "$logs/$name.stdout.txt" \
    2> "$logs/$name.stderr.txt"
  code=$?
  set -e
  echo "GUI smoke $name exit=$code"
  if [[ $code -ne 124 ]]; then
    echo "$name did not remain responsive for the smoke interval." >&2
    exit 1
  fi
done
kill "$xvfb_pid"
wait "$xvfb_pid" 2>/dev/null || true
xvfb_pid=""

run "$python_bin" tools/inspect_linux_artifact.py \
  --artifact-dir "$external_candidate" \
  --output "$logs/linux-artifact-dependencies.json"

set +e
env -u PLAYWRIGHT_BROWSERS_PATH "$python_bin" \
  tools/g3_windows_artifact_harness.py \
  --converter "$cli" \
  --manifest tests/fixtures/g2/manifest.json \
  --expected tests/goldens/g2/expected.json \
  --actual-dir "$evidence_root/canonical-actual" \
  --report "$evidence_root/canonical-report.json" \
  --diff-dir "$evidence_root/canonical-diff"
canonical_exit=$?
set -e
echo "Canonical comparison exit=$canonical_exit"
echo "$canonical_exit" > "$logs/canonical-exit.txt"

created="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
commit="$(git rev-parse HEAD)"
run "$python_bin" tools/generate_windows_sbom.py \
  --lock requirements/locks/linux-x86_64-py39.txt \
  --artifact-dir "$external_candidate" \
  --commit "$commit" \
  --created "$created" \
  --package-name "LibreMark PDF Linux x86_64 portable candidate" \
  --document-name "LibreMark-PDF-Linux-x86_64-${commit:0:12}" \
  --output "$artifacts/LibreMarkPDF-linux-x86_64.spdx.json"

cat > "$evidence_root/manual-linux-gui-review.md" <<'EOF'
# Exact Linux candidate manual GUI review

Status: **not completed**

Record reviewer, distribution/version, desktop environment, display server
(X11/Wayland), scaling, locale and time. Exercise EN/FR, keyboard focus,
contrast, drag-and-drop and fallback, preview scroll/zoom/stale-result handling,
progress/cancel/safe close, collisions, successful open actions, batch
continuation and theme selection. Retain screenshots or video. Automation
startup evidence does not replace this review.
EOF

network_state "$logs/network-after.txt"
assert_offline "$logs/network-after.txt"
git status --short --branch | tee "$logs/git-status-after.txt"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Candidate execution changed the clean source checkout." >&2
  exit 1
fi

find "$evidence_root" -type f \
  ! -name 'G3_LINUX_EVIDENCE_MANIFEST.sha256' \
  ! -name 'G3_LINUX_EVIDENCE.tar.gz' \
  ! -name 'G3_LINUX_EVIDENCE.tar.gz.sha256' \
  -print0 | sort -z | xargs -0 sha256sum \
  > "$evidence_root/G3_LINUX_EVIDENCE_MANIFEST.sha256"
tar --exclude='G3_LINUX_EVIDENCE.tar.gz' \
  --exclude='G3_LINUX_EVIDENCE.tar.gz.sha256' \
  -C "$evidence_root" -czf "$evidence_root/G3_LINUX_EVIDENCE.tar.gz" .
sha256sum "$evidence_root/G3_LINUX_EVIDENCE.tar.gz" \
  > "$evidence_root/G3_LINUX_EVIDENCE.tar.gz.sha256"

echo "Linux candidate evidence completed."
echo "Canonical comparison exit: $canonical_exit"
echo "Evidence: $evidence_root"
echo "Manual GUI and remaining distribution-matrix review are still required."
