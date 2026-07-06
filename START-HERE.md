# START HERE — MK2.5S → Klipper go-live guide

**Updated 2026-07-03.** Bench testing is **COMPLETE** — every connector was validated under a
temporary Marlin build, the stock LCD + dial works, and both firmware images are prepared.
This is the single ordered path to a printing machine. Tick straight down it.

**Printer:** Prusa MK2.5S · BTT SKR Mini E3 V3.0 (STM32G0B1, TMC2209 UART, **12V**) · E3D Revo 40W 12V 0.4mm ·
sensorless X/Y · PINDA2 Z · stock Prusa LCD + dial (working) · BTT ADXL345 (USB) · external bed MOSFET +
cooling fan · Pi 3B+ `mk25s.local` · MainsailOS · HyperPixel/KlipperScreen.

---

## ✅ Already done (bench, 2026-06-28/29) → [staging/BENCH-TEST-RESULTS.md](staging/BENCH-TEST-RESULTS.md)
- All 4 motors move; X/Y **sensorless homing proven**; dual-Z in sync; hotend heats/extrudes;
  both thermistors read; fans spin; filament sensor + PINDA polarities confirmed.
- **Z and E ran inverted → already pre-flipped** in `steppers.cfg` (verify on-device anyway).
- **Stock LCD + dial WORKING** on a custom pin map (the garble was filtered endstop pins — solved;
  don't re-route the display wiring, it's deliberate → [staging/config/display.cfg](staging/config/display.cfg)).
- Still untested: bed heater (kept unplugged), beeper (`M300` once on Klipper), MOSFET fan (new).

## The two images (both prepared)
| # | Target | What | Where |
|---|---|---|---|
| 1 | **Pi 3B+** (host) | MainsailOS — flash with Raspberry Pi Imager (step 1) | imager download, settings below |
| 2 | **SKR Mini E3 V3.0** (MCU) | Prebuilt Klipper `firmware.bin` (commit `7e64fc8`) | [staging/firmware/](staging/firmware/) |

---

## Order of the day

### 1 · Image #1 — flash MainsailOS to the Pi SD (~10 min, do first; everything else can overlap)
Raspberry Pi Imager (installed on this Mac):
1. **Choose Device** → Raspberry Pi 3.
2. **Choose OS** → *Other specific-purpose OS* → *3D printing* → **Mainsail OS** → the **32-bit Lite**
   variant (right choice for the 1GB 3B+).
3. **Choose Storage** → the Pi's microSD (≥8GB).
4. **Edit Settings** (⚙️): hostname **`mk25s`** · username **`david`** (same as the MK3S build) ·
   your Wi-Fi SSID/password · locale GB · **enable SSH** (password auth is fine).
