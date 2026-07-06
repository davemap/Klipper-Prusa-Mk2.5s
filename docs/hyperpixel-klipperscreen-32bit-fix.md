# HyperPixel 4.0 + KlipperScreen on 32-bit Raspberry Pi OS — the black-screen fix

**TL;DR:** On **32-bit (armv7l)** Raspberry Pi OS with the `vc4-kms` driver, the HyperPixel 4.0
(and other DPI panels) shows the **boot console fine but goes black the moment a compositor
(X *or* Wayland) starts** — backlight stays on, the app renders correctly, but nothing reaches the
panel. This is a **32-bit vc4 KMS *atomic-modeset* scanout bug** (64-bit is unaffected). The fix is to
run **KlipperScreen under Wayland/cage with the legacy (non-atomic) modeset + software renderer**:

```ini
# /etc/systemd/system/KlipperScreen.service.d/wayland-fix.conf
[Service]
Environment=BACKEND=W
Environment=WLR_RENDERER=pixman
Environment=WLR_RENDERER_ALLOW_SOFTWARE=1
Environment=WLR_NO_HARDWARE_CURSORS=1
Environment=WLR_DRM_NO_MODIFIERS=1
Environment=WLR_DRM_NO_ATOMIC=1
```
The single most important line is **`WLR_DRM_NO_ATOMIC=1`** (forces the same legacy modeset path the
working console uses). Requires `cage` + `seatd` installed. Rotation is then set with `wlr-randr`.

---

## Environment where this applies
- **Board:** Raspberry Pi 3B+ (VideoCore-IV).
- **OS:** Raspberry Pi OS Lite **Trixie (Debian 13), 32-bit (armv7l)**, kernel `6.18.34+rpt-rpi-v7`.
- **Display:** Pimoroni **HyperPixel 4.0 rectangular** (800×480 DPI / parallel-RGB), overlays:
  `dtoverlay=vc4-kms-v3d` + `dtoverlay=vc4-kms-dpi-hyperpixel4,rotate=270`.
- **App:** KlipperScreen (GTK3), launched by its own `KlipperScreen-start.sh`.

We ended up on 32-bit specifically to A/B-test a mid-print host-freeze (see the main README §9). The
identical display config works perfectly on the 64-bit MK3S twin — **only 32-bit is affected.**

## Symptom
- Boot/kernel **console displays fine** on the panel — readable text, backlight on.
- The instant **X or Wayland/cage** takes over → **panel goes black**, backlight stays on.
- The app *is* rendering: a `scrot`/screenshot of the compositor shows the full, correct UI.
- `/dev/fb0` = 480×800; `card0-DPI-1` = `connected`. Nothing looks wrong in software.

## Root cause (and how we proved it)
A Raspberry Pi engineer confirmed on the forums that this is a **32-bit userland display-server
issue**, not a kernel/driver bug (64-bit works with the identical config). We narrowed it precisely:

1. `scrot` shows the correct UI → **rendering is fine**; the problem is **scanout** (buffer → panel).
2. Inspecting the live KMS state (`/sys/kernel/debug/dri/0/state`) under cage showed the DPI plane
   committed with a **`modifier=0x0` (LINEAR)** framebuffer on `crtc=pixelvalve-0` at `480x800` — i.e.
   the commit was **already correct and linear**, yet the panel was black. So it is **not** a tiled-vs-
   linear buffer-format problem (a popular theory) and **not** a wrong-DRM-card problem (there is only
   `card0` + its `renderD128` render node).
3. `dmesg` showed **no** `flip_done`/commit timeouts → the kernel accepts the commit.
4. With the compositor stopped, the **console (fbcon) displays fine** on the panel.

The discriminator: **fbcon uses the simple *legacy* modeset path and works; compositors use the KMS
*atomic* path and don't.** On 32-bit vc4 + DPI, the atomic commit "succeeds" but never actually drives
the panel. Forcing the compositor onto the **legacy** modeset (`WLR_DRM_NO_ATOMIC=1`) fixes it.

## The working fix (step by step)
Assumes Klipper/Moonraker/KlipperScreen already installed, `vc4-kms-v3d` +
`vc4-kms-dpi-hyperpixel4,rotate=270` in `config.txt`, SPI/I²C disabled.

1. **Install the Wayland compositor + seat manager:**
   ```bash
   sudo apt-get install -y cage seatd wlr-randr
   sudo systemctl enable --now seatd
   sudo usermod -aG video,render,input,tty david
   ```
