# Bench-test results — connector/wiring validation (2026-06-28)

> ## ⚠️ USB "Lost communication" dropouts under load — DIAGNOSED & FIXED (2026-07-03/04)
> First real prints died with `Transition to shutdown: Lost communication with MCU 'mcu'`. Link was clean
> at idle but dropped under load. Isolation testing (X-only load PASSED clean; every failure involved Y)
> traced it to the **Y-axis mechanical drag**: the straining/near-stalling Y motor spiked current and
> **browned out the MCU**. Cured by the **Y bearing regrease + partial swap + belt tension** work — then a
> stress test (18 diagonal X+Y sweeps @100mm/s under full heat) passed with **zero retransmit growth**.
> Lessons: (1) "fine at idle, drops under load" = electrical/mechanical, not slicer/config; (2) a draggy
> axis can brown out the board — mechanical health matters electrically; (3) don't crash-and-restart the
> MCU repeatedly — it wedges the USB stack and needs a full power-cycle. Optional further insurance: a
> Pi↔SKR common ground wire + tight power terminals (wasn't needed to pass, but good practice).

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

## Display (stock Prusa 2004A HD44780 + dial) — ✅ WORKING (verified 2026-06-29 after clean-pin rewire; dial navigates menus. Beeper on PC12 not yet exercised — try M300 on the Pi.)
Long debug (2026-06-29). Symptom: garbled characters then blank, repeatable; only the upper data bits
wrong. RULED OUT (verified): wiring/continuity, firmware pin map, RS/EN swap, double-driving, shorts,
and (despite a tempting datasheet case) the 3.3V-vs-5V logic level. **Actual root cause = PIN CHOICE:**
D6/D7 had been placed on **PC12 (PWR-DET)** and **PC2 (Z-STOP)** — endstop inputs that carry an onboard
~100nF debounce cap (1K + 100nF + 10K). The cap smears the fast LCD data edge so D6/D7 can't settle
before the Enable strobe → garbage. D4(PB9)/D5(PA1) were on clean pins, so only the top two bits broke.
(Graphic 12864s avoid this — 3 SPI lines fit entirely on EXP1's 7 clean GPIOs; a 6-line parallel HD44780
must use spare pins, so put the SLOW signals there, never the data lines.)
**FIX (in display.cfg + firmware-DISPLAY-CLEAN.bin): all 6 data lines on CLEAN pins —**
  RS=PB8, EN=PD6, D4=PB9, D5=PA1, **D6=PB5 (was PC12)**, **D7=PA15 (was PC2)**; rotate EN1=PA9/EN2=PA10;
  **click=PC2, beeper=PC12** (the slow signals take the filtered pins). No diode/level shifter needed.

## Note
The temporary Marlin is **throwaway** — flash Klipper (SD-card `firmware.bin`) for the real setup. Tuned
values from Marlin (sensorless SGTHRS, PID, e-steps) do NOT transfer to Klipper; re-tune there.