5. Write. Boot the Pi from it (power the Pi from its own 5V supply — do NOT back-feed the SKR's rail).
6. Wait ~2-3 min on first boot, then confirm: `http://mk25s.local` loads Mainsail and
   `ssh david@mk25s.local` works. (Mainsail will show "printer not connected" — expected until step 3.)

### 2 · Final wiring deltas from the bench setup → [staging/scripts/wiring-map.md](staging/scripts/wiring-map.md)
Four changes from how the bench left it, then it's the final loom:
- **Move the heatbreak fan back to FAN1** (it was bench-tested on FAN0). Part-cooling fan → FAN0.
- **Bed via the MOSFET module** (never direct): PSU heavy-gauge 12V → module **IN** · module **OUT** → bed ·
  board **HB terminal** → module **Signal/Trigger**. Bed thermistor stays on **TB**. All screws TIGHT.
- **New: MOSFET cooling fan → FAN2** (12V). Config `[heater_fan bed_mosfet_fan]` runs it automatically
  whenever the bed is heating (and through cooldown) — no manual control needed.
- **X/Y DIAG jumpers stay IN** (sensorless), no X/Y endstop switches wired.
Everything else exactly as bench-validated (display loom included — don't touch it).

### 3 · Image #2 — flash Klipper to the SKR → [staging/firmware/README.md](staging/firmware/README.md)
```
SD into Mac → copy staging/firmware/klipper-skr-mini-e3-v3.0-7e64fc8.bin onto it AS firmware.bin
(delete FIRMWARE.CUR) → SD into SKR → power on → ~15 s → file renamed FIRMWARE.CUR = flashed.
```
- The LCD will sit blank/idle after this — **normal**. Klipper's MCU does nothing until the Pi connects.
- USB the SKR to the Pi, then on the Pi: `ls /dev/serial/by-id/*` → copy the
  `usb-Klipper_stm32g0b1xx_...-if00` path.
- If Mainsail later shows an MCU version-mismatch warning, rebuild on the Pi (settings in the
  firmware README) and re-do this step. Small skew is normally fine.

### 4 · Deploy the config → [staging/scripts/deploy-config.sh](staging/scripts/deploy-config.sh)
```bash
cd staging/scripts && ./deploy-config.sh david@mk25s.local
```
Then in Mainsail's config editor fill the two TODOs in `printer.cfg`:
- `[mcu] serial:` ← the by-id path from step 3.
- `[probe] z_offset =` ← your recorded stock Z-offset (absolute). Never recorded it? Leave 0.000 —
  step 6's PROBE_CALIBRATE derives it from scratch (just don't print before then).
Save & Restart → Klipper should connect: dashboard shows temps, and **the stock LCD comes alive**
with the Klipper status screen.

### 5 · First-power checks (5 min, DON'T SKIP) → [staging/ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md)
```
# temps: extruder + bed read ~room temp on the dashboard (wild readings -> fix thermistor first)
# directions (flips are PRE-APPLIED — this is the confirmation, Z FIRST, hand on power):
#   jog +Z 5mm -> nozzle RISES · +X -> carriage right · +Y -> bed moves forward/nozzle toward back
QUERY_PROBE                            # slide metal under PINDA -> flips to TRIGGERED
QUERY_FILAMENT_SENSOR SENSOR=fsensor   # filament in/out toggles it
M300 S440 P500                         # beeper (PC12) — first live test of it
# dial: scroll + click through the LCD menu (wrong scroll direction? swap encoder_pins in display.cfg)
SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=60   # bed via MOSFET + fan check: FAN2 spins up,
# bed climbs, MOSFET stays cool-ish. First bed heat ATTENDED. Then TARGET=0 (fan keeps running
# until the bed drops under 45°C, then stops — that's the config working).
```

### 6 · Sensorless homing tune + real Z-offset → [staging/config/tmc2209.cfg](staging/config/tmc2209.cfg)
```
G28 X            # hand on reset. Tune driver_SGTHRS (X then Y):
                 #   triggers early/mid-travel -> LOWER · rams the end -> RAISE. Save+restart between tries.
G28 Y
G28              # full home — Z probes off the PINDA at bed center
PROBE_CALIBRATE  # paper test -> ACCEPT -> SAVE_CONFIG   (this sets the REAL z_offset)
```

### 7 · PID both heaters — MANDATORY (placeholders in config are not your machine)
```
PID_CALIBRATE HEATER=extruder TARGET=215
SAVE_CONFIG
PID_CALIBRATE HEATER=heater_bed TARGET=60     # through the MOSFET; watch it the first time
SAVE_CONFIG
```

### 8 · First print (PLA, 60°C bed, attended)
- PrusaSlicer: import [staging/prusaslicer/MK2.5S-Klipper-printer.ini](staging/prusaslicer/MK2.5S-Klipper-printer.ini)
  (pair with Prusa MK2.5S 0.4mm Print/Filament presets) → [checklist](staging/prusaslicer/SETTINGS-CHECKLIST.md).
- Watch the first layer. Congratulations — it's a Klipper printer now.

### 9 · Tuning sessions (order matters) → [staging/ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md) steps 11-15
1. Extruder e-steps check (verify rotation_distance 24.06) → Ellis extruder calibration.
2. Pressure advance (per-filament, in slicer).
3. **Input shaping**: flash the BTT ADXL345 → [cheatsheet](staging/scripts/adxl345-btt-firmware-cheatsheet.md),
   uncomment `[include adxlmcu-BTT.cfg]`, `SHAPER_CALIBRATE AXIS=X` / `Y`, `SAVE_CONFIG`, re-comment.
   Then unlock the faster limits block in printer.cfg and RE-tune pressure advance.
4. `AXIS_TWIST_COMPENSATION_CALIBRATE` (PINDA bias) → bed mesh → `SKEW_PROFILE` last.

### 10 · Host extras (any time after step 4)
- **KlipperScreen + HyperPixel** → [staging/klipperscreen/SETUP-NOTES.md](staging/klipperscreen/SETUP-NOTES.md) ·
  [install-klipperscreen.sh](staging/klipperscreen/install-klipperscreen.sh). Both UIs run together —
  dial+LCD on the printer, touch on the Pi.
- **Webcams** → [staging/webcam/](staging/webcam/) (crowsnest; fill the `/dev/v4l/by-id/` paths;
  keep ≤800×600@15 on the 3B+'s shared USB bus).

---

## What's prepared (index)
| File | What it's for |
|---|---|
| [staging/firmware/](staging/firmware/) | **prebuilt Klipper firmware.bin for the SKR** + rebuild instructions |
| [staging/config/](staging/config/) | full Klipper config — bench findings + LCD map + MOSFET fan pre-applied |
| [staging/config/display.cfg](staging/config/display.cfg) | stock LCD/dial/beeper pin map + why it must not be "tidied" |
| [staging/BENCH-TEST-RESULTS.md](staging/BENCH-TEST-RESULTS.md) | everything validated on the bench + how |
| [staging/scripts/wiring-map.md](staging/scripts/wiring-map.md) | every cable → connector; MOSFET wiring; dual-Z; sensorless |
| [staging/scripts/deploy-config.sh](staging/scripts/deploy-config.sh) | rsync config to `mk25s.local` |
| [staging/VALUES.md](staging/VALUES.md) | confirmed values + remaining TODO-on-hardware list |
| [staging/ON-PI-RUNBOOK.md](staging/ON-PI-RUNBOOK.md) | detailed runbook behind this quickstart |
| [staging/prusaslicer/](staging/prusaslicer/) | 0.4mm printer profile + start/end gcode + checklist |
| [staging/klipperscreen/](staging/klipperscreen/) · [staging/webcam/](staging/webcam/) | HyperPixel/KlipperScreen + crowsnest |
| [staging/config/CHANGES.md](staging/config/CHANGES.md) | every divergence from the MK3S+ build, with rationale |

**Lineage note:** this build follows the same path as the MK3S+ one (charminULTRA's input-shaping guide →
dz0ny's klipper-prusa-mk3s config). What transfers: MainsailOS, config structure, macros, tuning order
(Ellis → input shaping → PA redo), axis-twist compensation. What does NOT (and why this tree diverges):
no Einsy/32U2 serial bug → no HoodLoader reflash; SD-card flash instead of `make flash`; TMC2209 UART +
sensorless instead of TMC2130 SPI; MK2.5S geometry (Z 8mm lead!, E 24.06); 12V everything; external bed
MOSFET; and the custom LCD pin map. Details: [staging/config/CHANGES.md](staging/config/CHANGES.md).
