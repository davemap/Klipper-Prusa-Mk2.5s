# Pi hard-reboots at first-layer full load — diagnosis & fix plan

Research synthesis (2026-07-04, 3 agents). Symptom: Pi HOST freezes then hard-reboots (network
down, ports closed, screen fades ~2s) the instant a print's first layer starts — hotend full PWM +
**extruder motor turning + part-cooling fan** on. Pi's own 5V rail clean (`throttled 0x0`).
An X/Y+heat-only stress test (no extruder/fan) PASSED. HyperPixel overlay disabled (display ruled out).

## Diagnosis (both electrical agents converge)
**Conducted common-mode / GROUND-transient noise riding into the Pi over the USB link — not power capacity.**
- The switching aggressors that engage at first layer (part-fan commutation, extruder stepper chopping,
  higher heater PWM) dump sharp transients onto the board's rails/ground.
- Pi and SKR share a ground reference ONLY through the thin USB ground wire. When the SKR ground bounces,
  that transient is delivered into the Pi's USB PHY → kernel dies. Fast noise, so the Pi's UV detector
  never trips (`0x0`).
- **CONFIRMED from BTT's V3.0 schematic: the SKR Mini E3 V3 has NO common-mode choke on USB** — only ESD
  varistors + 27Ω series R + a Schottky OR-diode on USB-5V. Zero on-board CM rejection. An external
  ferrite/isolator literally supplies the part BTT omitted.
- Klipper FAQ names this exactly: "high USB noise when both the printer's PSU and the host's 5V are mixed…
  may result in resets"; "don't let the USB cable go parallel to the heater power cable."

## KEY CORRECTION re: the SW_USB jumper
Removing `SW_USB` (or cutting USB +5V) breaks the **5V mixing** — correct and free — BUT agent 1 found a
CONFIRMED counter-report where a USB-5V isolator did NOT fix a hard mid-print crash, because the noise
also rides the **GROUND**, which the 5V-only fix leaves intact. So: **pull SW_USB, but don't expect it to
be sufficient alone.** The decisive fix is a full USB isolator (breaks 5V AND ground).

## PRIORITIZED PLAN (ranked for our exact signature)

### Free — do all, then test the first layer
1. **Diagnostic:** run the failing first layer with the **part-cooling fan unplugged** (cheap 2-wire fans
   are the top EMI suspect; also rules out a fan short/inrush). Note: slicers often disable the fan on
   layer 1, so the **extruder motor is the more certain layer-1 aggressor** — see #3.
2. **Reroute the USB cable** away from the fan/motor/heater/bed/PSU harness; keep it OFF the frame; cross
   power wires at 90°. Use a short, shielded USB cable.
3. **Reroute the extruder motor cable away from the board and USB.** ← one of the few CONFIRMED cures
   (a Voron builder fixed constant MCU disconnects this way *after* grounding-everything failed).
4. **Pull the `SW_USB` jumper** (next to the USB port) — single 5V source. Free adjunct. Verify: printer
   PSU off + Pi on → SKR LEDs go DARK.
5. **Re-seat/re-solder the SKR VIN power connector** while you're in there (CONFIRMED reboot-on-heat cause, BTT #598).

### Cheap (£2–10)
6. **100 nF ("104") ceramic across the part-fan terminals** at the fan + snap ferrite on its leads.
7. **Clamp-on ferrite (Mix 31) on the USB cable, both ends, 3+ turns** — supplies the missing CM choke.

