"""Bambu Lab PLA color catalog: approximate hex + color family (for swatches,
similar-color suggestions and 3MF import)."""
from __future__ import annotations

# name: (hex, family)
CATALOG: dict[str, tuple[str, str]] = {
    # PLA Basic
    "Basic Jade White": ("#FFFFFF", "white"),
    "Basic Beige": ("#F7E6DE", "beige/tan"),
    "Basic Light Gray": ("#D1D3D5", "gray"),
    "Basic Yellow": ("#F4EE2A", "yellow"),
    "Basic Sunflower Yellow": ("#FEC600", "yellow"),
    "Basic Pumpkin Orange": ("#FF9016", "orange"),
    "Basic Orange": ("#FF6A13", "orange"),
    "Basic Gold": ("#E4BD68", "gold"),
    "Basic Bright Green": ("#BECF00", "green"),
    "Basic Bambu Green": ("#00AE42", "green"),
    "Basic Mistletoe Green": ("#3F8E43", "green"),
    "Basic Pink": ("#F55A74", "pink"),
    "Basic Hot Pink": ("#F5547C", "pink"),
    "Basic Magenta": ("#EC008C", "pink"),
    "Basic Red": ("#C12E1F", "red"),
    "Basic Maroon Red": ("#9D2235", "red"),
    "Basic Purple": ("#5E43B7", "purple"),
    "Basic Indigo Purple": ("#482960", "purple"),
    "Basic Turquoise": ("#00B1B7", "turquoise/cyan"),
    "Basic Cyan": ("#0086D6", "turquoise/cyan"),
    "Basic Blue": ("#0A2989", "blue"),
    "Basic Cobalt Blue": ("#0056B8", "blue"),
    "Basic Brown": ("#9D432C", "brown"),
    "Basic Cocoa Brown": ("#6F5034", "brown"),
    "Basic Bronze": ("#847D48", "gold"),
    "Basic Gray": ("#8E9089", "gray"),
    "Basic Silver": ("#A6A9AA", "silver"),
    "Basic Blue Grey": ("#5B6579", "gray"),
    "Basic Dark Gray": ("#545454", "gray"),
    "Basic Black": ("#000000", "black"),
    # PLA Matte
    "Matte Ivory White": ("#FFFFFF", "white"),
    "Matte Bone White": ("#CBC6B8", "white"),
    "Matte Lemon Yellow": ("#F7D959", "yellow"),
    "Matte Mandarin Orange": ("#F99963", "orange"),
    "Matte Sakura Pink": ("#E8AFCF", "pink"),
    "Matte Lilac Purple": ("#AE96D4", "purple"),
    "Matte Plum": ("#950051", "purple"),
    "Matte Scarlet Red": ("#DE4343", "red"),
    "Matte Dark Red": ("#BB3D43", "red"),
    "Matte Apple Green": ("#C2E189", "green"),
    "Matte Grass Green": ("#61C680", "green"),
    "Matte Dark Green": ("#68724D", "green"),
    "Matte Ice Blue": ("#A3D8E1", "blue"),
    "Matte Sky Blue": ("#56B7E6", "blue"),
    "Matte Marine Blue": ("#0078BF", "blue"),
    "Matte Dark Blue": ("#042F56", "blue"),
    "Matte Desert Tan": ("#E8DBB7", "beige/tan"),
    "Matte Latte Brown": ("#D3B7A7", "beige/tan"),
    "Matte Caramel": ("#AE835B", "brown"),
    "Matte Terracotta": ("#B15533", "brown"),
    "Matte Dark Brown": ("#7D6556", "brown"),
    "Matte Dark Chocolate": ("#4D3324", "brown"),
    "Matte Ash Gray": ("#9B9EA0", "gray"),
    "Matte Nardo Gray": ("#757575", "gray"),
    "Matte Charcoal": ("#000000", "black"),
    # Gradients / specials seen in the sheet
    "Ocean to Meadow": ("#3FA8A0", "multicolor"),
}

FALLBACK = "#BBBBBB"
_BY_NORM = {" ".join(k.split()).casefold(): k for k in CATALOG}

# Keyword guesses for names that aren't in the catalog (e.g. other brands).
_FAMILY_WORDS = [
    ("white", "white"), ("ivory", "white"), ("black", "black"), ("charcoal", "black"),
    ("silver", "silver"), ("gold", "gold"), ("bronze", "gold"), ("grey", "gray"), ("gray", "gray"),
    ("yellow", "yellow"), ("lemon", "yellow"), ("orange", "orange"), ("mandarin", "orange"),
    ("pink", "pink"), ("magenta", "pink"), ("sakura", "pink"), ("purple", "purple"), ("lilac", "purple"),
    ("violet", "purple"), ("plum", "purple"), ("red", "red"), ("scarlet", "red"), ("maroon", "red"),
    ("turquoise", "turquoise/cyan"), ("cyan", "turquoise/cyan"), ("teal", "turquoise/cyan"),
    ("blue", "blue"), ("navy", "blue"), ("green", "green"), ("olive", "green"),
    ("beige", "beige/tan"), ("tan", "beige/tan"), ("latte", "beige/tan"), ("brown", "brown"),
    ("chocolate", "brown"), ("caramel", "brown"), ("terracotta", "brown"),
]


def canonical(name: str) -> str | None:
    return _BY_NORM.get(" ".join(name.split()).casefold())


def swatch(name: str) -> str:
    c = canonical(name)
    return CATALOG[c][0] if c else FALLBACK


def family(name: str) -> str | None:
    c = canonical(name)
    if c:
        return CATALOG[c][1]
    low = name.casefold()
    for word, fam in _FAMILY_WORDS:
        if word in low:
            return fam
    return None


def all_names() -> list[str]:
    return sorted(CATALOG, key=str.casefold)


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")[:6]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def nearest(hex_color: str, line: str | None = None) -> str:
    """Closest catalog color to a hex value; `line` ("Matte"/"Basic") narrows the search."""
    target = _rgb(hex_color)
    names = [n for n in CATALOG if line and n.startswith(line + " ")] or list(CATALOG)
    return min(names, key=lambda n: sum((a - b) ** 2 for a, b in zip(_rgb(CATALOG[n][0]), target)))
