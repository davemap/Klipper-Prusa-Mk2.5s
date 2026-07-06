# Printed parts & hardware modifications

Everything added/changed on top of a stock MK2.5S for this Klipper build. Links are to the source
models; the **Modification** column notes any cuts/edits made to the printed part.

## Printed parts

| Part | Source | Modification made | Notes |
|---|---|---|---|
| **External bed-MOSFET enclosure box** | [Thingiverse 1985754](https://www.thingiverse.com/thing:1985754) | **Custom lip + wiring harness added — ⚠️ TODO, see below** | Houses the 12 V MOSFET module (see purchased parts). Cooled by a dedicated 12 V fan (FAN2). |
| **Hybrid fan shroud (MK3S)** | [Printables 620993](https://www.printables.com/model/620993-hybrid-fan-shroud-for-mk3s) | **Cut off one of the lugs** | Part-cooling + hotend cooling shroud. |
| **Y-axis belt tensioner / idler pulley** (no threaded insert) | [Printables 77092](https://www.printables.com/model/77092-mk2-mk25s-y-axis-belt-tensioner-idler-pulley-no-th) | — | MK2/MK2.5S. Used during the Y belt-tension work. |
| **X-axis linear-rail upgrade + belt tensioner** | [Printables 281590](https://www.printables.com/model/281590-x-axis-upgrade-with-linear-rail-belt-tensioner-and) | — | Linear rail conversion for the X axis, with integrated belt tensioner. |
| **Vibration damper / rubber feet** | [Printables 8768](https://www.printables.com/model/8768-prusa-i3-mk2-vibration-damper-rubber-feet) | — | Decouples the printer from the table (addresses transmitted Y-axis noise / table amplification). |
| **HyperPixel 4.0 touchscreen cover** | [Printables 47153](https://www.printables.com/model/47153-lcd-hyperpixel-4-touchscreen-cover) | — | Bezel/cover for the HyperPixel display. |
| **(Bracket — tensioner clearance)** | [Thingiverse 4557234](https://www.thingiverse.com/thing:4557234) | **Cut up — removed the central part** to make room for the tensioner | |

## Non-printed modifications

- **Cut off the microswitch endstop mount from the Y-axis motor holder** — not needed, as X/Y use
  **sensorless homing** (TMC2209 StallGuard), so there's no physical endstop switch.

## Purchased hardware (added / changed vs stock)

| Item | Part / link |
|---|---|
| Mainboard | **BTT SKR Mini E3 V3.0** (STM32G0B1, 4× TMC2209 UART) — replaces the stock miniRambo |
| External bed-MOSFET module | **12 V MOSFET** — [Amazon B07DJYW5VD](https://www.amazon.co.uk/dp/B07DJYW5VD) (offloads the bed heater from the board) |
| Fans | **2× 12 V Noctua** — one cooling the **bed MOSFET** (FAN2), one on the **hotend** |
| USB cable (host ↔ SKR) | *currently a 2 m no-ferrite cable; a shorter shielded + ferrite cable is pending — see the host-reboot debugging in the main README* |

## ⚠️ TODO / reminders

- [ ] **Add the custom MOSFET-box lip + wiring harness you designed** (STL files + photos) to this repo —
      *you asked to be reminded of this.* The base box is Thingiverse 1985754; the lip + harness are your
      own additions and aren't captured anywhere yet.
