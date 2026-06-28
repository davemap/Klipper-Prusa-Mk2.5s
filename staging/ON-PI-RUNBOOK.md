# ON-PI RUNBOOK — MK2.5S → Klipper on SKR Mini E3 V3 (do these in order)

The single ordered checklist for the live session. Everything referenced is prepared in this
`staging/` folder. **Before you start**, complete `PREFLIGHT.md` — especially recording the Z-offset
off the stock firmware **before** you pull the old miniRambo board (that read is gone once it's out),
and wiring the SKR (PINDA→PROBE/PC14, IR sensor→E0-STOP/PC15, DIAG jumpers for X/Y).

Machine summary: Prusa **MK2.5S** · **BTT SKR Mini E3 V3.0** (STM32G0B1, TMC2209 UART, **12V**) ·
**E3D Revo 40W 12V**, 0.4mm · stock extruder · **TMC2209 sensorless** X/Y · **PINDA2** Z ·
**BTT ADXL345 (USB)** · **new dedicated Pi** (`mk25s.local`) · MainsailOS · two webcams · HyperPixel+KlipperScreen.

> 🔌 **BED, today vs tomorrow:** the external bed MOSFET arrives tomorrow. TODAY the bed runs **direct** to
> the board's HB terminal — measure bed R first, keep bed heating **short + attended**, watch the HB
> terminal temp. Fine for commissioning + a short PLA test. TOMORROW install the MOSFET (PSU→IN, bed→OUT,
> HB→trigger), re-run bed PID, then print unrestricted. Detail: `scripts/wiring-map.md` §1. This does NOT gate today.

---

## 0. Pre-flight (do `PREFLIGHT.md` first)
- [ ] Z-offset recorded **before** removing the old board → goes in `printer.cfg [probe] z_offset` (absolute).
- [ ] SKR wired + DIAG jumpers in + powered at **12V**.

## 1. Flash MainsailOS to the Pi's SD card
- [ ] Raspberry Pi Imager → **MainsailOS** → ⚙️ advanced: hostname **`mk25s`**, enable SSH, set
      username/password, configure Wi-Fi.
- [ ] Boot. Confirm `http://mk25s.local` loads Mainsail and `ssh <user>@mk25s.local` works.
      → Record host/user in `VALUES.md`; use it as the `user@host` arg below.

## 2. Update once, then stop
- [ ] Mainsail → **Update Manager**: update **everything once**, reboot. Then **stop updating**.

## 3. Back up, then deploy the config
- [ ] `ssh <user>@mk25s.local 'cp -r ~/printer_data/config ~/printer_data/config.bak.$(date +%F)'`
- [ ] From `staging/scripts/`: `./deploy-config.sh <user>@mk25s.local`
      → pushes `printer.cfg`, `skr-mini-e3-v3.cfg`, `tmc2209.cfg`, `steppers.cfg`, `display.cfg`,
      `macros.cfg`, `adxlmcu-BTT.cfg`, `adxlmcu-KUSBA.cfg`, `crowsnest.conf`.
      (`mainsail.cfg` is NOT shipped — MainsailOS owns it.)

## 4. Fill the TODO values in Mainsail's editor
- [ ] `[probe] z_offset` → your recorded **absolute** Z-offset.
- [ ] `[mcu] serial` → fill in step 6 after flashing (you read it then), or now if known.

## 5. (No 32U2 reflash) — N/A on this board
- [ ] The SKR does native USB; there is no 32U2 bridge to reflash. → `scripts/NO-32u2-reflash-needed.md`.

## 6. Flash Klipper firmware to the SKR (STM32G0B1, SD-card method)
- [ ] Follow `scripts/firmware-flash-cheatsheet.md`: `make menuconfig` (STM32 / STM32G0B1 / 8KiB
      bootloader / 8MHz crystal / USB PA11-PA12) → `make` → copy `out/klipper.bin` to the SKR's
      microSD as **`firmware.bin`** → power-cycle the board → confirm it became `FIRMWARE.CUR`.
- [ ] `ls /dev/serial/by-id/*` → paste the `usb-Klipper_stm32g0b1xx_...-if00` path into `[mcu] serial`,
      **Save & Restart**. Mainsail should connect.

## 7. Config checks — DO NOT SKIP, this board is all-new wiring
- [ ] **Temps:** extruder + bed read room temperature (if wildly off, fix thermistor type/pin first).
- [ ] **Motor directions:** jog each axis a few mm. +X right, +Y bed-forward, **+Z raises nozzle**.
      Flip the `!` on the relevant `dir_pin` in `steppers.cfg` for any reversed axis. **Check Z first**,
      hand on reset (a reversed Z drives down on a home).
- [ ] **Heaters/fans:** brief heat test; confirm hotend fan kicks in when hot, part fan responds to M106.
- [ ] **Probe polarity:** `QUERY_PROBE`, slide metal under the PINDA — reading must flip. If inverted,
      add `!` to `[probe] pin` (→ `^!PC14`).
- [ ] **Filament sensor:** `QUERY_FILAMENT_SENSOR`, insert/remove filament — must toggle. Flip `!` if needed.

## 8. Sensorless homing tuning (TMC2209 StallGuard) — specific to this build
- [ ] Confirm DIAG jumpers are installed (step 0). Tune `driver_SGTHRS` in `tmc2209.cfg` per its
      procedure: run `G28 X` then `G28 Y` with a hand on reset; raise/lower SGTHRS until each axis stops
      gently AT the end without ramming or false-triggering. Then back off a few counts for margin.
- [ ] Only after X/Y home reliably, let `G28` do Z (PINDA). Then `PROBE_CALIBRATE` for the real z_offset.

## 9. PID tuning — MANDATORY for the 40W 12V Revo
- [ ] `PID_CALIBRATE HEATER=extruder TARGET=215` → `SAVE_CONFIG`.
- [ ] `PID_CALIBRATE HEATER=heater_bed TARGET=60` → `SAVE_CONFIG`. **TODAY (bed direct): watch the HB
      terminal temp** during this (a few min at temp). **Re-run it tomorrow** after the MOSFET goes in.
      Placeholder PID is wrong for your Revo/bed — do NOT print before this.

## 10. Webcams
- [ ] `ls /dev/v4l/by-id/` → paste the two `-video-index0` paths into `crowsnest.conf` →
      `sudo systemctl restart crowsnest` → add both in Mainsail → Settings → Webcams. → `webcam/README.md`.

## 11. PrusaSlicer profile
- [ ] Apply `prusaslicer/SETTINGS-CHECKLIST.md` (MK2.5S profile, Klipper flavor, clear custom g-code,
      paste START/END, arc fitting OFF, detach presets).

## 12. Tuning — Ellis' guide (NOT optional)
- [ ] **Extruder calibration** (verify `rotation_distance` 24.06):
      https://ellis3dp.com/Print-Tuning-Guide/articles/extruder_calibration.html
- [ ] **Pressure advance** (first pass) → per-filament `SET_PRESSURE_ADVANCE` in slicer.

## 13. Input shaping (BTT ADXL345, USB)
- [ ] Mount accelerometer on toolhead. In `printer.cfg` uncomment **`[include adxlmcu-BTT.cfg]`**, fill
      its `[mcu adxl] serial:` from `ls /dev/serial/by-id/*`.
- [ ] `ACCELEROMETER_QUERY` → `SHAPER_CALIBRATE AXIS=X` → `SAVE_CONFIG`. Move to bed, swap `axes_map`
      (commented alt provided) → `SHAPER_CALIBRATE AXIS=Y` → `SAVE_CONFIG`.
- [ ] **Re-comment `[include adxlmcu-BTT.cfg]`** and remove the board (leaving it on without the board
      breaks startup). Your USB ADXL doesn't conflict with the HyperPixel.
- [ ] (Optional) Unlock the faster machine-limits profile in `printer.cfg [printer]`.

## 14. Re-do pressure advance
- [ ] Input shaping changes PA — re-run Ellis PA tuning and update per-filament values.

## 15. (Optional / fiddly) KlipperScreen + HyperPixel
- [ ] Confirm your HyperPixel model, then follow `klipperscreen/SETUP-NOTES.md` (dtoverlay →
      `install-klipperscreen.sh` → reboot). If painful, Mainsail in a browser is a fine fallback.

---
**Done when:** prints start via `PRINT_START`, temps hold (post-PID), first layer is dialed (z_offset +
`PROBE_CALIBRATE`), sensorless homing is reliable, PA + input shaping applied. Keep the old miniRambo +
its SD card as rollback until you're confident.
