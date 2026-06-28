# Marlin bench test — drive the SKR from the Mac (no Pi)

Quick standalone test: flash Marlin to the SKR, send G-code from the Mac over USB. Good for confirming
**motors move, coil pairing, directions, and MECHANICAL endstops** without a Klipper host.

## What this does / does NOT tell you
- ✅ Motors spin, correct coil pairing, **directions**, mechanical endstops trigger (`M119`).
- ❌ Does **NOT** validate Klipper **sensorless** homing (stock Marlin = mechanical endstops; enabling
  sensorless needs a custom Marlin build and the tuning doesn't transfer to Klipper).
- ⚠️ The pre-built firmware is the **Ender-3** config: steps/mm + bed size + directions are Ender-3
  defaults, NOT MK2.5S. Commanded mm will be wrong and an axis may jog backwards — it's a sanity test,
  not a calibrated one. Keep a hand on the power during `G28`.

## Prereqs (note: different from the Klipper sensorless test)
- [ ] X/Y/Z motors installed and moving freely.
- [ ] **Mechanical X/Y endstop switches wired** to X-STOP / Y-STOP, and **DIAG jumpers OUT** (Marlin homes
      off the switches, not StallGuard).
- [ ] **Hotend + bed thermistors connected** (TH0, TB) so they read room temp — otherwise Marlin's thermal
      protection sees a "disconnected sensor" and **halts**, and you can't jog. (Heaters can stay unwired.)
- [ ] USB cable from the SKR to the Mac.

## 1. Flash Marlin (same SD-card method as Klipper)
- Download `firmware-ender3.bin` (no BLTouch) from BTT:
  https://github.com/bigtreetech/BIGTREETECH-SKR-mini-E3/tree/master/firmware/V3.0/Marlin
- Rename to **`firmware.bin`**, copy to a FAT32 SD, put it in the SKR, power-cycle (becomes `FIRMWARE.CUR`).

## 2. G-code sender on the Mac — Pronterface (Printrun)
- Install: download from https://github.com/kliment/Printrun/releases  (or `pip3 install printrun` then run `pronterface`).
- Plug in USB. Find the port:
  ```bash
  ls /dev/cu.usbmodem*        # the SKR's native USB CDC
  ```
- In Pronterface: select that port, **baud 115200** (try 250000 if it won't connect), click **Connect**.
  You should see Marlin's startup banner in the log.

## 3. Test
```
M119                 ; report endstop states. Trigger each switch by hand and re-run M119 — it should flip.
; Jog carefully (Ender-3 directions may be inverted vs your printer — hand on the power switch):
G91
G1 X10 F1000         ; does X move? which way? (coil pairing wrong = grind/buzz/no move -> regroup coil wires)
G1 Y10 F1000
G1 Z2 F300
G90
G28 X                ; homes X to the mechanical switch. Be ready to cut power if it drives the wrong way.
G28 Y
```
- Motors don't move / buzz / vibrate in place → a motor connector coil pair is mis-grouped: swap the two
  wires of one coil on that connector.
- Wrong direction → expected (Ender-3 config). You're only confirming the motor *responds* and the switch works.

## 4. Revert to Klipper when done
- Reflash the Klipper firmware: rebuild if needed (`firmware-flash-cheatsheet.md`), copy `out/klipper.bin`
  to the SD as `firmware.bin`, power-cycle. Back to the normal bring-up.

## If you actually want the sensorless decision
Use the Klipper path instead — `sensorless-endstop-test.md` + `homing-test.cfg` on any Klipper host
(the new Pi's MainsailOS card is ~15 min to flash). Marlin can't answer that one cleanly.
