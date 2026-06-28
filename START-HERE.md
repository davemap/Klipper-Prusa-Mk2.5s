# START HERE — MK2.5S → Klipper bring-up (day-of guide)

Everything is staged. This is the single ordered path; each step links to the detailed file and lists the
exact commands. Tick straight down it.

**Printer:** Prusa MK2.5S · BTT SKR Mini E3 V3.0 (STM32G0B1, TMC2209 UART, **12V**) · E3D Revo 40W 12V 0.4mm ·
sensorless X/Y · PINDA2 Z · BTT ADXL345 (USB) · new Pi `mk25s.local` · MainsailOS · HyperPixel/KlipperScreen.

---

## ⚠️ The only thing to keep in your head: the BED (today vs tomorrow)
- **TODAY** — bed wired **direct** to the board's **HB** terminal. It's interim and monitored:
  1) **Measure bed resistance first** (multimeter, cold, across bed power lugs): current = 12 ÷ R.
     `≥1.5Ω`→~8A fine · `~1.1–1.4Ω`→~9–11A keep it short+attended · `≤1.0Ω`→~12A+, skip bed heating today.
  2) Bed screw terminal **TIGHT**, thick stock wire.
  3) Heat the bed only **short + attended**, watch the HB terminal temp (warm OK, too-hot-to-touch = stop).
  4) No long/unattended prints, keep bed ~60°C (PLA) today.
- **TOMORROW** — install the MOSFET (PSU→IN, bed→OUT, HB→trigger), **re-run bed PID**, then print freely.
- This does **NOT** gate today. Full detail + thresholds: [scripts/wiring-map.md](staging/scripts/wiring-map.md) §1.

> Also, if you haven't already and the **old miniRambo is still installed**: record the stock **Z-offset**
> (Menu → Calibration → Z-offset, make it absolute) — it's gone once that board is out.

---

## Order of the day

### 0 · Preflight + wire the board → [staging/PREFLIGHT.md](staging/PREFLIGHT.md) · [staging/scripts/wiring-map.md](staging/scripts/wiring-map.md)
- Wire the SKR per the wiring map. Key gotchas: **both Z motors → one Z port (series)**; **DIAG jumpers in**
  for X/Y sensorless; **PINDA → PROBE port**; **IR sensor → E0-DET**; **bed → HB direct (today)**; **12V VIN**.
- Bring-up safe order: wire everything, power at 12V with **heaters off first**, confirm before heating.

### 1 · Flash MainsailOS to the Pi SD (do this in parallel with wiring)
- Raspberry Pi Imager → MainsailOS → ⚙️: hostname **`mk25s`**, enable SSH, set user, Wi-Fi.
- Boot, confirm `http://mk25s.local` loads and `ssh <user>@mk25s.local` works.

### 2 · Back up + deploy the config → [staging/scripts/deploy-config.sh](staging/scripts/deploy-config.sh)
```bash
ssh <user>@mk25s.local 'cp -r ~/printer_data/config ~/printer_data/config.bak.$(date +%F)'
cd staging/scripts && ./deploy-config.sh <user>@mk25s.local
```

### 3 · Flash Klipper to the SKR → [staging/scripts/firmware-flash-cheatsheet.md](staging/scripts/firmware-flash-cheatsheet.md)
```bash
cd ~/klipper && make menuconfig     # STM32 · STM32G0B1 · 8KiB bootloader · 8MHz crystal · USB (PA11/PA12)
make
cp ~/klipper/out/klipper.bin /path/to/sdcard/firmware.bin && sync   # FAT32 card, name EXACTLY firmware.bin
# put card in the SKR, power-cycle the board, wait ~20s (firmware.bin -> FIRMWARE.CUR = success)
ls /dev/serial/by-id/*              # copy the usb-Klipper_stm32g0b1xx_...-if00 path
```

### 4 · Fill the two TODOs in Mainsail's config editor
- `[mcu] serial:` ← the by-id path from step 3.   ·   `[probe] z_offset =` ← your recorded absolute Z-offset.
- Save & Restart.

### 5 · Bring-up / config checks (DON'T SKIP) → [ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md) step 7
In the Mainsail console:
```
FIRMWARE_RESTART
# temps: confirm extruder + bed read room temp on the dashboard (if wild, fix thermistor first)
# directions — jog each axis a few mm in Mainsail: +X right, +Y bed forward, +Z RAISES nozzle.
#   CHECK Z FIRST, hand on power. Reversed axis -> add/remove the ! on its dir_pin in steppers.cfg, restart.
QUERY_PROBE                          # slide metal under PINDA, value must flip; if inverted -> ^!PC14
QUERY_FILAMENT_SENSOR SENSOR=fsensor # insert/remove filament toggles it; flip ! on switch_pin if needed
```

