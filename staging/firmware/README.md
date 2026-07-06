# Klipper firmware for the SKR Mini E3 V3.0 (image #2 of 2)

**USE THIS ONE:** `klipper-skr-mini-e3-v3.0-77d5d94-VERSION-MATCHED.bin` — built ON the Pi
(2026-07-03) at `v0.13.0-642-g77d5d942e`, the exact version the Pi's Klipper host runs.
No version-skew possible.

(`klipper-skr-mini-e3-v3.0-7e64fc8.bin` is an earlier Mac-built spare of the same config —
keep as backup only.)

- Built from the Pi's Klipper checkout.
- Build config (the exact `make menuconfig` answers, should you ever rebuild):
  - Micro-controller architecture: **STMicroelectronics STM32**
  - Processor model: **STM32G0B1**
  - Bootloader offset: **8KiB bootloader**
  - Clock reference: **8 MHz crystal**
  - Communication interface: **USB (on PA11/PA12)**

## Flash it (same SD dance as the Marlin bench builds)

1. Power the board OFF. SD card into the Mac.
2. Copy the `.bin` onto the card **renamed to `firmware.bin`** (delete any `FIRMWARE.CUR`).
3. Card into the SKR, power on, wait ~15 s. Success = the file is renamed to `FIRMWARE.CUR`.
4. The board now enumerates as `usb-Klipper_stm32g0b1xx_...` — it does NOTHING until a Klipper
   host (the Pi) connects to it. A blank/idle LCD at this point is NORMAL.

## Version-match note (read if Mainsail complains)

Klipper's host (Pi) and MCU (this .bin) versions should match closely. MainsailOS installs the
latest Klipper at image-flash time, which may be days/weeks newer than commit `7e64fc8`. Small
skew is normally tolerated; if Mainsail shows **"MCU protocol error"** or lists the MCU under
"should be updated", rebuild on the Pi and reflash:

```bash
ssh <user>@mk25s.local
cd ~/klipper && make menuconfig     # answers above
make
# copy ~/klipper/out/klipper.bin to the SD card as firmware.bin (scp it to your Mac, or use
# a USB SD reader on the Pi), flash as in steps 1-3.
scp ~/klipper/out/klipper.bin <you>@<mac>:/tmp/firmware.bin
```
