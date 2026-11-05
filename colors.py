"""Bambu Lab filament color catalog: approximate hex + color family, grouped by product line.

Used for the filament list, swatches, similar-color suggestions and 3MF import.
Hex values are approximations for display only.
"""
from __future__ import annotations

# (line label, name prefix, [(color, hex, family or None = guess from name)])
# PLA Basic / PLA Matte keep the "Basic X" / "Matte X" names used in the Google Sheet.
LINES: list[tuple[str, str, list[tuple[str, str, str | None]]]] = [
    ("PLA Basic", "Basic", [
        ("Jade White", "#FFFFFF", "white"), ("Beige", "#F7E6DE", "beige/tan"), ("Light Gray", "#D1D3D5", "gray"),
        ("Yellow", "#F4EE2A", None), ("Sunflower Yellow", "#FEC600", None), ("Pumpkin Orange", "#FF9016", None),
        ("Orange", "#FF6A13", None), ("Gold", "#E4BD68", "gold"), ("Bright Green", "#BECF00", None),
        ("Bambu Green", "#00AE42", None), ("Mistletoe Green", "#3F8E43", None), ("Pink", "#F55A74", None),
        ("Hot Pink", "#F5547C", None), ("Magenta", "#EC008C", "pink"), ("Red", "#C12E1F", None),
        ("Maroon Red", "#9D2235", None), ("Purple", "#5E43B7", None), ("Indigo Purple", "#482960", None),
        ("Turquoise", "#00B1B7", None), ("Cyan", "#0086D6", None), ("Blue", "#0A2989", None),
        ("Cobalt Blue", "#0056B8", None), ("Brown", "#9D432C", None), ("Cocoa Brown", "#6F5034", None),
        ("Bronze", "#847D48", "gold"), ("Gray", "#8E9089", None), ("Silver", "#A6A9AA", "silver"),
        ("Blue Grey", "#5B6579", "gray"), ("Dark Gray", "#545454", None), ("Black", "#000000", None),
    ]),
    ("PLA Basic Gradient", "", [
        ("Arctic Whisper", "#C9E4F2", "multicolor"), ("Solar Breeze", "#F6B44B", "multicolor"),
        ("Ocean to Meadow", "#3FA8A0", "multicolor"), ("Pink Citrus", "#F68A8A", "multicolor"),
        ("Mint Lime", "#A8E0A0", "multicolor"), ("Blueberry Bubblegum", "#8C8FE0", "multicolor"),
        ("Dusk Glare", "#E07A5F", "multicolor"), ("Cotton Candy Cloud", "#F3B6D8", "multicolor"),
    ]),
    ("PLA Matte", "Matte", [
        ("Ivory White", "#FFFFFF", "white"), ("Bone White", "#CBC6B8", "white"), ("Desert Tan", "#E8DBB7", "beige/tan"),
        ("Latte Brown", "#D3B7A7", "beige/tan"), ("Caramel", "#AE835B", "brown"), ("Terracotta", "#B15533", "brown"),
        ("Dark Brown", "#7D6556", None), ("Dark Chocolate", "#4D3324", "brown"), ("Lemon Yellow", "#F7D959", None),
        ("Mandarin Orange", "#F99963", None), ("Sakura Pink", "#E8AFCF", None), ("Lilac Purple", "#AE96D4", None),
        ("Plum", "#950051", "purple"), ("Scarlet Red", "#DE4343", None), ("Dark Red", "#BB3D43", None),
        ("Apple Green", "#C2E189", None), ("Grass Green", "#61C680", None), ("Dark Green", "#68724D", None),
        ("Ice Blue", "#A3D8E1", None), ("Sky Blue", "#56B7E6", None), ("Marine Blue", "#0078BF", None),
        ("Dark Blue", "#042F56", None), ("Ash Gray", "#9B9EA0", None), ("Nardo Gray", "#757575", None),
        ("Charcoal", "#000000", "black"),
    ]),
    ("PLA Silk+", "Silk+", [
        ("White", "#F2F2F2", None), ("Gold", "#F4A925", "gold"), ("Silver", "#C8C8C8", "silver"),
        ("Titan Gray", "#5F6367", "gray"), ("Champagne", "#F3CFB2", "gold"), ("Rose Gold", "#BA9594", "gold"),
        ("Pink", "#F7ADA6", None), ("Candy Red", "#D02727", None), ("Purple", "#8671CB", None),
        ("Blue", "#008BDA", None), ("Baby Blue", "#AEC3ED", "blue"), ("Mint", "#96DCB9", "green"),
        ("Candy Green", "#018814", "green"),
    ]),
    ("PLA Silk Multi-Color", "Silk", [
        ("Dawn Radiance", "#F4B6B6", "multicolor"), ("Aurora Purple", "#7F3696", "multicolor"),
        ("South Beach", "#4FC3D0", "multicolor"), ("Neon City", "#0047BB", "multicolor"),
        ("Midnight Blaze", "#0047BB", "multicolor"), ("Gilded Rose", "#ED8F9D", "multicolor"),
        ("Blue Hawaii", "#3AB0E8", "multicolor"), ("Velvet Eclipse", "#2A1A3A", "multicolor"),
    ]),
    ("PLA Metal", "Metal", [
        ("Iron Gray Metallic", "#43403D", "gray"), ("Iridium Gold Metallic", "#B39B84", "gold"),
        ("Copper Brown Metallic", "#AA6443", "brown"), ("Cobalt Blue Metallic", "#39699E", "blue"),
        ("Oxide Green Metallic", "#1D7C6A", "green"),
    ]),
    ("PLA Sparkle", "Sparkle", [
        ("Onyx Black", "#2D2B28", "black"), ("Classic Gold", "#E4BD68", "gold"), ("Crimson Red", "#792B36", "red"),
        ("Royal Purple", "#483D8B", "purple"), ("Slate Gray", "#8E9089", "gray"), ("Alpine Green", "#3F5443", "green"),
    ]),
    ("PLA Marble", "Marble", [
        ("White Marble", "#F7F3F0", "white"), ("Red Granite", "#AD4E38", "red"),
    ]),
    ("PLA Galaxy", "Galaxy", [
        ("Purple", "#594177", None), ("Green", "#3B665E", None), ("Nebulae", "#424379", "blue"),
        ("Brown", "#684A43", None),
    ]),
    ("PLA Glow", "Glow", [
        ("Green", "#A1FFAC", None), ("Blue", "#7AC0E9", None), ("Pink", "#F17B8F", None),
        ("Orange", "#FF9D5B", None), ("Yellow", "#F8FF80", None),
    ]),
    ("PLA Translucent", "PLA Translucent", [
        ("Clear", "#E8E8E8", "clear"), ("Light Jade", "#A4D6AD", "green"), ("Mellow Yellow", "#F5DB79", "yellow"),
        ("Cherry Pink", "#E9B6CC", "pink"), ("Orange", "#FF8F3D", None), ("Red", "#C13C3C", None),
        ("Purple", "#8E44AD", None), ("Blue", "#2A6FC9", None), ("Ice Blue", "#B5E3F2", None),
        ("Teal", "#1EA8A0", None),
    ]),
    ("PLA Wood", "Wood", [
        ("Black Walnut", "#4F3F24", "brown"), ("Rosewood", "#4C241C", "brown"), ("Clay Brown", "#995F11", "brown"),
        ("Classic Birch", "#918669", "beige/tan"), ("White Oak", "#D2CCA2", "beige/tan"),
        ("Ochre Yellow", "#C98935", "yellow"),
    ]),
    ("PLA-CF", "PLA-CF", [
        ("Black", "#000000", None), ("Lava Gray", "#4D5054", "gray"), ("Burgundy Red", "#951E23", "red"),
        ("Jeans Blue", "#6E88BC", "blue"), ("Royal Blue", "#2842AD", "blue"), ("Iris Purple", "#69398E", "purple"),
        ("Matcha Green", "#5C9748", "green"),
    ]),
    ("PLA Tough+", "Tough+", [
        ("Black", "#000000", None), ("White", "#FFFFFF", None), ("Gray", "#8E9089", None),
        ("Yellow", "#FFD00B", None), ("Cyan", "#0086D6", None), ("Orange", "#FF6A13", None),
    ]),
    ("PETG HF", "PETG HF", [
        ("Black", "#000000", None), ("White", "#FFFFFF", None), ("Gray", "#ADB1B2", None),
        ("Dark Gray", "#515151", None), ("Cream", "#F3E0B8", "beige/tan"), ("Peanut Brown", "#875718", "brown"),
        ("Yellow", "#FFD00B", None), ("Orange", "#F75403", None), ("Red", "#EB3A3A", None),
        ("Green", "#00AE42", None), ("Lime Green", "#6EE53C", None), ("Forest Green", "#39541A", None),
        ("Blue", "#002E96", None),
    ]),
    ("PETG Translucent", "PETG Translucent", [
        ("Clear", "#E8E8E8", "clear"), ("Gray", "#8E8E8E", None), ("Brown", "#C9A381", None),
        ("Orange", "#FF911A", None), ("Pink", "#F9C1BD", None), ("Purple", "#D6ABFF", None),
        ("Light Blue", "#61B0FF", "blue"), ("Teal", "#77EDD7", None), ("Olive", "#748C45", "green"),
    ]),
    ("PETG-CF", "PETG-CF", [
        ("Black", "#000000", None), ("Titan Gray", "#565656", "gray"), ("Brick Red", "#9F332A", "red"),
        ("Indigo Blue", "#324585", "blue"), ("Malachite Green", "#16B08E", "green"),
        ("Violet Purple", "#583061", "purple"),
    ]),
]

