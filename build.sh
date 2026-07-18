#!/usr/bin/env bash
# Compatibility entry for the authoritative no-download Linux candidate build.

set -euo pipefail
cd "$(dirname "$0")"
exec ./build_linux_portable.sh "$@"
