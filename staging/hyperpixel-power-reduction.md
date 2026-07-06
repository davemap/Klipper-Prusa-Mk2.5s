# HyperPixel 4.0 — cutting current draw & heat on the Pi 3B+

Research findings (2026-07-04). To APPLY when we re-enable the HyperPixel (currently the
overlay is disabled — kernel 6.18.34 boot-loop; see wiring notes). Verified against the actual
kernel overlay source (`vc4-kms-dpi-hyperpixel.dtsi` / `-hyperpixel4-overlay.dts`) and KlipperScreen `screen.py`.

## The number that matters
HyperPixel 4.0 draws **~150 mA @ 5V (~0.75 W)** total:
- **Backlight ≈ 110 mA (~73%)** ← the whole game
- Panel/DPI logic ≈ 30–40 mA
- GT911 touch ≈ 1–5 mA
**Attack the backlight. Everything else is rounding error.**

## P1 — Backlight OFF when idle (biggest win, free, software) ★ do this first
A **black screensaver saves ~0 mA** (LED stays on). Only **true DPMS-off** pulls GPIO19 low →
backlight physically off → **saves the full ~110 mA + its trapped heat**. DPMS-off *does* cut the
backlight on Pi 3-class HW (the "stays on" bug is Pi 4 only). KlipperScreen uses `xset dpms force off`
→ **X11 only** (on Wayland it force-disables DPMS and you get only the black screensaver = no saving).

`~/printer_data/config/KlipperScreen.conf`:
```ini
[main]
use_dpms: True
screen_blanking: 300            # idle seconds -> blank (or "off")
screen_blanking_printing: 3600  # longer timeout during a print
```
Verify on a meter it really drops ~0.1A:
```bash
ls /sys/class/backlight/                 # find device name
BL=/sys/class/backlight/<name>
echo 4 | sudo tee $BL/bl_power            # OFF (expect ~110mA drop)
echo 0 | sudo tee $BL/bl_power            # ON
```
Watch KlipperScreen log for "DPMS has failed and has been disabled" → means DPMS not working in
your session (Wayland/no DPMS ext) → only black screensaver. Fallback: idle watcher writing `bl_power`.

## P2 — PWM-dim backlight while ON (medium win, needs overlay edit)
Stock overlay = `gpio-backlight` on GPIO19 = **on/off only, max_brightness=1, NO dimming.**
To dim, replace with `pwm-backlight` (HW PWM on GPIO19): clone the two overlay files, change
`compatible="gpio-backlight"` → `pwm-backlight`, recompile with `dtc`, drop `.dtbo` in overlays.
~40–60% brightness ≈ saves ~50–65 mA continuously (even while active). **Loses analog audio**
(GPIO18/19 share PWM — irrelevant here). Do NOT userspace-PWM GPIO19 while gpio-backlight owns it.

## P3 — Heat/airflow (the real lever on the 58–60°C, not the rail)
- **Raise the HAT on standoffs + always-on 5V fan** through the gap (wire a plain 5V fan; the Fan
  Shim's control is dead since the HAT claims all GPIO). Biggest heat win.
- **Or move the display off-Pi** on a SHORT (~10–15cm) quality 2×20 ribbon → frees SoC for a normal
  heatsink/fan. DPI is timing-sensitive: long/cheap ribbon or header extenders corrupt the RGB signal — keep short, test.
- Low-profile thermal pad SoC→metal case. Tall heatsinks won't fit under the HAT.
- Separate-supply-for-backlight = invasive trace tapping, NOT recommended (new 5.1V supply has headroom anyway).

## P4 — skip these (negligible)
- `disable-touch` overlay param: saves only ~1–5 mA and kills the touchscreen (the point of KlipperScreen).
- Refresh/pixel-clock/color-depth: panel already 18-bit; DPI logic is tiny; ~2–5 mA for real flicker risk.

## Bottom line
1. DPMS + `screen_blanking` (verify on meter) → ~150→~40 mA idle (~73% cut), free.
2. PWM-backlight overlay @ ~50% → ~35% cut while active (loses audio, real effort).
3. Airflow (standoffs+fan or off-Pi ribbon) → biggest temperature win.
