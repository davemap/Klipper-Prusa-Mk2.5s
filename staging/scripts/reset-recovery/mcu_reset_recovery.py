#!/usr/bin/env python3
"""mcu-reset-recovery: auto-recover Klipper after a physical MCU reset.

Problem: pressing the SKR Mini E3 V3.0's physical RESET button reboots the
MCU behind Klipper's back. Klipper latches into state=shutdown with
"Lost communication with MCU 'mcu'" and stays there (LCD dead/garbled)
until someone manually issues FIRMWARE_RESTART.

This daemon polls Moonraker and, ONLY for that specific failure signature,
issues an automatic FIRMWARE_RESTART (escalating once to a klipper service
restart if that is not enough).

SAFETY GATING (deliberate, do not loosen):
  - Acts ONLY when state == "shutdown" AND state_message contains
    "Lost communication with MCU". Every other shutdown reason (thermal
    runaway / MCU 'mcu' shutdown, M112 emergency stop, klippy errors,
    config errors -> state "error") is left latched for a human.
  - Rate limit: max 3 recovery attempts per rolling 10 minutes. When
    exceeded, automatic recovery is suspended (loud CRIT log) until the
    window slides past — this prevents crash loops if the MCU is
    genuinely unstable (brownouts, bad USB cable, ...).

Logs go to stdout with <N> syslog priority prefixes; systemd/journald
parses these (SyslogLevelPrefix=true is the default), so use:
    journalctl -u mcu-reset-recovery
"""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

MOONRAKER = "http://localhost:7125"
SERIAL_DEVICE = (
    "/dev/serial/by-id/"
    "usb-Klipper_stm32g0b1xx_09003D000C50564837383420-if00"
)
MATCH = "Lost communication with MCU"

POLL_INTERVAL = 5.0        # seconds between Moonraker polls
USB_SETTLE_DELAY = 8.0     # wait after detection for USB re-enumeration
SERIAL_WAIT_EXTRA = 15.0   # additional wait for the serial node to reappear
ESCALATE_CHECK_DELAY = 30.0  # after firmware_restart, when to check state
STARTUP_GRACE = 20.0       # extra grace if klipper is mid-"startup"
MAX_ATTEMPTS = 3           # recovery attempts allowed ...
ATTEMPT_WINDOW = 600.0     # ... per this many seconds (rolling window)


def log(msg: str, pri: int = 6) -> None:
    print(f"<{pri}>{msg}", flush=True)


def info(msg: str) -> None:
    log(msg, 6)


def warn(msg: str) -> None:
    log(msg, 4)


def err(msg: str) -> None:
    log(msg, 3)


def crit(msg: str) -> None:
    log(msg, 2)


def get_printer_info():
    """Return Moonraker /printer/info result dict, or None if unreachable.

    Moonraker answers 503 while klippy's API socket is down (e.g. during a
    klipper service restart) — treat that the same as unreachable.
    """
    try:
        with urllib.request.urlopen(MOONRAKER + "/printer/info", timeout=5) as r:
            return json.load(r)["result"]
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            ValueError, KeyError):
        return None


def post(path: str) -> bool:
    req = urllib.request.Request(MOONRAKER + path, data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        warn(f"POST {path} failed: {e}")
        return False


def wait_for_ready(total_seconds: float, step: float = 5.0):
    """Poll until state==ready or time runs out. Returns final state str."""
    deadline = time.monotonic() + total_seconds
    state = None
    while time.monotonic() < deadline:
        time.sleep(step)
        st = get_printer_info()
        state = st.get("state") if st else None
        if state == "ready":
            return state
    return state


def attempt_recovery() -> None:
    info(f"MCU communication loss detected — waiting {USB_SETTLE_DELAY:.0f}s "
         "for USB re-enumeration")
    time.sleep(USB_SETTLE_DELAY)

    deadline = time.monotonic() + SERIAL_WAIT_EXTRA
    while not os.path.exists(SERIAL_DEVICE):
        if time.monotonic() > deadline:
            err(f"serial device {SERIAL_DEVICE} did not reappear within "
                f"{USB_SETTLE_DELAY + SERIAL_WAIT_EXTRA:.0f}s — skipping "
                "FIRMWARE_RESTART (board unplugged or in DFU?). "
                "Attempt counted toward rate limit.")
            return
        time.sleep(1.0)

    info("serial device present — issuing FIRMWARE_RESTART via Moonraker")
    post("/printer/firmware_restart")

    time.sleep(ESCALATE_CHECK_DELAY)
    st = get_printer_info()
    state = st.get("state") if st else None
    if state == "ready":
        info("recovery successful: Klipper is ready again")
        return
    if state == "startup":
        state = wait_for_ready(STARTUP_GRACE)
        if state == "ready":
            info("recovery successful: Klipper is ready again")
            return

    warn(f"Klipper still not ready {ESCALATE_CHECK_DELAY:.0f}s after "
         f"FIRMWARE_RESTART (state={state!r}) — escalating once to "
         "'sudo systemctl restart klipper'")
    try:
        proc = subprocess.run(
            ["sudo", "-n", "systemctl", "restart", "klipper"],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        err("'systemctl restart klipper' timed out")
        return
    if proc.returncode != 0:
        err("'sudo systemctl restart klipper' failed "
            f"(rc={proc.returncode}): {proc.stderr.strip()}")
        return

    state = wait_for_ready(60.0)
    if state == "ready":
        info("recovery successful after klipper service restart: "
             "Klipper is ready again")
    else:
        err(f"Klipper still not ready after service restart "
            f"(state={state!r}) — giving up on this attempt; manual "
            "intervention may be required")


def main() -> None:
    info(f"mcu-reset-recovery watcher started (poll={POLL_INTERVAL:.0f}s, "
         f"trigger='{MATCH}', limit={MAX_ATTEMPTS} attempts "
         f"per {ATTEMPT_WINDOW:.0f}s)")
    attempts: list[float] = []   # monotonic timestamps of recovery attempts
    last_ignored_msg = None      # dedupe "ignored shutdown" log lines
    lockout_logged = False       # dedupe the rate-limit CRIT log

    while True:
        st = get_printer_info()
        if st is not None:
            state = st.get("state")
            msg = st.get("state_message") or ""
            if state == "shutdown" and MATCH in msg:
                last_ignored_msg = None
                now = time.monotonic()
                attempts = [t for t in attempts if now - t < ATTEMPT_WINDOW]
                if len(attempts) >= MAX_ATTEMPTS:
                    if not lockout_logged:
                        crit(f"RATE LIMIT HIT: {MAX_ATTEMPTS} recovery "
                             f"attempts within {ATTEMPT_WINDOW:.0f}s — "
                             "suspending automatic recovery. The MCU keeps "
                             "dropping (power/USB problem?). Fix the cause, "
                             "then run FIRMWARE_RESTART manually.")
                        lockout_logged = True
                else:
                    attempts.append(now)
                    info(f"recovery attempt {len(attempts)}/{MAX_ATTEMPTS} "
                         "in current window")
                    attempt_recovery()
            elif state == "shutdown":
                if msg != last_ignored_msg:
                    info("shutdown detected but NOT an MCU communication "
                         "loss — leaving latched for manual recovery. "
                         f"state_message={msg!r}")
                    last_ignored_msg = msg
            else:
                # ready / startup / error: clear per-incident dedupe flags
                last_ignored_msg = None
                lockout_logged = False
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
