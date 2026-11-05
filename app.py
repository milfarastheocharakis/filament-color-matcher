"""Filament Color Matcher: tick the filaments you own, see which models you can print."""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from colors import LINE_ORDER, all_names, line_of, swatch
from edition import FRIENDS
from matcher import (Model, all_colors, best_next_colors, group_by_missing, norm, parse_sheet,
                     substitutes)
from threemf import read_3mf

APP_NAME = "Filament Color Matcher"
SHEET_ID = "1iFt5MCwUX8yB8hIwSoFZDM_vs67eL0S78uYKMnQlBxI"
SHEET_GID = "516579939"
DEFAULT_URL = "" if FRIENDS else f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
DEFAULT_CATEGORY = "My designs"
RESTORE_OWNED = [
    "Matte Ash Gray", "Basic Bambu Green", "Basic Beige", "Basic Dark Gray", "Basic Red",
    "Basic Sunflower Yellow", "Basic Yellow", "Matte Bone White", "Matte Caramel", "Matte Charcoal",
    "Matte Dark Blue", "Matte Dark Chocolate", "Matte Dark Green", "Matte Desert Tan", "Matte Ice Blue",
    "Matte Ivory White", "Matte Lilac Purple", "Matte Mandarin Orange", "Matte Marine Blue",
    "Matte Scarlet Red", "Matte Sky Blue",
]
ALL_CATEGORIES = "All categories"


def data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    d = Path(base) / ("FilamentColorMatcherShared" if FRIENDS else "FilamentColorMatcher")
    d.mkdir(parents=True, exist_ok=True)
    return d


def bundled_csv() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "data.csv"


SETTINGS = data_dir() / "settings.json"
CACHE = data_dir() / "sheet_cache.csv"
DESIGNS = data_dir() / "my_designs.json"


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        messagebox.showerror(APP_NAME, f"Couldn't save {path.name}:\n{exc}")


