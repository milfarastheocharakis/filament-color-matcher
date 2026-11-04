"""Filament Color Matcher: tick the filaments you own, see which models you can print."""
from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matcher import Model, all_colors, best_next_colors, group_by_missing, norm, parse_sheet
from swatches import swatch

APP_NAME = "Filament Color Matcher"
SHEET_ID = "1iFt5MCwUX8yB8hIwSoFZDM_vs67eL0S78uYKMnQlBxI"
SHEET_GID = "516579939"
DEFAULT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"


def data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    d = Path(base) / "FilamentColorMatcher"
    d.mkdir(parents=True, exist_ok=True)
    return d


def bundled_csv() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "data.csv"


SETTINGS = data_dir() / "settings.json"
CACHE = data_dir() / "sheet_cache.csv"


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(s: dict) -> None:
    try:
        SETTINGS.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def fetch_sheet(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "FilamentColorMatcher/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        text = r.read().decode("utf-8-sig")
    if not parse_sheet(text):
        raise ValueError("The sheet came back empty or not as CSV (is it shared publicly?)")
    return text


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x720")
        self.minsize(900, 560)
        self.settings = load_settings()
        self.sheet_url = self.settings.get("sheet_url", DEFAULT_URL)
        self.owned: set[str] = set(self.settings.get("owned", []))
        self.models: list[Model] = []
        self.color_vars: dict[str, tk.BooleanVar] = {}
        self.color_rows: dict[str, tk.Widget] = {}

        style = ttk.Style(self)
        try:
            style.theme_use("vista" if sys.platform == "win32" else "clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)
        style.configure("Big.TLabel", font=("Segoe UI", 13, "bold"))

        self._build_ui()
        self._load_initial()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text=APP_NAME, style="Big.TLabel").pack(side="left")
        ttk.Button(top, text="Load CSV file…", command=self.load_file).pack(side="right")
        ttk.Button(top, text="Sheet link…", command=self.change_url).pack(side="right", padx=4)
        ttk.Button(top, text="Refresh from Google Sheet", command=self.refresh).pack(side="right")
        self.status = ttk.Label(top, text="", foreground="#555")
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
        brow = ttk.Frame(left)
        brow.pack(fill="x")
        ttk.Button(brow, text="Select all", command=lambda: self._set_all(True)).pack(side="left")
        ttk.Button(brow, text="Clear", command=lambda: self._set_all(False)).pack(side="left", padx=4)
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
        ttk.Entry(frow, textvariable=self.model_search, width=30).pack(side="left", padx=4)

        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True, pady=(6, 0))
        self.trees: dict[str, ttk.Treeview] = {}
        for key, cols in (
            ("ready", ("Model", "Printable?", "Colors")),
            ("miss1", ("Model", "Printable?", "Missing", "Colors")),
            ("miss2", ("Model", "Printable?", "Missing", "Colors")),
            ("buy", ("Filament to buy", "Unlocks", "Models")),
            ("all", ("Model", "Printable?", "Missing", "Colors")),
        ):
            frame = ttk.Frame(self.nb)
            tree = ttk.Treeview(frame, columns=cols, show="headings")
            for c in cols:
                tree.heading(c, text=c)
                w = {"Model": 220, "Printable?": 80, "Missing": 220, "Unlocks": 70,
                     "Filament to buy": 200}.get(c, 500)
                tree.column(c, width=w, stretch=c in ("Colors", "Models"), anchor="w")
            ysb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=ysb.set)
            tree.pack(side="left", fill="both", expand=True)
            ysb.pack(side="right", fill="y")
            tree.tag_configure("odd", background="#F5F7FA")
            self.nb.add(frame, text=key)
            self.trees[key] = tree

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
            w = w.master

    def _build_color_list(self) -> None:
        for child in self.color_frame.winfo_children():
            child.destroy()
        self.color_vars.clear()
        self.color_rows.clear()
        counts = all_colors(self.models)
        owned_n = {norm(c) for c in self.owned}
        for color in sorted(counts, key=str.casefold):
            row = ttk.Frame(self.color_frame)
            sw = tk.Canvas(row, width=16, height=16, highlightthickness=1, highlightbackground="#888")
            sw.create_rectangle(0, 0, 18, 18, fill=swatch(color), outline="")
            sw.pack(side="left", padx=(0, 6))
            var = tk.BooleanVar(value=norm(color) in owned_n)
            cb = ttk.Checkbutton(row, text=f"{color}  ({counts[color]})", variable=var,
                                 command=self._on_color_toggle)
            cb.pack(side="left")
            self.color_vars[color] = var
            self.color_rows[color] = row
        self._filter_colors()

    def _filter_colors(self) -> None:
        q = self.color_search.get().strip().casefold()
        only = self.only_owned.get()
        for color, row in self.color_rows.items():
            show = (not q or q in color.casefold()) and (not only or self.color_vars[color].get())
            if show:
                row.pack(fill="x", anchor="w", pady=1)
            else:
                row.pack_forget()
        self.canvas.yview_moveto(0)

    def _set_all(self, value: bool) -> None:
        for color, var in self.color_vars.items():
            if self.color_rows[color].winfo_ismapped() or not self.color_search.get().strip():
                var.set(value)
        self._on_color_toggle()

    def _on_color_toggle(self) -> None:
        sheet_owned = {c for c, v in self.color_vars.items() if v.get()}
        # Keep colors the user owns that aren't in the current sheet.
        known = {norm(c) for c in self.color_vars}
        extra = {c for c in self.owned if norm(c) not in known}
        self.owned = sheet_owned | extra
        self.settings["owned"] = sorted(self.owned, key=str.casefold)
        save_settings(self.settings)
        if self.only_owned.get():
            self._filter_colors()
        self.update_results()

    # ---------- results ----------
    def update_results(self) -> None:
        q = self.model_search.get().strip().casefold()
        models = [m for m in self.models if not q or q in m.name.casefold()]
        groups = group_by_missing(models, self.owned)
        ready = groups.get(0, [])
        miss1 = groups.get(1, [])
        miss2 = groups.get(2, [])

        def fill(key: str, rows) -> None:
            tree = self.trees[key]
            tree.delete(*tree.get_children())
            for i, values in enumerate(rows):
                tree.insert("", "end", values=values, tags=("odd",) if i % 2 else ())

        fill("ready", [(m.name, m.status, ", ".join(m.colors)) for m, _ in ready])
        fill("miss1", [(m.name, m.status, ", ".join(x), ", ".join(m.colors)) for m, x in miss1])
        fill("miss2", [(m.name, m.status, ", ".join(x), ", ".join(m.colors)) for m, x in miss2])
        buy = best_next_colors(models, self.owned)
        fill("buy", [(c, n, ", ".join(names)) for c, n, names in buy])
        everything = sorted(((m, x) for k in groups for m, x in groups[k]),
                            key=lambda t: (len(t[1]), t[0].name.casefold()))
        fill("all", [(m.name, m.status, ", ".join(x) or "-", ", ".join(m.colors)) for m, x in everything])

        tabs = self.nb.tabs()
        self.nb.tab(tabs[0], text=f"  ✔ Can print ({len(ready)})  ")
        self.nb.tab(tabs[1], text=f"  Missing 1 color ({len(miss1)})  ")
        self.nb.tab(tabs[2], text=f"  Missing 2 colors ({len(miss2)})  ")
        self.nb.tab(tabs[3], text=f"  Best filament to buy next ({len(buy)})  ")
        self.nb.tab(tabs[4], text=f"  All models ({len(models)})  ")
        self.owned_label.config(text=f"{len(self.owned)} selected · tick what you have on the shelf")

    # ---------- data loading ----------
    def _set_models(self, text: str, source: str) -> None:
        models = parse_sheet(text)
        if not models:
            messagebox.showerror(APP_NAME, f"Couldn't find any models in {source}.")
            return
        self.models = models
        self._build_color_list()
        self.update_results()
        self.status.config(text=f"{len(models)} models · {source}")

    def _load_initial(self) -> None:
        for path, label in ((CACHE, "last downloaded copy"), (bundled_csv(), "built-in copy")):
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
                    if self.models:
                        self.status.config(text=f"{len(self.models)} models · offline copy (download failed)")
                    else:
                        self.status.config(text="No data")
                    if not quiet or not self.models:
                        messagebox.showwarning(APP_NAME, f"Couldn't download the sheet:\n{msg}")
                self.after(0, fail)

        threading.Thread(target=work, daemon=True).start()

    def change_url(self) -> None:
        win = tk.Toplevel(self)
        win.title("Google Sheet link")
        win.transient(self)
        ttk.Label(win, text="Paste the Google Sheet link (the sheet must be shared as 'Anyone with the link'):",
                  padding=10).pack(anchor="w")
        var = tk.StringVar(value=self.sheet_url)
        ttk.Entry(win, textvariable=var, width=90).pack(padx=10, fill="x")

        def ok() -> None:
            self.sheet_url = to_csv_url(var.get().strip()) or DEFAULT_URL
            self.settings["sheet_url"] = self.sheet_url
            save_settings(self.settings)
            win.destroy()
            self.refresh()

        bf = ttk.Frame(win, padding=10)
        bf.pack(fill="x")
        ttk.Button(bf, text="Reset to default", command=lambda: var.set(DEFAULT_URL)).pack(side="left")
        ttk.Button(bf, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(bf, text="Save & refresh", command=ok).pack(side="right", padx=4)

    def load_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            try:
                self._set_models(Path(path).read_text(encoding="utf-8-sig"), Path(path).name)
            except Exception as exc:
                messagebox.showerror(APP_NAME, str(exc))


def to_csv_url(link: str) -> str:
    """Turn a normal Google Sheets link into its CSV export link."""
    import re
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


if __name__ == "__main__":
    App().mainloop()
