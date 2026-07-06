# 32-bit Raspberry Pi OS migration (crash-mitigation A/B test)

Build a **32-bit (armhf) Raspberry Pi OS** on a **spare SD card** to test whether it survives the
mid-print host freeze that the 64-bit OS does not. **Non-destructive:** the working 64-bit card is
left untouched, so reverting is just a card swap.

## Why

The recurring failure is a **silent, instantaneous host hard-hang** during printing (see the main
README debugging section): the kernel logs *nothing* at the freeze — no panic, no RCU stall, no
under-voltage, no USB error — then the hardware watchdog reboots it ~60 s later. Resources
(RAM/CPU/temp) are healthy throughout. It happens on this SKR-based Pi but **never** on the twin
MK3S-based Pi running the *identical* 64-bit image.

This matches, **exactly**, `drdan_makes` in the Voron thread
[Random halts/freezes of Klipper RPi](https://forum.vorondesign.com/threads/random-halts-freezes-of-klipper-rpi-software-hardware.2148/):
Pi 3B+, mid-print freeze, log cuts off clean, temps/CPU/RAM fine, power-cycle to recover,
reinstalling 64-bit did **not** help — **switching to 32-bit Pi OS fixed it.** The Pi 3B+ is
known to be less stable on aarch64; a 32-bit kernel appears more resilient to whatever wedges it.

> Honest caveat: our forensics point to a **hardware electrical trigger** (only the un-choked SKR
> USB link crashes; the MK3S Einsy has a USB common-mode choke). 32-bit likely won't *prevent* the
> electrical event — but drdan_makes' result says it may let the kernel *survive* it. Run this
> alongside the **USB isolator** (which removes the glitch) — they're complementary.

## Prerequisites

- Spare SD card, **8 GB+** (16 GB+ recommended).
- Raspberry Pi Imager on your Mac.
- The config backup already captured in this repo at `pi-live-backup/` (printer_data/config + boot
  overlays + xorg HyperPixel confs).
- ~1 hour.

## Step 1 — Flash 32-bit Raspberry Pi OS Lite

In Raspberry Pi Imager:

1. **Choose OS** → *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite (32-bit)** (Bookworm, armhf).
   Do **not** pick the 64-bit one — that's the whole point.
2. **Choose Storage** → the spare SD.
3. **⚙ / Edit Settings** before writing:
   - Hostname: `prusa-mk2s-32` (distinct from the 64-bit card so you never confuse them on the LAN).
   - Enable SSH → *Use password auth* or paste your public key.
   - Username `david`, set password.
   - Configure Wi-Fi (SSID/pass/country) so it comes up headless.
   - Locale/timezone.
4. Write, then insert into the Pi (with the 64-bit card **removed and set aside**).

## Step 2 — First boot + base update

```bash
ssh david@prusa-mk2s-32.local        # or find the new IP from your router
uname -m                             # MUST show armv7l / armhf — NOT aarch64
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git
```

## Step 3 — Install Klipper + Moonraker + KlipperScreen (KIAUH)

```bash
cd ~ && git clone https://github.com/dw-0/kiauh.git
./kiauh/kiauh.sh
```
In KIAUH: **Install** → Klipper, then Moonraker, then (optionally) KlipperScreen, then a web UI
(Mainsail or Fluidd). Accept defaults.

## Step 4 — ⚠ Match the SKR firmware to the new host Klipper

KIAUH installs the *latest* Klipper. The SKR's flashed firmware is
**v0.13.0-642-g77d5d942e** — if the host version differs you'll get an MCU version-mismatch warning.
Cleanest fix: **re-flash the SKR from the new host** (you did this during the original conversion):

```bash
cd ~/klipper
make menuconfig     # STM32 / STM32G0B1 / 8KiB bootloader / USB (PA11/PA12) — same as before
make
# copy klipper.bin -> SD card as firmware.bin, insert into SKR, power-cycle to flash
```
(Alternative: `git checkout 77d5d942e` in `~/klipper`, reinstall the service, and skip re-flashing —
but re-flashing to latest on both sides is tidier.)

## Step 5 — Restore your config

Copy the working configs from this repo's `pi-live-backup/` onto the new card:

```bash
# from your Mac, adjust the repo path:
scp pi-live-backup/printer_data/config/*.cfg  david@prusa-mk2s-32.local:~/printer_data/config/
scp pi-live-backup/printer_data/config/*.conf david@prusa-mk2s-32.local:~/printer_data/config/
```
Check `printer.cfg` `[mcu] serial:` still points at the SKR's `/dev/serial/by-id/...` path
(re-run `ls /dev/serial/by-id/` on the new card — the ID is the same board, so it should match).

## Step 6 — HyperPixel display (if you want the screen on the test card)

Restore the overlay + rotation from the backup:

```bash
# /boot/firmware/config.txt: ensure the HyperPixel dtoverlay line is present (copy from backup)
sudo cp pi-live-backup/etc/X11/xorg.conf.d/90-hyperpixel-rotate.conf /etc/X11/xorg.conf.d/
sudo cp pi-live-backup/etc/X11/xorg.conf.d/91-hyperpixel-touch.conf  /etc/X11/xorg.conf.d/
```
(You can skip the screen for the first crash test — SSH/web UI is enough to run a Benchy.)

## Step 7 — Verify + run the crash test

```bash
uname -m                              # confirm armv7l (32-bit)
# home, then run the SAME Benchy that reliably froze the 64-bit card
```
Re-arm the disk crash-logger and watch it through the upper region (~74–82%) exactly as before.

- **Completes** → 32-bit is more resilient to the glitch → strong candidate for the daily-driver
  card (still add the USB isolator to fix the root cause).
- **Freezes at the same point** → the OS bitness isn't the axis → the fix is purely hardware
  (USB isolator + noise suppression). Swap the 64-bit card back in.

## Revert

Power off, swap the 64-bit card back in, power on. Nothing on the original card was touched.

---

## Real-world outcomes (this build)

We actually did this migration. Notes from the field:

**Crash A/B result — promising, not yet conclusive.** On 32-bit the same Benchy that froze the 64-bit
card **3 of its last 4 attempts** (in the 74–82% "danger zone") **completed cleanly twice in a row**,
including a **4 h 16 m continuous crash-free uptime**. Encouraging and it matches the documented
`drdan_makes` 32-bit fix — but the freeze is *intermittent*, so this isn't proof. The definitive test
is an **acceleration-stress run**: crank accel (via an `M204` multiplier, no re-slice) to raise the
electrical-noise level and see whether 32-bit can still be *forced* to freeze. If it can → it's
electrical noise (32-bit only raised the threshold); if it rides it out → genuine OS-level resilience.

**Boot-time MCU-USB glitch (intermittent).** On some boots Klipper comes up in an error state —
`Got error -1 in write: (19) No such device` / `Got EOF when reading from device` during the initial
MCU config (the same SKR USB flakiness, surfacing at connect-time). A `FIRMWARE_RESTART` clears it.
We installed an auto-recovery service so reboots self-heal:
`/etc/systemd/system/klipper-boot-recovery.service` → runs `~/klipper-boot-recovery.sh`, which waits
~25 s, and if Klipper isn't `ready` **and no print is running**, issues `FIRMWARE_RESTART` (up to 3×).
Band-aid; the USB isolator is the root fix.

**Klipper host version pin.** To keep the A/B honest (only OS bitness changes), pin the host to the
**exact** commit the SKR firmware was built at (`git checkout <commit>` in `~/klipper`) so there's no
MCU version mismatch and no need to re-flash the SKR.

**mainsail.cfg is a symlink.** The restored `printer.cfg` `[include mainsail.cfg]` points at
`~/mainsail-config/mainsail.cfg`; clone `github.com/mainsail-crew/mainsail-config` so the symlink
resolves, or Klipper won't start.

**LCD (stock 20×4 HD44780) needs the source patch.** The config alone isn't enough — reapply the two
`hd44780.py` timing patches (`staging/scripts/reapply-hd44780-patch.sh`) or the LCD garbles.

**⚠ HyperPixel touchscreen: hard on 32-bit.** The HyperPixel goes **black under any compositor** on
32-bit (console works, panel blanks) — a real `vc4`-KMS-atomic scanout bug that does **not** affect
64-bit. It *is* fixable (Wayland/cage + `WLR_DRM_NO_ATOMIC=1`) — see
**[hyperpixel-klipperscreen-32bit-fix.md](hyperpixel-klipperscreen-32bit-fix.md)**. If you want the
touchscreen with zero fuss, that's the strongest argument for staying on 64-bit and fixing the crash
with the USB isolator instead.
