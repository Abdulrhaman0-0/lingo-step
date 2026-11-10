#!/usr/bin/env bash
# Start LingoStep in the signed-in graphical user's session.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/data/logs"
exec >> "$ROOT/data/logs/autostart.log" 2>&1
echo "[$(date -Is)] Desktop launcher started"
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "No graphical desktop session. Tkinter cannot be started."
  exit 1
fi
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "Python environment missing. Run setup_raspberry.sh --no-run first."
  exit 1
fi
if command -v flock >/dev/null 2>&1; then
  exec 9>"$ROOT/data/lingostep-autostart.lock"
  if ! flock -n 9; then
    echo "Another LingoStep autostart instance is already active."
    exit 0
  fi
fi
sleep "${LINGOSTEP_STARTUP_DELAY:-8}"
cd "$ROOT"
export LINGOSTEP_MIC_DEVICE="${LINGOSTEP_MIC_DEVICE:-USB PnP Sound Device}"
echo "[$(date -Is)] Launching LingoStep"
exec bash "$ROOT/scripts/run_pi.sh"
