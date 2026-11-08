#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python scripts/configure_cloud.py pi-cloud-settings.json
export LINGOSTEP_MIC_DEVICE="${LINGOSTEP_MIC_DEVICE:-USB PnP Sound Device}"
exec .venv/bin/python main.py
