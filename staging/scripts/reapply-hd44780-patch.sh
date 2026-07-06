#!/usr/bin/env bash
# Re-apply the two local Klipper HD44780 patches after a Klipper update (git pull resets them).
# Why they exist (2026-07-03): the Prusa MK2.5S stock 2004A (clone HD44780) needs a more patient
# init + slower writes than stock Klipper provides. Symptoms without them: blank/garbled LCD,
# or only lines 1&3 alive.
set -e
F=~/klipper/klippy/extras/display/hd44780.py
sed -i "s|^HD44780_DELAY = .*|HD44780_DELAY = .000160|" $F
sed -i "s|init = \[\[0x33\], \[0x33\], \[0x32\], \[0x28, 0x28, 0x02\]\]|init = [[0x33], [0x33], [0x33], [0x33], [0x32], [0x28], [0x28], [0x02]]|" $F
grep -nE "HD44780_DELAY = |init = \[\[" $F | head -3
sudo systemctl restart klipper
echo "patches re-applied + klipper restarted"