### 6 · Sensorless homing tune → [staging/config/tmc2209.cfg](staging/config/tmc2209.cfg)
```
G28 X            # then G28 Y, hand on reset. Tune driver_SGTHRS in tmc2209.cfg:
                 #   stops before the end / triggers early -> LOWER SGTHRS
                 #   rams the end -> RAISE SGTHRS.  (Save & Restart between tries.)
G28              # once X/Y are solid, let it do Z off the PINDA
PROBE_CALIBRATE  # -> adjust with the paper test -> ACCEPT -> SAVE_CONFIG  (real z_offset)
```

> 🧪 **Deciding whether to keep the X/Y endstops?** You can prove sensorless homing on the real axes with a
> stripped motion-only config (no heaters/probe needed) **before** finishing the rebuild — and the X-STOP/
> Y-STOP pin is either-or (DIAG jumper *or* a switch), so test sensorless first. Full procedure + pass/fail
> criteria: [staging/scripts/sensorless-endstop-test.md](staging/scripts/sensorless-endstop-test.md)
> (uses [staging/config/homing-test.cfg](staging/config/homing-test.cfg)).

### 7 · PID tuning — MANDATORY (Revo) → [ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md) step 9
```
PID_CALIBRATE HEATER=extruder TARGET=215
SAVE_CONFIG
PID_CALIBRATE HEATER=heater_bed TARGET=60      # TODAY: watch the HB terminal temp while this runs
SAVE_CONFIG
```

### 8 · Short attended test print (PLA, ~60°C bed)
- Slice with the imported PrusaSlicer profile → [staging/prusaslicer/MK2.5S-Klipper-printer.ini](staging/prusaslicer/MK2.5S-Klipper-printer.ini)
  (pair with Prusa's MK2.5S 0.4mm Print/Filament presets). Watch the first layer + the bed terminal.

### 9 · TOMORROW — install the bed MOSFET → [staging/scripts/wiring-map.md](staging/scripts/wiring-map.md) §1
- Power off. PSU 12V → module **Power Input**; module **Output** → bed; board **HB** → module **Signal/Trigger**.
- No printer.cfg change. Power on → `PID_CALIBRATE HEATER=heater_bed TARGET=60` → `SAVE_CONFIG`. Now print freely.

### 10 · Tuning (over the next sessions) → [ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md) steps 11–15
- Extruder calibration (verify rotation_distance 24.06) → pressure advance (per-filament).
- **Input shaping:** first flash the BTT ADXL345 → [staging/scripts/adxl345-btt-firmware-cheatsheet.md](staging/scripts/adxl345-btt-firmware-cheatsheet.md),
  then uncomment `[include adxlmcu-BTT.cfg]`, `ACCELEROMETER_QUERY`, `SHAPER_CALIBRATE AXIS=X`/`Y` → `SAVE_CONFIG`, re-comment.
- Re-do pressure advance · KlipperScreen + HyperPixel → [staging/klipperscreen/SETUP-NOTES.md](staging/klipperscreen/SETUP-NOTES.md).

---

## What's prepared for you (index)
| File | What it's for |
|---|---|
| [staging/scripts/wiring-map.md](staging/scripts/wiring-map.md) | every Prusa cable → SKR connector; bed phasing; dual-Z; sensorless |
| [staging/scripts/firmware-flash-cheatsheet.md](staging/scripts/firmware-flash-cheatsheet.md) | SKR (STM32G0B1) SD-card flash |
| [staging/scripts/adxl345-btt-firmware-cheatsheet.md](staging/scripts/adxl345-btt-firmware-cheatsheet.md) | accelerometer rp2040 firmware for input shaping |
| [staging/scripts/deploy-config.sh](staging/scripts/deploy-config.sh) | rsync config to `mk25s.local` |
| [staging/config/](staging/config/) | printer.cfg + skr-mini-e3-v3.cfg + tmc2209.cfg + steppers.cfg + display.cfg + macros.cfg + accel |
| [staging/prusaslicer/](staging/prusaslicer/) | importable 0.4mm printer profile + checklist + start/end gcode |
| [staging/VALUES.md](staging/VALUES.md) | confirmed values + the TODO-on-hardware list |
| [staging/ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md) | the detailed ordered runbook (this guide is its quickstart) |
| [staging/PREFLIGHT.md](staging/PREFLIGHT.md) | physical/wiring checklist |
| [staging/config/CHANGES.md](staging/config/CHANGES.md) | every divergence from the MK3S+ build, with rationale |

**Still good to confirm when you can** (none block bringup): SSH username for `mk25s.local`, HyperPixel
model (for the dtoverlay), webcam models, that the SKR is a V3.0. → [staging/VALUES.md](staging/VALUES.md).
