# Bench-test results — connector/wiring validation (2026-06-28)

Before flashing Klipper, **every connector was bench-tested** by flashing a *temporary* custom Marlin
(Ender-3 SKR Mini E3 V3 config + `SENSORLESS_HOMING` + `FILAMENT_RUNOUT_SENSOR`, built from source) and
driving each output / reading each input over USB at 115200. This de-risked the wiring before Klipper.

## ✅ Validated
| Item | Connector | Result |
|---|---|---|
| X motor | X-MOT | moves; sensorless homes (StallGuard) reliably + repeatably |
| Y motor | Y-MOT | moves; sensorless homes reliably + repeatably |
| Z motors (×2, series) | Z-MOT | move together — **dual-Z in sync**; direction **inverted** |
| E motor | E0-MOT | moves; extrudes + retracts; direction **inverted** |
| Part-cooling fan | FAN0 | spins + PWM speed control |
| Extruder/heatbreak fan | (tested on FAN0) | spins + PWM → **move back to FAN1** for real use |
| Hotend thermistor | TH0 | reads room temp; tracked a heat to 220 °C cleanly |
| Bed thermistor | TB | reads room temp |
| HE0 heater | HE0 | heats clean (~53 s, 26→220 °C); melted + extruded filament |
| Filament sensor | E0-STOP / PC15 | tracks filament reliably (7/7 flips). 5 V Prusa IR sensor wired **direct** — PC15 IS 5 V-tolerant as a digital GPIO input (loses tolerance only in oscillator/analog mode), so no resistor/divider needed. |
| PINDA2 probe | PROBE / PC14 | detects ferrous metal reliably (4/4 flips); metal = TRIGGERED (matches `[probe] pin: ^PC14`). BROWN→5V, BLUE→GND, BLACK→PC14. Thermistor (WHITE) taped off — PRINT_START heat-soak used instead of temp-comp. |

## ⚙️ Findings to apply during Klipper bring-up
- **`stepper_z` direction — INVERTED on the bench** (commanded up → went down). Expect to flip
  `stepper_z: dir_pin` (add/remove the `!`). **VERIFY on-device FIRST** — Z direction is the dangerous one
  (hand on reset); the Marlin baseline differs from Klipper, so confirm, don't assume.
- **`extruder` direction — INVERTED on the bench** (commanded retract → extruded). Expect to flip
  `extruder: dir_pin`. Verify with a small extrude on-device.
- **Filament-sensor polarity:** the sensor outputs **0 V = filament present**. Klipper's
  `switch_pin: ^!PC15` (the `!`) already matches this → no change needed.
- **Dual-Z:** the two Z motors run in sync on Z-MOT (series wiring good).

## ⏳ Not bench-tested (do in Klipper)
- **Bed heater (HB):** kept unplugged during bench testing — verify in Klipper (and via the external MOSFET).
- (PINDA probe was tested via a temporary Marlin `FIX_MOUNTED_PROBE` build — see above.)

## Display (stock Prusa LCD + dial) — wired, not yet verified
- LCD + beeper on EXP1 (RS re-routed off the RST pin to EXP1 pin2/PA15); dial on spare pins PA1/PC12/PC2.
  Marlin can't easily drive this (needs board-file hacking); it's a clean `[display] hd44780` in Klipper
  (`display.cfg`) — verify there. See display.cfg for the full pin map.

## Note
The temporary Marlin is **throwaway** — flash Klipper (SD-card `firmware.bin`) for the real setup. Tuned
values from Marlin (sensorless SGTHRS, PID, e-steps) do NOT transfer to Klipper; re-tune there.
