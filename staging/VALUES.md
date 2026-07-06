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
| Display | **BOTH UIs**: stock Prusa 20x4 LCD + dial + beeper on the SKR (✅ WORKING, bench-verified 2026-06-29) AND HyperPixel + KlipperScreen on the Pi | `display.cfg` (custom clean-pin map — see its header) |
| Bed-MOSFET fan | 12V fan on **FAN2 (PB15)** cooling the external bed MOSFET | `skr-mini-e3-v3.cfg [heater_fan bed_mosfet_fan]` — auto with bed heat |
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
| **Z-offset** | ✅ CALIBRATED ON-DEVICE 2026-07-03: PROBE_CALIBRATE paper test → `z_offset = -0.211` (SAVE_CONFIG'd). The Rambo EEPROM value (-293 = Prusa Live-Z *babystep*) was a DIFFERENT reference frame and does NOT map to Klipper's absolute offset — do not use it as the offset. EEPROM read stands as proof the board's print history was real; dump archived in `reference/rambo-eeprom/`. Fine-tune -0.211 live on the first layer. | `printer.cfg [probe] z_offset` ✅ measured |
| **MCU serial** | ✅ FILLED 2026-07-03: `usb-Klipper_stm32g0b1xx_09003D000C50564837383420-if00` (this board). | `printer.cfg [mcu] serial` ✅ |
| **Motor directions** ×4 | ✅ ALL CONFIRMED ON-DEVICE 2026-07-03 (real travel, not blips): X ok, Y ok, **Z=`!PC5`** (settled via 15-20mm moves — small jogs misled us), **E=`PB4`** (filament fed + extruded through the Revo). | `steppers.cfg` dir_pin ✅ done |
| **Sensorless SGTHRS** X/Y | ✅ WORKING ON-DEVICE 2026-07-03. **Y tuned to `driver_SGTHRS: 110`** (80 under-triggered warm → rammed; 110 homes clean + repeatable warm). **X tuned to 115** (2026-07-04) — 80 crashed hard, 100 was inconsistent (1 soft/2 crash), 115 homes soft + consistent, still reaches the end. DIAG jumpers in, no physical endstops. StallGuard drifts with motor temp — see tmc2209.cfg notes. | `tmc2209.cfg` X ✅ / Y ✅ |
| **Probe polarity** | ✅ CONFIRMED ON-DEVICE 2026-07-03: `QUERY_PROBE` flips 1(steel)/0(clear); full `G28 Z` probes clean on the sheet. `^PC14` correct. **NOTE: the steel SHEET must be on the bed — bare MK52 has nothing ferrous for the PINDA to see.** | `skr-mini-e3-v3.cfg [probe]` ✅ |
| **Filament-sensor polarity** | ✅ Bench-confirmed 2026-06-28: sensor = 0V when filament present; `^!PC15` already matches → no change needed. | `skr-mini-e3-v3.cfg fsensor` |
| **PINDA x/y offset** | Measure on YOUR toolhead (PINDA tip vs nozzle) | `skr-mini-e3-v3.cfg [probe] x_offset/y_offset` |
| **Extruder PID** | ✅ TUNED ON-DEVICE 2026-07-03 @215: **Kp=33.231 Ki=5.539 Kd=49.847** (vs the wrong placeholder 21.5/1.06/109 — confirms the 40W Revo needed it). SAVE_CONFIG owns it in the autosave block. | `[extruder]` PID ✅ |
| **Bed PID** | ⏳ NEXT: `PID_CALIBRATE HEATER=heater_bed TARGET=60` → `SAVE_CONFIG` (through the external MOSFET; watch the MOSFET + its FAN2 fan run). | `[heater_bed]` PID |
| **HyperPixel + KlipperScreen** | ✅ WORKING 2026-07-03: HyperPixel 4.0, `vc4-kms-dpi-hyperpixel4,rotate=270`, X11 rotate-left + touch matrix (cloned from mk3s). Fix was disabling `dtparam=spi/i2c_arm` (they stole the DPI GPIOs). | `/boot/firmware/config.txt` ✅ |
| **rotation_distance** (verify) | Ellis extruder calibration | `steppers.cfg [extruder]` |
| **Pressure advance** | Ellis PA tuning (redo after input shaping) | slicer per-filament `SET_PRESSURE_ADVANCE` |
| **Input shaper** X/Y | On Pi: `SHAPER_CALIBRATE` per axis → `SAVE_CONFIG` | `[input_shaper]` |
| **Thermistor types** | Confirm temps look right; switch type if off (Revo may be 104NT-4) | `skr-mini-e3-v3.cfg` sensor_type |
| **Camera by-id paths** ×2 | On Pi: `ls /dev/v4l/by-id/` | `crowsnest.conf` |
| **HyperPixel overlay** | Validate live (klipperscreen/SETUP-NOTES.md) | `/boot/firmware/config.txt` |

## Still need from user (not blocking config authoring)

- [x] **Pi model = Raspberry Pi 3B+** (same as the MK3S+ build). → keep webcams conservative (<=800x600,
      <=15fps) on the shared USB 2.0 bus. Pi needs 5V — on this 12V machine, power it from a separate 5V
      supply OR a 12V→5V buck converter off the printer PSU (don't back-feed the SKR's logic rail).
- [ ] **SSH username** for `mk25s.local` (the MK3S+ build used `david`; confirm same).
- [ ] **Webcam models** + target resolution/fps.
- [ ] **HyperPixel model** (4.0 / 4.0 Square / 2.1 Round / other) — decides the dtoverlay line.
- [x] **Display = stock Prusa LCD + dial + beeper, WORKING** (bench-verified 2026-06-29 under Marlin;
      identical pin map staged in `display.cfg` for Klipper). Root cause of the earlier garble was LCD
      data lines on filtered endstop pins (100nF debounce caps) — final map keeps all 6 data lines on
      clean pins and spills the SLOW signals instead (beeper→PC12, click→PC2). HyperPixel = second UI.
- [ ] **Confirm the SKR board revision is V3.0** (this build assumes V3.0 pinout).
- [ ] **Confirm bed leveling / frame** is square before tuning.
