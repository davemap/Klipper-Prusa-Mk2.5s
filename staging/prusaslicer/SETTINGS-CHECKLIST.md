# PrusaSlicer — Klipper conversion (Prusa MK2.5S + Revo 0.4mm)

> The `PRINT_START` macro already defaults to `PRINTER_MODEL="MK2.5S"` (with the PINDA heat-soak path),
> so the start G-code works even without the model argument — but the provided snippet passes it
> explicitly so you can also slice for other machines from the same PrusaSlicer install.

## FAST PATH — import the ready-made printer profile (recommended)
A finished **printer** profile is provided: [`MK2.5S-Klipper-printer.ini`](MK2.5S-Klipper-printer.ini),
preset for the **0.4 mm Revo**. It already encodes everything in the manual list below (Klipper flavor,
START/END g-code, arc-fitting off, no binary g-code, MK2.5S bed/limits, Mainsail thumbnails, object
labels for cancel-object).

1. **Add the MK2.5S once** via Configuration Wizard (so you get Prusa's tuned MK2.5S **Print + Filament**
   0.4mm presets — we don't recreate those). Switch to **Expert** mode.
2. **File → Import → Import Config Bundle…** → pick `MK2.5S-Klipper-printer.ini`.
3. Select printer preset **"MK2.5S Klipper SKR Revo 0.4"**, then pick a Prusa **MK2.5S 0.4mm Print**
   preset and a **Filament** preset. If they look hidden, untick **"Compatible only"** in those
   dropdowns (the printer is custom, so the compatibility filter may hide them — they still work).
4. Do the **per-filament pressure advance** step (#9 below) for each filament.

> Nozzle swaps: the profile is 0.4mm. For another size, change `nozzle_diameter` in Printer Settings
> AND switch to a matching-size Print preset.

If you'd rather click through it by hand (or to verify the import), the full path is below.

---

## Manual path / verification
Apply these on your PC. The G-code snippets are in the two `.txt` files next to this one.

## One-time setup

1. **Add the printer.** Configuration Wizard → add the **Prusa MK2.5S** profile (correct bed size
   250×210×210 and origin). Switch PrusaSlicer to **Expert** mode (top-right).
2. **Detach the printer preset.** Printer Settings → Dependencies → **Detach from system preset**.
   Rename it, e.g. **"MK2.5S Klipper"**, and save.
3. **G-code flavor.** Printer Settings → General → Firmware → **G-code flavor = Klipper**.
4. **Binary G-code.** Same page → **uncheck "Supports binary G-code"** (if present).
5. **Custom G-code boxes.** Printer Settings → Custom G-code:
   - **Clear ALL boxes** (Start, End, Before/After layer change, Tool change, etc.).
   - **Uncheck "Emit temperature commands automatically"** (PRINT_START handles heating).
6. **Paste Start/End G-code:**
   - **Start G-code** ← contents of [`start-gcode-MK25S.txt`](start-gcode-MK25S.txt):
     ```
     PRINT_START EXTRUDER_TEMP=[first_layer_temperature] BED_TEMP=[first_layer_bed_temperature] PRINTER_MODEL="MK2.5S"
     ```
   - **End G-code** ← contents of [`end-gcode.txt`](end-gcode.txt):
     ```
     PRINT_END
     ```
7. **Arc fitting OFF.** Print Settings → Advanced → **disable "Arc fitting"** (no G2/G3 to Klipper here).
8. **Klipper/Mainsail niceties** (Printer Settings → General, unless noted):
   - **Machine limits → usage = "Use for time estimate only"** (don't emit M201/M203 — Klipper owns limits).
   - **Thumbnails** (Printer Settings → General → Thumbnails): `32x32,400x300`, format **PNG** → Mainsail previews.
   - **Label objects** (Output options → "Label objects" = **Firmware/Klipper**) → enables Mainsail's
     cancel-object (pairs with `[exclude_object]` in printer.cfg).
   - **Supports remaining times = OFF** (M73 isn't a built-in Klipper command; progress still shows in
     Mainsail/KlipperScreen). Turn on only if you add an M73 macro.
9. **Detach + rename the other presets.** Detach **Print Settings** and **Filament** presets from the
   MK2.5S system presets too, and rename them for Klipper use (so system updates can't clobber them).

## Per-filament (do for each filament you use)

10. **Pressure advance per filament.** Filament Settings → Custom G-code → **Start G-code**, add:
   ```
   SET_PRESSURE_ADVANCE ADVANCE=0.0XX
   ```
   - `0.0XX` is **TODO** — from Ellis PA tuning on the printer, **re-tuned after input shaping**.
   - Preferred over a global value in `printer.cfg` (kept commented there).

## Nozzle / filament sanity
- This printer has a **0.4 mm** Revo nozzle → keep PrusaSlicer's **0.40 mm nozzle** print profiles.

## Speed/accel note
- Machine limits live in **Klipper** (`printer.cfg [printer]`), not here. The config ships with the
  **stock MK2.5S limits** (max_accel 1000) as a safe default; raise to the faster input-shaping
  profile in `printer.cfg` only after input shaping is done. You don't need to mirror these in the slicer.
