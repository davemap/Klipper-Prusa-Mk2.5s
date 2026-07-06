# Prusa MK2.5S → Klipper conversion (BTT SKR Mini E3 V3.0)

A full conversion of a **Prusa i3 MK2.5S** to **Klipper**, running on a **BTT SKR Mini E3 V3.0**
mainboard with a **Raspberry Pi 3B+** host. Keeps the stock Prusa 20×4 LCD *and* adds a HyperPixel
touchscreen, a webcam, and an E3D Revo hotend.

This repo is both the working config set **and an honest build log** — including every problem we hit
and how it was diagnosed — so the machine is reproducible and the debugging is useful to others doing
the same conversion.

> ⚠️ **Open issue (2026-07-05):** the Pi *host* intermittently hard-reboots mid-print. Diagnosed as
> electrical noise coupling into the SKR's un-filtered USB (the MK2.5S's board has no USB common-mode
> choke; an identical-software MK3S with a filtered Einsy board is rock-stable). Mitigation in progress —
> see **[The debugging journey → #9](#9-the-recurring-pi-host-reboot-open)**.

---

## Status

| Subsystem | State |
|---|---|
| Motion, homing (sensorless X/Y StallGuard), dual-Z | ✅ working + tuned |
| Heaters — hotend + bed (via external MOSFET) + PID | ✅ tuned on-device |
| PINDA2 probe + Z-offset (paper test) | ✅ `z_offset = -0.211` |
| Input shaping (ADXL345) | ✅ X `ei`@48.2 Hz, Y `mzv`@44.8 Hz |
| Pressure advance | ✅ `0.045` (per-filament) |
| Stock 20×4 HD44780 LCD + rotary + beeper | ✅ on the SKR |
| HyperPixel 4.0 + KlipperScreen | ✅ (+ DPMS backlight blanking) |
| Webcam (Mainsail) | ✅ |
| PrusaSlicer physical-printer (Moonraker) | ✅ slice → send → print |
| **Host stability under print load** | ⚠️ intermittent hard-reboot — see #9 |

---

## Hardware (bill of materials)

| Item | Part | Notes |
|---|---|---|
| Printer | Prusa i3 **MK2.5S** | 250 × 210 × 210, bed-slinger, direct-drive extruder |
| Mainboard | **BTT SKR Mini E3 V3.0** | STM32G0B1, 4× onboard TMC2209 (UART), Micro-USB. *No USB common-mode choke.* |
| Host | **Raspberry Pi 3B+** (1 GB) | MainsailOS (Debian 13 / kernel 6.18.34, 64-bit), Wi-Fi |
| Hotend | **E3D Revo**, 40 W, **12 V**, 0.4 mm | whole machine is 12 V — never feed 24 V |
| Z probe | **PINDA2** (inductive) | no temp-comp table → heat-soaked in `PRINT_START` |
| Display 1 | stock Prusa **20×4 HD44780** + rotary + beeper | wired to EXP1 on the SKR |
| Display 2 | **HyperPixel 4.0** (800×480 DPI) | KlipperScreen, rotated 270° |
| Accelerometer | **BTT ADXL345** (USB, rp2040) | input shaping only; config normally left `#include`d-out |
| Fans | 2× **12 V Noctua** — bed-MOSFET (FAN2, auto-on with bed heat) + hotend | quiet upgrade |
| External bed MOSFET | 12 V module ([B07DJYW5VD](https://www.amazon.co.uk/dp/B07DJYW5VD)) | offloads the bed heater; sits in a printed enclosure |
| USB cable (host↔SKR) | *2 m no-ferrite (shorter shielded + ferrite pending — see #3/#9)* | the crash-relevant one |
| Power | Pi on a **separate 5.1 V/2.5 A** supply | do NOT back-feed the SKR logic rail |

**Printed parts, mods & the full added-hardware list** (linear-rail X-axis upgrade, Y-belt tensioner,
hybrid fan shroud, vibration-damper feet, HyperPixel cover, MOSFET box + the cut/edit made to each):
see **[`hardware/printed-parts-and-mods.md`](hardware/printed-parts-and-mods.md)**.

Reference machine: an **MK3S (Einsy Rambo, TMC2130)** also running Klipper — used throughout as an
"identical-twin" A/B control to separate software faults from board/hardware ones. Invaluable.

---

## Repository layout

```
staging/config/        the Klipper .cfg files (source of truth = the live Pi, see below)
staging/prusaslicer/   PrusaSlicer profiles (printer / filament / print / physical_printer)
staging/firmware/      version-matched SKR firmware .bin + build notes
staging/scripts/       deploy / patch / recovery helpers
staging/*.md           runbooks (PREFLIGHT, ON-PI-RUNBOOK, VALUES, BENCH-TEST-RESULTS)
staging/pi-crash-usb-emi-fix.md         USB-noise diagnosis + ranked fixes
staging/hyperpixel-power-reduction.md   HyperPixel current/heat reduction research
reference/             Prusa firmware header, stock SKR sample cfg, sample LCD cfg
```

**Source of truth = the live Pi.** The authoritative configs are on the Pi at
`~/printer_data/config/` (they hold the SAVE_CONFIG autosave block: PID, z-offset, input shaper).
Pull them with `scripts/pull-configs.sh` (see Reproduce) before committing.

Key config files: `printer.cfg`, `steppers.cfg`, `tmc2209.cfg`, `skr-mini-e3-v3.cfg`,
`display.cfg`, `macros.cfg`, `adxlmcu-BTT.cfg`, `moonraker.conf`, `crowsnest.conf`.

---

## Reproduce (high level)

1. **Flash Klipper to the SKR Mini E3 V3.0** — build for STM32G0B1, 8 KiB bootloader, USB (PA11/PA12),
   `make menuconfig` → copy `klipper.bin` to the SD card as `firmware.bin`, power-cycle. **Match the
   firmware version to the host's Klipper version.**
2. **Flash MainsailOS** to the Pi SD, boot, get on the network. (See the host-power warnings below.)
3. **Deploy the configs** from `staging/config/` to `~/printer_data/config/`, edit the `[mcu] serial`
   to your board's `/dev/serial/by-id/…`.
4. **Bring-up in order** (do NOT skip verification — motor directions, probe polarity, and sensorless
   thresholds must be confirmed on *your* hardware, not assumed): motor directions → sensorless homing
   thresholds (`driver_SGTHRS`) → probe polarity → PID both heaters → Z-offset → input shaping →
   pressure advance. See `staging/PREFLIGHT.md` and `staging/ON-PI-RUNBOOK.md`.
5. **Wiring** is in `staging/config/*` headers and `reference/`. Critical lesson: **don't put fast LCD
   data lines on filtered endstop pins** (see #1).
6. **HyperPixel + webcam** are optional second UIs; the Pi's 5 V rail is marginal with all of it — see #4.

---

## The debugging journey

Every one of these cost real time; documenting so you don't repeat them.

### 1. Stock Prusa LCD garbled on the SKR
**Symptom:** 20×4 HD44780 showed garbage then blanked — only the upper data bits wrong.
**Root cause:** D6/D7 had been placed on **PC12 (PWR-DET)** and **PC2 (Z-STOP)** — endstop inputs with an
onboard ~100 nF debounce cap that smears the fast LCD data edge so the bits can't settle before the
Enable strobe.
**Fix:** put **all 6 data lines on clean GPIOs**, spill the *slow* signals (click, beeper) onto the
filtered pins instead. Plus two Klipper `hd44780.py` timing patches for this 2004A clone. (`display.cfg`.)

### 2. USB "Lost communication" dropouts under load (SKR side)
**Symptom:** first prints died with `Lost communication with MCU` — fine at idle, dropped under load.
**Root cause:** a mechanically **draggy Y axis** near-stalled the Y motor → current spike → **MCU
brownout**. Isolation testing: X-only load passed clean; every failure involved Y.
**Fix:** Y bearing regrease/partial swap + belt tension. Then an 18-sweep stress test held with zero
retransmit growth. Lesson: "fine at idle, drops under load" = electrical/mechanical, not slicer/config.

### 3. Pi *host* crashes during print — the big one
**Symptom:** the whole Pi drops off the network mid-print (not an MCU shutdown — the *host* dies).
**Diagnostic that cracked it:** the **identical-twin MK3S** (same Pi 3B+, kernel, OS, Klipper commit)
is rock-stable → **not software**. The only difference is the board — and the **SKR Mini E3 V3 has no
common-mode choke on USB** (schematic-confirmed), while the Einsy does. So printer switching noise
couples straight into the Pi.
**Fix (partial):** a bad/charge-only USB cable was swapped for a proper shielded data cable → the first
full Benchy printed clean (76 min). See #9 — this is **not fully closed**; spreadCycle re-opened it.

### 4. Pi undervoltage / brownout
**Symptom:** kernel logged `Undervoltage detected!`; Pi reset under load.
**Fix:** dedicated **5.1 V/2.5 A** supply with a good short cable (voltage sag on a thin cable is a top
cause). Still **marginal** running Pi + HyperPixel + webcam together — recurring recoverable UV dips.
Longer-term: beefier 5 V supply and/or a powered USB hub for the webcam. **DPMS backlight blanking** was
added to cut ~110 mA when the screen is idle.

### 5. "Boot loop" after a software update (misdiagnosis worth recording)
**Symptom:** after an `apt` update bumped the kernel to 6.18.34, the Pi appeared to boot-loop with the
HyperPixel re-enabled.
**What it actually was:** a **slow boot** (fsck after unclean shutdowns) that our aggressive 4-second
SSH-timeout watchers couldn't connect to — so they wrongly reported "never came back." The HyperPixel
overlay is **fine** on this kernel (both Pis run it). Lesson: don't let a monitoring artifact become a
diagnosis. Recovery-by-SD-card-edit (comment the overlay in `config.txt`) is the reliable break-glass.

### 6. HyperPixel restore + power tuning
Re-enabled the DPI overlay; added **DPMS backlight blanking** (X11 `xset dpms force off` physically cuts
the ~110 mA backlight on a Pi 3B+). Research on further current/heat reduction:
`staging/hyperpixel-power-reduction.md`.

### 7. Input shaping — trust, but verify
Ran `SHAPER_CALIBRATE` per axis (ADXL345 on toolhead for X, moved to bed for Y).
**Gotcha:** both axes auto-picked complex `3hump_ei`/`2hump_ei` shapers at suspiciously high/scattered
frequencies — the classic sign of a **non-rigid accelerometer mount**. We locked in the safe,
physically-plausible simpler shapers instead (**X `ei`@48.2**, **Y `mzv`@44.8**). Re-run with a rigid
mount for optimal.

### 8. Y-axis slippage at MK3 speeds — stealthChop vs spreadCycle
**Symptom:** at MK3-level acceleration, the print crept steadily toward the front of the bed = **Y
step-loss** (directional, cumulative).
**Root cause (counterintuitive):** *not* current — the MK2.5S runs Y at **0.55 A**, *more* than the
MK3's 0.37 A. The difference is **driver mode**: MK2.5S Y was **stealthChop** (`stealthchop_threshold:
999999`), whose torque **collapses at high speed/accel**; the MK3 runs **spreadCycle**. A ramp test
confirmed spreadCycle Y slings clean to 3000 mm/s² where stealthChop crept at 2000.
**Fix:** **hybrid `stealthchop_threshold: 80`** on X and Y — stealthChop below 80 mm/s (so **sensorless
homing still works as tuned**, homing speed is 40) and spreadCycle above 80 for torque.
**Klipper gotchas learned:** (a) `stealthchop_threshold: 0` does **not** give spreadCycle — you must
*omit* the line, or use a hybrid value; (b) Klipper has **no per-axis acceleration** (`max_accel` is a
single global scalar; the slicer's per-axis `M201` is ignored) — so you fix the weak axis's *torque*
rather than throttling the strong one.

### 9. The recurring Pi host freeze/reboot (OPEN — intermittent; prime suspect: motor crimps)
**Symptom:** Pi hard-**freezes** mid-print, then the watchdog reboots it ~60 s later — chronic
(Moonraker counted 14+ unclean host deaths). Klipper never shuts down (no MCU fault); the USB data link
is *pristine* at the instant of death.
**Why we kept losing the logs:** a stock RPi-OS drop-in
(`/usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf`) forced `Storage=volatile` — the
journal lived in RAM and was wiped every boot, silently overriding our `persistent` setting. **Fixed**
with a `99-` drop-in; `dtoverlay=ramoops` + `kernel.panic_on_rcu_stall` armed; an on-Pi 2 s disk logger
(`crashmon`) captures the trajectory across the reboot.

**What the captured freezes show (2 caught):** a **silent, total hard-hang**. pstore stays **empty even
with ramoops registered** → no panic, no oops, no RCU-stall → the CPU stops *instantly*. The kernel log
ends mid-stride on a benign line at ~2845 s uptime with **zero** warning; every `dwc_otg`/undervoltage/
USB error is **boot-only** (first ~400 s), then ~40 min of *silent* printing, then death. RAM/load/temp
are **healthy** throughout. That fingerprint = an **instantaneous electrical transient** hard-locking
the SoC — not software, not resources, not a slow brownout.

**It's INTERMITTENT, not deterministic.** Three runs on identical hardware (webcam off, short+ferrite
cable): froze at **82%**, then **74%**, then **completed a full Benchy**. So the "same gcode position"
was coincidence — a random noise event that only *sometimes* couples badly enough to lock the CPU. This
rules out a fixed gcode trigger and makes single-run A/B tests unreliable (a "pass" can be luck).

**Diagnosis:** software is **ruled out** — the identical-software MK3S (same kernel/OS/HyperPixel/
watchdog, spreadCycle Y) is stable for hours. It's an **electrical noise transient** coupling into the
Pi over the **SKR's un-choked USB** (the Einsy/MK3S has a USB common-mode choke; the SKR does not).
Refuted along the way: RAM/OOM (healthy), webcam load (removed, still froze), cable length + ferrites
(still froze), a deterministic gcode/accel trigger (the completed run).

**Prime suspect (surfaced late): poorly-crimped motor connectors.** An intermittent/high-resistance
crimp on an *energized* stepper coil produces inductive flyback (`V = −L·di/dt`) and **arcing** — the
sharpest, highest-energy EMI source on the machine, and intermittent by nature (make/break under
vibration). Fits *better* than steady spreadCycle noise: it explains the intermittency, the instant
silent lock, and the clustering in fast/high-accel upper layers. ⚠️ It also risks **killing the TMC2209
drivers** (open-circuiting an energized coil), and likely contributed to the earlier Y skipping (#8).

**Fixes, in order (source before path):**
1. **Re-terminate every motor connector**, both ends — proper JST-XH crimp or solder+heatshrink.
   Removes the noise *source* and the driver-damage risk. Check first: tug-test each pin; compare the
   two coil resistances per motor (~1–4 Ω, should match).
2. **USB isolator** (ADuM3160/4160, full-speed 12 Mbps — matches the SKR's USB) — galvanic break of the
   conducted noise/ground path. Belt-and-suspenders with the re-crimp.
3. Clip-on ferrites on motor + USB leads; **32-bit Pi OS** on a spare SD (documented exact-symptom fix
   on the Pi 3B+ — see `docs/32bit-os-migration.md`) as a host-resilience A/B.

Validate by **crash-free reliability over several prints**, not one Benchy (it's intermittent).
Full analysis: `staging/pi-crash-usb-emi-fix.md`.

**Update — 32-bit A/B (promising, not conclusive).** Built a 32-bit (armhf Trixie) card as a
host-resilience test (`docs/32bit-os-migration.md`). Same Benchy that froze the 64-bit card **3 of 4**
times **completed cleanly ×2** on 32-bit, incl. **4 h 16 m** crash-free uptime. Encouraging, but the
freeze is intermittent — the deciding test is an **acceleration-stress run** (raise accel → raise
noise → can we still force a freeze?). Trade-off surfaced: 32-bit fixes the freeze but the HyperPixel
touchscreen goes black under any compositor (a real 32-bit `vc4`-KMS-atomic bug — fixable via
Wayland/cage + `WLR_DRM_NO_ATOMIC=1`, see `docs/hyperpixel-klipperscreen-32bit-fix.md`). The
**USB isolator on 64-bit** remains the endgame that gives *both* stability and the touchscreen.

---

## Key lessons (the transferable bits)

- **Keep an identical-twin control if you can.** A second Klipper Pi on known-good hardware, running the
  same OS/kernel, is the fastest way to split "software bug" from "this machine's hardware."
- **The SKR Mini E3 V3 has no USB common-mode choke.** On a noisy printer it's genuinely reboot-prone;
  budget for a shielded/short cable, ferrites, or a USB isolator from the start.
- **"Host dies" ≠ "MCU shutdown."** A Klipper MCU shutdown is graceful (heaters off, logged, host alive).
  A host reboot/freeze is hardware/power/kernel — Klipper just vanishes with it.
- **stealthChop is quiet but weak at speed; spreadCycle is strong but noisy.** On a bed-slinger with
  *sensorless homing*, the answer is a hybrid `stealthchop_threshold` (stealthChop for the slow home,
  spreadCycle for fast moves) — not one or the other.
- **Persistent journald can be silently overridden** by a `40-rpi-volatile-storage.conf` drop-in. If you
  can't capture a crash, check `journalctl --list-boots` and the drop-in dir before anything else.
- **The Pi 3B+ 5 V rail is marginal** with a display + webcam; treat power as a first-class constraint.
- **An intermittent fault masquerades as a deterministic one.** Two freezes landed in the upper layers
  and looked like a fixed "gcode position"; a third run completed and proved it *random*. Don't over-fit
  two data points — with intermittent failures, a single clean run is not a fix, and a single crash is
  not a repro. Prove reliability (or breakage) across *several* runs.
- **A bad crimp is an EMI source, not just a mechanical fault.** An intermittent connection on an
  energized stepper coil arcs and flings inductive-flyback spikes — enough to hard-lock nearby
  electronics *and* kill the stepper driver. On unexplained electrical weirdness, re-terminate the
  motor leads before chasing exotic causes.

---

## Credits / method

Built and debugged interactively. The most valuable technique throughout was **change one variable,
verify on-device, and A/B against the identical-twin MK3S** — assumptions about motor directions, probe
polarity, driver modes, and crash causes were repeatedly wrong until measured.
</content>
</invoke>
