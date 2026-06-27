# PrusaSlicer — Klipper conversion checklist (Prusa MK2.5S)

Apply these on your PC. PrusaSlicer's GUI can't be automated from here, so this is the exact
click-path plus the G-code snippets (in the two `.txt` files next to this one) to paste in.

> The `PRINT_START` macro already defaults to `PRINTER_MODEL="MK2.5S"` (with the PINDA heat-soak path),
> so the start G-code works even without the model argument — but the provided snippet passes it
> explicitly so you can also slice for other machines from the same PrusaSlicer install.

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
8. **Detach + rename the other presets.** Detach **Print Settings** and **Filament** presets from the
   MK2.5S system presets too, and rename them for Klipper use (so system updates can't clobber them).

## Per-filament (do for each filament you use)

9. **Pressure advance per filament.** Filament Settings → Custom G-code → **Start G-code**, add:
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
