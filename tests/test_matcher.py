from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from matcher import parse_sheet, group_by_missing, best_next_colors, all_colors

TEXT = (Path(__file__).parent / "sample.csv").read_text(encoding="utf-8")

def test_parse():
    ms = parse_sheet(TEXT)
    assert len(ms) == 9
    assert ms[0].name == "#0001 - Bulbasaur" and ms[0].status == "1"
    assert ms[1].status == "✔" and ms[1].colors == ["Matte Grass Green", "Matte Charcoal", "Matte Ivory White"]

def test_match_case_insensitive():
    ms = parse_sheet(TEXT)
    g = group_by_missing(ms, {"matte scarlet red", "Matte Ivory White", "Matte Charcoal"})
    assert sorted(m.name for m, _ in g[0]) == ["#0100 - Voltorb", "Cherish Ball", "Premier Ball"]
    one = {m.name: x for m, x in g[1]}
    assert one["Great Ball"] == ["Matte Marine Blue"]

def test_best_next():
    ms = parse_sheet(TEXT)
    b = best_next_colors(ms, {"Matte Scarlet Red", "Matte Ivory White", "Matte Charcoal"})
    assert ("Matte Marine Blue", 1, ["Great Ball"]) in b
    assert all_colors(ms)["Matte Charcoal"] == 8


def test_similar_colors():
    from matcher import Model, substitutes
    m = Model("Fox", "", ["Basic Orange", "Matte Charcoal"])
    subs = substitutes(m, {"Matte Mandarin Orange", "Matte Charcoal"})
    assert subs == {"Basic Orange": ["Matte Mandarin Orange"]}
    assert substitutes(m, {"Matte Charcoal"}) is None  # no orange owned
    assert substitutes(Model("x", "", ["Matte Charcoal"]), {"Matte Charcoal"}) is None  # nothing missing


def test_read_3mf(tmp_path):
    import json, zipfile
    from threemf import read_3mf
    p = tmp_path / "My_Cool_Fox.3mf"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Metadata/project_settings.config", json.dumps({
            "filament_colour": ["#F99963", "#000000", "#FFFFFF", "#FF6A13"],
            "filament_settings_id": ["Bambu PLA Matte @BBL A1", "Bambu PLA Matte @BBL A1",
                                     "Bambu PLA Matte @BBL A1", "Bambu PLA Basic @BBL A1"],
        }))
        z.writestr("Metadata/slice_info.config",
                   '<config><plate><filament id="1" color="#F99963"/><filament id="2" color="#000000"/>'
                   '<filament id="4" color="#FF6A13"/></plate></config>')
    name, colors = read_3mf(p)
    assert name == "My Cool Fox"
    assert colors == ["Matte Mandarin Orange", "Matte Charcoal", "Basic Orange"]


def test_read_3mf_unsliced(tmp_path):
    import json, zipfile
    from threemf import read_3mf
    p = tmp_path / "a.3mf"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Metadata/project_settings.config", json.dumps({
            "filament_colour": ["#FFFFFF", "#000000"], "filament_settings_id": ["Bambu PLA Basic @BBL X1C"] * 2}))
    assert read_3mf(p)[1] == ["Basic Jade White", "Basic Black"]


def test_petg_import_and_no_cross_material(tmp_path):
    import json, zipfile
    from threemf import read_3mf
    from matcher import Model, substitutes
    p = tmp_path / "b.3mf"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Metadata/project_settings.config", json.dumps({
            "filament_colour": ["#EB3A3A", "#F2F2F2"],
            "filament_settings_id": ["Bambu PETG HF @BBL X1C", "Bambu PLA Silk+ @BBL X1C"]}))
    assert read_3mf(p)[1] == ["PETG HF Red", "Silk+ White"]
    # A PETG red is not offered as a swap for a missing PLA red.
    assert substitutes(Model("x", "", ["Basic Red"]), {"PETG HF Red"}) is None
    assert substitutes(Model("x", "", ["Basic Red"]), {"Matte Scarlet Red"}) == {"Basic Red": ["Matte Scarlet Red"]}
