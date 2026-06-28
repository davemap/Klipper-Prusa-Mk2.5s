# Sensorless homing test — decide: keep the endstops, or remove them?

Goal: prove whether TMC2209 StallGuard sensorless homing on X and Y is reliable enough on YOUR machine,
so you can decide before final assembly. (Z always homes off the PINDA — this is only about X/Y.)

> Reassurance: the MK3S uses sensorless X/Y homing **stock**, so this class of printer is proven to work
> sensorless. The MK2.5S ships with mechanical switches, but sensorless is very achievable — we're just
> confirming it on your hardware before you commit.

## The decision is genuinely either/or (same pin)
On the SKR, the **X-STOP/Y-STOP pin (PC0/PC1)** carries EITHER the TMC **DIAG** (sensorless, via the board
jumper) OR a **mechanical switch** — not both at once. So:
- **Sensorless** = DIAG jumper IN, no switch wired.
- **Mechanical** = DIAG jumper OUT, switch wired to X-STOP/Y-STOP.
Test sensorless first; only wire the switches if it fails.

## Prerequisites
- [ ] X/Y/Z motors **installed and driving the real axes**, belts on and **tensioned** (loose belts are the
      #1 cause of flaky sensorless — ideally fit the belt tensioners first).
- [ ] **X and Y DIAG jumpers** fitted on the board.
- [ ] SKR flashed with Klipper + connected to the Pi. No heaters/probe needed.
- [ ] Deploy the configs, then load the test config:
      ```bash
      cd ~/printer_data/config
      cp printer.cfg printer.cfg.real
      cp homing-test.cfg printer.cfg          # fill [mcu] serial to match
      ```
      Mainsail → FIRMWARE_RESTART.

## Step 1 — directions first (so homing goes toward the end, not away)
In the console, jog gently and watch:
```
G91
G0 X-10 F1000     ; should move the carriage TOWARD the X home end (left). If it goes away, flip dir_pin ! on stepper_x.
G0 Y-10 F1000     ; should move the bed TOWARD the Y home end. If not, flip dir_pin ! on stepper_y.
G90
```
Fix any reversed axis in homing-test.cfg, FIRMWARE_RESTART, re-check.

## Step 2 — first homing + SGTHRS tuning (one axis at a time, hand near power)
```
G28 X
```
Watch the carriage:
- **Triggers before it reaches the end / stops in mid-travel** → too sensitive → **LOWER** `driver_SGTHRS` (e.g. 80→65).
- **Rams the end and grinds without stopping** → not sensitive enough → **RAISE** `driver_SGTHRS` (e.g. 80→100). Hit emergency stop / cut power if it grinds.
- Edit `homing-test.cfg`, FIRMWARE_RESTART, repeat. Find the highest SGTHRS that does NOT false-trigger,
  then back off ~5–10 for margin.
Repeat the whole step for **Y** (`G28 Y`) — X and Y usually want different SGTHRS values.

Tip: tune at the **homing_speed** you'll actually use (40). StallGuard shifts with speed and with motor
temperature, so also re-check after the motors have run a few minutes (warm).

## Step 3 — the reliability test (this is the actual decision)
Klipper always reports position 0 after homing, so measure repeatability **physically**:
1. Put a mark or a dial indicator against the X carriage.
2. `G28 X` → note the physical position.
3. `G90` `G0 X125 F3000` (move to middle) → `G28 X` again → compare the physical position.
4. Repeat **15–20 times**. Then do the same for Y.

**PASS (remove the endstops, run sensorless):**
- Homes every time, never rams, never triggers early.
- Returns to within ~**0.1–0.2 mm** physically each time.
- Still passes when the motors are warm and after a couple of SGTHRS-stable runs.
- (X/Y home repeatability of a couple tenths is fine here — your first layer is set by the **PINDA + adaptive
  bed mesh**, not by where X/Y home.)

**FAIL (keep the mechanical endstops):**
- Occasionally rams or triggers early; needs SGTHRS re-tuned when warm vs cold; physical spread > ~0.3 mm.

## Step 4 — apply the decision, then restore the real config
```bash
cd ~/printer_data/config
cp printer.cfg.real printer.cfg     # back to the full config
```
- **PASS → sensorless:** copy your tuned `driver_SGTHRS` X and Y values into the real `tmc2209.cfg`
  (they're already wired for sensorless there). Leave the mechanical switches unwired. Done.
- **FAIL → mechanical:** remove the X/Y DIAG jumpers, wire the switches to X-STOP/Y-STOP, and in
  `steppers.cfg` comment out the sensorless block and **uncomment the mechanical-endstop fallback** for
  X and Y (it's already there). FIRMWARE_RESTART.

FIRMWARE_RESTART after restoring. Then continue the normal bring-up (PROBE_CALIBRATE, PID, …).