def fetch_sheet(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "FilamentColorMatcher/1.1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        text = r.read().decode("utf-8-sig")
    if not parse_sheet(text):
        raise ValueError("The sheet came back empty or not as CSV (is it shared publicly?)")
    return text


def to_edit_url(url: str) -> str:
    """Show the normal (browser) link for a CSV export link."""
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)/export", url or "")
    if not m:
        return url or ""
    g = re.search(r"gid=(\d+)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/edit" + (f"#gid={g.group(1)}" if g else "")


def to_csv_url(link: str) -> str:
    """Turn a normal Google Sheets link into its CSV export link."""
    if not link:
        return ""
    if "export?format=csv" in link or "output=csv" in link:
        return link
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", link)
    if not m:
        return link
    g = re.search(r"gid=(\d+)", link)
    url = f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
    return url + (f"&gid={g.group(1)}" if g else "")


def printed_key(m: Model) -> str:
    return f"{m.category}|{m.name}"


def center_on(win: tk.Toplevel, parent: tk.Misc) -> None:
    """Place a dialog in the middle of the main app window."""
    win.withdraw()
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    x = max(0, px + (pw - w) // 2)
    y = max(0, py + (ph - h) // 2)
    win.geometry(f"+{x}+{y}")
    win.deiconify()


class DesignDialog(tk.Toplevel):
    """Add or edit one of the user's own designs."""

    def __init__(self, app: "App", design: dict | None = None, preset: tuple[str, list[str]] | None = None):
        super().__init__(app)
        self.app = app
        self.original = design
        self.title("Edit my design" if design else "Add my design")
        self.transient(app)
        self.resizable(True, True)
        catalog = all_names()
        known = {norm(c) for c in catalog}
        self.color_names = catalog + sorted((c for c in all_colors(app.models) if norm(c) not in known),
                                            key=str.casefold)

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text="Name:").grid(row=0, column=0, sticky="w", pady=3)
        self.name = tk.StringVar(value=(design or {}).get("name", ""))
        ttk.Entry(body, textvariable=self.name, width=40).grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(body, text="Category / tag:").grid(row=1, column=0, sticky="w", pady=3)
        self.category = tk.StringVar(value=(design or {}).get("category", DEFAULT_CATEGORY))
        cats = sorted({d.get("category", DEFAULT_CATEGORY) for d in app.designs} | {DEFAULT_CATEGORY})
        ttk.Combobox(body, textvariable=self.category, values=cats).grid(row=1, column=1, sticky="ew", pady=3)

        hdr = ttk.Frame(body)
        hdr.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 2))
        ttk.Label(hdr, text="Colors needed:", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(hdr, text="Fill from .3mf file…", command=self.import_3mf).pack(side="right")
        ttk.Label(body, text="Pick from the list or type any name. Empty rows are ignored.",
                  foreground="#666").grid(row=3, column=0, columnspan=2, sticky="w")

        self.rows_frame = ttk.Frame(body)
        self.rows_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=4)
        body.rowconfigure(4, weight=1)
        self.rows: list[tuple[ttk.Frame, tk.StringVar]] = []
        ttk.Button(body, text="+ Add color", command=lambda: self.add_row("")).grid(
            row=5, column=0, sticky="w")

        bf = ttk.Frame(body)
        bf.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        if design:
            ttk.Button(bf, text="Delete design", command=self.delete).pack(side="left")
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(bf, text="Save", command=self.save).pack(side="right", padx=6)

        colors = (design or {}).get("colors", [])
        if preset:
            self.name.set(preset[0])
            colors = preset[1]
        for c in colors:
            self.add_row(c)
        for _ in range(max(0, 4 - len(colors))):
            self.add_row("")
        center_on(self, app)
        self.grab_set()

    def add_row(self, value: str) -> None:
        row = ttk.Frame(self.rows_frame)
        row.pack(fill="x", pady=2)
        var = tk.StringVar(value=value)
        sw = tk.Canvas(row, width=18, height=18, highlightthickness=1, highlightbackground="#888")
        rect = sw.create_rectangle(0, 0, 20, 20, fill=swatch(value) if value else "#FFFFFF", outline="")
        sw.pack(side="left", padx=(0, 6))
        cb = ttk.Combobox(row, textvariable=var, values=self.color_names, width=34)
        cb.pack(side="left", fill="x", expand=True)
        var.trace_add("write", lambda *_: sw.itemconfigure(rect, fill=swatch(var.get()) if var.get().strip() else "#FFFFFF"))
        entry = (row, var)

        def remove() -> None:
            row.destroy()
            self.rows.remove(entry)

        ttk.Button(row, text="✕", width=3, command=remove).pack(side="left", padx=4)
        self.rows.append(entry)

    def import_3mf(self) -> None:
        path = filedialog.askopenfilename(parent=self, filetypes=[("3MF project", "*.3mf"), ("All files", "*.*")])
        if not path:
            return
        try:
            name, colors = read_3mf(path)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Couldn't read that .3mf file:\n{exc}", parent=self)
            return
        if not self.name.get().strip():
            self.name.set(name)
        for row, _ in self.rows:
            row.destroy()
        self.rows.clear()
        for c in colors:
            self.add_row(c)
        if not colors:
            self.add_row("")
            messagebox.showinfo(APP_NAME, "No filament colors found in that file. Please add them by hand.", parent=self)
        else:
            messagebox.showinfo(APP_NAME, f"Found {len(colors)} colors. The names are matched to the closest "
                                "Bambu Lab color, so please check them before saving.", parent=self)

    def save(self) -> None:
        name = self.name.get().strip()
        colors: list[str] = []
        for _, var in self.rows:
            c = " ".join(var.get().split())
            if c and norm(c) not in {norm(x) for x in colors}:
                colors.append(c)
        if not name:
            messagebox.showwarning(APP_NAME, "Please give the design a name.", parent=self)
            return
        if not colors:
            messagebox.showwarning(APP_NAME, "Please add at least one color.", parent=self)
            return
        design = {"name": name, "category": self.category.get().strip() or DEFAULT_CATEGORY, "colors": colors}
        if self.original is not None and self.original in self.app.designs:
            self.app.designs[self.app.designs.index(self.original)] = design
            old = f"{self.original.get('category', DEFAULT_CATEGORY)}|{self.original['name']}"
            if old in self.app.printed:  # keep the Printed tick when renaming
                self.app.printed.discard(old)
                self.app.printed.add(f"{design['category']}|{design['name']}")
                self.app.settings["printed"] = sorted(self.app.printed)
                save_json(SETTINGS, self.app.settings)
        else:
            self.app.designs.append(design)
        self.app.designs_changed()
        self.destroy()

    def delete(self) -> None:
        if messagebox.askyesno(APP_NAME, f"Delete “{self.original['name']}”?", parent=self):
            self.app.designs.remove(self.original)
            self.app.designs_changed()
            self.destroy()


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1240x760")
        self.minsize(960, 580)
        self.settings = load_json(SETTINGS, {})
        self.sheet_url = self.settings.get("sheet_url", DEFAULT_URL)
        self.owned: set[str] = set(self.settings.get("owned", []))
        if not FRIENDS and not self.settings.get("restored_owned_v1"):
            # One-time restore of the filaments the user had ticked before they were cleared by accident.
            self.owned |= set(RESTORE_OWNED)
            self.settings["restored_owned_v1"] = True
            self.settings["owned"] = sorted(self.owned, key=str.casefold)
            save_json(SETTINGS, self.settings)
        self.designs: list[dict] = load_json(DESIGNS, [])
        self.sheet_models: list[Model] = []
        self.models: list[Model] = []
        self.color_vars: dict[str, tk.BooleanVar] = {}
        self.color_rows: dict[str, tk.Widget] = {}
        self.item_design: dict[str, dict] = {}
        self.item_model: dict[str, Model] = {}
        self.printed: set[str] = set(self.settings.get("printed", []))

        style = ttk.Style(self)
        try:
            style.theme_use("vista" if sys.platform == "win32" else "clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)
        style.configure("Big.TLabel", font=("Segoe UI", 13, "bold"))

        self._build_ui()
        self._rebuild_models()
        self._load_initial()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text=APP_NAME, style="Big.TLabel").pack(side="left")
        ttk.Button(top, text="+ Add my design", command=lambda: DesignDialog(self)).pack(side="left", padx=(16, 4))
        ttk.Button(top, text="Import .3mf…", command=self.quick_import_3mf).pack(side="left")
        self.status = ttk.Label(top, text="", foreground="#555")
        if not FRIENDS:  # the shared version has no Google Sheet / CSV, only your own designs
            ttk.Button(top, text="Refresh", command=self.refresh_dialog).pack(side="right", padx=4)
            self.status.pack(side="right", padx=12)

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left: owned colors
        left = ttk.Frame(paned, padding=4)
        paned.add(left, weight=1)
        ttk.Label(left, text="My filaments", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.owned_label = ttk.Label(left, text="", foreground="#555")
        self.owned_label.pack(anchor="w")
        srow = ttk.Frame(left)
        srow.pack(fill="x", pady=4)
        ttk.Label(srow, text="Find:").pack(side="left")
        self.color_search = tk.StringVar()
        self.color_search.trace_add("write", lambda *_: self._filter_colors())
        ttk.Entry(srow, textvariable=self.color_search).pack(side="left", fill="x", expand=True, padx=4)
        self.only_owned = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="Show only the ones I own", variable=self.only_owned,
                        command=self._filter_colors).pack(anchor="w", pady=(4, 0))

        canvas_frame = ttk.Frame(left)
        canvas_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0, width=300)
        sb = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.color_frame = ttk.Frame(self.canvas)
        self.color_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.color_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", lambda e: self._scroll_widget(e, -1))
        self.canvas.bind_all("<Button-5>", lambda e: self._scroll_widget(e, 1))

        # Right: results
        right = ttk.Frame(paned, padding=4)
        paned.add(right, weight=3)
        frow = ttk.Frame(right)
        frow.pack(fill="x")
        ttk.Label(frow, text="Search models:").pack(side="left")
        self.model_search = tk.StringVar()
        self.model_search.trace_add("write", lambda *_: self.update_results())
        ttk.Entry(frow, textvariable=self.model_search, width=28).pack(side="left", padx=4)
        ttk.Label(frow, text="Category:").pack(side="left", padx=(12, 0))
        self.cat_filter = tk.StringVar(value=ALL_CATEGORIES)
        self.cat_box = ttk.Combobox(frow, textvariable=self.cat_filter, state="readonly", width=22)
        self.cat_box.pack(side="left", padx=4)
        self.cat_box.bind("<<ComboboxSelected>>", lambda e: self.update_results())

        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True, pady=(6, 0))
        self.trees: dict[str, ttk.Treeview] = {}
        widths = {"Model": 210, "Category": 120, "Printed": 70, "Missing": 230, "Unlocks": 70,
                  "Filament to buy": 200, "Swap": 300}
        self.tab_frames: dict[str, ttk.Frame] = {}
        for key, cols in (
            ("all", ("Printed", "Model", "Category", "Missing", "Colors")),
            ("ready", ("Printed", "Model", "Category", "Colors")),
            ("similar", ("Printed", "Model", "Category", "Swap", "Colors")),
            ("miss1", ("Printed", "Model", "Category", "Missing", "Colors")),
            ("miss2", ("Printed", "Model", "Category", "Missing", "Colors")),
            ("buy", ("Filament to buy", "Unlocks", "Models")),
            ("mine", ("Printed", "Model", "Category", "Missing", "Colors")),
            ("printed", ("Printed", "Model", "Category", "Missing", "Colors")),
        ):
            frame = ttk.Frame(self.nb)
            tree = ttk.Treeview(frame, columns=cols, show="headings")
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=widths.get(c, 480), stretch=c in ("Colors", "Models"),
                            anchor="center" if c == "Printed" else "w")
            ysb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=ysb.set)
            tree.pack(side="left", fill="both", expand=True)
            ysb.pack(side="right", fill="y")
            tree.tag_configure("odd", background="#F5F7FA")
            tree.tag_configure("mine", foreground="#1A5FB4")
            tree.bind("<Double-1>", self._on_double_click)
            tree.bind("<Button-1>", self._on_click)
            self.nb.add(frame, text=key)
            self.trees[key] = tree
            self.tab_frames[key] = frame
        # "All" sits first, but the app opens on "Can print".
        self.nb.select(self.tab_frames["ready"])

        self.similar_note = ttk.Label(right, foreground="#666", wraplength=820, text=(
            "“Similar colors” = models you can print if you swap a missing color for one you own from the "
            "same color family (e.g. Basic Orange → Matte Mandarin Orange)."))

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab)

    def _on_tab(self, _e=None) -> None:
        if self.nb.select() == str(self.tab_frames["similar"]):
            self.similar_note.pack(anchor="w", pady=(4, 0))
        else:
            self.similar_note.pack_forget()

    def _on_wheel(self, e) -> None:
        self._scroll_widget(e, int(-e.delta / 120) or (-1 if e.delta > 0 else 1))

    def _scroll_widget(self, e, units: int) -> None:
        w = self.winfo_containing(e.x_root, e.y_root)
        while w is not None:
            if w is self.canvas:
                self.canvas.yview_scroll(units, "units")
                return
            if isinstance(w, ttk.Treeview):
                w.yview_scroll(units, "units")
                return
            if isinstance(w, tk.Toplevel):
                return
            w = w.master

    def _on_click(self, e):
        """Clicking the Printed cell toggles it."""
        tree = e.widget
        if tree.identify_region(e.x, e.y) != "cell":
            return None
        col = tree.identify_column(e.x)
        if tree.heading(col, "text") != "Printed":
            return None
        m = self.item_model.get(f"{id(tree)}:{tree.identify_row(e.y)}")
        if m is None:
            return None
        key = printed_key(m)
        if key in self.printed:
            self.printed.discard(key)
        else:
            self.printed.add(key)
        self.settings["printed"] = sorted(self.printed)
        save_json(SETTINGS, self.settings)
        y = tree.yview()[0]
        self.update_results()
        tree.yview_moveto(y)
        return "break"

    def _on_double_click(self, e) -> None:
        tree = e.widget
        if tree.heading(tree.identify_column(e.x), "text") == "Printed":
            return
        item = tree.identify_row(e.y)
        design = self.item_design.get(f"{id(tree)}:{item}")
        if design is not None:
            DesignDialog(self, design)

    def _build_color_list(self) -> None:
        for child in self.color_frame.winfo_children():
            child.destroy()
        self.color_vars.clear()
        self.color_rows.clear()
        self.color_groups: list[tuple[tk.Widget, list[str]]] = []
        counts = all_colors(self.models)
        known = {norm(c) for c in counts}
        # List every Bambu PLA/PETG color (even unused) so you can tick everything you own.
        for name in all_names():
            if norm(name) not in known:
                counts[name] = 0
                known.add(norm(name))
        groups: dict[str, list[str]] = {}
        for color in counts:
            groups.setdefault(line_of(color) or "Other", []).append(color)
        order = LINE_ORDER + ["Other"]
        owned_n = {norm(c) for c in self.owned}
        for line in sorted(groups, key=lambda g: order.index(g) if g in order else len(order)):
            header = ttk.Label(self.color_frame, text=line, font=("Segoe UI", 10, "bold"))
            names = groups[line] if line == "Other" else [n for n in all_names() if n in groups[line]]
            if line == "Other":
                names = sorted(names, key=str.casefold)
            for color in names:
                row = ttk.Frame(self.color_frame)
                sw = tk.Canvas(row, width=16, height=16, highlightthickness=1, highlightbackground="#888")
                sw.create_rectangle(0, 0, 18, 18, fill=swatch(color), outline="")
                sw.pack(side="left", padx=(8, 6))
                var = tk.BooleanVar(value=norm(color) in owned_n)
                label = f"{color}  ({counts[color]})" if counts[color] else color
                ttk.Checkbutton(row, text=label, variable=var, command=self._on_color_toggle).pack(side="left")
                self.color_vars[color] = var
                self.color_rows[color] = row
            self.color_groups.append((header, names))
        self._filter_colors()

    def _filter_colors(self) -> None:
        q = self.color_search.get().strip().casefold()
        only = self.only_owned.get()
        for child in self.color_frame.winfo_children():
            child.pack_forget()
        for header, names in self.color_groups:
            visible = [c for c in names
                       if (not q or q in c.casefold() or q in (line_of(c) or "").casefold())
                       and (not only or self.color_vars[c].get())]
            if not visible:
                continue
            header.pack(anchor="w", pady=(8, 2))
            for c in visible:
                self.color_rows[c].pack(fill="x", anchor="w", pady=1)
        self.canvas.yview_moveto(0)

    def _on_color_toggle(self) -> None:
        sheet_owned = {c for c, v in self.color_vars.items() if v.get()}
        known = {norm(c) for c in self.color_vars}
        extra = {c for c in self.owned if norm(c) not in known}
        self.owned = sheet_owned | extra
        self.settings["owned"] = sorted(self.owned, key=str.casefold)
        save_json(SETTINGS, self.settings)
        if self.only_owned.get():
            self._filter_colors()
        self.update_results()

    # ---------- results ----------
    def update_results(self) -> None:
        q = self.model_search.get().strip().casefold()
        cat = self.cat_filter.get()
        models = [m for m in self.models
                  if (not q or q in m.name.casefold()) and (cat == ALL_CATEGORIES or m.category == cat)]
        groups = group_by_missing(models, self.owned)
        ready = groups.get(0, [])
        miss1 = groups.get(1, [])
        miss2 = groups.get(2, [])
        similar = []
        for m in models:
            subs = substitutes(m, self.owned)
            if subs:
                swap = "; ".join(f"{k} → {' / '.join(v[:3])}" for k, v in subs.items())
                similar.append((m, swap))
        similar.sort(key=lambda t: (len(t[1].split(";")), t[0].name.casefold()))
        self.item_design.clear()
        self.item_model.clear()

        def pm(m: Model) -> str:
            return "☑" if printed_key(m) in self.printed else "☐"

        def catlabel(m: Model) -> str:
            return f"★ {m.category}" if m.custom else m.category

        def fill(key: str, rows) -> None:
            tree = self.trees[key]
            tree.delete(*tree.get_children())
            for i, (m, values) in enumerate(rows):
                tags = (("odd",) if i % 2 else ()) + (("mine",) if m is not None and m.custom else ())
                item = tree.insert("", "end", values=values, tags=tags)
                if m is not None:
                    self.item_model[f"{id(tree)}:{item}"] = m
                if m is not None and m.custom:
                    self.item_design[f"{id(tree)}:{item}"] = self._design_for(m)

        fill("ready", [(m, (pm(m), m.name, catlabel(m), ", ".join(m.colors))) for m, _ in ready])
        fill("similar", [(m, (pm(m), m.name, catlabel(m), s, ", ".join(m.colors))) for m, s in similar])
        fill("miss1", [(m, (pm(m), m.name, catlabel(m), ", ".join(x), ", ".join(m.colors))) for m, x in miss1])
        fill("miss2", [(m, (pm(m), m.name, catlabel(m), ", ".join(x), ", ".join(m.colors))) for m, x in miss2])
        buy = best_next_colors(models, self.owned)
        fill("buy", [(None, (c, n, ", ".join(names))) for c, n, names in buy])
        everything = sorted(((m, x) for k in groups for m, x in groups[k]),
                            key=lambda t: (len(t[1]), t[0].name.casefold()))
        mine = [(m, x) for m, x in everything if m.custom]
        fill("mine", [(m, (pm(m), m.name, catlabel(m), ", ".join(x) or "-", ", ".join(m.colors)))
                      for m, x in mine])
        done = sorted(((m, x) for m, x in everything if printed_key(m) in self.printed),
                      key=lambda t: t[0].name.casefold())
        fill("printed", [(m, (pm(m), m.name, catlabel(m), ", ".join(x) or "-", ", ".join(m.colors)))
                         for m, x in done])
        fill("all", [(m, (pm(m), m.name, catlabel(m), ", ".join(x) or "-", ", ".join(m.colors)))
                     for m, x in everything])

        t = self.tab_frames
        self.nb.tab(t["all"], text=f" All ({len(models)}) ")
        self.nb.tab(t["ready"], text=f" ✔ Can print ({len(ready)}) ")
        self.nb.tab(t["similar"], text=f" ≈ Similar colors ({len(similar)}) ")
        self.nb.tab(t["miss1"], text=f" Missing 1 ({len(miss1)}) ")
        self.nb.tab(t["miss2"], text=f" Missing 2 ({len(miss2)}) ")
        self.nb.tab(t["buy"], text=f" Buy next ({len(buy)}) ")
        self.nb.tab(t["mine"], text=f" ★ My designs ({len(mine)}) ")
        self.nb.tab(t["printed"], text=f" ☑ Printed ({len(done)}) ")
        self.owned_label.config(text=f"{len(self.owned)} selected · tick what you have on the shelf")

    def _design_for(self, m: Model) -> dict | None:
        for d in self.designs:
            if d.get("name") == m.name and d.get("category", DEFAULT_CATEGORY) == m.category:
                return d
        return None

    # ---------- data ----------
    def _rebuild_models(self) -> None:
        custom = [Model(d["name"], "", list(d.get("colors", [])), d.get("category", DEFAULT_CATEGORY), True)
                  for d in self.designs if d.get("name") and d.get("colors")]
        self.models = custom + self.sheet_models
        cats = [ALL_CATEGORIES] + sorted({m.category for m in self.models}, key=str.casefold)
        self.cat_box.configure(values=cats)
        if self.cat_filter.get() not in cats:
            self.cat_filter.set(ALL_CATEGORIES)
        self._build_color_list()
        self.update_results()

    def designs_changed(self) -> None:
        save_json(DESIGNS, self.designs)
        self._rebuild_models()

    def quick_import_3mf(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("3MF project", "*.3mf"), ("All files", "*.*")])
        if not path:
            return
        try:
            name, colors = read_3mf(path)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Couldn't read that .3mf file:\n{exc}")
            return
        # Open the editor pre-filled so the user can check names/colors before saving.
        DesignDialog(self, preset=(name, colors))

    def _set_models(self, text: str, source: str) -> None:
        models = parse_sheet(text)
        if not models:
            messagebox.showerror(APP_NAME, f"Couldn't find any models in {source}.")
            return
        self.sheet_models = models
        self._rebuild_models()
        self.status.config(text=f"{len(models)} sheet models · {source}")

    def _load_initial(self) -> None:
        if FRIENDS:
            return
        if not self.sheet_url:
            self.status.config(text="No Google Sheet linked · click Refresh to add one")
            return
        sources = [(CACHE, "last downloaded copy")] + ([] if FRIENDS else [(bundled_csv(), "built-in copy")])
        for path, label in sources:
            try:
                if path.exists():
                    self._set_models(path.read_text(encoding="utf-8-sig"), label)
                    break
            except Exception:
                continue
        self.refresh(quiet=True)

    def refresh(self, quiet: bool = False) -> None:
        self.status.config(text="Downloading sheet…")
        url = self.sheet_url

        def work() -> None:
            try:
                text = fetch_sheet(url)
                CACHE.write_text(text, encoding="utf-8")
                self.after(0, lambda: self._set_models(text, "live from Google Sheet"))
            except Exception as exc:
                msg = str(exc)

                def fail() -> None:
                    if self.sheet_models:
                        self.status.config(text=f"{len(self.sheet_models)} sheet models · offline copy")
                    else:
                        self.status.config(text="No sheet data")
                    if not quiet or not self.sheet_models:
                        messagebox.showwarning(APP_NAME, f"Couldn't download the sheet:\n{msg}")
                self.after(0, fail)

        threading.Thread(target=work, daemon=True).start()

    def refresh_dialog(self) -> None:
        win = tk.Toplevel(self)
        win.title("Refresh from Google Sheet")
        win.transient(self)
        win.resizable(True, False)
        body = ttk.Frame(win, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Google Sheet link", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(body, foreground="#666", text=(
            "Paste a new link here if the sheet changed. It must be shared as 'Anyone with the link can view'. "
            "Columns: Printable?, Modell, then the colors." + (" Leave it empty to use only your own designs."
                                                                if FRIENDS else "")),
                  wraplength=640).pack(anchor="w", pady=(2, 6))
        var = tk.StringVar(value=to_edit_url(self.sheet_url))
        entry = ttk.Entry(body, textvariable=var, width=95)
        entry.pack(fill="x")
        entry.focus_set()
        entry.select_range(0, "end")
        entry.icursor("end")

        def run() -> None:
            url = to_csv_url(var.get().strip())
            self.sheet_url = url
            self.settings["sheet_url"] = url
            save_json(SETTINGS, self.settings)
            win.destroy()
            if url:
                self.refresh()
            else:
                self.sheet_models = []
                try:
                    CACHE.unlink()
                except Exception:
                    pass
                self._rebuild_models()
                self.status.config(text="No Google Sheet linked · click Refresh to add one")

        bf = ttk.Frame(body)
        bf.pack(fill="x", pady=(12, 0))
        if DEFAULT_URL:
            ttk.Button(bf, text="Reset to default link",
                       command=lambda: var.set(to_edit_url(DEFAULT_URL))).pack(side="left")
        ttk.Button(bf, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(bf, text="Refresh now", command=run).pack(side="right", padx=6)
        win.bind("<Return>", lambda e: run())
        win.bind("<Escape>", lambda e: win.destroy())
        center_on(win, self)
        win.grab_set()

    def load_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            try:
                self._set_models(Path(path).read_text(encoding="utf-8-sig"), Path(path).name)
            except Exception as exc:
                messagebox.showerror(APP_NAME, str(exc))


if __name__ == "__main__":
    App().mainloop()
