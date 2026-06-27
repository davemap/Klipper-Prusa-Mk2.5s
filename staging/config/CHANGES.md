# CHANGES — MK2.5S / SKR Mini E3 V3 config vs. the MK3S+ build

This build mirrors the MK3S+ Klipper setup but on **different hardware**, so several files were
**rebuilt**, not copied. Pin source of truth: `reference/generic-bigtreetech-skr-mini-e3-v3.0.cfg`
(official Klipper). Geometry source of truth: `reference/Prusa-MK25S-RAMBo13a.h` (Prusa's own MK2.5S
firmware). Nothing measured-on-hardware was fabricated — those are TODO/VERIFY (see VALUES.md).

## File-by-file

| MK3S+ build | MK2.5S build | Status |
|---|---|---|
| `einsy-rambo.cfg` | `skr-mini-e3-v3.cfg` | **REBUILT** — STM32G0B1 pins for heaters/thermistors/fans/probe/fsensor |
| `tmc2130.cfg` (SPI) | `tmc2209.cfg` (UART) | **REBUILT** — 4× TMC2209 on shared UART PC11/PC10, addr X0/Y2/Z1/E3; sensorless homing |
| `steppers.cfg` | `steppers.cfg` | **REBUILT** — SKR pins + MK2.5S geometry |
| `display.cfg` (Einsy HD44780) | `display.cfg` (EXP1) | **REBUILT** — see "Display" below |
| `printer.cfg` | `printer.cfg` | **ADAPTED** — board includes, MK2.5S limits, Revo 40W/12V, PINDA |
| `macros.cfg` | `macros.cfg` | **ADAPTED** — PRINT_START defaults to MK2.5S + uses PINDA heat-soak path |
| `adxlmcu-BTT.cfg` / `-KUSBA.cfg` | same | **ADAPTED** — bed-center probe point 125,105 |
| `32u2-hoodserial-flash-cheatsheet.md` | `NO-32u2-reflash-needed.md` | **N/A** — SKR has native USB, no 32U2 bridge |
| `firmware-flash-cheatsheet.md` (AVR) | same name | **REBUILT** — STM32G0B1, SD-card `firmware.bin`, no `make flash` |

## Key value decisions (and where they came from)

| Setting | Value | Source / why |
|---|---|---|
| X/Y rotation_distance | 32 | MK2.5S firmware (100 steps/mm @ 16 µsteps) — same as MK3S |
| **Z rotation_distance** | **8** | MK2.5S firmware `3200/8` = 400 steps/mm = 8mm lead. (NOT 0.8/M5 — verified from Prusa firmware.) |
| Extruder rotation_distance | 24.06015 | MK2.5S firmware E=133 steps/mm @ 16 µsteps. **Differs from MK3S+ (22.96)** — different gearing. VERIFY via calibration. |
| Build volume | 250 × 210 × 210 | MK2.5S firmware X/Y/Z_MAX_POS |
| Machine limits (default) | vel 200 / accel 1000 / Zvel 12 / Zaccel 200 | MK2.5S firmware stock limits. Faster IS profile commented for after input shaping. |
| X/Y homing | TMC2209 sensorless (StallGuard) | Your choice. diag_pin ^PC0/^PC1 + driver_SGTHRS (TUNE). Mechanical-switch fallback commented in steppers.cfg. |
| Z homing | PINDA2 probe (PROBE port PC14) | MK2.5S has a PINDA2 (no SuperPINDA temp comp) → PRINT_START heat-soaks it. |
| Extruder PID | placeholder (21.527/1.063/108.982) | MANDATORY `PID_CALIBRATE HEATER=extruder` for the 40W 12V Revo. Not fabricated as final. |
| Bed PID | placeholder (54.027/0.770/948.182) | MANDATORY `PID_CALIBRATE HEATER=heater_bed`. |
| Extruder thermistor | ATC Semitec 104GT-2 | Matches MK3S+ Revo build; verify vs your Revo (may be 104NT-4). |
| Bed thermistor | EPCOS 100K B57560G104F | Prusa MK42 standard; verify if temps read off. |
| Run currents | X/Y/Z 0.55A, E 0.45A (RMS) | Conservative TMC2209 equivalents of Prusa's ~0.75A-peak RAMBo currents. Tune. |

## Display (read this — it's a real constraint)
You asked to wire the **stock Prusa LCD** to the board. The SKR Mini E3 V3 has only **one** LCD header
(EXP1, no EXP2) with **7 usable GPIO** (EXP1_4 is RESET). A parallel HD44780 + rotary encoder + beeper
needs 10 signals — **they don't all fit**. So `display.cfg`:
- Leaves the **BEEPER active** on EXP1_1 (PB5) — that fits, so M300/feedback tones work.
- Provides a commented **BTT mini12864** block (SPI — *does* fit) if you want a real on-printer menu knob.
- Provides a commented **status-only HD44780** block, flagged that the encoder can't be added.
- Points at the **HyperPixel + KlipperScreen** as the primary UI (klipperscreen/SETUP-NOTES.md).
> Also note: FAN2 (PB15) shares a pin with EXP1_8, so it's unavailable when a display is on EXP1 — you
> don't need it (FAN0 part-cooling + FAN1 hotend cover the MK2.5S).

## Deliberately NOT changed
- **Bed-mesh faulty regions** from the MK3S+ build were **removed** (those magnet coords are MK52/MK3,
  wrong for the MK42). Clean 5×5 grid instead; add MK42-specific regions later if needed.
- **Accelerometer includes** left commented (enabled only during input shaping). USB ADXL — no GPIO/
  HyperPixel conflict.
- **`[input_shaper]`**, **`[skew_correction]`**, **z_offset**, **PID**, everything below SAVE_CONFIG —
  populated on-device.

## Self-review
- No hard tabs. No duplicate `[section]` headers across included files (one `[board_pins]`, one of each).
- Remaining template tokens are intentional TODOs: `[probe] z_offset`, `[mcu] serial`, camera by-id, PID.

## Files that ship to the Pi (`~/printer_data/config/`)
`printer.cfg`, `skr-mini-e3-v3.cfg`, `tmc2209.cfg`, `steppers.cfg`, `display.cfg`, `macros.cfg`,
`adxlmcu-BTT.cfg`, `adxlmcu-KUSBA.cfg`, plus `crowsnest.conf` (from `../webcam/`).
> `printer.cfg` does `[include mainsail.cfg]` — **mainsail.cfg is provided by MainsailOS**, do not ship ours.