FALLBACK = "#BBBBBB"

# Keyword guesses for names without an explicit family (and names not in the catalog).
_FAMILY_WORDS = [
    ("white", "white"), ("ivory", "white"), ("black", "black"), ("charcoal", "black"), ("onyx", "black"),
    ("silver", "silver"), ("gold", "gold"), ("bronze", "gold"), ("grey", "gray"), ("gray", "gray"),
    ("yellow", "yellow"), ("lemon", "yellow"), ("orange", "orange"), ("mandarin", "orange"),
    ("pink", "pink"), ("magenta", "pink"), ("sakura", "pink"), ("purple", "purple"), ("lilac", "purple"),
    ("violet", "purple"), ("plum", "purple"), ("red", "red"), ("scarlet", "red"), ("maroon", "red"),
    ("burgundy", "red"), ("turquoise", "turquoise/cyan"), ("cyan", "turquoise/cyan"), ("teal", "turquoise/cyan"),
    ("blue", "blue"), ("navy", "blue"), ("azure", "blue"), ("green", "green"), ("olive", "green"),
    ("lime", "green"), ("mint", "green"), ("jade", "green"), ("beige", "beige/tan"), ("cream", "beige/tan"),
    ("tan", "beige/tan"), ("latte", "beige/tan"), ("brown", "brown"), ("chocolate", "brown"),
    ("caramel", "brown"), ("terracotta", "brown"), ("clear", "clear"),
]


