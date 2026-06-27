# VALUES — MK2.5S / SKR Mini E3 V3 build

Single source of truth for machine-specific values. Anything marked `TODO` must be filled
**on the Pi / from the printer** — it was never fabricated here.

## Confirmed by user (2026-06-27)

| Value | Setting | Where it lands |
|---|---|---|
| Printer | Prusa **MK2.5S** | `PRINT_START` default `PRINTER_MODEL="MK2.5S"` (PINDA heat-soak path) |
| Mainboard | **BTT SKR Mini E3 V3.0** (STM32G0B1, 4× TMC2209 UART) | `skr-mini-e3-v3.cfg` + `tmc2209.cfg` + `steppers.cfg` |
| Hotend | E3D **Revo**, **40 W**, **12 V** core, 0.4mm | `printer.cfg [extruder] nozzle_diameter: 0.40`, heater on HE (PC8) |
| System voltage | **12 V** | Power SKR VIN at 12V. Fans + heaters switch VIN = 12V. **Never 24V.** |
| Extruder | **Stock MK2.5S** | `steppers.cfg` rotation_distance 24.06015 (from MK2.5S firmware) — verify via calibration |
| X/Y homing | **TMC2209 sensorless (StallGuard)** | `tmc2209.cfg` diag_pin + driver_SGTHRS (TUNE); mechanical fallback commented |
| Z probe | **PINDA2** (no temp comp) → PROBE port PC14 | `skr-mini-e3-v3.cfg [probe]`; heat-soaked in PRINT_START |
| Accelerometer | **BTT ADXL345** (USB) | `adxlmcu-BTT.cfg` (enabled only during input shaping) |
| Display | **Touchscreen-only**: HyperPixel + KlipperScreen (mini12864 later if a knob is wanted) | `display.cfg` (beeper only on the board side) |
| Pi | **New dedicated Pi**, hostname `mk25s` → `mk25s.local` | deploy with `./deploy-config.sh <user>@mk25s.local` |
| Filament dia | 1.75 mm | `filament_diameter: 1.750` |

## Geometry derived from Prusa MK2.5S firmware (reference/Prusa-MK25S-RAMBo13a.h) — authoritative

| Axis | steps/mm (firmware) | rotation_distance @16µsteps | travel |
|---|---|---|---|
| X | 100 | 32 | 0..250 |
| Y | 100 | 32 | -4..210 |
| **Z** | **400** (`3200/8`) | **8** (8mm lead — NOT M5/0.8) | -2..210 |
| E | 133 | 24.06015 | — |

Stock limits: max_feedrate {200,200,12,120}, max_accel {1000,1000,200,5000}.

## TODO — measured on hardware / read on Pi (NEVER guess these)

| Value | How to get it | Blocks |
|---|---|---|
| **Z-offset** | Stock firmware → *Menu → Calibration → Z-offset*. **Read BEFORE flashing — irreversible.** Make absolute. | `printer.cfg [probe] z_offset` |
| **MCU serial** | On Pi: `ls /dev/serial/by-id/*` → `usb-Klipper_stm32g0b1xx_...-if00` | `printer.cfg [mcu] serial` |
| **Motor directions** ×4 | Jog each axis in Mainsail; flip `!` on dir_pin if reversed. **Check Z first** (reversed Z homes downward). | `steppers.cfg` dir_pin |
| **Sensorless SGTHRS** X/Y | On Pi: tune `driver_SGTHRS` per `tmc2209.cfg` procedure (DIAG jumpers installed first) | `tmc2209.cfg` |
| **Probe polarity** | On Pi: `QUERY_PROBE` (slide metal under PINDA) — flip `!` on `[probe] pin` if inverted | `skr-mini-e3-v3.cfg [probe]` |
| **Filament-sensor polarity** | On Pi: `QUERY_FILAMENT_SENSOR` — flip `!` on switch_pin if inverted | `skr-mini-e3-v3.cfg fsensor` |
| **PINDA x/y offset** | Measure on YOUR toolhead (PINDA tip vs nozzle) | `skr-mini-e3-v3.cfg [probe] x_offset/y_offset` |
| **Extruder PID** | On Pi: `PID_CALIBRATE HEATER=extruder TARGET=215` → `SAVE_CONFIG` | `[extruder]` PID — mandatory for the 40W 12V Revo |
| **Bed PID** | On Pi: `PID_CALIBRATE HEATER=heater_bed TARGET=60` → `SAVE_CONFIG` | `[heater_bed]` PID |
| **rotation_distance** (verify) | Ellis extruder calibration | `steppers.cfg [extruder]` |
| **Pressure advance** | Ellis PA tuning (redo after input shaping) | slicer per-filament `SET_PRESSURE_ADVANCE` |
| **Input shaper** X/Y | On Pi: `SHAPER_CALIBRATE` per axis → `SAVE_CONFIG` | `[input_shaper]` |
| **Thermistor types** | Confirm temps look right; switch type if off (Revo may be 104NT-4) | `skr-mini-e3-v3.cfg` sensor_type |
| **Camera by-id paths** ×2 | On Pi: `ls /dev/v4l/by-id/` | `crowsnest.conf` |
| **HyperPixel overlay** | Validate live (klipperscreen/SETUP-NOTES.md) | `/boot/firmware/config.txt` |

## Still need from user (not blocking config authoring)

- [ ] **Pi model** for the MK2.5S (3B+ vs 4 vs 5) — decides webcam res/fps headroom.
- [ ] **SSH username** for `mk25s.local` (the MK3S+ build used `david`; confirm same).
- [ ] **Webcam models** + target resolution/fps.
- [ ] **HyperPixel model** (4.0 / 4.0 Square / 2.1 Round / other) — decides the dtoverlay line.
- [x] **Display decision = touchscreen-only** (HyperPixel + KlipperScreen). The stock Prusa LCD/knob
      can't fit the SKR's single EXP1 header; a BTT mini12864 is the drop-in if a physical knob is wanted
      later (block in reference/klipper-sample-lcd.cfg). `display.cfg` now wires only the beeper.
- [ ] **Confirm the SKR board revision is V3.0** (this build assumes V3.0 pinout).
- [ ] **Confirm bed leveling / frame** is square before tuning.
