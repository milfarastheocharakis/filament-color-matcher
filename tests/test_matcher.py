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
