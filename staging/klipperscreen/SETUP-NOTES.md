# KlipperScreen + HyperPixel — setup notes (validate LIVE on the MK2.5S Pi)

> ⚠️ This is the **least-standardized, most likely-to-need-iteration** step. MainsailOS is headless
> (Pi OS Lite, no desktop), and the HyperPixel drives the panel over the Pi's **GPIO/DPI** bus.
> Everything `dtoverlay`-related below is **UNVERIFIED for your exact panel + OS build** — treat the
> lines as *candidates to try*, not guaranteed. If it fights you, use the fallback at the bottom.

This is identical to the MK3S+ build — the HyperPixel + KlipperScreen are host-side (the Pi), so the
control-board swap (Einsy → SKR Mini E3 V3) changes nothing here.

## The two separate sub-problems
1. **Get the HyperPixel panel + touch working** under the MainsailOS kernel — add the right
   `dtoverlay=` to `/boot/firmware/config.txt` (newer Pi OS path; older was `/boot/config.txt`).
2. **Make KlipperScreen render to that panel** — installed separately (see `install-klipperscreen.sh`);
   MainsailOS does **not** ship KlipperScreen.

## FIRST: confirm which HyperPixel you have  ← TODO(user)
The overlay differs per model. Check the board/label or your old setup:
- **HyperPixel 4.0** (rectangular, 800×480)
- **HyperPixel 4.0 Square** (720×720)
- **HyperPixel 2.1 Round** (480×480)
- **HyperPixel 2.0 / older revisions**

## Candidate dtoverlay lines (UNVERIFIED — try, don't trust)
On current Raspberry Pi OS / MainsailOS (Bookworm-based) the HyperPixel DPI drivers are built in —
you add ONE line to `/boot/firmware/config.txt`:

| Your panel | Candidate line to try |
|---|---|
| HyperPixel 4.0 (rectangular) | `dtoverlay=vc4-kms-dpi-hyperpixel4` |
| HyperPixel 4.0 Square | `dtoverlay=vc4-kms-dpi-hyperpixel4sq` |
| HyperPixel 2.1 Round | (no stock `vc4-kms-dpi-*`; likely needs Pimoroni's installer — see below) |

Rotation (KlipperScreen on a printer is often rotated): append `,rotate=90` (or 180/270), e.g.
```
dtoverlay=vc4-kms-dpi-hyperpixel4,rotate=90
```

### Things that bite you on Pi OS Lite + HyperPixel
- **Disable conflicting interfaces.** The HyperPixel claims nearly all GPIO. Pimoroni's docs say to
  **disable I2C, SPI, and other GPIO interfaces** in `raspi-config` / `config.txt` or device-tree
  conflicts leave the screen blank. Check MainsailOS hasn't auto-enabled `dtparam=spi=on` etc.
- **Your accelerometer is USB, so no GPIO conflict.** Forum reports of "HyperPixel breaks input shaping"
  are about ADXL345 boards wired to the Pi's GPIO SPI pins. Your **BTT ADXL345 is USB-attached**
  (`adxlmcu-BTT.cfg` uses `[mcu adxl] serial:`), so it doesn't touch Pi GPIO SPI and won't fight the
  panel — keep the HyperPixel mounted during input shaping.
- **The Pimoroni one-line installer targets full desktop Pi OS**, not Lite — prefer the built-in
  `dtoverlay` approach first; only fall back to `curl https://get.pimoroni.com/hyperpixel4 | bash` if the
  overlay alone doesn't light the panel, and expect to clean up afterward.
- **Backlight pin.** Some revisions use GPIO19 for backlight; panel on but black is usually
  backlight/rotation, not the driver.

## Install order on the Pi (summary — full steps in ON-PI-RUNBOOK.md)
1. Get Mainsail/Klipper fully working FIRST (don't debug the screen until the printer side is solid).
2. Add the candidate `dtoverlay` line → reboot → confirm the panel shows the console/boot text.
3. Run `install-klipperscreen.sh` → reboot → KlipperScreen should render on the panel.
4. Touch calibration / rotation tweaks as needed.

## Fallback (totally acceptable)
If the HyperPixel proves too painful headless, **skip the local screen** and use Mainsail from a
phone/tablet/PC at `http://mk25s.local`. KlipperScreen is a nice-to-have, not required to print.

## Sources (verify against your panel + OS build)
- Pimoroni HyperPixel 4 driver repo: https://github.com/pimoroni/hyperpixel4
- Getting Started with HyperPixel 4.0: https://learn.pimoroni.com/article/getting-started-with-hyperpixel-4
- KlipperScreen install docs: https://klipperscreen.readthedocs.io/en/latest/Installation/
- MainsailOS docs: https://docs-os.mainsail.xyz/
