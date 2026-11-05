"""Read the filament colors out of a Bambu Studio / Orca .3mf project file."""
from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from colors import canonical, nearest

# Bambu filament ids -> product line
_LINE_BY_ID = {"GFA00": "Basic", "GFA01": "Matte"}


def _line(settings_id: str, fil_id: str) -> str | None:
    s = settings_id.casefold()
    if "matte" in s:
        return "Matte"
    if "basic" in s:
        return "Basic"
    return _LINE_BY_ID.get(fil_id)


def read_3mf(path: str | Path) -> tuple[str, list[str]]:
    """Return (design name from file name, [Bambu color names]) for a .3mf file.

    Uses the filaments actually used by the sliced plates when the file contains slice
    info; otherwise all filaments configured in the project.
    """
    path = Path(path)
    name = re.sub(r"[_]+", " ", path.stem).strip()
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        settings: dict = {}
        if "Metadata/project_settings.config" in names:
            try:
                settings = json.loads(z.read("Metadata/project_settings.config").decode("utf-8"))
            except Exception:
                settings = {}
        hexes = list(settings.get("filament_colour", []))
        setting_ids = list(settings.get("filament_settings_id", []))
        fil_ids = list(settings.get("filament_ids", []))

        used_idx: list[int] | None = None
        if "Metadata/slice_info.config" in names:
            try:
                root = ET.fromstring(z.read("Metadata/slice_info.config"))
                seen: list[int] = []
                extra_hex: dict[int, str] = {}
                for f in root.iter("filament"):
                    i = int(f.get("id", "0")) - 1
                    if i >= 0 and i not in seen:
                        seen.append(i)
                        if f.get("color"):
                            extra_hex[i] = f.get("color")
                if seen:
                    used_idx = sorted(seen)
                    for i, h in extra_hex.items():
                        while len(hexes) <= i:
                            hexes.append("")
                        if not hexes[i]:
                            hexes[i] = h
            except Exception:
                used_idx = None

    if used_idx is None:
        used_idx = list(range(len(hexes)))

    colors: list[str] = []
    for i in used_idx:
        if i >= len(hexes) or not hexes[i]:
            continue
        sid = setting_ids[i] if i < len(setting_ids) else ""
        fid = fil_ids[i] if i < len(fil_ids) else ""
        c = nearest(hexes[i], _line(sid, fid))
        if c not in colors:
            colors.append(c)
    return name, colors
