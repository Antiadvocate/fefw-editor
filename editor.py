"""
Fortune's Weave Save Editor — Fire Emblem: Fortune's Weave (Eden / eglantine slots).

A Tkinter GUI over fefw_save.py.  Every slot in the save folder is loaded; edits
stay in memory until you press Save (Ctrl+S), which writes every slot that was
changed.  With "Apply to every slot" on, an edit goes into the same unit / list
in every slot of the folder, because mid-chapter the game resumes from a
Chapter_* slot rather than Auto.
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# fefw_layer re-exports all of fefw_save and answers the structural questions
# (units, item slots, skill lists, convoy, gold) from fefw_core, which reads the
# save's own block table / unit pool / object tree instead of pattern-matching.
from fefw_layer import USER_DIR, current_gold  # noqa: E402
from fefw_layer import set_gold as write_gold  # noqa: E402
from fefw_layer import (GRADES, ITEM_KINDS, SKILL_NAMES, SKILL_THRESHOLDS,  # noqa: E402
                        STAT_NAMES, SaveError, SaveFile, live_convoy, set_convoy_item,
                        set_convoy_qty, default_save_dir, grade_label, grade_of,
                        is_enemy, is_shadow, is_slot_name, item_category, item_ids,
                        item_kind, item_label, job_ids, job_name, next_threshold, pick_live)
import fefw_layer as layer  # noqa: E402
import supports  # noqa: E402  (support pair chart + conversation flags)
import fefw_core as core  # noqa: E402  (save object tree: resizing edits)
from editor_advanced import AdvancedMixin  # noqa: E402  (Player / Classes / Flags pages)
from ui_util import enable_multi_select, last_tree  # noqa: E402  (Ctrl+A / Shift+drag in tables)

APP_NAME = "Fortune's Weave Save Editor"
__version__ = "1.3.4"
SETTINGS_PATH = os.path.join(USER_DIR, "editor_settings.json")
ICON_DIR = os.path.join(USER_DIR, "icons")

STAT_MAX = 255          # the record parser rejects stat blocks with values >= 300
SKILL_MAX = 9999        # find_skills() stops recognising a table above this
QTY_MAX = 999           # quantities seen in real saves stay well under this

STAT_LONG = {"HP": "Hit points", "Str": "Strength", "Mag": "Magic", "Dex": "Dexterity",
             "Spd": "Speed", "Lck": "Luck", "Def": "Defense", "Res": "Resistance",
             "Cha": "Charm"}

# --------------------------------------------------------------------------
# look
# --------------------------------------------------------------------------
PALETTES = {
    "dark": dict(
        bg="#14161b", side="#191c22", card="#20242c", raised="#272c36", border="#2f3541",
        fg="#e7e9ef", muted="#9ba2b2", faint="#666e7e", accent="#7c9cff",
        accent_fg="#0d1120", accent_hi="#9db4ff", sel="#2c3758", entry="#171a20",
        track="#2a303b", ok="#4fd1a5", warn="#f5b453", danger="#ff7676"),
    "light": dict(
        bg="#f3f4f7", side="#eceef3", card="#ffffff", raised="#f6f7fa", border="#dadee6",
        fg="#1b1f2c", muted="#596173", faint="#8d94a3", accent="#3d5afe",
        accent_fg="#ffffff", accent_hi="#5a73ff", sel="#dde4ff", entry="#ffffff",
        track="#e6e9f0", ok="#16936b", warn="#b26b00", danger="#d23f3f"),
}

KIND_COLORS = {
    "Sword": "#ef6f7c", "Lance": "#5fa8f5", "Axe": "#e39a52", "Bow": "#8fcf6a",
    "Tome": "#b77df0", "Staff": "#f2cc5c", "Fist": "#ff8f66", "Shield": "#4cc3c9",
    "Weapon": "#d58aa8", "Accessory": "#f29ad8", "Consumable": "#5fd3a2", "Item": "#8e97a8",
}

GRADE_COLORS = ["#7b8494", "#8b93a3", "#5aa9e6", "#4c9be0", "#4fc29a", "#3fb489",
                "#e3c04d", "#e0ab3a", "#f0884f", "#ec7040", "#e8557a", "#d9417e"]

CAT_LABEL = {"weapon": "weapons", "accessory": "accessories", "consumable": "consumables"}


def _pick_family(candidates, fallback):
    try:
        have = {f.lower() for f in tkfont.families()}
    except tk.TclError:
        return fallback
    for c in candidates:
        if c.lower() in have:
            return c
    return fallback


def _initials(name: str) -> str:
    parts = [p for p in re.split(r"[\s_\-]+", name) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].title()
    return (parts[0][0] + parts[1][0]).upper()


def _name_color(name: str) -> str:
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return list(KIND_COLORS.values())[h % 10]


def _fmt_time(ts: float) -> str:
    now = time.time()
    if now - ts < 86400 and time.localtime(now).tm_mday == time.localtime(ts).tm_mday:
        return "today " + time.strftime("%H:%M", time.localtime(ts))
    return time.strftime("%b %d %H:%M", time.localtime(ts))


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# --------------------------------------------------------------------------
# small widgets
# --------------------------------------------------------------------------
class SearchEntry(ttk.Entry):
    """Entry with placeholder text and a debounced change callback."""

    def __init__(self, master, placeholder: str, on_change, delay: int = 140, **kw):
        self._var = tk.StringVar()
        super().__init__(master, textvariable=self._var, **kw)
        self._ph = placeholder
        self._on_change = on_change
        self._delay = delay
        self._job = None
        self._showing_ph = False
        self._show_ph()
        self.bind("<FocusIn>", self._focus_in)
        self.bind("<FocusOut>", lambda e: self._show_ph())
        self.bind("<Escape>", lambda e: self.clear())
        self._var.trace_add("write", self._changed)

    def _show_ph(self):
        if not self._var.get():
            self._showing_ph = True
            self._var.set(self._ph)
            self.configure(style="Placeholder.TEntry")

    def _focus_in(self, _e=None):
        if self._showing_ph:
            self._showing_ph = False
            self._var.set("")
            self.configure(style="TEntry")

    def _changed(self, *_a):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(self._delay, self._fire)

    def _fire(self):
        self._job = None
        self._on_change()

    def get_query(self) -> str:
        return "" if self._showing_ph else self._var.get().strip()

    def clear(self):
        if self._showing_ph:
            return
        self._var.set("")
        if self.focus_get() is not self:
            self._show_ph()


class Bar(tk.Canvas):
    """Flat horizontal progress bar."""

    def __init__(self, master, app, width=120, height=8, **kw):
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, **kw)
        self.app = app
        self._bw, self._bh = width, height
        self._frac, self._color = 0.0, None
        app.register_canvas(self)
        self.bind("<Configure>", self._resize)

    def _resize(self, e):
        self._bw = e.width
        self.redraw()

    def set(self, frac: float, color: str | None = None):
        self._frac = max(0.0, min(1.0, frac))
        self._color = color
        self.redraw()

    def redraw(self):
        p = self.app.p
        bg = p["card"] if getattr(self, "on_card", True) else p["bg"]
        self.configure(background=bg)
        self.delete("all")
        w, h = max(self._bw, 4), self._bh
        self.create_rectangle(0, 0, w, h, fill=p["track"], outline="")
        if self._frac > 0:
            self.create_rectangle(0, 0, max(2, int(w * self._frac)), h,
                                  fill=self._color or p["accent"], outline="")


class Avatar(tk.Canvas):
    """Unit portrait: icons/units/<name>.png if present, otherwise initials."""

    def __init__(self, master, app, size=60):
        super().__init__(master, width=size, height=size, highlightthickness=0, bd=0)
        self.app, self.size = app, size
        self._name, self._img = "", None
        app.register_canvas(self)

    def show(self, name: str, pid: str = ""):
        self._name = name
        self._img = self.app.unit_image(name, pid, self.size)
        self.redraw()

    def redraw(self):
        p = self.app.p
        self.configure(background=p["card"])
        self.delete("all")
        s = self.size
        if self._img is not None:
            self.create_image(s // 2, s // 2, image=self._img)
            return
        if not self._name:
            return
        self.create_oval(2, 2, s - 2, s - 2, fill=_name_color(self._name), outline="")
        self.create_text(s // 2, s // 2, text=_initials(self._name), fill="#10131a",
                         font=(self.app.family, int(s * 0.3), "bold"))


def scrolled_tree(master, **kw) -> ttk.Treeview:
    frame = ttk.Frame(master, style="Card.TFrame")
    tree = ttk.Treeview(frame, **kw)
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    tree.container = frame
    enable_multi_select(tree)
    return tree


# --------------------------------------------------------------------------
# item picker (shared by Inventory and Convoy)
# --------------------------------------------------------------------------
class ItemPicker(ttk.Frame):
    MAX_ROWS = 600

    def __init__(self, master, app, on_activate, action_text: str):
        super().__init__(master, style="Card.TFrame", padding=12)
        self.app = app
        self.on_activate = on_activate
        self.lock_category: str | None = None

        top = ttk.Frame(self, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Item catalogue", style="CardH3.TLabel").pack(side="left")
        self.count_lbl = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.count_lbl.pack(side="right")

        self.search = SearchEntry(self, "Search by name, Japanese name or id…", self.refresh)
        self.search.pack(fill="x", pady=(8, 6))
        self.search.bind("<Return>", lambda e: self._activate())
        self.search.bind("<Down>", self._to_list)

        row = ttk.Frame(self, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Type", style="CardMuted.TLabel").pack(side="left")
        self.kind_var = tk.StringVar(value="All types")
        kb = ttk.Combobox(row, textvariable=self.kind_var, state="readonly", width=14,
                          values=["All types"] + ITEM_KINDS)
        kb.pack(side="left", padx=(6, 12))
        kb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        app.register_combo(kb)
        ttk.Checkbutton(row, text="Internal duplicates", style="Card.TCheckbutton",
                        variable=app.show_internal, command=self.refresh).pack(side="left")

        self.lock_lbl = ttk.Label(self, text="", style="CardWarn.TLabel", wraplength=360)
        self._lock_anchor = row

        bottom = ttk.Frame(self, style="Card.TFrame")
        bottom.pack(side="bottom", fill="x")
        self.action_btn = ttk.Button(bottom, text=action_text, style="Accent.TButton",
                                     command=self._activate)
        self.action_btn.pack(side="right")
        ttk.Label(bottom, text="Double-click or Enter also works",
                  style="CardFaint.TLabel").pack(side="left")

        self.tree = scrolled_tree(self, columns=("kind", "jp", "id"), show="tree headings",
                                  selectmode="browse", height=6)
        self.tree.heading("#0", text="Item", anchor="w")
        self.tree.heading("kind", text="Type", anchor="w")
        self.tree.heading("jp", text="Japanese", anchor="w")
        self.tree.heading("id", text="Id", anchor="w")
        self.tree.column("#0", width=210, minwidth=140, stretch=True)
        self.tree.column("kind", width=90, minwidth=70, stretch=False)
        self.tree.column("jp", width=130, minwidth=60, stretch=True)
        self.tree.column("id", width=78, minwidth=70, stretch=False)
        self.tree.container.pack(fill="both", expand=True, pady=(8, 8))
        self.tree.bind("<Double-1>", lambda e: self._activate())
        self.tree.bind("<Return>", lambda e: self._activate())
        self.refresh()

    def _to_list(self, _e=None):
        kids = self.tree.get_children()
        if kids:
            self.tree.focus_set()
            self.tree.selection_set(kids[0])
            self.tree.focus(kids[0])
        return "break"

    def _activate(self):
        iid = self.selected()
        if iid is None:
            kids = self.tree.get_children()
            if len(kids) == 1:
                self.tree.selection_set(kids[0])
                iid = int(kids[0], 16)
        if iid is None:
            self.app.flash("Pick an item from the catalogue first.", "warn")
            return
        self.on_activate(iid)

    def selected(self) -> int | None:
        sel = self.tree.selection()
        return int(sel[0], 16) if sel else None

    def set_lock(self, category: str | None, allow_any: bool):
        self.lock_category = None if allow_any or category in (None, "misc") else category
        if self.lock_category:
            self.lock_lbl.configure(
                text=f"Showing {CAT_LABEL.get(self.lock_category, self.lock_category)} "
                     "only, to match the selected slot.")
            self.lock_lbl.pack(fill="x", pady=(6, 0), after=self._lock_anchor)
        else:
            self.lock_lbl.pack_forget()
        self.refresh()

    def refresh(self):
        q = self.search.get_query().lower()
        tokens = q.split()
        kind = self.kind_var.get()
        show_internal = self.app.show_internal.get()
        hits = []
        for row in self.app.item_rows:
            iid, meta, en, jp, k, cat, shadow, blob = row
            if shadow and not show_internal:
                continue
            if kind != "All types" and k != kind:
                continue
            if self.lock_category and cat != self.lock_category:
                continue
            if tokens and not all(t in blob for t in tokens):
                continue
            el = en.lower()
            if not q:
                score = 3
            elif el == q or f"{iid:08x}" == q:
                score = 0
            elif el.startswith(q):
                score = 1
            elif re.search(r"\b" + re.escape(q), el):
                score = 2
            else:
                score = 3
            hits.append((score, el, row))
        hits.sort(key=lambda h: (h[0], h[1]))
        prev = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for _s, _el, (iid, meta, en, jp, k, cat, shadow, blob) in hits[:self.MAX_ROWS]:
            self.tree.insert("", "end", iid=f"{iid:08x}", text=" " + en,
                             image=self.app.item_icon(iid, meta, k),
                             values=(k, jp, f"{iid:08x}"))
        if prev and self.tree.exists(prev[0]):
            self.tree.selection_set(prev[0])
            self.tree.see(prev[0])
        more = len(hits) - self.MAX_ROWS
        self.count_lbl.configure(text=f"{len(hits):,} match" + ("" if len(hits) == 1 else "es")
                                 + (f" · first {self.MAX_ROWS}" if more > 0 else ""))


# --------------------------------------------------------------------------
# the app
# --------------------------------------------------------------------------
class App(AdvancedMixin, tk.Tk):
    def __init__(self, folder: str | None = None):
        super().__init__()
        self.title(APP_NAME)
        self.ui_scale = _install_scaling(self)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(self.px(1240), sw - 40), min(self.px(780), sh - 80)
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        self.minsize(min(self.px(1000), w), min(self.px(640), h))

        self.settings = self._load_settings()
        self.p = PALETTES.get(self.settings.get("theme"), PALETTES["dark"])
        self.style = ttk.Style(self)
        self._canvases: list[tk.Canvas] = []
        self._combos: list[ttk.Combobox] = []
        self._img_cache: dict = {}
        self._fonts()

        # state
        self.folder: str | None = None
        self.slot_paths: list[str] = []
        self.files: dict[str, SaveFile] = {}
        self.mtimes: dict[str, float] = {}
        self.dirty: set[str] = set()
        self.sv: SaveFile | None = None
        self.uid: int | None = None          # unit shown in the form
        self.money_off: int | None = None
        self.gold_auto = False              # gold found by its record, not by search
        self._gold_cands: list[int] = []
        self._inv_items: list[tuple[int, int, int]] = []
        self._conv_rows: list = []          # ConvoyRow, in slot order
        self._skill_rows: list = []
        self._shown: dict = {}
        self._skill_shown: dict[int, int] = {}
        self._flash_job = None

        # Off by default: Auto is the live save, the other slots are snapshots.
        # (New key, so a "mirror": true saved by an older version doesn't stick.)
        self.mirror = tk.BooleanVar(value=self.settings.get("mirror_route", False))
        self.show_enemies = tk.BooleanVar(value=self.settings.get("show_enemies", False))
        self.show_internal = tk.BooleanVar(value=False)
        self.show_bad_classes = tk.BooleanVar(value=False)
        self.allow_any_item = tk.BooleanVar(value=False)

        self.item_rows = self._build_item_rows()
        self.apply_theme()
        self._build()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        start = folder or self.settings.get("last_folder")
        if not (start and os.path.isdir(start)):
            start = default_save_dir()
        if start and os.path.isdir(start):
            self.after(50, lambda: self.open_folder(start))
        else:
            self.after(50, self._show_welcome)

    # ------------------------------------------------------------ settings
    def _load_settings(self) -> dict:
        try:
            with open(SETTINGS_PATH, encoding="utf8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _save_settings(self):
        self.settings.update(theme=self.theme_name(), mirror_route=bool(self.mirror.get()),
                             show_enemies=bool(self.show_enemies.get()),
                             last_folder=self.folder)
        try:
            with open(SETTINGS_PATH, "w", encoding="utf8") as fh:
                json.dump(self.settings, fh, indent=1)
        except OSError:
            pass

    def theme_name(self) -> str:
        return "light" if self.p is PALETTES["light"] else "dark"

    # --------------------------------------------------------------- theme
    # ------------------------------------------------------------ scaling
    def px(self, n: float) -> int:
        """A size given in 96-dpi pixels, in this display's pixels."""
        return int(round(n * self.ui_scale))

    def pad(self, *v):
        return tuple(self.px(x) for x in v)

    def _row_height(self) -> int:
        """Treeview rows sized from the font, not a fixed 28 px, so text and the
        22 px icons aren't clipped when fonts grow with the display's DPI."""
        line = tkfont.Font(self, font=self.f_body).metrics("linespace")
        return max(line + self.px(10), self.px(28), 28)

    def place_dialog(self, win, w: int | None = None, h: int | None = None):
        """Size a dialog for the display's DPI and centre it over the main window
        (left alone, Windows opens it small in the screen's top-left corner)."""
        win.update_idletasks()
        w = self.px(w) if w else win.winfo_reqwidth()
        h = self.px(h) if h else win.winfo_reqheight()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h = min(w, sw - 40), min(h, sh - 80)
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 3
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h))
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _fonts(self):
        fam = _pick_family(["Segoe UI Variable Text", "Segoe UI", "Inter", "SF Pro Text",
                            "Helvetica Neue", "Noto Sans", "Cantarell", "DejaVu Sans"],
                           "TkDefaultFont")
        mono = _pick_family(["Cascadia Mono", "Consolas", "JetBrains Mono", "Menlo",
                             "DejaVu Sans Mono"], "TkFixedFont")
        self.family, self.mono = fam, mono
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                tkfont.nametofont(name).configure(family=fam, size=10)
            except tk.TclError:
                pass
        self.f_body = (fam, 10)
        self.f_small = (fam, 9)
        self.f_bold = (fam, 10, "bold")
        self.f_h3 = (fam, 11, "bold")
        self.f_h2 = (fam, 14, "bold")
        self.f_h1 = (fam, 18, "bold")
        self.f_huge = (fam, 30, "bold")
        self.f_mono = (mono, 9)

    def apply_theme(self):
        p, s = self.p, self.style
        s.theme_use("clam")
        self.configure(background=p["bg"])
        s.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["entry"],
                    bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
                    troughcolor=p["track"], focuscolor=p["accent"], selectbackground=p["sel"],
                    selectforeground=p["fg"], insertcolor=p["fg"], font=self.f_body,
                    arrowcolor=p["muted"], relief="flat")
        for name, bg in (("TFrame", p["bg"]), ("Side.TFrame", p["side"]),
                         ("Card.TFrame", p["card"]), ("Header.TFrame", p["side"])):
            s.configure(name, background=bg)
        s.configure("Card.TFrame", bordercolor=p["border"])
        s.configure("Outlined.TFrame", background=p["card"], bordercolor=p["border"],
                    relief="solid", borderwidth=1)

        def lab(name, bg, fg, font=None):
            s.configure(name, background=bg, foreground=fg, **({"font": font} if font else {}))

        lab("TLabel", p["bg"], p["fg"])
        lab("Muted.TLabel", p["bg"], p["muted"])
        lab("Faint.TLabel", p["bg"], p["faint"], self.f_small)
        lab("Side.TLabel", p["side"], p["fg"])
        lab("SideMuted.TLabel", p["side"], p["muted"], self.f_small)
        lab("SideH3.TLabel", p["side"], p["fg"], self.f_h3)
        lab("Title.TLabel", p["side"], p["fg"], self.f_h2)
        lab("Subtitle.TLabel", p["side"], p["muted"], self.f_small)
        lab("Card.TLabel", p["card"], p["fg"])
        lab("CardMuted.TLabel", p["card"], p["muted"])
        lab("CardFaint.TLabel", p["card"], p["faint"], self.f_small)
        lab("CardBold.TLabel", p["card"], p["fg"], self.f_bold)
        lab("CardH3.TLabel", p["card"], p["fg"], self.f_h3)
        lab("CardH1.TLabel", p["card"], p["fg"], self.f_h1)
        lab("CardHuge.TLabel", p["card"], p["accent"], self.f_huge)
        lab("CardWarn.TLabel", p["card"], p["warn"], self.f_small)
        lab("CardOk.TLabel", p["card"], p["ok"], self.f_small)
        lab("CardMono.TLabel", p["card"], p["muted"], self.f_mono)
        lab("StatName.TLabel", p["card"], p["muted"], self.f_bold)
        lab("Status.TLabel", p["side"], p["muted"], self.f_small)
        lab("StatusWarn.TLabel", p["side"], p["warn"], self.f_small)
        lab("StatusOk.TLabel", p["side"], p["ok"], self.f_small)
        lab("StatusErr.TLabel", p["side"], p["danger"], self.f_small)
        lab("Chip.TLabel", p["raised"], p["muted"], self.f_small)
        s.configure("Chip.TLabel", padding=(8, 2))
        lab("ChipWarn.TLabel", p["raised"], p["warn"], self.f_small)
        s.configure("ChipWarn.TLabel", padding=(8, 2))
        lab("ChipOk.TLabel", p["raised"], p["ok"], self.f_small)
        s.configure("ChipOk.TLabel", padding=(8, 2))

        # buttons
        s.configure("TButton", background=p["raised"], foreground=p["fg"], padding=(12, 6),
                    bordercolor=p["border"], lightcolor=p["raised"], darkcolor=p["raised"],
                    focusthickness=0, anchor="center")
        s.map("TButton",
              background=[("disabled", p["card"]), ("pressed", p["border"]),
                          ("active", p["border"])],
              foreground=[("disabled", p["faint"])],
              lightcolor=[("active", p["border"])], darkcolor=[("active", p["border"])])
        s.configure("Accent.TButton", background=p["accent"], foreground=p["accent_fg"],
                    bordercolor=p["accent"], lightcolor=p["accent"], darkcolor=p["accent"],
                    font=self.f_bold)
        s.map("Accent.TButton",
              background=[("disabled", p["raised"]), ("pressed", p["accent"]),
                          ("active", p["accent_hi"])],
              foreground=[("disabled", p["faint"])],
              bordercolor=[("disabled", p["border"]), ("active", p["accent_hi"])],
              lightcolor=[("active", p["accent_hi"])], darkcolor=[("active", p["accent_hi"])])
        s.configure("Danger.TButton", foreground=p["danger"])
        s.configure("Small.TButton", padding=(8, 3), font=self.f_small)
        s.configure("Icon.TButton", padding=(8, 4))

        # inputs
        for w in ("TEntry", "TSpinbox", "TCombobox"):
            s.configure(w, fieldbackground=p["entry"], foreground=p["fg"], padding=(8, 5),
                        bordercolor=p["border"], lightcolor=p["entry"], darkcolor=p["entry"],
                        background=p["raised"], arrowcolor=p["muted"], insertcolor=p["fg"])
            s.map(w, bordercolor=[("focus", p["accent"])],
                  lightcolor=[("focus", p["accent"])],
                  fieldbackground=[("readonly", p["entry"]), ("disabled", p["card"])],
                  foreground=[("disabled", p["faint"])],
                  arrowcolor=[("active", p["fg"])], background=[("active", p["border"])])
        s.configure("Placeholder.TEntry", foreground=p["faint"])
        s.configure("Stat.TSpinbox", font=(self.family, 13, "bold"), padding=(6, 3))
        s.map("TCombobox", selectbackground=[("readonly", p["entry"])],
              selectforeground=[("readonly", p["fg"])])
        self.option_add("*TCombobox*Listbox.background", p["card"])
        self.option_add("*TCombobox*Listbox.foreground", p["fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", p["sel"])
        self.option_add("*TCombobox*Listbox.selectForeground", p["fg"])
        self.option_add("*TCombobox*Listbox.font", self.f_body)
        self.option_add("*TCombobox*Listbox.borderWidth", 0)

        self._paint_checks()
        for name, bg in (("TCheckbutton", p["bg"]), ("Card.TCheckbutton", p["card"]),
                         ("Side.TCheckbutton", p["side"])):
            s.layout(name, [("Checkbutton.padding", {"sticky": "nswe", "children": [
                ("Fancy.indicator", {"side": "left", "sticky": ""}),
                ("Checkbutton.label", {"side": "left", "sticky": "nswe"})]})])
            s.configure(name, background=bg, foreground=p["fg"], indicatorbackground=p["entry"],
                        indicatorforeground=p["accent_fg"], indicatormargin=(0, 0, 6, 0),
                        upperbordercolor=p["border"], lowerbordercolor=p["border"],
                        focusthickness=0)
            s.map(name, background=[("active", bg)],
                  indicatorbackground=[("selected", p["accent"]), ("active", p["raised"])],
                  foreground=[("disabled", p["faint"])])

        # lists
        s.configure("Treeview", background=p["card"], fieldbackground=p["card"],
                    foreground=p["fg"], rowheight=self._row_height(), borderwidth=0, relief="flat",
                    font=self.f_body)
        s.map("Treeview", background=[("selected", p["sel"])],
              foreground=[("selected", p["fg"])])
        s.configure("Treeview.Heading", background=p["card"], foreground=p["faint"],
                    relief="flat", font=self.f_small, padding=self.pad(6, 6), borderwidth=0,
                    bordercolor=p["card"], lightcolor=p["card"], darkcolor=p["card"])
        s.map("Treeview.Heading", background=[("active", p["raised"])])
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        s.configure("Side.Treeview", background=p["side"], fieldbackground=p["side"])

        s.configure("Vertical.TScrollbar", background=p["raised"], troughcolor=p["card"],
                    bordercolor=p["card"], lightcolor=p["raised"], darkcolor=p["raised"],
                    arrowcolor=p["faint"], gripcount=0, arrowsize=12)
        s.map("Vertical.TScrollbar", background=[("active", p["border"])])

        # tabs
        s.configure("TNotebook", background=p["bg"], borderwidth=0, tabmargins=(0, 4, 0, 0))
        s.configure("TNotebook.Tab", background=p["bg"], foreground=p["muted"],
                    padding=self.pad(16, 8), borderwidth=0, font=self.f_bold,
                    lightcolor=p["bg"], bordercolor=p["bg"])
        s.map("TNotebook.Tab", background=[("selected", p["card"]), ("active", p["raised"])],
              foreground=[("selected", p["fg"]), ("active", p["fg"])],
              lightcolor=[("selected", p["accent"])],
              expand=[("selected", (0, 0, 0, 0))])
        s.configure("Main.TNotebook", background=p["side"], tabmargins=(12, 0, 0, 0))
        s.configure("Main.TNotebook.Tab", background=p["side"], padding=self.pad(20, 10),
                    lightcolor=p["side"], bordercolor=p["side"])
        s.map("Main.TNotebook.Tab", background=[("selected", p["bg"]), ("active", p["raised"])],
              lightcolor=[("selected", p["accent"])])
        s.configure("TPanedwindow", background=p["bg"])
        s.configure("Sash", sashthickness=6, gripcount=0, background=p["bg"],
                    lightcolor=p["bg"], bordercolor=p["bg"])
        s.configure("TSeparator", background=p["border"])
        s.configure("Horizontal.TProgressbar", background=p["accent"], troughcolor=p["track"],
                    bordercolor=p["track"], lightcolor=p["accent"], darkcolor=p["accent"])

        for c in self._canvases:
            try:
                c.redraw()
            except tk.TclError:
                pass
        for cb in self._combos:
            try:
                pd = self.tk.call("ttk::combobox::PopdownWindow", cb)
                self.tk.call(f"{pd}.f.l", "configure", "-background", p["card"],
                             "-foreground", p["fg"], "-selectbackground", p["sel"],
                             "-selectforeground", p["fg"])
            except tk.TclError:
                pass
        if hasattr(self, "unit_tree"):
            self._style_trees()
            self.refresh_skills()

    def _paint_checks(self):
        """Rounded checkbox images, repainted in place when the theme changes."""
        p = self.p
        if not hasattr(self, "_chk"):
            self._chk = {k: tk.PhotoImage(width=16, height=16) for k in ("off", "hover", "on")}
            self.style.element_create("Fancy.indicator", "image", self._chk["off"],
                                      ("selected", self._chk["on"]),
                                      ("active", self._chk["hover"]),
                                      border=0, width=24, sticky="w")
        tick = set()
        for (x0, y0), (x1, y1) in (((4, 8), (7, 11)), ((7, 11), (12, 5))):
            for t in range(41):
                x = x0 + (x1 - x0) * t / 40
                y = y0 + (y1 - y0) * t / 40
                tick.add((int(round(x)), int(round(y))))
                tick.add((int(round(x)), int(round(y)) - 1))
        for key, (fill, edge) in {"off": (p["entry"], p["faint"]),
                                  "hover": (p["raised"], p["accent"]),
                                  "on": (p["accent"], p["accent"])}.items():
            img = self._chk[key]
            img.blank()
            for y in range(1, 15):
                for x in range(1, 15):
                    # rounded corners: skip the outermost corner pixels
                    cx = min(x - 1, 14 - x)
                    cy = min(y - 1, 14 - y)
                    if cx + cy < 2 and cx < 2 and cy < 2 and (cx, cy) != (1, 1):
                        continue
                    border = x in (1, 14) or y in (1, 14) or (cx, cy) == (1, 1)
                    col = edge if border else fill
                    if key == "on" and (x, y) in tick:
                        col = p["accent_fg"]
                    img.put(col, (x, y))

    def _style_trees(self):
        p = self.p
        for tree in (self.unit_tree,):
            tree.tag_configure("enemy", foreground=p["faint"])
        for tree in (self.conv_tree, self.inv_tree):
            tree.tag_configure("empty", foreground=p["faint"])
        self.inv_tree.tag_configure("header", foreground=p["muted"], font=self.f_small)
        for tree in (getattr(self, "cls_tree", None), getattr(self, "mas_tree", None),
                     getattr(self, "flag_tree", None), getattr(self, "mount_tree", None),
                     getattr(self, "pool_tree", None)):
            if tree is not None:
                tree.tag_configure("flag_unknown", foreground=p["muted"])
                tree.tag_configure("empty", foreground=p["faint"])

    def toggle_theme(self):
        self.p = PALETTES["light" if self.theme_name() == "dark" else "dark"]
        self._img_cache = {k: v for k, v in self._img_cache.items() if k[0] != "dot"}
        self.apply_theme()
        self.theme_btn.configure(text="☀" if self.theme_name() == "dark" else "☾")
        self._save_settings()

    def register_canvas(self, c):
        self._canvases.append(c)

    def register_combo(self, cb):
        self._combos.append(cb)

    # ------------------------------------------------------------- images
    def _dot(self, color: str, size: int = 12) -> tk.PhotoImage:
        key = ("dot", color, size)
        img = self._img_cache.get(key)
        if img is None:
            pad = 4
            img = tk.PhotoImage(width=size + pad, height=size)
            r = size / 2 - 0.5
            c = size / 2 - 0.5
            for y in range(size):
                dy = y - c
                span = (r * r - dy * dy)
                if span < 0:
                    continue
                half = span ** 0.5
                x0, x1 = int(round(c - half)), int(round(c + half)) + 1
                if x1 > x0:
                    img.put(color, to=(x0, y, x1, y + 1))
            self._img_cache[key] = img
        return img

    def _load_png(self, path: str, size: int):
        key = ("png", path, size)
        if key in self._img_cache:
            return self._img_cache[key]
        try:
            img = tk.PhotoImage(file=path)
            f = max(1, max(img.width(), img.height()) // size)
            if f > 1:
                img = img.subsample(f, f)
        except tk.TclError:
            img = None
        self._img_cache[key] = img
        return img

    def item_icon(self, iid: int, meta: dict, kind: str):
        folder = os.path.join(ICON_DIR, "items")
        if os.path.isdir(folder):
            for name in (f"{iid:08x}.png", _slug(meta.get("en") or "") + ".png"):
                path = os.path.join(folder, name)
                if os.path.isfile(path):
                    img = self._load_png(path, 22)
                    if img is not None:
                        return img
        return self._dot(KIND_COLORS.get(kind, KIND_COLORS["Item"]))

    def unit_image(self, name: str, pid: str, size: int):
        folder = os.path.join(ICON_DIR, "units")
        if not os.path.isdir(folder):
            return None
        for stem in (name, _slug(name), pid):
            path = os.path.join(folder, stem + ".png")
            if os.path.isfile(path):
                return self._load_png(path, size)
        return None

    def _build_item_rows(self):
        rows = []
        for iid, meta in item_ids().items():
            en = item_label(iid, meta)
            jp = meta.get("jp") or ""
            blob = f"{en} {jp} {iid:08x}".lower()
            rows.append((iid, meta, en, jp, item_kind(meta), item_category(meta),
                         is_shadow(meta), blob))
        rows.sort(key=lambda r: (r[2].lower(), r[0]))
        return rows

    # ----------------------------------------------------------------- ui
    def _build(self):
        p = self.p
        # ---- header
        head = ttk.Frame(self, style="Header.TFrame", padding=(18, 12, 18, 10))
        head.pack(fill="x")
        brand = ttk.Frame(head, style="Header.TFrame")
        brand.pack(side="left")
        ttk.Label(brand, text="Fortune's Weave", style="Title.TLabel").pack(anchor="w")
        ttk.Label(brand, text=f"SAVE EDITOR  ·  v{__version__}",
                  style="Subtitle.TLabel").pack(anchor="w")

        right = ttk.Frame(head, style="Header.TFrame")
        right.pack(side="right")
        self.theme_btn = ttk.Button(right, text="☀" if self.theme_name() == "dark" else "☾",
                                    width=3, style="Icon.TButton", command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=(8, 0))
        self.save_btn = ttk.Button(right, text="Save", style="Accent.TButton",
                                   command=self.save_all)
        self.save_btn.pack(side="right", padx=(8, 0))
        self.revert_btn = ttk.Button(right, text="⟳ Reload", command=self.reload)
        self.revert_btn.pack(side="right")
        ttk.Button(right, text="Snapshot", command=self.take_snapshot).pack(side="right", padx=(0, 8))
        ttk.Button(right, text="Restore…", command=self.restore_snapshot).pack(side="right")

        mid = ttk.Frame(head, style="Header.TFrame")
        mid.pack(side="left", padx=(32, 0), fill="x", expand=True)
        r1 = ttk.Frame(mid, style="Header.TFrame")
        r1.pack(fill="x")
        ttk.Label(r1, text="Slot", style="Side.TLabel").pack(side="left")
        self.slot_var = tk.StringVar()
        self.slot_box = ttk.Combobox(r1, textvariable=self.slot_var, state="readonly", width=52)
        self.slot_box.pack(side="left", padx=(8, 8))
        self.slot_box.bind("<<ComboboxSelected>>", self.on_slot_pick)
        self.register_combo(self.slot_box)
        ttk.Button(r1, text="Open folder…", command=self.open_dialog).pack(side="left")
        r2 = ttk.Frame(mid, style="Header.TFrame")
        r2.pack(fill="x", pady=(6, 0))
        self.mirror_chk = ttk.Checkbutton(r2, text="Also edit this route's other saves",
                                          style="Side.TCheckbutton", variable=self.mirror,
                                          command=self._mirror_changed)
        self.mirror_chk.pack(side="left")
        self.file_lbl = ttk.Label(r2, text="", style="SideMuted.TLabel")
        self.file_lbl.pack(side="left", padx=(16, 0))

        # ---- status bar (packed before the body so it keeps its space)
        bar = ttk.Frame(self, style="Header.TFrame", padding=(18, 6))
        bar.pack(side="bottom", fill="x")
        self.status_lbl = ttk.Label(bar, text="Ready", style="Status.TLabel")
        self.status_lbl.pack(side="left")
        self.dirty_lbl = ttk.Label(bar, text="", style="Status.TLabel")
        self.dirty_lbl.pack(side="right")

        # ---- pages
        self.pages = ttk.Notebook(self, style="Main.TNotebook")
        self.pages.pack(fill="both", expand=True)
        self.units_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.convoy_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.gold_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.supports_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.player_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.classes_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.flags_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.mounts_page = ttk.Frame(self.pages, padding=(14, 14, 14, 8))
        self.pages.add(self.units_page, text="Units")
        self.pages.add(self.convoy_page, text="Convoy")
        self.pages.add(self.gold_page, text="Gold")
        self.pages.add(self.supports_page, text="Supports")
        self.pages.add(self.player_page, text="Player")
        self.pages.add(self.classes_page, text="Classes")
        self.pages.add(self.flags_page, text="Flags")
        self.pages.add(self.mounts_page, text="Mounts")

        self._build_units()
        self._build_convoy()
        self._build_gold()
        self._build_supports()
        self._build_player()
        self._build_classes()
        self._build_flags()
        self._build_mounts()
        self._style_trees()
        self._enable_multi_select_all()
        self._update_dirty()

    def _enable_multi_select_all(self):
        """Ctrl+A / Shift+drag on every list except the two row-pickers.

        The unit lists drive the edit form, so they stay single-choice; every
        other table (convoy, classes, masteries, flags, mounts) takes a range.
        """
        skip = {id(getattr(self, "unit_tree", None)),
                id(getattr(self, "cls_unit_tree", None))}

        def walk(w):
            for child in w.winfo_children():
                if isinstance(child, ttk.Treeview) and id(child) not in skip:
                    enable_multi_select(child)
                walk(child)

        walk(self)

    # -------------------------------------------------------- units page
    def _build_units(self):
        pane = ttk.PanedWindow(self.units_page, orient="horizontal")
        pane.pack(fill="both", expand=True)

        side = ttk.Frame(pane, style="Card.TFrame", padding=12)
        pane.add(side, weight=0)
        top = ttk.Frame(side, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Units", style="CardH3.TLabel").pack(side="left")
        self.unit_count = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.unit_count.pack(side="right")
        self.unit_search = SearchEntry(side, "Search units or classes…  (Ctrl+F)",
                                       self.refresh_units, width=30)
        self.unit_search.pack(fill="x", pady=(8, 6))
        self.unit_search.bind("<Down>", lambda e: (self.unit_tree.focus_set(), "break")[1])
        ttk.Checkbutton(side, text="Show enemies & NPCs", style="Card.TCheckbutton",
                        variable=self.show_enemies,
                        command=lambda: (self.refresh_units(), self._save_settings())
                        ).pack(anchor="w", pady=(0, 6))
        self.unit_tree = scrolled_tree(side, columns=("lv",), show="tree headings",
                                       selectmode="browse")
        self.unit_tree.heading("#0", text="Name", anchor="w")
        self.unit_tree.heading("lv", text="Lv", anchor="e")
        self.unit_tree.column("#0", width=200, minwidth=140)
        self.unit_tree.column("lv", width=44, minwidth=40, anchor="e", stretch=False)
        self.unit_tree.container.pack(fill="both", expand=True)
        self.unit_tree.bind("<<TreeviewSelect>>", self.on_unit_select)
        acts = ttk.Frame(side, style="Card.TFrame")
        acts.pack(fill="x", pady=(8, 0))
        ttk.Button(acts, text="Copy unit in…", style="Small.TButton",
                   command=self.copy_unit_in).pack(fill="x")
        ttk.Button(acts, text="Remove unit", style="Small.TButton",
                   command=self.remove_current_unit).pack(fill="x", pady=(6, 0))

        main = ttk.Frame(pane)
        pane.add(main, weight=1)

        # unit header card
        card = ttk.Frame(main, style="Card.TFrame", padding=(16, 14))
        card.pack(fill="x", padx=(10, 0))
        self.avatar = Avatar(card, self, size=60)
        self.avatar.pack(side="left")
        info = ttk.Frame(card, style="Card.TFrame")
        info.pack(side="left", padx=(14, 0), fill="x", expand=True)
        self.unit_name = ttk.Label(info, text="No unit selected", style="CardH1.TLabel")
        self.unit_name.pack(anchor="w")
        self.unit_sub = ttk.Label(info, text="Open a save folder to begin.",
                                  style="CardMuted.TLabel")
        self.unit_sub.pack(anchor="w", pady=(2, 0))
        chips = ttk.Frame(card, style="Card.TFrame")
        chips.pack(side="right", anchor="n")
        self.copies_chip = ttk.Label(chips, text="", style="Chip.TLabel")
        self.copies_chip.pack(anchor="e")
        self.sync_btn = ttk.Button(chips, text="Make copies match", style="Small.TButton",
                                   command=self.sync_copies)

        self.unit_tabs = ttk.Notebook(main)
        self.unit_tabs.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 0))
        self._build_stats_tab()
        self._build_skill_tab()
        self._build_inventory_tab()
        self._build_class_tab()

    def _num_vcmd(self):
        return (self.register(lambda P: P == "" or (P.isdigit() and len(P) <= 7)), "%P")

    def _build_stats_tab(self):
        tab = ttk.Frame(self.unit_tabs, style="Card.TFrame", padding=18)
        self.unit_tabs.add(tab, text="Stats")
        self._stat_spins: list[ttk.Spinbox] = []
        vcmd = self._num_vcmd()

        row = ttk.Frame(tab, style="Card.TFrame")
        row.pack(fill="x")
        self.lvl_var, self.exp_var = tk.StringVar(), tk.StringVar()
        for label, var, fn, lo, hi in (("Level", self.lvl_var, self.commit_level, 1, 99),
                                       ("EXP", self.exp_var, self.commit_exp, 0, 99)):
            box = ttk.Frame(row, style="Card.TFrame")
            box.pack(side="left", padx=(0, 28))
            ttk.Label(box, text=label.upper(), style="StatName.TLabel").pack(anchor="w")
            sp = ttk.Spinbox(box, from_=lo, to=hi, width=6, textvariable=var, command=fn,
                             validate="key", validatecommand=vcmd, style="Stat.TSpinbox")
            sp.pack(anchor="w", pady=(4, 0))
            self._stat_spins.append(sp)
            sp.bind("<Return>", lambda e, f=fn: f())
            sp.bind("<FocusOut>", lambda e, f=fn: f())
        self.exp_bar = Bar(row, self, width=160, height=6)
        self.exp_bar.pack(side="left", anchor="s", pady=(0, 12))
        hpbox = ttk.Frame(row, style="Card.TFrame")
        hpbox.pack(side="left", padx=(40, 0))
        ttk.Label(hpbox, text="HP", style="StatName.TLabel").pack(anchor="w")
        self.maxhp_lbl = ttk.Label(hpbox, text="—", style="CardH1.TLabel")
        self.maxhp_lbl.pack(anchor="w")

        ttk.Separator(tab).pack(fill="x", pady=16)
        gh = ttk.Frame(tab, style="Card.TFrame")
        gh.pack(fill="x", pady=(0, 10))
        ttk.Label(gh, text="Points gained from level-ups", style="CardH3.TLabel").pack(anchor="w")
        ttk.Label(gh, style="CardFaint.TLabel", wraplength=700, justify="left",
                  text="These are what the unit has gained from levelling, not the totals "
                       "shown in game: the game adds them to the unit's class and personal "
                       "bases, and stat-up items aren't included. Raising one raises the "
                       "in-game stat by the same amount.").pack(anchor="w")

        grid = ttk.Frame(tab, style="Card.TFrame")
        grid.pack(fill="x")
        self.stat_vars, self.stat_bars = [], []
        for i, name in enumerate(STAT_NAMES):
            cell = ttk.Frame(grid, style="Card.TFrame", padding=(0, 0, 24, 18))
            cell.grid(row=i // 3, column=i % 3, sticky="ew")
            grid.columnconfigure(i % 3, weight=1, uniform="stat")
            head = ttk.Frame(cell, style="Card.TFrame")
            head.pack(fill="x")
            ttk.Label(head, text=name.upper(), style="StatName.TLabel").pack(side="left")
            ttk.Label(head, text=STAT_LONG.get(name, ""), style="CardFaint.TLabel"
                      ).pack(side="left", padx=(6, 0))
            body = ttk.Frame(cell, style="Card.TFrame")
            body.pack(fill="x", pady=(4, 0))
            v = tk.StringVar()
            sp = ttk.Spinbox(body, from_=0, to=STAT_MAX, width=5, textvariable=v,
                             command=lambda i=i: self.commit_stat(i), validate="key",
                             validatecommand=vcmd, style="Stat.TSpinbox")
            sp.pack(side="left")
            self._stat_spins.append(sp)
            sp.bind("<Return>", lambda e, i=i: self.commit_stat(i))
            sp.bind("<FocusOut>", lambda e, i=i: self.commit_stat(i))
            bar = Bar(body, self, width=100, height=6)
            bar.pack(side="left", fill="x", expand=True, padx=(12, 0))
            self.stat_vars.append(v)
            self.stat_bars.append(bar)

        ttk.Label(tab, style="CardFaint.TLabel", wraplength=700, justify="left",
                  text="Changing HP gained moves max HP with it. Edits apply on Enter / Tab; "
                       "Save writes them."
                  ).pack(anchor="w", side="bottom")


    def _build_inventory_tab(self):
        tab = ttk.Frame(self.unit_tabs, style="Card.TFrame", padding=(18, 18, 6, 18))
        self.unit_tabs.add(tab, text="Inventory")
        pane = ttk.PanedWindow(tab, orient="horizontal")
        pane.pack(fill="both", expand=True)
        left = ttk.Frame(pane, style="Card.TFrame", padding=(0, 0, 12, 0))
        pane.add(left, weight=1)
        ttk.Label(left, text="Carried items", style="CardH3.TLabel").pack(anchor="w")
        ttk.Label(left, text="Select a slot, then choose its replacement.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 8))
        ttk.Checkbutton(left, text="Allow any item type (can break the game)",
                        style="Card.TCheckbutton", variable=self.allow_any_item,
                        command=self._inv_lock).pack(side="bottom", anchor="w", pady=(8, 0))
        ib = ttk.Frame(left, style="Card.TFrame")
        ib.pack(side="bottom", anchor="w", pady=(8, 0))
        ttk.Button(ib, text="Add item…", style="Small.TButton",
                   command=self.add_item).pack(side="left")
        ttk.Button(ib, text="Remove item", style="Small.TButton",
                   command=self.remove_item).pack(side="left", padx=(6, 0))
        self.inv_tree = scrolled_tree(left, columns=("kind",), show="tree headings",
                                      selectmode="browse", height=6)
        self.inv_tree.heading("#0", text="Item", anchor="w")
        self.inv_tree.heading("kind", text="Type", anchor="w")
        self.inv_tree.column("#0", width=220)
        self.inv_tree.column("kind", width=90, stretch=False)
        self.inv_tree.container.pack(fill="both", expand=True)
        self.inv_tree.bind("<<TreeviewSelect>>", lambda e: self._inv_lock())
        self.inv_picker = ItemPicker(pane, self, self.replace_item, "Put in selected slot")
        self.inv_picker.configure(padding=(12, 0, 0, 0))
        pane.add(self.inv_picker, weight=2)

    def _build_class_tab(self):
        tab = ttk.Frame(self.unit_tabs, style="Card.TFrame", padding=18)
        self.unit_tabs.add(tab, text="Class")
        cur = ttk.Frame(tab, style="Card.TFrame")
        cur.pack(fill="x")
        ttk.Label(cur, text="Current class", style="CardMuted.TLabel").pack(side="left")
        self.class_now = ttk.Label(cur, text="—", style="CardH3.TLabel")
        self.class_now.pack(side="left", padx=(10, 0))

        row = ttk.Frame(tab, style="Card.TFrame")
        row.pack(fill="x", pady=(12, 6))
        self.class_search = SearchEntry(row, "Search classes…", self.refresh_classes)
        self.class_search.pack(side="left", fill="x", expand=True)
        ttk.Checkbutton(row, text="Include monster / internal classes",
                        style="Card.TCheckbutton", variable=self.show_bad_classes,
                        command=self.refresh_classes).pack(side="left", padx=(12, 0))
        bottom = ttk.Frame(tab, style="Card.TFrame")
        bottom.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Button(bottom, text="Change class", style="Accent.TButton",
                   command=self.apply_class).pack(side="right", anchor="n")
        ttk.Label(bottom, style="CardWarn.TLabel", wraplength=560, justify="left",
                  text="Only the class id is written. Movement, usable weapons, class skills "
                       "and max HP come from the class and are not recalculated — check the "
                       "unit screen in game after loading."
                  ).pack(side="left", fill="x", expand=True)
        self.class_tree = scrolled_tree(tab, columns=("jp",), show="tree headings",
                                        selectmode="browse", height=6)
        self.class_tree.heading("#0", text="Class", anchor="w")
        self.class_tree.heading("jp", text="Internal name", anchor="w")
        self.class_tree.column("#0", width=260)
        self.class_tree.column("jp", width=260)
        self.class_tree.container.pack(fill="both", expand=True)
        self.class_tree.bind("<Double-1>", lambda e: self.apply_class())
        self.refresh_classes()

    # ------------------------------------------------------- convoy page
    def _build_convoy(self):
        pane = ttk.PanedWindow(self.convoy_page, orient="horizontal")
        pane.pack(fill="both", expand=True)
        left = ttk.Frame(pane, style="Card.TFrame", padding=12)
        pane.add(left, weight=1)
        top = ttk.Frame(left, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Convoy", style="CardH3.TLabel").pack(side="left")
        self.conv_count = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.conv_count.pack(side="right")
        ttk.Label(left, text="Everything in storage, materials included, by slot.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 6))
        self.conv_problem = ttk.Frame(left, style="Card.TFrame")
        self.conv_problem_lbl = ttk.Label(self.conv_problem, text="", style="CardWarn.TLabel",
                                          wraplength=420, justify="left")
        self.conv_problem_lbl.pack(fill="x")
        self.conv_repair_btn = ttk.Button(self.conv_problem, text="Repair convoy",
                                          style="Accent.TButton", command=self.repair_convoy_ui)
        self.conv_filter = SearchEntry(left, "Filter the convoy…", self.refresh_convoy)
        self.conv_filter.pack(fill="x", pady=(0, 6))
        ctl = ttk.Frame(left, style="Card.TFrame")
        ctl.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Label(left, style="CardFaint.TLabel", wraplength=420, justify="left",
                  text="Every item has its own convoy slot. Add item… puts a stack in it and "
                       "Remove empties a slot; the list keeps its slot count and everything "
                       "after it is moved safely. All materials… stocks every ore, meat, "
                       "fish and plant at one quantity."
                  ).pack(side="bottom", anchor="w", pady=(8, 0))
        self.conv_tree = scrolled_tree(left, columns=("kind", "qty"), show="tree headings",
                                       selectmode="extended", height=6)
        self.conv_tree.heading("#0", text="Slot · Item", anchor="w")
        self.conv_tree.heading("kind", text="Type", anchor="w")
        self.conv_tree.heading("qty", text="Qty", anchor="e")
        self.conv_tree.column("#0", width=250)
        self.conv_tree.column("kind", width=90, stretch=False)
        self.conv_tree.column("qty", width=56, anchor="e", stretch=False)
        self.conv_tree.container.pack(fill="both", expand=True)
        self.conv_tree.bind("<<TreeviewSelect>>", self._conv_row_picked)

        ttk.Label(ctl, text="Quantity", style="Card.TLabel").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        qs = ttk.Spinbox(ctl, from_=1, to=QTY_MAX, width=5, textvariable=self.qty_var,
                         validate="key", validatecommand=self._num_vcmd())
        qs.pack(side="left", padx=(8, 12))
        qs.bind("<Return>", lambda e: self.set_convoy_qty())
        ttk.Button(ctl, text="Set qty", command=self.set_convoy_qty).pack(side="left")
        ttk.Button(ctl, text="Add item…", style="Small.TButton",
                   command=self.add_convoy_item_ui).pack(side="left", padx=(10, 0))
        ttk.Button(ctl, text="Remove", style="Small.TButton",
                   command=self.remove_convoy_item_ui).pack(side="left", padx=(6, 0))
        ttk.Button(ctl, text="All materials…", style="Small.TButton",
                   command=self.fill_materials_ui).pack(side="left", padx=(6, 0))

        right = ttk.Frame(pane, padding=(10, 0, 0, 0))
        pane.add(right, weight=1)
        self.conv_picker = ItemPicker(right, self, self.replace_convoy, "Put in selected row")
        self.conv_picker.pack(fill="both", expand=True)

    # --------------------------------------------------------- gold page
    def _build_gold(self):
        wrap = ttk.Frame(self.gold_page)
        wrap.pack(fill="both", expand=True)
        card = ttk.Frame(wrap, style="Card.TFrame", padding=24)
        card.pack(fill="x")
        ttk.Label(card, text="GOLD", style="StatName.TLabel").pack(anchor="w")
        self.gold_now = ttk.Label(card, text="—", style="CardHuge.TLabel")
        self.gold_now.pack(anchor="w")
        self.gold_hint = ttk.Label(card, text="", style="CardMuted.TLabel")
        self.gold_hint.pack(anchor="w", pady=(0, 14))
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(anchor="w")
        ttk.Label(row, text="New amount", style="Card.TLabel").pack(side="left")
        self.gold_new = tk.StringVar()
        e = ttk.Entry(row, textvariable=self.gold_new, width=14)
        e.pack(side="left", padx=8)
        e.bind("<Return>", lambda ev: self.set_gold())
        ttk.Button(row, text="Set gold", style="Accent.TButton",
                   command=self.set_gold).pack(side="left")
        for amt in (10_000, 100_000, 999_999):
            ttk.Button(row, text=f"{amt:,}", style="Small.TButton",
                       command=lambda a=amt: (self.gold_new.set(f"{a:,}"), self.set_gold())
                       ).pack(side="left", padx=(8 if amt == 10_000 else 4, 0))

        ttk.Label(wrap, style="CardFaint.TLabel", wraplength=760, justify="left",
                  text="Gold lives at a fixed place in every slot of this game (GameUserData "
                       "+ 6), so there is nothing to locate: the amount below is what the game "
                       "will read. Chapter and battle snapshots keep their own amount."
                  ).pack(anchor="w", pady=(12, 0))

    # --------------------------------------------------------- keys / misc

    def _visible_units(self) -> int:
        """Units the save's own unit list holds (the party and its reserves)."""
        try:
            return len(self.core_of().units())
        except Exception:  # noqa: BLE001 — fall back to the scanned copies
            return len(self._unit_map())

    def _build_supports(self):
        self.sup_party_only = tk.BooleanVar(value=True)
        pane = ttk.PanedWindow(self.supports_page, orient="horizontal")
        pane.pack(fill="both", expand=True)

        side = ttk.Frame(pane, style="Card.TFrame", padding=12)
        pane.add(side, weight=0)
        top = ttk.Frame(side, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Characters", style="CardH3.TLabel").pack(side="left")
        self.sup_count = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.sup_count.pack(side="right")
        ttk.Label(side, text="Every character's supports, with the points this save "
                             "holds for each pair.",
                  style="CardMuted.TLabel", wraplength=210, justify="left"
                  ).pack(anchor="w", pady=(2, 8))
        self.sup_search = SearchEntry(side, "Search characters…", self.refresh_support_chars,
                                      width=26)
        self.sup_search.pack(fill="x", pady=(0, 6))
        ttk.Checkbutton(side, text="Only characters in this save",
                        style="Card.TCheckbutton", variable=self.sup_party_only,
                        command=self.refresh_support_chars).pack(anchor="w", pady=(0, 6))
        self.sup_char_tree = scrolled_tree(side, columns=("n", "top"), show="tree headings",
                                           selectmode="browse")
        self.sup_char_tree.heading("#0", text="Character", anchor="w")
        self.sup_char_tree.heading("n", text="Convs", anchor="e")
        self.sup_char_tree.heading("top", text="Top", anchor="e")
        self.sup_char_tree.column("#0", width=140, minwidth=100)
        self.sup_char_tree.column("n", width=48, anchor="e", stretch=False)
        self.sup_char_tree.column("top", width=52, anchor="e", stretch=False)
        self.sup_char_tree.container.pack(fill="both", expand=True)
        self.sup_char_tree.bind("<<TreeviewSelect>>", self.on_support_char)

        main = ttk.Frame(pane)
        pane.add(main, weight=1)

        card = ttk.Frame(main, style="Card.TFrame", padding=(16, 14))
        card.pack(fill="x", padx=(10, 0))
        self.sup_avatar = Avatar(card, self, size=60)
        self.sup_avatar.pack(side="left")
        info = ttk.Frame(card, style="Card.TFrame")
        info.pack(side="left", padx=(14, 0), fill="x", expand=True)
        self.sup_name = ttk.Label(info, text="No character selected", style="CardH1.TLabel")
        self.sup_name.pack(anchor="w")
        self.sup_sub = ttk.Label(info, text="Open a save to see what it records.",
                                 style="CardMuted.TLabel")
        self.sup_sub.pack(anchor="w", pady=(2, 0))

        # the note is packed before the table so a short window shrinks the
        # table instead of pushing the buttons and the note out of sight
        ttk.Label(main, style="CardFaint.TLabel", justify="left", wraplength=620,
                  text="Points are what the game turns into a support level: 3200 is the "
                       "maximum (level 5). The save keeps a slot for every pair, so a pair "
                       "whose support hasn't opened yet still has a value here — the game may "
                       "not show it until it opens the relationship itself. “Seen” is the "
                       "save's 支援会話 flag for a conversation; Max is the highest rank the "
                       "game data gives the pair."
                  ).pack(side="bottom", fill="x", anchor="w", padx=(12, 0), pady=(10, 0))

        body = ttk.Frame(main, style="Card.TFrame", padding=(12, 10))
        body.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 0))

        acts = ttk.Frame(body, style="Card.TFrame")
        acts.pack(side="bottom", fill="x", pady=(8, 0))
        ttk.Label(acts, text="Record conversation as seen:", style="Card.TLabel").pack(side="left")
        for r in ("C", "B", "A"):
            ttk.Button(acts, text=r, width=3, style="Small.TButton",
                       command=lambda rr=r: self.sup_set_rank(rr)).pack(side="left", padx=(6, 0))
        ttk.Button(acts, text="Forget…", style="Small.TButton",
                   command=self.sup_forget_rank).pack(side="left", padx=(12, 0))
        self.sup_write_lbl = ttk.Label(acts, text="", style="CardFaint.TLabel")
        self.sup_write_lbl.pack(side="left", padx=(12, 0))

        pts = ttk.Frame(body, style="Card.TFrame")
        pts.pack(side="bottom", fill="x", pady=(8, 0))
        ttk.Label(pts, text="Support points:", style="Card.TLabel").pack(side="left")
        self.sup_pt_var = tk.StringVar(value="")
        self.sup_pt_spin = ttk.Spinbox(pts, from_=0, to=supports.max_points(), increment=50,
                                       width=8, textvariable=self.sup_pt_var,
                                       command=self.sup_apply_points)
        self.sup_pt_spin.pack(side="left", padx=(8, 0))
        self.sup_pt_spin.bind("<Return>", lambda _e: (self.sup_apply_points(), "break")[1])
        ttk.Button(pts, text="Apply", style="Small.TButton",
                   command=self.sup_apply_points).pack(side="left", padx=(6, 0))
        ttk.Button(pts, text="Max", style="Small.TButton",
                   command=lambda: self.sup_set_points(supports.max_points())
                   ).pack(side="left", padx=(6, 0))
        ttk.Button(pts, text="0", width=3, style="Small.TButton",
                   command=lambda: self.sup_set_points(0)).pack(side="left", padx=(6, 0))
        self.sup_pt_lbl = ttk.Label(pts, text="", style="CardFaint.TLabel")
        self.sup_pt_lbl.pack(side="left", padx=(12, 0))

        self.sup_tree = scrolled_tree(body, columns=("jp", "points", "max", "seen", "party"),
                                      show="tree headings", selectmode="browse")
        self.sup_tree.heading("#0", text="Support partner", anchor="w")
        self.sup_tree.heading("jp", text="Japanese", anchor="w")
        self.sup_tree.heading("points", text="Points", anchor="e")
        self.sup_tree.heading("max", text="Max", anchor="center")
        self.sup_tree.heading("seen", text="Conversations seen", anchor="w")
        self.sup_tree.heading("party", text="In party", anchor="center")
        self.sup_tree.column("#0", width=180, minwidth=130)
        self.sup_tree.column("jp", width=140)
        self.sup_tree.column("points", width=64, anchor="e", stretch=False)
        self.sup_tree.column("max", width=50, anchor="center", stretch=False)
        self.sup_tree.column("seen", width=160, stretch=False)
        self.sup_tree.column("party", width=74, anchor="center", stretch=False)
        self.sup_tree.container.pack(fill="both", expand=True)
        self.sup_tree.bind("<<TreeviewSelect>>", self.on_support_pair)

    def _party_pids(self) -> set[str]:
        try:
            return {u.pid for u in self._unit_map().values() if getattr(u, "pid", "")}
        except Exception:  # noqa: BLE001 — never break the page over a bad record
            return set()

    def _support_flags(self) -> set[int]:
        if not self.sv:
            return set()
        key = (self.sv.path, id(self.sv.payload))
        cache = getattr(self, "_sup_flag_cache", None)
        if cache and cache[0] == key:
            return cache[1]
        try:
            f = self.core_of()
            flags = {x.hash for m in core.flag_maps(f) for x in m.flags}
        except Exception:  # noqa: BLE001 — the byte scan is only a fallback
            flags = supports.present_flags(bytes(self.sv.payload))
        self._sup_flag_cache = (key, flags)
        return flags

    def _support_points(self):
        """{pair hash: (points, extra, offset)} from the save's GameUserData."""
        if not self.sv:
            return None
        key = (self.sv.path, id(self.sv.payload))
        cache = getattr(self, "_sup_pt_cache", None)
        if cache and cache[0] == key:
            return cache[1]
        try:
            f = self.core_of()
            blk = f.block("GameUserData")
            table = supports.find_table(f.payload, blk.start, blk.end) if blk else None
        except Exception:  # noqa: BLE001 — never break the page over a missing table
            table = None
        self._sup_pt_cache = (key, table)
        return table

    def _sup_chars(self) -> list[tuple[str, dict]]:
        """Every character the point table knows, with the conversation chart merged in."""
        chart = supports.by_char()
        out: list[tuple[str, dict]] = []
        seen: set[str] = set()
        for jp, en in supports.point_chars():
            rec = chart.get(jp) or {}
            out.append((jp, {"jp": jp, "en": rec.get("en") or en or jp,
                             "partners": rec.get("partners") or []}))
            seen.add(jp)
        for jp, rec in chart.items():
            if jp not in seen:
                out.append((jp, rec))
        out.sort(key=lambda kv: (kv[1]["en"] or kv[0]).lower())
        return out

    def _top_points(self, jp: str, points) -> int | None:
        """The pair with the most points this character has in this save."""
        if not points:
            return None
        best = 0
        for pa in supports.point_partners().get(jp, ()):
            best = max(best, supports.points_of(points, pa["hash"]) or 0)
        return best

    def _sup_partners(self, jp: str, rec: dict, points) -> list[dict]:
        """Every partner of ``jp`` with its points, richest support first."""
        chart = {p["jp"]: p for p in (rec.get("partners") or [])}
        table = supports.point_partners().get(jp) or []
        src = ([{"jp": p["jp"], "en": p["en"], "hash": p["hash"]} for p in table]
               or [{"jp": p["jp"], "en": p["en"], "hash": None}
                   for p in (rec.get("partners") or [])])
        out = []
        for p in src:
            out.append({"jp": p["jp"], "en": p["en"] or p["jp"], "hash": p["hash"],
                        "points": supports.points_of(points, p["hash"]),
                        "chart": chart.get(p["jp"]) or {}})
        out.sort(key=lambda r: (-(r["points"] or 0), r["en"].lower()))
        return out

    def refresh_supports(self):
        self._sup_flag_cache = None
        self._sup_pt_cache = None
        self.refresh_support_chars()
        self.on_support_char()

    def refresh_support_chars(self):
        if not hasattr(self, "sup_char_tree"):
            return
        q = self.sup_search.get_query().strip().lower()
        party = self._party_pids() if (self.sv and self.sup_party_only.get()) else None
        keep = getattr(self, "_sup_char", None)
        points = self._support_points()
        self.sup_char_tree.delete(*self.sup_char_tree.get_children())
        self._sup_rows = {}
        iids: dict[str, str] = {}
        first = None
        n = 0
        for jp, rec in self._sup_chars():
            en = rec["en"] or jp
            if q and q not in en.lower() and q not in jp.lower():
                continue
            if party is not None and ("PID_" + jp) not in party:
                continue
            top = self._top_points(jp, points)
            iid = self.sup_char_tree.insert("", "end", text=en,
                                            values=(len(rec.get("partners") or []),
                                                    "" if top is None else f"{top:,}"))
            self._sup_rows[iid] = (jp, rec)
            iids[jp] = iid
            n += 1
            first = first or iid
        self.sup_count.configure(text=f"{n} character{'s' if n != 1 else ''}"
                                       + (" in this save" if party is not None else ""))
        target = iids.get(keep or "") or first
        if target:
            self.sup_char_tree.selection_set(target)
            self.on_support_char()
        else:
            self._sup_char = None
            self.sup_tree.delete(*self.sup_tree.get_children())
            self.sup_name.configure(text="Nothing to show")
            self.sup_sub.configure(text="Open a save, or untick “Only characters in this save”.")

    def on_support_char(self, _e=None):
        sel = self.sup_char_tree.selection() if hasattr(self, "sup_char_tree") else ()
        rows = getattr(self, "_sup_rows", {})
        if not sel or sel[0] not in rows:
            return
        jp, rec = rows[sel[0]]
        en = rec["en"] or jp
        if getattr(self, "_sup_char", None) != jp:
            self._sup_partner = None          # new character: don't keep the old partner
        self._sup_char = jp
        self.sup_name.configure(text=en)
        self.sup_avatar.show(en, "PID_" + jp)

        present = self._support_flags()
        points = self._support_points()
        party = self._party_pids()
        keep = getattr(self, "_sup_partner", None)
        plist = self._sup_partners(jp, rec, points)
        self.sup_tree.delete(*self.sup_tree.get_children())
        self._sup_pairs = {}
        self._sup_pt = {}
        iids: dict[str, str] = {}
        seen_pairs = 0
        for pa in plist:
            got = [r for r in supports.RANKS if supports.seen(pa["chart"], present).get(r)]
            if got:
                seen_pairs += 1
            pts = pa["points"]
            iid = self.sup_tree.insert(
                "", "end", text=pa["en"],
                values=(pa["jp"],
                        "—" if pts is None else f"{pts:,}",
                        pa["chart"].get("max") or "—",
                        ", ".join(got) if got else "—",
                        "✓" if ("PID_" + pa["jp"]) in party else ""),
                tags=("sup_seen",) if (got or pts) else ("sup_none",))
            self._sup_pairs[iid] = ({"a_en": en, "b_en": pa["en"]},
                                    dict(pa["chart"].get("flags") or {}))
            if pa["hash"] is not None:
                self._sup_pt[iid] = (pa["hash"], pts, pa["jp"])
            iids[pa["jp"]] = iid
        self._paint_support_tags()
        best = max((pa["points"] or 0) for pa in plist) if plist else 0
        self.sup_sub.configure(
            text=f"{len(plist)} partners · top {best:,} points · "
                 f"{seen_pairs} conversation{'s' if seen_pairs != 1 else ''} recorded "
                 f"in this save")
        if iids:
            target = iids.get(keep or "") or next(iter(iids.values()))
            self._sup_partner = next(k for k, v in iids.items() if v == target)
            self.sup_tree.selection_set(target)
            self.sup_tree.focus(target)
            self.sup_tree.see(target)
            self.on_support_pair()

    def on_support_pair(self, _e=None):
        """Mirror the selected pair's points into the editor row."""
        if not hasattr(self, "sup_pt_var"):
            return
        sel = self.sup_tree.selection() if hasattr(self, "sup_tree") else ()
        pt = getattr(self, "_sup_pt", {})
        if not sel or sel[0] not in pt:
            self.sup_pt_var.set("")
            self.sup_pt_lbl.configure(text="")
            return
        _h, pts, _jp = pt[sel[0]]
        self.sup_pt_var.set("" if pts is None else str(pts))
        name = self.sup_tree.item(sel[0], "text")
        self.sup_pt_lbl.configure(
            text=(f"{name}: {pts:,} of {supports.max_points():,} points")
            if pts is not None else f"{name}: no entry in this save")

    def _paint_support_tags(self):
        p = self.p
        if hasattr(self, "sup_tree"):
            self.sup_tree.tag_configure("sup_seen", foreground=p["fg"])
            self.sup_tree.tag_configure("sup_none", foreground=p["muted"])

    def _bind_keys(self):
        self.bind_all("<Control-s>", lambda e: self.save_all())
        self.bind_all("<Control-o>", lambda e: self.open_dialog())
        self.bind_all("<Control-f>", self._focus_search)
        self.bind_all("<Control-a>", self._select_all_focused)
        self.bind_all("<F5>", lambda e: self.reload())
        self.bind_all("<Control-z>", lambda e: (self.undo(), "break")[1])
        self.bind_all("<Control-y>", lambda e: (self.redo(), "break")[1])
        self.bind("<FocusIn>", lambda e: self.after_idle(self._check_disk)
                  if e.widget is self else None)

    def _select_all_focused(self, _e=None):
        """Ctrl+A in a table selects every row; elsewhere it stays normal."""
        w = self.focus_get()
        if not isinstance(w, ttk.Treeview):
            w = last_tree()
        if isinstance(w, ttk.Treeview):
            rows = w.get_children("")
            if rows:
                w.selection_set(rows)
                w.focus(rows[-1])
            return "break"
        return None

    def _focus_search(self, _e=None):
        """Ctrl+F jumps to the search box of whatever page is showing."""
        sel = self.pages.select()
        target = None
        if sel == str(self.units_page):
            tab = self.unit_tabs.index(self.unit_tabs.select())
            target = {2: self.inv_picker.search, 3: self.class_search}.get(tab, self.unit_search)
        elif sel == str(self.convoy_page):
            target = self.conv_picker.search
        elif sel == str(self.supports_page):
            target = self.sup_search
        elif sel == str(self.flags_page):
            target = self.flag_search
        elif sel == str(self.classes_page):
            target = self.cls_search
        elif sel == str(self.mounts_page):
            target = None
        if target is None:
            return
        target.focus_set()
        target.select_range(0, "end")
        return "break"

    def flash(self, msg: str, kind: str = "info"):
        style = {"info": "Status.TLabel", "warn": "StatusWarn.TLabel",
                 "ok": "StatusOk.TLabel", "error": "StatusErr.TLabel"}[kind]
        self.status_lbl.configure(text=msg, style=style)

    def _mirror_changed(self):
        self._save_settings()
        self.flash("Edits now also go into this route's other saves (never chapter "
                   "checkpoints)." if self.mirror.get()
                   else "Edits now go into the selected slot only.")

    def _show_welcome(self):
        self.unit_name.configure(text="No save folder open")
        self.unit_sub.configure(text="Use “Open folder…” (Ctrl+O) and pick any slot file "
                                     "(Auto, Chapter_*, Route_*) inside your save folder.")
        self.flash("No Eden save folder found automatically — open one to begin.", "warn")

    # ============================================================== files
    def _slot_files(self, folder: str) -> list[str]:
        out = []
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if is_slot_name(name) and os.path.isfile(path):
                out.append(path)
        # Auto (the live save) first, then the rest newest first
        out.sort(key=lambda pth: (os.path.basename(pth) != "Auto", -os.path.getmtime(pth)))
        return out

    def _get(self, path: str) -> SaveFile | None:
        """Cached SaveFile; re-read from disk when the game changed it (and we didn't)."""
        key = os.path.abspath(path)
        sv = self.files.get(key)
        try:
            mtime = os.path.getmtime(key)
        except OSError:
            return sv
        if sv is not None and (key in self.dirty or self.mtimes.get(key) == mtime):
            return sv
        try:
            sv = SaveFile(key)
        except Exception as exc:  # noqa: BLE001 — any unreadable slot is just skipped
            self.files.pop(key, None)
            self.flash(f"Can't read {os.path.basename(key)}: {exc}", "error")
            return None
        self.files[key] = sv
        self.mtimes[key] = mtime
        return sv

    def open_dialog(self):
        if not self._confirm_discard("open another folder"):
            return
        start = self.folder or default_save_dir() or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            parent=self, initialdir=start, title="Open any slot in your save folder",
            filetypes=[("Save slots", "Auto Chapter_* Route_*"), ("All files", "*.*")])
        if not path:
            return
        self.open_folder(os.path.dirname(path), prefer=path)

    def open_folder(self, folder: str, prefer: str | None = None):
        slots = self._slot_files(folder)
        if not slots and prefer:
            slots = [prefer]
        if not slots:
            messagebox.showerror(APP_NAME, f"No Auto / Chapter_* / Route_* slots in\n{folder}")
            return
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            self.folder = folder
            self.files.clear()
            self.mtimes.clear()
            self.dirty.clear()
            self.slot_paths = [os.path.abspath(p) for p in slots]
            for pth in self.slot_paths:
                self._get(pth)
            self._save_settings()
            target = os.path.abspath(prefer) if prefer else self._default_slot()
            self._populate_slot_box()
            self.load(target)
        finally:
            self.config(cursor="")

    def _default_slot(self) -> str:
        """Auto is the live save the game continues from; open it first."""
        for pth in self.slot_paths:
            if os.path.basename(pth) == "Auto":
                return pth
        return self.slot_paths[0]

    def _populate_slot_box(self):
        labels = []
        for pth in self.slot_paths:
            sv = self.files.get(pth)
            mark = "● " if pth in self.dirty else ""
            base = os.path.basename(pth)
            star = "★ " if base == "Auto" else ""          # the live save
            # which lord / part / chapter the slot was saved in, read from the save
            route = layer.route_label(sv.payload) if sv else ""
            labels.append(f"{mark}{star}{base}  ·  {route + '  ·  ' if route else ''}"
                          f"{_fmt_time(os.path.getmtime(pth))}")
        self.slot_box.configure(values=labels)
        if self.sv is not None and self.sv.path in self.slot_paths:
            self.slot_box.current(self.slot_paths.index(self.sv.path))

    def on_slot_pick(self, _e=None):
        i = self.slot_box.current()
        if 0 <= i < len(self.slot_paths):
            self._commit_form()
            self.load(self.slot_paths[i])

    def load(self, path: str):
        path = os.path.abspath(path)
        sv = self._get(path)
        if sv is None:
            return
        keep = self.uid
        self.sv = sv
        self.uid = None
        if path in self.slot_paths:
            self.slot_box.current(self.slot_paths.index(path))
        self._update_file_label()
        peers = [os.path.basename(p) for p in self._peers()]
        if self._is_checkpoint(path):
            text = "Also edit this route's other saves (off in checkpoints)"
        elif peers:
            text = f"Also edit this route's other saves (+ {', '.join(peers)})"
        else:
            text = "Also edit this route's other saves (none here)"
        self.mirror_chk.configure(text=text)
        self.refresh_units(keep=keep)
        self.refresh_convoy()
        self.locate_gold()
        self.refresh_supports()
        self.refresh_core_pages()
        self.refresh_mounts()
        self._update_dirty()
        self.flash(f"Opened {os.path.basename(path)} — {self._visible_units()} units.")

    def _update_file_label(self):
        if not self.sv:
            self.file_lbl.configure(text="")
            return
        bad = self.sv.verify() if self.sv.path not in self.dirty else []
        folder = os.path.normpath(self.folder or os.path.dirname(self.sv.path))
        parts = folder.split(os.sep)
        shown = folder if len(parts) <= 4 else os.sep.join(["…"] + parts[-3:])
        self.file_lbl.configure(text=f"{shown}" + (f"   ⚠ {', '.join(bad)}" if bad else ""))

    def _changed_on_disk(self, path: str) -> bool:
        try:
            return os.path.getmtime(path) != self.mtimes.get(path)
        except OSError:
            return False

    def _check_disk(self, _e=None):
        """When the window comes back into focus, pick up saves the game made.

        A slot with no unsaved edits is simply re-read.  One with unsaved edits
        is left alone, and the warning in save_all() stops it overwriting the
        game's newer file.
        """
        if not self.folder or getattr(self, "_checking", False):
            return
        self._checking = True
        try:
            changed = [p for p in self.slot_paths if self._changed_on_disk(p)]
            if not changed:
                return
            clean = [p for p in changed if p not in self.dirty]
            if clean:
                for p in clean:
                    self.files.pop(p, None)
                    self._get(p)
                self._populate_slot_box()
                if self.sv is not None and self.sv.path in clean:
                    self._shown, self._skill_rows = {}, []
                    self.load(self.sv.path)
                self.flash("Picked up a newer save from the game: "
                           + ", ".join(os.path.basename(p) for p in clean), "ok")
            if len(clean) < len(changed):
                self.flash("The game saved a slot you have unsaved edits in. Saving now "
                           "would overwrite the game's progress. Reload to start again "
                           "from the game's save.", "warn")
        finally:
            self._checking = False

    def _confirm_discard(self, what: str) -> bool:
        if not self.dirty:
            return True
        ans = messagebox.askyesnocancel(
            APP_NAME, f"{len(self.dirty)} slot(s) have unsaved changes.\n\n"
                      f"Save them before you {what}?", parent=self)
        if ans is None:
            return False
        if ans:
            return self.save_all()
        return True

    def reload(self):
        if not self.folder:
            return
        if self.dirty and not messagebox.askyesno(
                APP_NAME, f"Reload from disk and throw away the unsaved changes in "
                          f"{len(self.dirty)} slot(s)?", parent=self):
            return
        cur = self.sv.path if self.sv else None
        self._shown, self._skill_rows = {}, []    # don't write the form into fresh data
        self.open_folder(self.folder, prefer=cur)
        self.flash("Re-read every slot from disk.", "ok")

    def save_all(self) -> bool:
        if not self.sv:
            return False
        self._commit_form()
        if not self.dirty:
            self.flash("Nothing to save — no changes yet.")
            return True
        newer = [p for p in self.dirty if self._changed_on_disk(p)]
        if newer and not messagebox.askyesno(
                APP_NAME, "The game has saved " + ", ".join(os.path.basename(p) for p in newer)
                + " since the editor read it.\n\nSaving now would replace that newer save "
                  "with the editor's older copy plus your edits, and anything you did in "
                  "game since would be lost.\n\nOverwrite anyway? (No = keep the game's "
                  "save; then press Reload and redo your edits.)", icon="warning", parent=self):
            self.flash("Not saved — the game's newer save was kept. Press Reload, then redo "
                       "your edits.", "warn")
            return False
        written, failed = [], []
        for pth in sorted(self.dirty, key=os.path.basename):
            sv = self.files.get(pth)
            if not sv:
                continue
            try:
                sv.save(pth)
                self.mtimes[pth] = os.path.getmtime(pth)
                self.dirty.discard(pth)
                written.append(os.path.basename(pth))
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{os.path.basename(pth)}: {exc}")
        self._populate_slot_box()
        self._update_file_label()
        self._update_dirty()
        if failed:
            messagebox.showerror(APP_NAME, "Some slots could not be written:\n\n"
                                 + "\n".join(failed) + "\n\nIs the game still running?")
            return False
        self.flash(f"Saved {', '.join(written)}. Originals kept as .bak next to each slot.",
                   "ok")
        return True

    def on_close(self):
        self._commit_form()
        if not self._confirm_discard("quit"):
            return
        self._save_settings()
        self.destroy()

    def _update_dirty(self):
        n = len(self.dirty)
        if n:
            self.dirty_lbl.configure(text=f"● {n} slot{'s' if n > 1 else ''} with unsaved "
                                          "changes  ·  Ctrl+S to save", style="StatusWarn.TLabel")
            self.save_btn.configure(text=f"Save ({n})", state="normal")
        else:
            self.dirty_lbl.configure(text="All changes saved" if self.sv else "",
                                     style="Status.TLabel")
            self.save_btn.configure(text="Save", state="normal" if self.sv else "disabled")
        self.revert_btn.configure(state="normal" if self.folder else "disabled")
        name = os.path.basename(self.sv.path) if self.sv else ""
        self.title(f"{'● ' if n else ''}{name + ' — ' if name else ''}{APP_NAME}")

    # ---------------------------------------------------------- targets
    @staticmethod
    def _party(sv: SaveFile) -> set[int]:
        return {u.uid for u in sv.units if not is_enemy(u)}

    def _same_route(self, other: SaveFile) -> bool:
        """True when `other` holds the same playthrough as the open slot.

        Each lord's route has its own party, convoy and gold (Auto may be
        Theodora's route while Route_Ism is Ishmael's).  Slots of one route
        share most of their party — an older Chapter_* slot just has fewer
        members — so at least half of the smaller party must overlap.
        """
        a, b = self._party(self.sv), self._party(other)
        if not a or not b:
            return False
        return len(a & b) * 2 >= min(len(a), len(b))

    @staticmethod
    def _is_checkpoint(path: str) -> bool:
        """Chapter_* slots are chapter checkpoints the game can rewind to."""
        return os.path.basename(path).startswith("Chapter_")

    def _peers(self) -> list[str]:
        """Other slots an edit is mirrored into: the same route's live saves.

        Chapter_* checkpoints are never included — they are the points the
        game's "go back in time" feature returns to, so each keeps its own
        state.  When the open slot is itself a checkpoint, nothing is
        mirrored: editing one point in time leaves the others alone.
        """
        if not self.sv or self._is_checkpoint(self.sv.path):
            return []
        out = []
        for pth in self.slot_paths:
            if pth == self.sv.path or self._is_checkpoint(pth):
                continue
            sv = self._get(pth)
            if sv is not None and self._same_route(sv):
                out.append(pth)
        return out

    def _targets(self) -> list[SaveFile]:
        """The open slot, plus the same route's live saves when mirroring."""
        if not self.sv:
            return []
        out = [self.sv]
        if self.mirror.get():
            out += [self.files[p] for p in self._peers()]
        return out

    def _touch(self, svs):
        before = set(self.dirty)
        for sv in svs:
            self.dirty.add(sv.path)
        if self.dirty != before:
            self._populate_slot_box()
        self._update_dirty()

    def _read_only(self) -> bool:
        """Enemy / NPC records are only partly understood (their stat block is
        found one field off for some), so they can be viewed but not edited."""
        u = self._current()
        if u is not None and is_enemy(u):
            self.flash("Enemy and NPC records are read-only — their layout isn't fully "
                       "known, so an edit could land on the wrong bytes.", "warn")
            return True
        return False

    def _edit_units(self, fn) -> tuple[int, int]:
        """fn(record, savefile) -> bool for every copy of the shown unit.

        Returns (copies changed, slots changed).
        """
        if self._read_only():
            return 0, 0
        self.push_undo()
        copies, touched = 0, []
        for sv in self._targets():
            hit = 0
            for r in sv.units:
                if r.uid == self.uid and fn(r, sv) is not False:
                    hit += 1
            if hit:
                copies += hit
                touched.append(sv)
        self._touch(touched)
        return copies, len(touched)

    def _where(self, copies: int, slots: int) -> str:
        c = f"{copies} cop{'y' if copies == 1 else 'ies'}"
        return c if slots <= 1 else f"{c} in {slots} slots"

    # ============================================================== units
    def _unit_map(self) -> dict[int, object]:
        groups: dict[int, list] = {}
        for u in (self.sv.units if self.sv else []):
            groups.setdefault(u.uid, []).append(u)
        return {uid: pick_live(recs) for uid, recs in groups.items()}

    def refresh_units(self, keep: int | None = None):
        if keep is None:
            keep = self.uid
        tree = self.unit_tree
        tree.delete(*tree.get_children())
        q = self.unit_search.get_query().lower()
        units = sorted(self._unit_map().values(),
                       key=lambda u: (is_enemy(u), u.name.lower()))
        shown = 0
        for u in units:
            enemy = is_enemy(u)
            if enemy and not self.show_enemies.get():
                continue
            if q and q not in f"{u.name} {u.pid} {u.job}".lower():
                continue
            tree.insert("", "end", iid=str(u.uid), text=" " + u.name,
                        image=self._dot(_name_color(u.name), 10),
                        values=(u.level,), tags=("enemy",) if enemy else ())
            shown += 1
        total = sum(1 for u in units if self.show_enemies.get() or not is_enemy(u))
        self.unit_count.configure(text=f"{shown}" if shown == total else f"{shown} / {total}")
        kids = tree.get_children()
        if keep is not None and tree.exists(str(keep)):
            pick = str(keep)
        else:
            pick = kids[0] if kids else None
        if pick:
            tree.selection_set(pick)
            tree.see(pick)
            if self.uid != int(pick):
                self.on_unit_select()
        else:
            self._clear_unit_form()

    def _tree_lv(self, uid: int, lv: int):
        if self.unit_tree.exists(str(uid)):
            self.unit_tree.set(str(uid), "lv", lv)

    def _clear_unit_form(self):
        self.uid = None
        self._shown = {}
        self._skill_rows = []
        self.avatar.show("")
        self.unit_name.configure(text="No unit selected" if self.sv else "No save folder open")
        self.unit_sub.configure(text="" if self.sv else "Open a save folder to begin.")
        self.copies_chip.configure(text="")
        self.sync_btn.pack_forget()
        for v in self.stat_vars + [self.lvl_var, self.exp_var]:
            v.set("")
        for tree in getattr(self, "_skill_trees", {}).values():
            tree.delete(*tree.get_children())
        self.inv_tree.delete(*self.inv_tree.get_children())
        self.class_now.configure(text="—")

    def _current(self):
        if not self.sv or self.uid is None:
            return None
        recs = [r for r in self.sv.units if r.uid == self.uid]
        return pick_live(recs) if recs else None

    def on_unit_select(self, _e=None):
        sel = self.unit_tree.selection()
        if not sel:
            return
        uid = int(sel[0])
        if uid != self.uid:
            self._commit_form()       # flush a half-typed value into the PREVIOUS unit
        self.uid = uid
        self.show_unit()

    def show_unit(self):
        u = self._current()
        if not u:
            self._clear_unit_form()
            return
        self.avatar.show(u.name, u.pid)
        self.unit_name.configure(text=u.name)
        pid = u.pid.replace("PID_", "")
        self.unit_sub.configure(text=f"{u.job}   ·   Level {u.level}   ·   {pid}")
        # what the form shows; a field only writes when it differs from this, so
        # tabbing through fields never copies untouched values into other slots
        self._shown = {"lvl": u.level, "exp": u.exp, **dict(enumerate(u.stats))}
        self.lvl_var.set(str(u.level))
        self.exp_var.set(str(u.exp))
        self.exp_bar.set(min(u.exp, 100) / 100)
        self.maxhp_lbl.configure(text=str(u.max_hp) if u.max_hp else "—")
        top = max(40, max(u.stats))
        for i, v in enumerate(self.stat_vars):
            v.set(str(u.stats[i]))
            self.stat_bars[i].set(u.stats[i] / top)
        self._update_copies_chip(u)
        self.refresh_skills()
        self.refresh_inventory()
        self.class_now.configure(text=u.job)
        self.refresh_classes()

    def _update_copies_chip(self, u):
        """One record per unit now: the chip says what the game will read."""
        self.sync_btn.pack_forget()
        enemy = is_enemy(u)
        for sp in self._stat_spins:
            sp.configure(state="disabled" if enemy else "normal")
        if enemy:
            self.copies_chip.configure(text="🔒 Enemy / NPC — read-only", style="ChipWarn.TLabel")
        else:
            self.copies_chip.configure(
                text=f"live record · {u.job}", style="Chip.TLabel")


    def _num(self, var, lo, hi):
        try:
            v = int(str(var.get()).replace(",", "").strip())
        except (TypeError, ValueError):
            return None
        return v if lo <= v <= hi else None

    def _commit_form(self):
        """Write any value still sitting in a field (typed but not yet applied)."""
        if self.uid is None or not self.sv:
            return
        self.commit_level()
        self.commit_exp()
        for i in range(len(STAT_NAMES)):
            self.commit_stat(i)


    def _bad_input(self, var, lo, hi, current, label):
        var.set(str(current))
        self.flash(f"{label} must be a number from {lo} to {hi}.", "warn")

    def commit_level(self):
        u = self._current()
        if not u or self.lvl_var.get() == "":
            return
        v = self._num(self.lvl_var, 1, 99)
        if v is None:
            return self._bad_input(self.lvl_var, 1, 99, u.level, "Level")
        if v == self._shown.get("lvl"):
            return
        self._shown["lvl"] = v

        def fn(r, sv):
            if r.level == v:
                return False
            r.set_level(v, sv.payload)
            r.level = v
        n, s = self._edit_units(fn)
        if n:
            self._tree_lv(u.uid, v)
            self.unit_sub.configure(text=f"{u.job}   ·   Level {v}   ·   {u.pid.replace('PID_', '')}")
            self._update_copies_chip(u)
            self.flash(f"{u.name}: level → {v}  ({self._where(n, s)})")

    def commit_exp(self):
        u = self._current()
        if not u or self.exp_var.get() == "":
            return
        v = self._num(self.exp_var, 0, 99)
        if v is None:
            return self._bad_input(self.exp_var, 0, 99, u.exp, "EXP")
        if v == self._shown.get("exp"):
            return
        self._shown["exp"] = v

        def fn(r, sv):
            if r.exp == v:
                return False
            r.set_exp(v, sv.payload)
            r.exp = v
        n, s = self._edit_units(fn)
        self.exp_bar.set(min(v, 100) / 100)
        if n:
            self._update_copies_chip(u)
            self.flash(f"{u.name}: EXP → {v}  ({self._where(n, s)})")

    def commit_stat(self, i: int):
        u = self._current()
        var = self.stat_vars[i]
        if not u or var.get() == "":
            return
        v = self._num(var, 0, STAT_MAX)
        if v is None:
            return self._bad_input(var, 0, STAT_MAX, u.stats[i], STAT_NAMES[i])
        if v == self._shown.get(i):
            return
        self._shown[i] = v

        def fn(r, sv):
            if r.stats[i] == v:
                return False
            if i == 0:
                self._move_max_hp(r, sv, v - r.stats[0])
            r.set_stat(i, v, sv.payload)
            r.stats[i] = v
        n, s = self._edit_units(fn)
        self.maxhp_lbl.configure(text=str(u.max_hp) if u.max_hp else "—")
        top = max(40, max(u.stats))
        for k, bar in enumerate(self.stat_bars):
            bar.set(u.stats[k] / top)
        if n:
            self._update_copies_chip(u)
            self.flash(f"{u.name}: {STAT_LONG[STAT_NAMES[i]]} → {v}  ({self._where(n, s)})")

    @staticmethod
    def _move_max_hp(r, sv, delta: int):
        """Keep max HP = base + HP gained (true in every unedited save checked)."""
        if delta and r.max_hp:
            new = max(1, min(999, r.max_hp + delta))
            r.set_hp(new, sv.payload)
            r.max_hp = new

    def sync_copies(self):
        u = self._current()
        if not u:
            return
        lv = self._num(self.lvl_var, 1, 99)
        ex = self._num(self.exp_var, 0, 255)
        stats = [self._num(v, 0, STAT_MAX) for v in self.stat_vars]
        if lv is None or ex is None or None in stats:
            self.flash("One of the fields isn't a valid number.", "warn")
            return

        def fn(r, sv):
            r.set_level(lv, sv.payload)
            r.set_exp(ex, sv.payload)
            r.level, r.exp = lv, ex
            self._move_max_hp(r, sv, stats[0] - r.stats[0])
            for k, val in enumerate(stats):
                r.set_stat(k, val, sv.payload)
                r.stats[k] = val
        n, s = self._edit_units(fn)
        self._shown = {"lvl": lv, "exp": ex, **dict(enumerate(stats))}
        self._tree_lv(u.uid, lv)
        self._update_copies_chip(u)
        self.flash(f"{u.name}: every copy now matches the values shown ({self._where(n, s)})",
                   "ok")

    # ---------------------------------------------------------- ranks
    def refresh_skills(self):
        self.refresh_skill_lists()







    # ------------------------------------------------------- inventory
    def refresh_inventory(self):
        tree = self.inv_tree
        prev = tree.selection()
        tree.delete(*tree.get_children())
        u = self._current()
        self._inv_items = []
        if not u:
            return
        inv = u.inventory(bytes(self.sv.payload))
        names = item_ids()
        if inv is None:
            tree.insert("", "end", iid="none", text="  Couldn't find this unit's item list",
                        tags=("empty",))
            self._inv_lock()
            return
        self._inv_items = inv.items
        for n, (_off, iid, _tag) in enumerate(inv.items):
            meta = names.get(iid, {})
            kind = item_kind(meta) if meta else "Item"
            tree.insert("", "end", iid=f"i{n}", text=f" {n + 1}.  {item_label(iid, meta)}",
                        image=self.item_icon(iid, meta, kind), values=(kind,))
        if not inv.items:
            tree.insert("", "end", iid="none", text="  Carrying nothing", tags=("empty",))
        if inv.spells:
            tree.insert("", "end", iid="spells", text="  SPELLS  (read-only)",
                        tags=("header",))
            for n, (_off, iid, _tag) in enumerate(inv.spells):
                meta = names.get(iid, {})
                tree.insert("", "end", iid=f"s{n}", text="      " + item_label(iid, meta),
                            image=self._dot(KIND_COLORS["Tome"]), values=("Spell",),
                            tags=("empty",))
        if prev and tree.exists(prev[0]) and prev[0].startswith("i"):
            tree.selection_set(prev[0])
        self._inv_lock()

    def _inv_slot(self) -> int | None:
        sel = self.inv_tree.selection()
        if not sel or not sel[0].startswith("i"):
            return None
        return int(sel[0][1:])

    def _inv_lock(self):
        idx = self._inv_slot()
        cat = None
        if idx is not None and idx < len(self._inv_items):
            cat = item_category(item_ids().get(self._inv_items[idx][1], {}))
        self.inv_picker.set_lock(cat, self.allow_any_item.get())

    def replace_item(self, new_id: int):
        idx = self._inv_slot()
        u = self._current()
        if u is None or idx is None:
            self.flash("Pick an inventory slot first.", "warn")
            return
        old = self._inv_items[idx][1] if idx < len(self._inv_items) else None
        if new_id == old:
            self.flash("That slot already holds this item.")
            return
        self.push_undo()
        changed = False
        for sv in self._targets():
            if layer.set_item(sv.payload, u.uid, idx, new_id):
                sv.scan()
                sv._core_cache = None
                changed = True
        if not changed:
            self.flash("Nothing changed — that unit has no such item slot here.", "warn")
            return
        self._touch(self._targets())
        self.refresh_inventory()
        self.flash(f"{u.name}: slot {idx + 1} → {item_label(new_id)}")

    def add_item(self):
        u = self._current()
        if u is None:
            self.flash("Pick a unit first.", "warn")
            return
        new_id = self.inv_picker.selected()
        if new_id is None:
            self.flash("Pick an item from the catalogue first.", "warn")
            return
        self.push_undo()
        for sv in self._targets():
            layer.add_item(sv.payload, u.uid, new_id)
            sv.scan()
            sv._core_cache = None
        self._touch(self._targets())
        self.refresh_inventory()
        self.flash(f"{u.name}: added {item_label(new_id)}")

    def remove_item(self):
        idx = self._inv_slot()
        u = self._current()
        if u is None or idx is None:
            self.flash("Pick an inventory slot first.", "warn")
            return
        self.push_undo()
        for sv in self._targets():
            layer.remove_item(sv.payload, u.uid, idx)
            sv.scan()
            sv._core_cache = None
        self._touch(self._targets())
        self.refresh_inventory()
        self.flash(f"{u.name}: removed the item in slot {idx + 1}")


    # ----------------------------------------------------------- class
    def refresh_classes(self):
        if not hasattr(self, "class_tree"):
            return
        tree = self.class_tree
        tree.delete(*tree.get_children())
        q = self.class_search.get_query().lower()
        show_all = self.show_bad_classes.get()
        u = self._current()
        cur = u.job_hash if u else None
        rows = []
        for h, m in job_ids().items():
            en = m.get("en") or ""
            jp = (m.get("jp") or "").replace("JID_", "")
            if not en and not show_all:
                continue
            if q and q not in f"{en} {jp} {h:08x}".lower():
                continue
            rows.append((en.lower() or "~" + jp, h, en or f"({jp})", jp))
        rows.sort()
        for _k, h, en, jp in rows:
            tree.insert("", "end", iid=f"{h:08x}", text=("✓  " if h == cur else "    ") + en,
                        values=(jp,))
        if cur is not None and tree.exists(f"{cur:08x}"):
            tree.selection_set(f"{cur:08x}")
            tree.see(f"{cur:08x}")

    def apply_class(self):
        u = self._current()
        sel = self.class_tree.selection()
        if not u or not sel:
            self.flash("Pick a class from the list first.", "warn")
            return
        if self._read_only():
            return
        new_hash = int(sel[0], 16)
        if new_hash == u.job_hash:
            self.flash(f"{u.name} is already a {u.job}.")
            return
        name = job_name(new_hash)
        n = len(self._targets())
        scope = f"{n} saves of this route" if n > 1 else "this slot"
        if not messagebox.askyesno(
                "Change class",
                f"Change {u.name} from {u.job} to {name} in {scope}?\n\n"
                "Only the class id is written. Movement, usable weapons, class skills and "
                "max HP are not recalculated. Nothing hits the disk until you Save.",
                parent=self):
            return
        touched, ids = [], 0
        for sv in self._targets():
            hit = sv.set_class(self.uid, new_hash)
            if hit:
                ids += hit
                touched.append(sv)
        self._touch(touched)
        self.flash(f"{u.name}: class → {name}  ({ids} ids in {len(touched)} slot(s))")
        self.show_unit()

    # ========================================================== convoy
    def refresh_convoy(self, select: list[int] | None = None):
        """List the live convoy.  Tree ids are slot numbers."""
        tree = self.conv_tree
        prev = select if select is not None else [int(i) for i in tree.selection()
                                                  if i.isdigit()]
        tree.delete(*tree.get_children())
        conv = live_convoy(bytes(self.sv.payload)) if self.sv else None
        # live_convoy() returns every slot; only the filled ones are items
        self._conv_rows = [r for r in (conv.rows if conv else []) if r.qty and r.iid]
        names = item_ids()
        q = self.conv_filter.get_query().lower()
        shown = 0
        for row in self._conv_rows:
            meta = names.get(row.iid, {})
            kind = item_kind(meta) if meta else "Item"
            label = item_label(row.iid, meta)
            if q and not all(t in f"{label} {meta.get('jp', '')} {kind}".lower()
                             for t in q.split()):
                continue
            tree.insert("", "end", iid=str(row.slot), text=f" {row.slot + 1:>4} · {label}",
                        image=self.item_icon(row.iid, meta, kind), values=(kind, row.qty))
            shown += 1
        salvage = None
        if conv is None and self.sv:
            salvage = layer.salvage_convoy(bytes(self.sv.payload))
        if conv is None:
            tree.insert("", "end", iid="none",
                        text="  This slot's convoy list is damaged — see above" if salvage
                        else "  No convoy list found in this slot", tags=("empty",))
        total = len(self._conv_rows)
        self.conv_count.configure(text="" if conv is None else
                                  f"{total} items · {conv.slots} slots" if shown == total
                                  else f"{shown} of {total} items")
        if salvage:
            n_items = sum(1 for sl in salvage[1] if sl.item)
            self.conv_problem_lbl.configure(
                text="⚠ This convoy list is damaged: an older version's “Add” wrote an item "
                     "over empty slots and knocked the rest of the list out of line, so the "
                     f"game can't read it. Repair rebuilds it as a clean {salvage[0]}-slot "
                     f"list keeping all {n_items} items it can still find. Undo works, and "
                     "the original stays in the slot's .bak.")
            self.conv_repair_btn.pack(anchor="w", pady=(6, 0))
            self.conv_problem.pack(fill="x", pady=(0, 6), before=self.conv_filter)
        else:
            self.conv_problem.pack_forget()
        keep = [str(i) for i in prev if tree.exists(str(i))]
        if keep:
            tree.selection_set(keep)
            tree.see(keep[-1])

    def repair_convoy_ui(self):
        got = layer.salvage_convoy(bytes(self.sv.payload)) if self.sv else None
        if not got:
            self.flash("This slot's convoy doesn't need repairing.")
            return
        n_items = sum(1 for sl in got[1] if sl.item)
        if not messagebox.askyesno(
                "Repair convoy",
                f"Rebuild this slot's convoy as a clean {got[0]}-slot list with the "
                f"{n_items} items found in it?\n\nNothing is written until you Save, "
                "Undo can take it back, and the original stays in the slot's .bak.",
                parent=self):
            return
        self.push_undo()
        if self._core_edit(lambda f: (layer.repair_convoy(f.payload) >= 0 and f.payload) or None,
                           "Repair convoy"):
            self.flash(f"Convoy repaired: {n_items} items, {got[0]} slots — Ctrl+S to write it.",
                       "ok")
        self.refresh_convoy()

    def _conv_row(self, slot: int):
        return next((r for r in self._conv_rows if r.slot == slot), None)

    def _conv_selected(self) -> list[int]:
        return sorted(int(i) for i in self.conv_tree.selection() if i.isdigit())

    def _conv_row_picked(self, _e=None):
        slots = self._conv_selected()
        if len(slots) == 1:
            row = self._conv_row(slots[0])
            if row:
                self.qty_var.set(str(row.qty))

    def _qty(self) -> int | None:
        v = self._num(self.qty_var, 1, QTY_MAX)
        if v is None:
            self.flash(f"Quantity must be 1 – {QTY_MAX}.", "warn")
        return v

    def _convoy_edit(self, slots: list[int], fn) -> int:
        """fn(payload, row) for the given slots of the live list in every target.

        In other saves a slot is only touched when it holds the same item as
        here, so a list that has moved on is left alone.
        """
        self.push_undo()
        want = {s: self._conv_row(s).iid for s in slots if self._conv_row(s)}
        touched = []
        for sv in self._targets():
            conv = live_convoy(bytes(sv.payload))
            if conv is None:
                continue
            hit = False
            for row in conv.rows:
                if row.slot in want and row.iid == want[row.slot]:
                    fn(sv.payload, row)
                    hit = True
            if hit:
                touched.append(sv)
        self._touch(touched)
        return len(touched)

    def replace_convoy(self, iid: int):
        slots = self._conv_selected()
        if len(slots) != 1:
            self.flash("Select one convoy row to replace (any spare item you put there in "
                       "game).", "warn")
            return
        row = self._conv_row(slots[0])
        if row.iid == iid:
            self.flash("That row already holds this item.")
            return
        old = item_label(row.iid)
        n = self._convoy_edit(slots, lambda p, r: set_convoy_item(p, r, iid))
        self.refresh_convoy(select=slots)
        self.flash(f"Convoy slot {slots[0] + 1}: {old} → {item_label(iid)}"
                   + (f" in {n} saves" if n > 1 else ""))

    def set_convoy_qty(self):
        slots = self._conv_selected()
        if not slots:
            self.flash("Select a convoy row first.", "warn")
            return
        qty = self._qty()
        if qty is None:
            return
        n = self._convoy_edit(slots, lambda p, r: set_convoy_qty(p, r, qty))
        self.refresh_convoy(select=slots)
        self.flash(f"Quantity → {qty} on {len(slots)} row(s)" + (f" in {n} saves" if n > 1 else ""))

    # ============================================================ gold
    def _show_gold(self, val: int | None, hint: str):
        self.gold_now.configure(text="—" if val is None else f"{val:,}")
        self.gold_hint.configure(text=hint)

    def locate_gold(self):
        self.gold_auto = False
        self.money_off = None
        if not self.sv:
            return self._show_gold(None, "")
        cur = current_gold(bytes(self.sv.payload))
        if cur is None:
            return self._show_gold(None, "This slot has no GameUserData record.")
        self.money_off = cur[1]
        self.gold_auto = True
        self._show_gold(cur[0], "Read from this slot's own record.")


    def find_gold(self):
        """Gone: gold has a fixed address."""
        self.flash("Gold is read straight from the save — nothing to search for.", "info")


    def on_gold_pick(self, _e=None):
        return None


    def set_gold(self):
        if not self.sv:
            return
        try:
            val = int(self.gold_new.get().replace(",", "").strip())
        except ValueError:
            self.flash("Type the new gold amount as a number.", "warn")
            return
        if not 0 <= val <= 0xFFFFFFFF:
            self.flash("Gold must be between 0 and 4,294,967,295.", "warn")
            return
        self.push_undo()
        touched = [sv for sv in self._targets() if write_gold(sv.payload, val)]
        self._touch(touched)
        self.locate_gold()
        self.flash(f"Gold → {val:,}" + (f" in {len(touched)} slots" if len(touched) > 1 else ""))


    def _set_gold_auto(self):
        self.set_gold()



def _dpi_aware():
    """Ask Windows for real pixels instead of a blurry bitmap-stretched window:
    per-monitor (2), else system-wide (1), else the pre-8.1 call."""
    if sys.platform != "win32":
        return
    import ctypes
    for mode in (2, 1):
        try:
            if ctypes.windll.shcore.SetProcessDpiAwareness(mode) == 0:
                return
        except Exception:  # noqa: BLE001
            break
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001
        pass


def _install_scaling(root) -> float:
    """The display's scale against 96 dpi (1.0, 1.25, 1.5, 2.0…).  Treeview
    column widths are plain pixels while fonts grow with the DPI, so widths
    set with .column() are scaled to match."""
    try:
        scale = max(1.0, root.winfo_fpixels("1i") / 96.0)
    except tk.TclError:
        scale = 1.0
    if scale > 1.0 and not getattr(ttk.Treeview, "_fefw_scaled", False):
        orig = ttk.Treeview.column

        def column(self, column, option=None, **kw):
            for k in ("width", "minwidth"):
                if isinstance(kw.get(k), int):
                    kw[k] = int(round(kw[k] * scale))
            return orig(self, column, option, **kw)

        ttk.Treeview.column = column
        ttk.Treeview._fefw_scaled = True
    return scale


def main():
    _dpi_aware()
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and os.path.isfile(arg):
        arg = os.path.dirname(arg)
    App(arg).mainloop()


if __name__ == "__main__":
    main()
