#!/usr/bin/env bash
set -euo pipefail
# Compatibility entrypoint: install/update without opening the app.
exec bash "$(dirname "$0")/../setup_raspberry.sh" --no-run "$@"
