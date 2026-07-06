# mcu-reset-recovery — auto-recovery after the board's physical RESET button

## What this is

Pressing the SKR Mini E3 V3.0's physical RESET button reboots the MCU behind
Klipper's back. Klipper latches into `state=shutdown` with
`Lost communication with MCU 'mcu'` and stays there — Mainsail shows the red
shutdown banner and the HD44780 LCD stays dead/garbled — until someone manually
issues `FIRMWARE_RESTART` (and occasionally a full `systemctl restart klipper`).

Neither Klipper nor Moonraker offers this out of the box: Klipper deliberately
latches all shutdown states for safety, and Moonraker's only auto-restart hook
(`[power]` + `restart_klipper_when_powered`) applies to Moonraker-controlled
power devices, not a physical reset. Hence this small daemon.

`mcu_reset_recovery.py` runs as a systemd service on the Pi, polls Moonraker's
`/printer/info` every 5 s, and automates exactly the manual recovery — for this
one failure signature only.

## Recovery flow

1. Detect `state == "shutdown"` **and** `state_message` containing
   `Lost communication with MCU`.
2. Wait 8 s for the USB device to re-enumerate; verify
   `/dev/serial/by-id/usb-Klipper_stm32g0b1xx_09003D000C50564837383420-if00`
   exists (waits up to 15 s more, else aborts the attempt).
3. `POST /printer/firmware_restart` (Moonraker → Klipper `FIRMWARE_RESTART`).
   This reconnects the MCU and re-runs display init, so the LCD comes back too.
4. If Klipper is still not `ready` 30 s later, escalate **once** per attempt:
   `sudo systemctl restart klipper` (user `david` has passwordless sudo on
   MainsailOS; no extra sudoers rule needed — if you ever remove general
   passwordless sudo, add a narrow rule:
   `david ALL=(root) NOPASSWD: /usr/bin/systemctl restart klipper`).

## Safety gating (deliberate — do not loosen)

- **Only** the `Lost communication with MCU` shutdown is auto-recovered.
  Thermal runaway / heater faults, `M112` emergency stops, klippy internal
  errors, config errors, etc. stay latched for a human to inspect. The watcher
  logs that it saw such a shutdown and ignored it.
- **Rate limit:** max 3 recovery attempts per rolling 10-minute window. Beyond
  that it suspends itself and logs at CRIT priority — if the MCU is dropping
  repeatedly (brownouts, failing USB cable), auto-restarting in a loop would
  mask a real problem. Once the window slides past it will try again; restart
  the service to reset the counter immediately.

## Files

| Staging file | Installed to (Pi, 192.168.1.93) |
|---|---|
| `mcu_reset_recovery.py` | `/home/david/mcu-reset-recovery/mcu_reset_recovery.py` |
| `mcu-reset-recovery.service` | `/etc/systemd/system/mcu-reset-recovery.service` |
| `README.md` | `/home/david/mcu-reset-recovery/README.md` |
| `install.sh` | (installer, run on the Pi) |

## Install / reinstall

```sh
scp -r "…/staging/scripts/reset-recovery" david@192.168.1.93:/tmp/
ssh david@192.168.1.93 'bash /tmp/reset-recovery/install.sh'
```

## Operating it

```sh
journalctl -u mcu-reset-recovery -f      # watch it work
systemctl status mcu-reset-recovery
sudo systemctl restart mcu-reset-recovery  # also resets the rate-limit counter
sudo systemctl disable --now mcu-reset-recovery  # turn it off
```

## Test log (2026-07-03)

- Service enabled + running, clean startup log.
- **Negative test (M112):** emergency stop via Moonraker → state `shutdown`
  with "Shutdown due to M112 command". Watcher logged
  "shutdown detected but NOT an MCU communication loss — leaving latched" and
  took no action (verified still shutdown 25 s later). Cleared manually via
  `/printer/firmware_restart`.
- **Positive test (simulated button press):** `USBDEVFS_RESET` ioctl on the
  MCU's USB device while Klipper was connected → Klipper went to `shutdown` /
  `Lost communication with MCU 'mcu'`. Watcher detected it, waited 8 s,
  verified the serial node, issued `firmware_restart`; klippy raced the
  still-configured MCU and landed in `error`, so 30 s later the watcher
  escalated to `sudo systemctl restart klipper` — **ready again ~50 s after
  the fault, zero manual steps**. (The escalation firing in this simulation
  is expected: the MCU wasn't actually rebooted so it kept its old session
  config. A real button press reboots the MCU cleanly, so `firmware_restart`
  alone will usually suffice — and the escalation covers it when it doesn't,
  which matches the previously-observed manual behaviour.)
- Note: an earlier simulation attempt using sysfs USB unbind/rebind left the
  CDC device half-broken (host re-enumerated but MCU USB stack stale) and the
  watcher correctly gave up loudly after its escalation failed. That failure
  mode is an artifact of the unbind trick, not of the reset button. Healed
  with a `USBDEVFS_RESET` + service restart.
- **Remaining manual test:** press the physical RESET button on the board once
  while the printer is idle; within ~15–60 s Klipper (and the LCD) should
  recover on their own. Watch `journalctl -u mcu-reset-recovery -f` while
  doing it.
