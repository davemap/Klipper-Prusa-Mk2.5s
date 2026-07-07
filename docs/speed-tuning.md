# Speed tuning (Klipper MK2.5S) — one variable at a time

**Goal:** unlock print speed on the bed-slinger *without* (a) losing Y steps or (b) making the
intermittent electrical-noise host crash worse (see `README.md` §9). **Method:** change **one**
limit per print, run the *same* Benchy, keep the last known-good, revert on failure.

## What controls what (config vs slicer)

- **`max_velocity`, `square_corner_velocity` (SCV)** — hard caps in `printer.cfg`. This firmware
  build emits no `M203`/`M205`, so the config *is* the ceiling.
- **`max_accel`** — only a *default* in config; the slicer's `M204` overrides it per-move up to the
  machine limit. So the Benchy's real acceleration = what PrusaSlicer emits (the 41 m profile peaks
  at `M204 S4000`), **not** the `max_accel: 1000` line in the config.
- **Klipper has no per-axis acceleration** — one accel/SCV for all axes, so the weakest axis (Y, the
  moving bed) sets the limit for the whole machine.
- On a curvy model like a Benchy, wall-clock is bounded by **flow** (slicer `max_volumetric_speed`) +
  **SCV** (cornering) + **accel** — *not* top velocity. `max_velocity` mostly affects travel moves.

## Method (the discipline)

1. Establish a known-good config; back it up (`printer.cfg.bak-*` on the Pi).
2. Change **one** limit. `FIRMWARE_RESTART`. Run the **same** Benchy.
3. Watch two failure modes: **(a) freeze/reboot** (the crash — a monitor catches it) and **(b) Y
   layer shift / skip** (needs *your eyes* on the model — Klipper keeps printing through a skip).
4. Clean → this becomes the new known-good, advance one more step. Skip/freeze → revert to the last
   known-good `.bak`.

> ⚠ **Never change two variables at once.** We learned this the hard way: an SCV 5→8 **and**
> velocity 200→250 bump (plus a re-slice to higher accel) skipped Y, and we couldn't tell which
> change caused it. Isolating them afterwards is what produced the results below.

## Results (this machine — PLA Benchy, 32-bit Pi)

| # | Variable under test | Held constant | Result | Conclusion |
|---|---|---|---|---|
| 0 | baseline | accel ≤3000, vel 200, SCV 5, Y 0.55 A | clean | known-good |
| 1 | **accel 4000** (slicer M204) | vel 200, SCV 5, Y 0.55 A | **clean** — 45.4 min, MCU 9 retransmits, no shift | **accel 4000 is safe on Y**; slicer ceiling reached |
| 2 | **max_velocity 250** | SCV 5, accel 4000, Y 0.55 A | **Y skip** | velocity ceiling is **< 250** at stock current |
| 3 | **Y run_current 0.55 → 0.70 A** | vel 250, SCV 5, accel 4000 | *pending* | testing whether more Y torque clears 250 mm/s |
| — | SCV 5 → ? | vel 200 | *not yet run* | still unknown whether SCV 8 alone is OK |

**Bisection payoff:** the original three-variable skip is now explained — accel 4000 is fine and
velocity 250 skips, so **velocity was (at least) a culprit**. Whether SCV 8 alone (at vel 200) is
acceptable remains the informative next single-variable test.

## Why Y is the limit (bed-slinger torque-at-speed)

Y drags the entire heated bed. Stepper torque falls off as RPM rises (back-EMF), so high
velocity / accel / SCV on **Y** is where steps get lost first. This machine's Y:
`run_current 0.550 A` (conservative), `microsteps 16`, `rotation_distance 32`, and
`stealthchop_threshold: 80` — meaning it is **already on spreadCycle** (the higher-torque driver
mode) above 80 mm/s. So the 250 mm/s skip is **raw torque**, not a driver-mode problem to toggle.

## Mitigation levers (ranked by cost/benefit — *noise matters here*)

This printer has an intermittent **electrical-noise host crash**, and motor current is a noise
source, so these levers are **not** free:

1. **Mechanical — zero noise cost, do first.** Y belt tension (firm, low "twang", not floppy);
   smooth rods clean + lightly oiled; bed glides freely by hand with power off. A loose belt or dry
   bearing is the **#1 cause of high-speed Y skips** and costs nothing electrically.
2. **Y `run_current` bump** (tried: 0.55 → 0.70 A, +27 %). Direct torque, **but adds electrical
   noise + heat**. The Prusa Y motor is rated well above this; keep RMS ≲ 0.8 A on the SKR's
   un-fanned TMC2209. ⚠ **Side effect — sensorless homing:** StallGuard's stall signature depends on
   current, so after a current change **watch the first Y home** — if Y rams the frame
   (under-trigger) or stops short (over-trigger), re-tune `driver_SGTHRS` (this build already raised
   it 80 → 110 once when the motors ran warm).
3. **Accept the axis ceiling / reframe.** On a Benchy, top velocity only speeds *travels* (print
   moves are flow/accel-bound), so 200 → 250 saves ≈ 1 min on a 45-min print. The bigger, Y-safe
   time levers are **accel** (already at 4000) and **SCV**. Given the noise trade-off, banking
   vel 200 and chasing accel/SCV is often the better call.

## Revert

Every change leaves a timestamped backup in `~/printer_data/config/` on the Pi:
`printer.cfg.bak-prespeedbump`, `printer.cfg.bak-velskip-*`, `printer.cfg.bak-precurrent-*`,
`tmc2209.cfg.bak-precurrent-*`. Restore the relevant `.bak`, then `FIRMWARE_RESTART`.

The repo's `pi-live-backup/` tracks the last **confirmed-good** config (currently vel 200 / SCV 5 /
Y 0.55 A) — it is intentionally **not** advanced to an under-test value, so "restore from repo"
always lands on a proven config.

## See also

- Crash / electrical-noise diagnosis: `README.md` §9, `staging/pi-crash-usb-emi-fix.md`
- 32-bit OS migration (host resilience): `docs/32bit-os-migration.md`
