"""Core logic: parse the filament sheet and match models against owned colors."""
from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Model:
    name: str
    status: str  # the sheet's "Printable?" column, shown as-is
    colors: list[str] = field(default_factory=list)


def norm(color: str) -> str:
    """Normalize a color name for comparison (case/spacing-insensitive)."""
    return " ".join(color.split()).casefold()


def parse_sheet(text: str) -> list[Model]:
    """Parse the sheet CSV. Expected columns: Printable?, Modell, color columns..."""
    text = text.lstrip("﻿")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    header = [h.strip().casefold() for h in rows[0]]
    # Locate the model column; fall back to column 1.
    model_idx = next((i for i, h in enumerate(header) if h in ("modell", "model", "name")), 1)
    status_idx = 0 if model_idx != 0 else None
    models: list[Model] = []
    for row in rows[1:]:
        if len(row) <= model_idx:
            continue
        name = row[model_idx].strip()
        if not name:
            continue
        colors: list[str] = []
        seen = set()
        for c in row[model_idx + 1:]:
            c = " ".join(c.split())
            if c and norm(c) not in seen:
                seen.add(norm(c))
                colors.append(c)
        if not colors:
            continue
        status = row[status_idx].strip() if status_idx is not None and len(row) > status_idx else ""
        models.append(Model(name, status, colors))
    return models


def all_colors(models: list[Model]) -> Counter:
    """Count how many models use each color (keyed by display name)."""
    counts: Counter = Counter()
    display: dict[str, str] = {}
    for m in models:
        for c in m.colors:
            display.setdefault(norm(c), c)
            counts[display[norm(c)]] += 1
    return counts


def missing_colors(model: Model, owned: set[str]) -> list[str]:
    owned_n = {norm(c) for c in owned}
    return [c for c in model.colors if norm(c) not in owned_n]


def group_by_missing(models: list[Model], owned: set[str]) -> dict[int, list[tuple[Model, list[str]]]]:
    """Map number-of-missing-colors -> [(model, missing colors)]."""
    out: dict[int, list[tuple[Model, list[str]]]] = {}
    for m in models:
        miss = missing_colors(m, owned)
        out.setdefault(len(miss), []).append((m, miss))
    return out


def best_next_colors(models: list[Model], owned: set[str]) -> list[tuple[str, int, list[str]]]:
    """For each color you don't own: how many extra models it would unlock on its own.

    Returns [(color, unlock_count, [model names])] sorted by unlock_count desc.
    """
    unlocks: dict[str, list[str]] = {}
    for m in models:
        miss = missing_colors(m, owned)
        if len(miss) == 1:
            unlocks.setdefault(miss[0], []).append(m.name)
    return sorted(((c, len(n), n) for c, n in unlocks.items()), key=lambda t: (-t[1], t[0]))
