"""Approximate swatch colors for common Bambu Lab filament names (display only)."""

SWATCHES = {
    "matte ivory white": "#FFFFF0", "matte charcoal": "#2B2B2D", "matte bone white": "#CBC6B8",
    "matte ice blue": "#A3D8E1", "matte dark green": "#3B6E3B", "basic mistletoe green": "#3F8E43",
    "basic bambu green": "#00AE42", "basic sunflower yellow": "#FEC600", "matte scarlet red": "#DE4343",
    "matte mandarin orange": "#F99963", "matte dark blue": "#042F56", "matte ash gray": "#9B9EA0",
    "basic hot pink": "#F5547C", "matte sakura pink": "#E8AFCF", "matte marine blue": "#0078BF",
    "matte grass green": "#61C680", "basic magenta": "#EC008C", "matte caramel": "#AE835B",
    "matte dark brown": "#7D6556", "basic pink": "#F55A74", "basic pumpkin orange": "#FF9016",
    "matte lemon yellow": "#F7D959", "matte desert tan": "#E8DBB7", "matte dark red": "#BB3D43",
    "matte sky blue": "#73B2E5", "basic cobalt blue": "#0056B8", "basic dark gray": "#545454",
    "basic brown": "#9D432C", "matte lilac purple": "#AE96D4", "matte latte brown": "#D3B7A7",
    "basic yellow": "#F4EE2A", "basic cocoa brown": "#6F5034", "basic turquoise": "#00B1B7",
    "matte dark chocolate": "#4D3324", "basic light gray": "#D1D3D5", "basic indigo purple": "#482960",
    "basic beige": "#F7E6DE", "matte terracotta": "#B15533", "basic blue grey": "#5B6579",
    "basic red": "#C12E1F", "basic orange": "#FF6A13", "matte nardo gray": "#757575",
    "basic gold": "#E4BD68", "basic silver": "#A6A9AA", "basic purple": "#5E43B7",
    "matte plum": "#950051", "matte apple green": "#C2E189", "basic cyan": "#0086D6",
    "basic blue": "#0A2989", "ocean to meadow": "#3FA8A0",
}

FALLBACK = "#BBBBBB"


def swatch(name: str) -> str:
    return SWATCHES.get(" ".join(name.split()).casefold(), FALLBACK)
