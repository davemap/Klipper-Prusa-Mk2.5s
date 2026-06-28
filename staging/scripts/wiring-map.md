# Wiring map — Prusa MK2.5S → BTT SKR Mini E3 V3.0

The board swap is the riskiest part of the conversion. This maps each Prusa MK2.5S cable to the SKR
connector and the Klipper pin it uses. **Label every Prusa cable before you unplug the miniRambo.**
Pins are board-fixed (see `config/skr-mini-e3-v3.cfg` + `reference/`). Directions/polarity are verified
in software (ON-PI-RUNBOOK step 7) — don't trust connector orientation.

> Power the board's VIN from the printer's **12V** PSU. All fan/heater outputs switch VIN = 12V. Never 24V.

## 🔴 READ FIRST — two things that aren't plug-and-play

### 1) Heated bed → use an EXTERNAL bed MOSFET (don't run it through the board)
Your 12V MK42 bed draws **~10–11 A** (~130 W at 12 V — a 24 V bed of the same power pulls only ~5 A).
The SKR Mini E3 V3's onboard bed output (WSK220N04 FET, shared 20 A board fuse) and its bed screw
terminal are sized for ~24 V/~5 A beds — **~11 A risks overheating the board's bed terminal/traces.**
- **Do:** add an **external bed MOSFET module** (or a 12 V-rated SSR). Bed power (12 V) runs PSU → MOSFET →
  bed. The board's **HB output** becomes the low-current *trigger* into the MOSFET's signal input.
- Keep the **bed thermistor** on the board's TB input regardless (that's just a sensor).
- The **hotend** is fine on-board: the 40 W 12 V Revo is only ~3.3 A → SKR HE0 handles it directly.

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
| **Bed heater (MK42 12V)** | **external MOSFET** (triggered by **HB**) | heater_pin PC9 | see "external bed MOSFET" above — ~11 A |
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