2. **Point KlipperScreen at Wayland + the legacy/software path** — drop-in
   `/etc/systemd/system/KlipperScreen.service.d/wayland-fix.conf` with the block at the top of this doc.
   (KlipperScreen's `KlipperScreen-start.sh` uses cage when `BACKEND=W`, else `xinit`.)
3. **Persist the rotation** — `wlr-randr` is runtime-only, so re-apply it each launch via an
   `ExecStartPost` hook `/etc/systemd/system/KlipperScreen.service.d/rotate.conf`:
   ```ini
   [Service]
   ExecStartPost=/home/david/ks-rotate.sh
   ```
   `~/ks-rotate.sh` waits for the wayland socket then runs
   `wlr-randr --output DPI-1 --transform 90` (transform value depends on your panel mounting — we
   needed **90**; 270 came out upside-down).
4. `sudo systemctl daemon-reload && sudo systemctl restart KlipperScreen`.

**Backlight/blank timeout:** set in `KlipperScreen.conf` (`screen_blanking: 300`,
`screen_blanking_printing: 600`) — note KlipperScreen mirrors these in a `#~#` auto-save block at the
bottom of the file, so change them in **both** places.

## Touch calibration (rotated display)
After rotating the output, **touch does not follow** — the cursor roams and clicks land in the wrong
place. Cause: cage/wlroots doesn't apply the output transform to touch input when libinput reports a
**null `output_name`** for the device (cage bug #126 / wlroots #928). Fix it one level down, at
**libinput**, with a calibration matrix via a udev rule (bypasses the compositor):
```
# /etc/udev/rules.d/99-hyperpixel-touch.rules
ATTRS{name}=="Goodix Capacitive TouchScreen", ENV{LIBINPUT_CALIBRATION_MATRIX}="0 -1 1 1 0 0"
```
Then `sudo udevadm control --reload && sudo udevadm trigger`, and restart KlipperScreen. The
`0 -1 1 1 0 0` matrix is the 90° rotation (identical to the X11 `TransformationMatrix` that worked for
this orientation on the 64-bit twin). If touch comes out mirrored/wrong-way, try the other rotations:
180° = `-1 0 1 0 -1 1`, 270° = `0 1 0 -1 0 1`.

## What did NOT work (so you don't waste time)
- X11 (default `modesetting`), X11 `Option "PageFlip" "false"`, X11 `fbdev` driver — all black.
- Wayland/cage with the **default GLES renderer** — black.
- `WLR_RENDERER=pixman` **alone** — black (rendering was fine, scanout still atomic).
- `video=DPI-1:e` / `video=DPI-1:480x800@60` in `cmdline.txt` — no effect (connector already enabled).
- `vc4-fkms-v3d` — not viable: Trixie removed the legacy firmware-DPI stack the fkms path needs, and
  the `vc4-kms-dpi-hyperpixel4` overlay is full-KMS-only.
- Reinstalling KlipperScreen / a clean OS install — the app was never the problem.

## Caveats & trade-offs
- **This is 32-bit-specific.** On **64-bit** the standard `vc4-kms` + X11 path just works — if you only
  need the touchscreen, 64-bit is the simplest answer.
- We're on 32-bit to fix a mid-print **host freeze** (README §9). So there's a real trade-off: 32-bit
  (freeze appears fixed, this display fix needed) vs 64-bit (display trivial, freeze present). The
  endgame that gives **both** is a **USB isolator on 64-bit**.
- The exact minimal env set wasn't bisected — `WLR_DRM_NO_ATOMIC=1` is the key; the others are
  belt-and-suspenders (software renderer + linear buffers + no HW cursor) and harmless.

## Sources (verified)
- **[Raspberry Pi 3, vc4-kms blackscreen only with 32bit](https://forums.raspberrypi.com/viewtopic.php?p=2343864)** — reproduces by swapping armhf↔arm64 SD cards on one Pi 3 (64-bit `vc4-kms-v3d` works, 32-bit = black). RPi engineer **Dom**: *"the kernel driver is fine but you have a userland issue with X… I wonder if this issue is an old X issue where it gets confused over the two dri cards."*
- **["Works in console, stops working in X"](https://forums.raspberrypi.com/viewtopic.php?p=2347351)** (same thread) — *"The framebuffer console (both the initial firmware one and the later DRM one) both work perfectly fine. Starting Xorg causes the issues."*
- **[CM5 + vc4-kms: "only LINEAR scans out / --use-pixman works"](https://forums.raspberrypi.com/viewtopic.php?p=2309955)** — corroborates the *mechanism* (non-LINEAR/tiled buffers don't scan out on vc4; software/pixman rendering restores output). ⚠️ This is a **CM5 + Buildroot/Weston** case, not HyperPixel/Pi 3 — cited for the mechanism, not the same hardware.
- **[wlroots `docs/env_vars.md`](https://github.com/swaywm/wlroots/blob/master/docs/env_vars.md)** — `WLR_RENDERER=pixman` (software renderer), `WLR_DRM_NO_ATOMIC=1` (legacy modeset), `WLR_DRM_NO_MODIFIERS=1` (allocate planes without modifiers).
- **Pimoroni hyperpixel4:** [#177 PSA (64-bit)](https://github.com/pimoroni/hyperpixel4/issues/177), [#154](https://github.com/pimoroni/hyperpixel4/issues/154), [#229](https://github.com/pimoroni/hyperpixel4/issues/229) — black-screen reports.
- **Touch:** [cage #126](https://github.com/cage-kiosk/cage/issues/126) (touch doesn't follow output transform — null `output_name`), [wlroots #928](https://github.com/swaywm/wlroots/issues/928) (touch events ignore output rotation).
