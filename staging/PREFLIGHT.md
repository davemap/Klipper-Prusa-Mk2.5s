# PREFLIGHT — physical checklist (do BEFORE the Pi session)

The non-software things that stall the conversion if missing or wrong. This build ALSO swaps the
mainboard (miniRambo → SKR Mini E3 V3), so there's extra hardware work vs the MK3S+ build.

## Irreversible / must-do-FIRST (while the OLD board + stock firmware are still installed)
- [ ] **Record the Z-offset NOW.** Stock firmware → *Menu → Calibration → Z-offset*. Write it down and
      make it absolute (drop the minus). On the MK2.5S this lives on the **old miniRambo** — once you
      pull that board it's gone. → goes in `config/printer.cfg [probe] z_offset` and `VALUES.md`.
- [ ] **Confirm XYZ calibration / frame is square** on stock firmware. A skewed frame is a physical fix
      first — Klipper can't paper over it.
- [ ] **Print the accelerometer mounts** (BTT ADXL345 toolhead + bed mount) while the printer still
      prints on stock firmware. Same for any HyperPixel/Pi bracket.

## Mainboard swap (miniRambo → SKR Mini E3 V3.0)
> Full pin-by-pin mapping: `scripts/wiring-map.md`. The two non-obvious items are called out below.
- [ ] **Confirm the board is a V3.0** (this config uses the V3.0 pinout).
- [ ] **Power: 12V.** The MK2.5S PSU is 12V → wire it to the SKR VIN. The board's fan + heater outputs
      switch VIN, so fans/heaters see 12V (correct for this hardware). **Do NOT feed 24V.**
- [ ] **EXTERNAL BED MOSFET (buy one).** The 12V MK42 bed draws ~10–11 A — above what the SKR's onboard
      bed terminal/FET should carry continuously (it's sized for 24V/~5A beds). Drive the bed through an
      external 12V MOSFET module (or SSR) triggered by the board's HB output. The hotend (Revo ~3.3 A) is
      fine on-board. → `scripts/wiring-map.md`.
- [ ] **Dual Z motors.** The MK2.5S has Z-left + Z-right; the SKR has one Z port. Wire both to Z-MOT in
      series and confirm both screws turn the same direction. → `scripts/wiring-map.md`.
- [ ] **Label every Prusa cable before unplugging** from the miniRambo: X/Y/**both Z**/E motors, hotend
      heater, hotend thermistor, bed heater, bed thermistor, part fan, hotend fan, PINDA, IR filament sensor.
- [ ] **Motors:** Prusa motor connectors may not match SKR polarity. Direction WILL be verified in
      software (runbook step 7) — expect to flip some `!` on dir_pin. Don't assume.
- [ ] **PINDA (Z probe):** signal → board **PROBE** port (PC14); power PINDA from 5V+GND. It's NPN
      open-collector (safe with Klipper pull-up). Polarity verified on-device (`QUERY_PROBE`).
- [ ] **IR filament sensor:** signal → **E0-STOP** (PC15); 5V+GND from a 5V pin. Polarity verified
      on-device (`QUERY_FILAMENT_SENSOR`).
- [ ] **Sensorless homing:** install the **DIAG jumpers** for X and Y on the SKR so StallGuard reaches
      X-STOP/Y-STOP (see tmc2209.cfg). Without them, homing drives into the end of travel.
- [ ] **Display = touchscreen-only** (HyperPixel + KlipperScreen). No board LCD/knob to wire. Optionally
      run a piezo to **EXP1_1 (PB5)** for M300 beeps. (Stock Prusa LCD/knob can't fit the SKR's single
      EXP1 header; a BTT mini12864 is the drop-in later if you want a physical knob — see config/display.cfg.)

## SD cards (TWO different cards)
- [ ] **microSD for the SKR board** — small, **FAT32**. Klipper firmware is flashed by copying
      `firmware.bin` to it (scripts/firmware-flash-cheatsheet.md).
- [ ] **microSD for the Pi** — MainsailOS. Use a fresh card; this is a brand-new dedicated Pi.

## Have on hand
- [ ] **USB-A↔USB-C (or micro-USB)** cable for the SKR↔Pi (check which USB port your V3.0 has).
- [ ] Pi power supply that holds 5V under load (two webcams + HyperPixel draw a lot).
- [ ] BTT ADXL345 board + USB cable (USB, not GPIO). Optionally pre-flash its rp2040 firmware.

## Mechanical sanity (input shaping will expose these)
- [ ] **Belt tension** (X and Y). Loose belts ghost and ruin shaper results — and hurt sensorless homing.
- [ ] Smooth rods / bearings clean; no binding.
- [ ] Idler screw tension correct before extruder calibration:
      https://help.prusa3d.com/article/idler-screw-tension_177367

## Know your rollback
- [ ] **Keep the old miniRambo board + its SD card.** Reinstalling it + reflashing stock Prusa firmware
      (PrusaSlicer → Configuration → Flash Firmware) returns the printer to stock (~30-60 min incl.
      rewiring). That's your full rollback for this build.
