#!/usr/bin/env bash
# Per-user XDG desktop autostart: safe to run repeatedly.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$HOME/.config/autostart/lingostep.desktop"
case "${1:---enable}" in
  --disable)
    rm -f "$TARGET"
    echo "Autostart disabled."
    exit 0 ;;
  --status)
    if [[ -f "$TARGET" ]]; then echo "Enabled: $TARGET"; else echo "Disabled"; fi
    exit 0 ;;
  --enable) ;;
  *) echo "Usage: bash scripts/install_autostart.sh [--enable|--disable|--status]" >&2; exit 2 ;;
esac
if [[ "$EUID" -eq 0 ]]; then
  echo "Run as the Raspberry desktop user, not with sudo." >&2
  exit 1
fi
if [[ ! -f "$ROOT/main.py" || ! -f "$ROOT/scripts/run_pi.sh" ]]; then
  echo "Project incomplete." >&2
  exit 1
fi
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "Run bash setup_raspberry.sh --no-run to install dependencies first." >&2
  exit 1
fi
mkdir -p "$HOME/.config/autostart"
# Desktop entry paths are quoted for users with spaces in their directory.
cat > "$TARGET" <<EOF
[Desktop Entry]
Type=Application
Name=LingoStep
Comment=Offline alphabet learning for children
Exec=/usr/bin/env bash "$ROOT/scripts/launch_on_desktop.sh"
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
chmod 644 "$TARGET"
echo "LingoStep enabled at next Desktop login: $TARGET"
echo "To run after power-on without login, enable Desktop Autologin in raspi-config."
