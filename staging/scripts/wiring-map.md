# Wiring map — Prusa MK2.5S → BTT SKR Mini E3 V3.0

The board swap is the riskiest part of the conversion. This maps each Prusa MK2.5S cable to the SKR
connector and the Klipper pin it uses. **Label every Prusa cable before you unplug the miniRambo.**
Pins are board-fixed (see `config/skr-mini-e3-v3.cfg` + `reference/`). Directions/polarity are verified
in software (ON-PI-RUNBOOK step 7) — don't trust connector orientation.

> **Power (PSU → board).** The MK2.5S 12V PSU has TWO outputs — a **main 12V** and a dedicated
> **heated-bed 12V** (same rail; the bed one is heavy-gauge for the ~11A bed). The SKR has only ONE power
> input (VIN), no separate bed input. So:
>  - **Main 12V → SKR "Power In" (VIN)**, + to +, − to − (verify polarity with a meter; reversed = dead board).
>    Powers board, motors, hotend.
>  - **Heated-bed 12V → the external bed MOSFET's power input** (Phase 2) → MOSFET out → bed. Routes the
>    ~11A straight from the PSU through the MOSFET, bypassing the SKR — exactly what that output is for.
>  - **Motor-only / bench test:** you don't need the bed output at all — just VIN.
> All fan/heater outputs switch VIN = 12V. Never feed 24V.

## 🔴 READ FIRST — two things that aren't plug-and-play

