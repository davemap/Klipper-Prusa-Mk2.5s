# MK2.5S → Klipper (on SKR Mini E3 V3) Conversion — Off-Pi Prep Guide

## Purpose
Sibling of the MK3S+ prep guide, for the **second printer**: a Prusa **MK2.5S** that is
(a) getting its **mainboard replaced** with a **BTT SKR Mini E3 V3.0**, and (b) getting an
**E3D Revo (40W, 12V)** hotend. The host-side stack is the same as the MK3S+ build (MainsailOS +
Mainsail + Moonraker, HyperPixel + KlipperScreen, two webcams, BTT ADXL345 input shaping), on a
**separate, dedicated Raspberry Pi** at `mk25s.local`.

Everything staged here is meant to be `rsync`'d to that Pi so the on-device session is fast.

> ⚠️ **Safety:** measured/tuned values (Z-offset, PID, pressure advance, e-steps, sensorless SGTHRS,
> probe polarity) are left as clearly-marked TODO/VERIFY — never fabricated. A misconfigured Klipper
> printer can crash the nozzle. Validate every config on-device (config checks, PID tuning) before printing.

---

## What's the SAME as the MK3S+ build (carried over)
- Host stack: MainsailOS, Mainsail/Moonraker, KlipperScreen on a HyperPixel, crowsnest two-camera.
- The macro library (`macros.cfg`) — PRINT_START/END, PRUSA_LINE_PURGE, M600, LOAD/UNLOAD, Marlin-compat.
- BTT ADXL345 (USB) input-shaping flow.
- The overall tuning order (config checks → PID → extruder cal → PA → input shaping → re-PA).

## What's DIFFERENT (and why it's a real rebuild, not a copy)
| Area | MK3S+ build | MK2.5S build |
|---|---|---|
| Board | Einsy RAMBo (ATmega2560, 8-bit AVR) | **SKR Mini E3 V3.0 (STM32G0B1, 32-bit)** |
| Drivers | TMC2130 over **SPI** | **TMC2209 over UART** (PC11/PC10; addr X0/Y2/Z1/E3) |
| X/Y homing | sensorless (TMC2130) | **sensorless (TMC2209 StallGuard)** — diag_pin + SGTHRS to tune |
| Z probe | SuperPINDA (temp-compensated) | **PINDA2** (no comp) → PRINT_START heat-soaks it |
| Firmware flash | AVR `make flash` over USB | **STM32 SD-card** (`firmware.bin`), no `make flash` |
| USB bridge | 32U2 Hoodserial reflash needed | **none** — STM32 native USB (step removed) |
| Hotend | Revo 60W | **Revo 40W, 12V** |
| System voltage | 24V | **12V** (power SKR VIN at 12V; never 24V) |
| Z mechanics | 8mm lead | **8mm lead too** (verified from Prusa firmware; rotation_distance 8) |
| Extruder e-steps | 22.96 | **24.06015** (MK2.5S firmware E=133 steps/mm — different gearing) |
| Display | Einsy HD44780 | HyperPixel/KlipperScreen primary; **stock LCD can't fully fit the SKR's single EXP1** (see display.cfg) |

Authoritative sources used (in `reference/`):
- `generic-bigtreetech-skr-mini-e3-v3.0.cfg` — official Klipper board pinout (FIXED pins).
- `Prusa-MK25S-RAMBo13a.h` — Prusa's own MK2.5S firmware (steps/mm, travel, limits).
- `klipper-sample-lcd.cfg` — Klipper's EXP1 display wiring reference.

---

## Deliverable layout (this folder)
```
mk25s/Klipper/
  reference/                         # authoritative pinout + firmware values (do not edit)
  staging/
    config/
      printer.cfg                    # main config — MK2.5S + Revo 40W/12V
      skr-mini-e3-v3.cfg             # board pins: heaters, thermistors, fans, PINDA, fsensor, mesh
      tmc2209.cfg                    # TMC2209 UART drivers + sensorless homing
      steppers.cfg                   # SKR pins + MK2.5S geometry
      display.cfg                    # EXP1 beeper + LCD options (HyperPixel is primary)
      macros.cfg                     # macros (PRINT_START defaults to MK2.5S + PINDA heat-soak)
      adxlmcu-BTT.cfg / -KUSBA.cfg   # accelerometer (enabled only during input shaping)
      CHANGES.md                     # every divergence from the MK3S+ build, with rationale
    prusaslicer/                     # MK2.5S checklist + start/end gcode
    webcam/                          # two-camera crowsnest config
    klipperscreen/                   # HyperPixel + KlipperScreen notes & installer
    scripts/                         # deploy + SKR firmware flash cheatsheets
    VALUES.md                        # confirmed values + the TODO/VERIFY list
    ON-PI-RUNBOOK.md                 # the ordered on-Pi checklist
    PREFLIGHT.md                     # physical checklist (incl. the mainboard swap + Z-offset read)
```

## How to use it
1. Read `PREFLIGHT.md` — **record the Z-offset before pulling the old miniRambo**, wire the SKR.
2. Flash MainsailOS (hostname `mk25s`), then `scripts/deploy-config.sh <user>@mk25s.local`.
3. Flash Klipper to the SKR via `scripts/firmware-flash-cheatsheet.md` (SD-card method).
4. Work top-to-bottom through `ON-PI-RUNBOOK.md` (config checks → sensorless tuning → PID → tuning →
   input shaping → screen). Fill every TODO from `VALUES.md` on-device — don't guess.

## Definition of done
- `printer.cfg` + board/driver/stepper cfgs customized for the SKR Mini E3 V3 + MK2.5S geometry +
  Revo, with every measurable value flagged TODO/VERIFY (not fabricated).
- Firmware flash + deploy scripts exist and target the SKR / `mk25s.local`.
- `ON-PI-RUNBOOK.md`, `PREFLIGHT.md`, `VALUES.md`, `CHANGES.md` tie it together in order.
- Display reality (stock LCD vs EXP1 pin limit) is documented, not glossed over.