### Definitive (£10–15) — the decisive fix for this signature
8. **USB isolator (ADuM3160/ADuM4160, full-speed 12 Mbps, WITH an isolated DC/DC on board).** Galvanically
   severs BOTH the 5V and GROUND loops — the only option that removes the path the noise is using, not just
   attenuates it. Duet3D officially recommends USB isolators for USB ground-loop resets. Full-speed is fine:
   the SKR is a USB-CDC serial device, Klipper has no rate floor → no bottleneck. Buy one WITH isolated
   DC/DC (device side needs its own 5V; isolator doesn't pass VBUS). Avoid the cheapest noisy-DCDC units.

### Fallbacks if still crashing
9. Star-ground bond Pi-GND↔SKR-GND↔PSU V- at ONE point + earth frame/motor casings/PSU chassis to mains PE.
   (Do star, never daisy-chain/both-ends — ground straps can help OR hurt; counter-reports exist.)
10. Twist stepper coil pairs & heater/bed +/- pairs; shield steppers (ground one end); twist/shield PINDA.
11. Nuclear: move host↔MCU off USB to **UART or CAN** (deletes the USB noise path — CONFIRMED cure).
12. Rule-out: RPi 3B+ 64-bit Pi OS has a confirmed random-freeze bug fixed by 32-bit Pi OS Lite (our
    load-locked trigger argues against software, but it's a 5-min back-pocket item). Also try `dtoverlay=dwc2`.

## Recommendation
Do the FREE stack (1–5) now and re-test. But because ground-borne faults resist partial measures, **order
the USB isolator (#8) in parallel** — it's the highest-confidence definitive cure for our clean-rail,
ground-transient signature.

---

# Software / kernel angle (agent 3) — and the definitive way to STOP GUESSING

## "Did we misconfigure something?" — authoritatively NO
A bad printer.cfg/Moonraker/OS config **cannot** panic the kernel or hard-reboot the Pi. Klippy/Moonraker
are unprivileged userspace — a config fault produces at most a graceful **"MCU shutdown"/error with the host
still alive** (SSH + web UI stay up; recovery is FIRMWARE_RESTART, not a power cycle). Klipper maintainer
Sineos: *"Except for a hardware problem with the RPi (cables, power, SD card etc.), I cannot imagine Klipper
forcing the RPi into a reboot."* A true hard reboot = hardware / power / kernel. (Only deliberate opt-ins
could reboot on purpose: a Moonraker `[power]` relay, a `machine.reboot` call, an enabled `watchdog`, or a
user `sudo reboot` macro — verify none are set.)
- **Fast test:** after a crash, look at `/tmp/klippy.log` (or ~/printer_data/logs/klippy.log). Clean "MCU
  shutdown" line at the end = software (host lived). **Truncates mid-write, no shutdown msg = host died
  underneath it = hardware/kernel** (this is our case — ports were closed).

## Second live hypothesis: the brand-new kernel 6.18.34+rpt-rpi-v8
- Real + very new: RPi OS jumped 6.12 → 6.18.34 in the 2026-06-18 apt update — days before our reboots.
  Temporal correlation is the reason to suspect it. But NO field report yet names 6.18.34/3B+ as reboot-buggy
  (too new) → UNCONFIRMED. Precedent: open bug raspberrypi/linux#6172 = `dwc_otg` USB driver freeze-under-load
  → watchdog reboot — but documented on 6.6.y / Pi 3B+4B, not 6.18/3B+. Plausible class, not a proven match.
- **Key reasoning that argues AGAINST the kernel: our passing stress test (18 diagonal sweeps @100mm/s)
  generated HEAVIER continuous USB step-traffic than a slow first layer. A USB-load kernel bug would have
  crashed the stress test too — it didn't. What's different at first layer is the fan + extruder ELECTRICAL
  loads, not USB volume.** → favors the electrical cause; kernel stays secondary.

## THE DISCRIMINATOR — capture the crash on the serial console (we have the FTDI C232HM)
The two hypotheses print DIFFERENT signatures as the Pi dies:
- **Kernel panic / oops backtrace on the console → software/kernel/driver** (supports 6.18 / dwc_otg).
- **Clean cutoff mid-line (or an "Under-voltage detected!" line) with NO panic → power/electrical** (supports fan/USB transient).

Serial console setup (do next if the jumper doesn't fully fix it):
- `/boot/firmware/config.txt`: `enable_uart=1`  (on 3B+ this pins core_freq=250 so mini-UART 115200 is stable)
- `/boot/firmware/cmdline.txt` (one line, remove `quiet`): `... console=serial0,115200 console=tty1`
- Wire C232HM (3.3V logic — safe): **Orange TXD → Pi pin 10 (RXD); Yellow RXD → Pi pin 8 (TXD); Black GND → pin 6; RED VCC → DO NOT CONNECT.** (confirm colors vs the cable's card)
- On Mac: `ls /dev/cu.usbserial-*` then `screen /dev/cu.usbserial-XXXX 115200` — reproduce a print and watch.

pstore/ramoops (post-mortem backup): `dtoverlay=ramoops` + sysctl `kernel.panic_on_oops=1`, `kernel.panic=10`;
read `/var/lib/systemd/pstore/` + `journalctl -b 0` after; test with `echo c | sudo tee /proc/sysrq-trigger`.

## Backup kernel test (if electrical fixes don't fully cure it)
- Quick: add `dtoverlay=dwc2,dr_mode=host` to config.txt (dr_mode=host MANDATORY on 3B+, else you lose all
  USB+Ethernet). Tests the dwc_otg hypothesis without a downgrade.
- Full rollback: `apt`-downgrade linux-image-rpi-v8 to a 6.12.x `+rpt-rpi-v8` from archive.raspberrypi.com,
  then `apt-mark hold linux-image-rpi-v8 linux-headers-rpi-v8 raspi-firmware`. (Never `rpi-update` — that's bleeding-edge.)

## Two cheap tests that separate electrical vs kernel fast
1. Run one first layer with the **part fan unplugged** → survives = electrical.
2. `apt-mark hold` + roll back to 6.12 (or `dtoverlay=dwc2,dr_mode=host`) → survives on old kernel = kernel.
