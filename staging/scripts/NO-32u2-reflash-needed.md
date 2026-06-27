# No 32U2 "USB driver" reflash on this build (unlike the MK3S+)

The MK3S+ Einsy build needed a **32U2 Hoodserial reflash** because the Einsy RAMBo uses a separate
ATmega32U2 as a USB-to-serial bridge, and Prusa's stock 32U2 firmware corrupts serial under Klipper's
throughput (high `bytes_invalid`, crashed prints).

**The SKR Mini E3 V3 has none of that.** Its STM32G0B1 does **native USB** directly — there is no
32U2 bridge to reflash. So this entire step from the MK3S+ build is **not applicable** here.

You can delete this note; it exists only so the absence of the 32U2 step isn't mistaken for an omission.

If you ever see serial errors on the SKR build, check the actual USB cable / port and Klipper log:
```bash
grep -E "bytes_invalid|bytes_retransmit" ~/printer_data/logs/klippy.log | tail -5
```
(but with native USB you should see `bytes_invalid: 0`).
