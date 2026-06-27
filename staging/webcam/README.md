# Webcams (crowsnest) — on-Pi finishing steps (MK2.5S Pi)

`crowsnest.conf` here is a **two-camera** config. Two placeholders must be filled on the Pi.

## Why by-id paths (not /dev/video0)
`/dev/video0` / `video1` are assigned in USB enumeration order and **reorder across reboots**, so your
two cameras can swap. The `/dev/v4l/by-id/...` paths are tied to each camera's identity and are stable.

## Steps on the Pi
1. Plug in both webcams.
2. List the stable paths:
   ```bash
   ls /dev/v4l/by-id/
   ```
   Use the entry ending in **`-video-index0`** for each camera (ignore `-index1` metadata nodes).
3. Edit `~/printer_data/config/crowsnest.conf`, replacing:
   - `REPLACE_WITH_CAMERA1_BY_ID` → first camera's full `/dev/v4l/by-id/usb-...-video-index0` path
   - `REPLACE_WITH_CAMERA2_BY_ID` → second camera's full path
4. Restart crowsnest:
   ```bash
   sudo systemctl restart crowsnest
   ```
5. In Mainsail: **Settings → Webcams → Add** two webcams, each pointing at a stream
   (service `ustreamer-adaptive`; URLs typically `/webcam/?action=stream` and `/webcam2/?action=stream`
   — confirm against `~/printer_data/logs/crowsnest.log`).

## If it's flaky (Pi 3-class host)
The 3B/3B+ shares one USB 2.0 bus across both cameras **and** the printer serial. If you get dropped
frames, USB resets, or the printer disconnecting mid-print:
- Lower one/both cameras to `640x480` and `max_fps: 10`.
- Consider running only one camera while actually printing.
- A powered USB hub doesn't add bus bandwidth but helps with power dips.
- On a Pi 4/5 these constraints largely go away — raise res/fps as you like.
