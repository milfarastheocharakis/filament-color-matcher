"""Export / import all user data (owned filaments, own designs, printed list) as an Excel file."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

from colors import line_of

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="3B5B92")


def _header(ws, cols: list[str], widths: list[int]) -> None:
    ws.append(cols)
    for i, w in enumerate(widths, start=1):
        cell = ws.cell(row=1, column=i)
        cell.font, cell.fill = HEADER_FONT, HEADER_FILL
        ws.column_dimensions[cell.column_letter].width = w
    ws.freeze_panes = "A2"


def export_backup(path: str | Path, owned: set[str], designs: list[dict], printed: set[str],
                  sheet_url: str = "", app_version: str = "") -> None:
    wb = Workbook()

    ws = wb.active
    ws.title = "My filaments"
    _header(ws, ["Color", "Type"], [34, 22])
    for c in sorted(owned, key=lambda c: ((line_of(c) or "zz"), c.casefold())):
        ws.append([c, line_of(c) or "Other"])

    ws = wb.create_sheet("My designs")
    max_colors = max([len(d.get("colors", [])) for d in designs] + [1])
    _header(ws, ["Name", "Category", "Printed"] + [f"Color {i}" for i in range(1, max_colors + 1)],
            [34, 20, 10] + [24] * max_colors)
    for d in designs:
        cat = d.get("category", "My designs")
        done = "yes" if f"{cat}|{d['name']}" in printed else ""
        ws.append([d["name"], cat, done] + list(d.get("colors", [])))

    ws = wb.create_sheet("Printed")
    _header(ws, ["Model", "Category"], [40, 22])
    for key in sorted(printed, key=str.casefold):
        cat, _, name = key.partition("|")
        ws.append([name, cat])

    ws = wb.create_sheet("Info")
    for row in (["Filament Color Matcher backup"], ["Exported", datetime.now().strftime("%Y-%m-%d %H:%M")],
                ["App version", app_version], ["Google Sheet link", sheet_url],
                [], ["Load this file with “Load backup…” in the app to restore everything."]):
        ws.append(row)
    ws["A1"].font = Font(bold=True, size=13)
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 80
    wb.save(path)


def _rows(wb, name: str):
    if name not in wb.sheetnames:
        return []
    rows = list(wb[name].iter_rows(values_only=True))[1:]
    return [[("" if v is None else str(v).strip()) for v in r] for r in rows]


def import_backup(path: str | Path) -> dict:
    """Returns {"owned": [...], "designs": [...], "printed": [...], "sheet_url": str|None}."""
    wb = load_workbook(path, read_only=True, data_only=True)
    if "My filaments" not in wb.sheetnames and "My designs" not in wb.sheetnames:
        raise ValueError("This doesn't look like a Filament Color Matcher backup.")
    owned = [r[0] for r in _rows(wb, "My filaments") if r and r[0]]
    designs, printed = [], set()
    for r in _rows(wb, "My designs"):
        if not r or not r[0]:
            continue
        name, cat = r[0], (r[1] if len(r) > 1 and r[1] else "My designs")
        colors = [c for c in r[3:] if c]
        if colors:
            designs.append({"name": name, "category": cat, "colors": colors})
        if len(r) > 2 and r[2].casefold() in ("yes", "y", "x", "true", "1", "✔", "☑"):
            printed.add(f"{cat}|{name}")
    for r in _rows(wb, "Printed"):
        if r and r[0]:
            printed.add(f"{r[1] if len(r) > 1 and r[1] else 'Google Sheet'}|{r[0]}")
    sheet_url = None
    if "Info" in wb.sheetnames:
        for r in wb["Info"].iter_rows(values_only=True):
            if r and r[0] == "Google Sheet link" and len(r) > 1:
                sheet_url = (r[1] or "").strip()
    wb.close()
    return {"owned": owned, "designs": designs, "printed": sorted(printed), "sheet_url": sheet_url}