def _guess_family(name: str) -> str | None:
    low = name.casefold()
    for word, fam in _FAMILY_WORDS:
        if word in low:
            return fam
    return None


CATALOG: dict[str, tuple[str, str | None]] = {}  # name -> (hex, family)
LINE_OF: dict[str, str] = {}  # name -> line label
for _line, _prefix, _colors in LINES:
    for _color, _hex, _fam in _colors:
        _name = f"{_prefix} {_color}".strip()
        CATALOG[_name] = (_hex, _fam or _guess_family(_color))
        LINE_OF[_name] = _line
LINE_ORDER = [line for line, _, _ in LINES]

_BY_NORM = {" ".join(k.split()).casefold(): k for k in CATALOG}


def canonical(name: str) -> str | None:
    return _BY_NORM.get(" ".join(name.split()).casefold())


def swatch(name: str) -> str:
    c = canonical(name)
    return CATALOG[c][0] if c else FALLBACK


def family(name: str) -> str | None:
    c = canonical(name)
    if c:
        return CATALOG[c][1]
    return _guess_family(name)


def line_of(name: str) -> str | None:
    c = canonical(name)
    return LINE_OF[c] if c else None


def all_names() -> list[str]:
    return list(CATALOG)


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")[:6]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def nearest(hex_color: str, line: str | None = None) -> str:
    """Closest catalog color to a hex value; `line` (e.g. "PLA Matte") narrows the search."""
    target = _rgb(hex_color)
    names = [n for n in CATALOG if line and LINE_OF[n] == line] or list(CATALOG)
    return min(names, key=lambda n: sum((a - b) ** 2 for a, b in zip(_rgb(CATALOG[n][0]), target)))
