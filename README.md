# Filament Color Matcher

A small Windows app: tick the 3D-printing filament colors you own, and it tells you which models from the
[Pokéball / Pokémon color sheet](https://docs.google.com/spreadsheets/d/1iFt5MCwUX8yB8hIwSoFZDM_vs67eL0S78uYKMnQlBxI/edit?gid=516579939)
you can print right now.

## Download

Grab **FilamentColorMatcher.exe** from the [latest release](../../releases/latest) and run it. No install needed.

**Sharing with friends?** Send them
[FilamentColorMatcher-Shared.exe](https://github.com/milfarastheocharakis/filament-color-matcher/releases/latest/download/FilamentColorMatcher-Shared.exe):
the same app without the Pokéball sheet built in. They add their own designs (by hand or from .3mf) and can link
their own Google Sheet with **Refresh**. It keeps its data separately (`%APPDATA%\FilamentColorMatcherShared`).
(Windows SmartScreen may warn because the exe isn't signed: *More info → Run anyway*.)

## What it shows

- **Can print** – every model whose colors you all own.
- **Missing 1 color / Missing 2 colors** – near misses, with the exact colors you're missing.
- **≈ Similar colors** – models you could print by swapping a missing color for one you own from the
  same color family (e.g. Basic Orange → Matte Mandarin Orange). The *Swap* column says what to use.
- **☑ Printed** – everything you've marked as printed. Click the ☐ in the *Printed* column of any tab to
  tick a model as printed (click again to untick).
- **★ My designs** – your own designs, with your own category tag.
- **Best filament to buy next** – which single spool would unlock the most new models.
- **All models** – everything, sorted by how close you are.

## Adding your own designs

Click **+ Add my design**: type a name, pick a category/tag (e.g. "My designs"), and choose the colors from the
full Bambu Lab PLA Basic + Matte list (or type any name). Or click **Import .3mf…** / **Fill from .3mf file…**:
the name comes from the file name and the colors from the Bambu Studio project (the filaments the sliced
plates actually use, matched to the closest Bambu color); check them and save. Double-click one of your designs
in any tab to edit or delete it. Designs are saved in `%APPDATA%\FilamentColorMatcher\my_designs.json`.

Your ticked colors are saved automatically (`%APPDATA%\FilamentColorMatcher\settings.json`).

## Data

On start the app downloads the sheet live, so edits to the sheet show up after **Refresh**
(it opens a window with the sheet link prefilled, so you can paste a new one, then press **Refresh now**). If you're offline
it uses the last downloaded copy, or the copy bundled into the exe at build time. The sheet must be
shared as "Anyone with the link". You can also open a CSV with
**Load CSV file…**. Expected columns: `Printable?, Modell, <color>, <color>, …`.

## Run from source

```
python app.py          # Python 3.10+ with tkinter
python -m pytest tests # tests
```

Every push to `main` builds the exe on GitHub Actions and publishes it as a release.
