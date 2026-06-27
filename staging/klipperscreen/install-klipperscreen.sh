#!/usr/bin/env bash
# install-klipperscreen.sh — best-effort KlipperScreen install on the MK2.5S Pi (run ON the Pi).
#
# Prereqs (do these FIRST, see SETUP-NOTES.md):
#   1) MainsailOS up and Klipper/Mainsail working.
#   2) HyperPixel panel lit via the right dtoverlay in /boot/firmware/config.txt (panel shows boot text).
#
# This runs the OFFICIAL KlipperScreen installer, which is designed for Pi OS Lite and creates its own
# systemd service. It does NOT configure the HyperPixel overlay — that's a separate, manual step.
set -euo pipefail

if [ ! -d "$HOME/KlipperScreen" ]; then
  echo ">> Cloning KlipperScreen..."
  git clone https://github.com/KlipperScreen/KlipperScreen.git "$HOME/KlipperScreen"
else
  echo ">> KlipperScreen already cloned; pulling latest..."
  git -C "$HOME/KlipperScreen" pull --ff-only || true
fi

echo ">> Running official installer (uses sudo, installs apt packages, creates a venv + systemd service)..."
"$HOME/KlipperScreen/scripts/KlipperScreen-install.sh"

echo
echo ">> Done. Reboot, then KlipperScreen should render on the HyperPixel."
echo ">> If the panel stays blank: it's almost always the dtoverlay / rotation / backlight"
echo ">> (see SETUP-NOTES.md), NOT KlipperScreen itself. Mainsail in a browser is the fallback."
