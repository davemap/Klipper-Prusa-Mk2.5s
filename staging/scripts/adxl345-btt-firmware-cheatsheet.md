# BTT ADXL345 (USB) firmware — build & flash cheatsheet (for input shaping)

The BTT ADXL345 USB board is an **rp2040**. To use it with Klipper you build a *second* Klipper firmware
(for the rp2040) and flash it — separate from the SKR (STM32G0B1) firmware. Do this on the Pi before the
input-shaping step.

> Your MK3S+ build hit exactly this: the board shipped **Klipper v0.11.0**, too old for the host
> (v0.13), so input shaping failed until the rp2040 firmware was rebuilt to MATCH the host version.
> Rebuilding it (below) keeps the board and host in lockstep. Same board, same fix here.

## 1. Build the rp2040 firmware
The SKR build lives in `~/klipper/out/`. Building the ADXL firmware overwrites `out/` — that's fine,
the SKR is already flashed. (If you want to keep both, copy the SKR `out/klipper.bin` aside first.)
```bash
cd ~/klipper
make menuconfig
```
Set:
- **Micro-controller Architecture:** `Raspberry Pi RP2040`
- **Communication interface:** `USB`
- Leave the rest default. Save & exit.
```bash
make clean
make            # produces ~/klipper/out/klipper.uf2
```

## 2. Put the board in bootloader (BOOTSEL) mode
- Unplug the BTT ADXL345 USB.
- **Hold the BOOT button** on the board while plugging the USB back into the Pi (keep holding ~1s).
- It mounts as a USB mass-storage drive named **`RPI-RP2`**.
  ```bash
  ls /dev/disk/by-label/ 2>/dev/null; lsblk   # confirm RPI-RP2 appeared
  ```

## 3. Flash (copy the UF2)
Easiest — copy the UF2 onto the RPI-RP2 drive (it reboots itself when done):
```bash
# find the RPI-RP2 mount (often /media/<user>/RPI-RP2); then:
cp ~/klipper/out/klipper.uf2 /media/$USER/RPI-RP2/
sync
```
(Alternatively: `make flash FLASH_DEVICE=2e8a:0003` while it's in BOOTSEL mode.)

## 4. Get its serial path → into the config
```bash
ls /dev/serial/by-id/*
```
Look for the rp2040 / `btt_acc` entry. Paste it into `config/adxlmcu-BTT.cfg` `[mcu adxl] serial:`.

## 5. Rebuild the SKR firmware? (only if you flash the SKR again)
You do NOT need to reflash the SKR — it's already running its firmware. But note `out/` now holds the
rp2040 build. If you ever rebuild the SKR, re-run `make menuconfig` (STM32G0B1 / 8KiB / USB) → `make`
→ SD-card `firmware.bin` again (scripts/firmware-flash-cheatsheet.md).

## 6. Then do input shaping (ON-PI-RUNBOOK step 13)
Uncomment `[include adxlmcu-BTT.cfg]`, `ACCELEROMETER_QUERY`, `SHAPER_CALIBRATE AXIS=X/Y`, `SAVE_CONFIG`,
then re-comment the include and remove the board.

Sources: BTT ADXL345 manual https://github.com/bigtreetech/ADXL345 · Klipper Measuring Resonances
https://www.klipper3d.org/Measuring_Resonances.html
