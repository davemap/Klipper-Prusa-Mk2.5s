# Klipper firmware flash — BTT SKR Mini E3 V3.0 (STM32G0B1) — copy-paste cheatsheet

Run this **on the Pi**, after MainsailOS is up. Unlike the MK3S+ Einsy (AVR, `make flash` over USB),
the SKR Mini E3 V3 is a 32-bit STM32 board that is flashed by **copying a file to a microSD card** —
there is **no `make flash`** and **no 32U2 USB-bridge reflash** (the STM32 does native USB itself).

## 0. One-time: the board's microSD
- Use a small **FAT32**-formatted microSD card in the SKR's onboard slot.
- The bootloader looks for a file named exactly **`firmware.bin`** at the card root on power-up,
  flashes it, then renames it to `FIRMWARE.CUR` (that rename = success).

## 1. Build the firmware
```bash
cd ~/klipper/
make menuconfig
```
In the `menuconfig` TUI, set:
- **[*] Enable extra low-level configuration options**
- **Micro-controller Architecture:** `STMicroelectronics STM32`
- **Processor model:** `STM32G0B1`
- **Bootloader offset:** `8KiB bootloader`
- **Clock Reference:** `8 MHz crystal`   ← the SKR Mini E3 V3 has an 8 MHz crystal
- **Communication interface:** `USB (on PA11/PA12)`
- Leave the rest at defaults. **Save** (Q → Y), then exit.

> If unsure about any option, follow BTT's current SKR Mini E3 V3 Klipper guide and the Klipper
> docs (https://www.klipper3d.org/SKR_mini_E3.html) — they track board revisions.

Then compile:
```bash
make
```
This produces `~/klipper/out/klipper.bin`.

## 2. Copy to the SD card as firmware.bin
With the microSD mounted on the Pi (adapter), or copy then move the card to the board:
```bash
# Example if the card mounts at /media/<user>/<LABEL> — adjust the path to yours:
cp ~/klipper/out/klipper.bin /path/to/sdcard/firmware.bin
sync
```
Properly eject, put the card in the **SKR's** microSD slot.

## 3. Flash = power-cycle the board
- Power the printer/board off, then on (or hit the board's reset).
- Wait ~15-30s. The bootloader flashes `firmware.bin` and renames it to `FIRMWARE.CUR`.
- Re-check the card later: seeing `FIRMWARE.CUR` (not `firmware.bin`) confirms it flashed.
  If `firmware.bin` is still there unchanged, the build/options were wrong — re-do step 1.

## 4. Find the printer's serial path
```bash
ls /dev/serial/by-id/*
```
Expect something like `/dev/serial/by-id/usb-Klipper_stm32g0b1xx_XXXXXXXXXXXX-if00`.
> Paste this into `printer.cfg` `[mcu] serial:` (the TODO we left there), then **Save & Restart**.

## 5. Verify
- In Mainsail the printer should connect (no "mcu 'mcu' shutdown" / "Unable to connect").
- Run a quick `STATUS` / check temps read room temperature before anything else.

## If the board won't enumerate / won't flash
- Confirm the SD card is **FAT32** (not exFAT) and the file is named exactly `firmware.bin`.
- Confirm the **8KiB bootloader** offset was selected (wrong offset = silent no-flash).
- Try a different/smaller SD card — some large or fast cards aren't read by the bootloader.
- USB cable must be data-capable (not charge-only). The board can also be powered by VIN while
  the USB only carries data.
- Klipper SKR Mini E3 docs: https://www.klipper3d.org/SKR_mini_E3.html
