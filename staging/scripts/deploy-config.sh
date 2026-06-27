#!/usr/bin/env bash
# deploy-config.sh — push the finished MK2.5S Klipper config to its Pi.
#   Usage:   ./deploy-config.sh david@mk25s.local
#            ./deploy-config.sh david@192.168.1.43
#
# Runs from anywhere — it resolves paths relative to its own location.
set -euo pipefail

PI_HOST="${1:?usage: deploy-config.sh user@host   (e.g. david@mk25s.local)}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HERE/../config"
WEBCAM_CONF="$HERE/../webcam/crowsnest.conf"
DEST="$PI_HOST:~/printer_data/config/"

# !!! BACK UP FIRST !!!
# This OVERWRITES files in ~/printer_data/config/ on the Pi. Before the first run, back up the
# stock MainsailOS configs so you can roll back:
#     ssh "$PI_HOST" 'cp -r ~/printer_data/config ~/printer_data/config.bak.$(date +%F)'
echo ">> Deploying MK2.5S config to $DEST"
echo ">> (Reminder: did you back up the Pi's existing ~/printer_data/config first?)"

# --- Klipper config files (printer.cfg + all includes + both accelerometer cfgs) ---
# Ships: printer.cfg, skr-mini-e3-v3.cfg, tmc2209.cfg, steppers.cfg, display.cfg, macros.cfg,
#        adxlmcu-BTT.cfg, adxlmcu-KUSBA.cfg
# NOTE: we do NOT ship mainsail.cfg — MainsailOS provides that itself. Exclude our docs.
rsync -avz \
  --exclude 'CHANGES.md' \
  --exclude 'mainsail.cfg' \
  "$CONFIG_DIR"/ "$DEST"

# --- two-camera crowsnest config ---
rsync -avz "$WEBCAM_CONF" "$DEST"

echo
echo ">> Done. Now in Mainsail: fill the TODO values (Z-offset, MCU serial, camera by-id),"
echo ">> then restart Klipper (Mainsail: top-right menu > Restart, or 'Save & Restart' in the editor)."