### 1) Heated bed — external MOSFET (PHASED: direct today, MOSFET tomorrow)
Your 12V MK42 bed draws **~10–15 A** (~130 W at 12 V — a 24 V bed of the same power pulls only ~5 A).
The SKR Mini E3 V3's WSK220N04 bed FET itself loafs at this current (~0.25 W) — the real limit is the
board's **bed screw terminal + PCB traces + the shared 20 A fuse headroom**, all sized for 24 V/~5 A beds.
The documented failure mode is a **hot/melted bed terminal** (a thermal/fire risk), not a clean shutdown —
and **Klipper cannot detect it** (it's a wiring issue, not a sensor/heater fault). So the high-current path
gets moved off the board onto an external MOSFET. (Note: even Prusa's own miniRambo has an "add a bed
MOSFET" mod for this same 12 V bed current.)

A heated-bed MOSFET module is **purchased**, arriving ~next day. The hotend (Revo ~3.3 A) is fine on-board
regardless. The bed thermistor stays on the board's **TB** input in both phases (it's just a sensor).

**PHASE 1 — TODAY, bed wired DIRECT to the board (interim, MONITORED). This does NOT gate bringup.**
- **Measure the bed first** (multimeter across the bed power terminals, cold): current = 12 ÷ R.
  - ≥1.5 Ω (~≤8 A): low risk — proceed, still watch the first heat.
  - ~1.1–1.4 Ω (~9–11 A): marginal — proceed but keep bed heating SHORT + ATTENDED.
  - ≤1.0 Ω (~12 A+): don't heat the bed direct even briefly — do the non-bed commissioning today, wait for the MOSFET.
- Bed → SKR **HB** terminal; screw **TIGHT**, use the thick stock bed wire (a loose screw is the #1 melt cause).
- Do ALL non-bed commissioning freely today (directions, sensorless homing, probe/fsensor polarity, hotend
  PID, extruder, fans). Then a SHORT attended bed heat + bed PID tune while you watch the HB terminal temp
  (finger-near / IR thermometer). Warm = OK; too-hot-to-touch = stop.
- **Until the MOSFET is in:** no long/unattended prints with the bed on, and keep bed temp modest (PLA ~60 °C,
  not 90–100 °C ABS) — high temp = max current for the longest.

**PHASE 2 — TOMORROW, install the MOSFET module (then unrestricted):**
- Power off. Move the bed wires off the board's HB terminal.
- Wire the module (standard heated-bed MOSFET, 3 terminal pairs):
  - **PSU 12 V  →  module "Power Input"** (VCC/IN)
  - **module "Output"  →  bed** (to the bed's power leads)
  - **board's HB terminal  →  module "Signal/Trigger" input** (low-current trigger only)
- Mount the module where it gets a little airflow; terminals tight.
- **No printer.cfg change** — `heater_pin: PC9` now switches the trigger instead of the bed.
- Power on → short heat test → **re-run `PID_CALIBRATE HEATER=heater_bed TARGET=60` → SAVE_CONFIG**
  (the drive path changed slightly; cheap to re-confirm). Then resume normal/unattended printing.

### 2) Z has TWO motors, the SKR has ONE Z port
The MK2.5S has a **Z-left and a Z-right** motor (dual lead screws). Wire **both** to the single SKR
**Z-MOT** port, in **series** (the Prusa norm; keeps current matched). After power-up, jog Z a few mm:
**both screws must turn the same way** — if one is backwards, reverse THAT motor's connector (swap one
coil pair), then set overall direction with the `!` on `stepper_z: dir_pin` in `steppers.cfg`.

---

## Stepper motors (4-pin each → SKR motor ports)
| Prusa cable | SKR connector | Klipper | Notes |
|---|---|---|---|
| X motor | **X-MOT** | `stepper_x` (PB13/PB12/PB14) | coil pairing may differ from Prusa's plug — if it buzzes/won't move, regroup the 2 wires per coil |
| Y motor | **Y-MOT** | `stepper_y` (PB10/PB2/PB11) | " |
| Z motors ×2 (L+R) | **Z-MOT** (both, series) | `stepper_z` (PB0/PC5/PB1) | see "Z has TWO motors" above |
| Extruder motor | **E0-MOT** | `extruder` (PB3/PB4/PD1) | direction = extrude vs retract; verify before extruding |

## Heaters & thermistors
| Prusa cable | SKR connector | Klipper | Notes |
|---|---|---|---|
| Hotend heater (Revo 40W 12V) | **HE0** | heater_pin PC8 | ~3.3 A, on-board OK |
| Hotend thermistor (Revo) | **TH0** | sensor_pin PA0 | type ATC Semitec 104GT-2 (verify vs your Revo) |
| **Bed heater (MK42 12V)** | TODAY: **HB** direct (monitored) · TOMORROW: via external MOSFET | heater_pin PC9 | phased — see §1; ~10–15 A |
| Bed thermistor | **TB** | sensor_pin PC4 | EPCOS 100K B57560G104F |

## Fans (12V on VIN)
| Prusa cable | SKR connector | Klipper | Notes |
|---|---|---|---|
| Part-cooling fan | **FAN0** | `[fan]` PC6 | slicer-controlled M106 |
| Hotend/heatbreak fan | **FAN1** | `[heater_fan heatbreak_cooling_fan]` PC7 | auto-on when hotend hot |
| (FAN2 unused) | — | — | PB15 shares EXP1_8; no tach inputs on these ports |

## Probe, endstops, filament sensor
| Prusa cable | SKR connector | Klipper | Notes |
|---|---|---|---|
| PINDA2 — inductive (3 wires: +V, GND, signal) | **PROBE** | `[probe] pin: ^PC14` | power +5V/GND; NPN, safe w/ pull-up; verify polarity `QUERY_PROBE` |
| PINDA2 — thermistor (2 wires) | **not connected** | — | no spare ADC on the SKR; PRINT_START heat-soaks instead of temp-comp |
| X endstop switch | **not wired** (sensorless) | StallGuard via DIAG jumper | install X/Y DIAG jumpers; mechanical wiring is the commented fallback in steppers.cfg |
| Y endstop switch | **not wired** (sensorless) | StallGuard via DIAG jumper | " |
| Z endstop | n/a | PINDA is the Z endstop (`probe:z_virtual_endstop`) | — |
| IR filament sensor (3 wires) | **E0-DET** | `fsensor` switch_pin ^!PC15 | 5V sensor → verify signal level vs PC15 + polarity (`QUERY_FILAMENT_SENSOR`); optional, can disable |

## Display / misc
- **No board LCD** (touchscreen-only). Optional: a piezo on **EXP1 pin 1 (PB5)** gives M300 beeps.
- HyperPixel + Pi are separate (host side) — not wired to this board.
- Optional: **PWR-DET** (PC12) for power-loss detection — not configured; ignore for now.

## Order of operations (safe bring-up)
1. Wire everything EXCEPT bed + hotend heaters. Power on at 12V over USB only (or PSU with heaters off).
2. Confirm Klipper connects, thermistors read room temp, motors jog the right way (esp. **Z up**).
3. Then connect heaters (bed via the external MOSFET), do a brief heat test, then PID tune.
