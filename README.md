# Filament Color Matcher

A small Windows app: tick the 3D-printing filament colors you own, and it tells you which models from the
[Pokéball / Pokémon color sheet](https://docs.google.com/spreadsheets/d/1iFt5MCwUX8yB8hIwSoFZDM_vs67eL0S78uYKMnQlBxI/edit?gid=516579939)
you can print right now.

## Download

Grab **FilamentColorMatcher.exe** from the [latest release](../../releases/latest) and run it. No install needed.
(Windows SmartScreen may warn because the exe isn't signed: *More info → Run anyway*.)

## What it shows

- **Can print** – every model whose colors you all own.
- **Missing 1 color / Missing 2 colors** – near misses, with the exact colors you're missing.
- **Best filament to buy next** – which single spool would unlock the most new models.
- **All models** – everything, sorted by how close you are.

Your ticked colors are saved automatically (`%APPDATA%\FilamentColorMatcher\settings.json`).

## Data

On start the app downloads the sheet live, so edits to the sheet show up after **Refresh**. If you're offline
it uses the last downloaded copy, or the copy bundled into the exe at build time. You can point it at
another sheet with **Sheet link…** (must be shared as "Anyone with the link"), or open a CSV with
**Load CSV file…**. Expected columns: `Printable?, Modell, <color>, <color>, …`.

## Run from source

```
python app.py          # Python 3.10+ with tkinter
python -m pytest tests # tests
```

Every push to `main` builds the exe on GitHub Actions and publishes it as a release.
