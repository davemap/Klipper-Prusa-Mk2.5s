#!/usr/bin/env bash
# Install the mcu-reset-recovery watcher on the Klipper Pi.
# Run ON THE PI (or adapt: scp these files over first, then run).
# Requires: user david with passwordless sudo (MainsailOS default).
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR=/home/david/mcu-reset-recovery

mkdir -p "$DEST_DIR"
install -m 0755 "$SRC_DIR/mcu_reset_recovery.py" "$DEST_DIR/mcu_reset_recovery.py"
[ -f "$SRC_DIR/README.md" ] && install -m 0644 "$SRC_DIR/README.md" "$DEST_DIR/README.md"

sudo install -m 0644 "$SRC_DIR/mcu-reset-recovery.service" \
    /etc/systemd/system/mcu-reset-recovery.service
sudo systemctl daemon-reload
sudo systemctl enable --now mcu-reset-recovery.service

systemctl --no-pager status mcu-reset-recovery.service
echo "Done. Follow logs with: journalctl -u mcu-reset-recovery -f"
