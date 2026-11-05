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
from fefw_save import USER_DIR  # noqa: E402
from fefw_save import (GRADES, ITEM_KINDS, SKILL_NAMES, SKILL_THRESHOLDS,  # noqa: E402
                       STAT_NAMES, SaveError, SaveFile, add_convoy_item, convoy_blocks,
                       default_save_dir, find_money_candidates, grade_label, grade_of,
                       is_enemy, is_shadow, is_slot_name, item_category, item_ids,
                       item_kind, item_label, job_ids, job_name, load_money_sig,
                       locate_money, money_signature, next_threshold, pick_live,
                       save_money_sig, set_convoy_row)

APP_NAME = "Fortune's Weave Save Editor"
__version__ = "1.0.2"
SETTINGS_PATH = os.path.join(USER_DIR, "editor_settings.json")
ICON_DIR = os.path.join(USER_DIR, "icons")

STAT_MAX = 255          # the record parser rejects stat blocks with values >= 300
SKILL_MAX = 9999        # find_skills() stops recognising a table above this
QTY_MAX = 999           # convoy_blocks() stops recognising a row above this

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
class App(tk.Tk):
    def __init__(self, folder: str | None = None):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1240x780")
        self.minsize(1000, 640)

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
        self._gold_cands: list[int] = []
        self._inv_items: list[tuple[int, int, int]] = []
        self._conv_rows: list[tuple[int, int, int]] = []
        self._skill_rows: list = []
        self._shown: dict = {}
        self._skill_shown: dict[int, int] = {}
        self._flash_job = None

        self.mirror = tk.BooleanVar(value=self.settings.get("mirror", True))
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
        self.settings.update(theme=self.theme_name(), mirror=bool(self.mirror.get()),
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
                    foreground=p["fg"], rowheight=28, borderwidth=0, relief="flat",
                    font=self.f_body)
        s.map("Treeview", background=[("selected", p["sel"])],
              foreground=[("selected", p["fg"])])
        s.configure("Treeview.Heading", background=p["card"], foreground=p["faint"],
                    relief="flat", font=self.f_small, padding=(6, 6), borderwidth=0,
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
                    padding=(16, 8), borderwidth=0, font=self.f_bold,
                    lightcolor=p["bg"], bordercolor=p["bg"])
        s.map("TNotebook.Tab", background=[("selected", p["card"]), ("active", p["raised"])],
              foreground=[("selected", p["fg"]), ("active", p["fg"])],
              lightcolor=[("selected", p["accent"])],
              expand=[("selected", (0, 0, 0, 0))])
        s.configure("Main.TNotebook", background=p["side"], tabmargins=(12, 0, 0, 0))
        s.configure("Main.TNotebook.Tab", background=p["side"], padding=(20, 10),
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
        self.gold_tree.tag_configure("ctx", foreground=p["muted"])

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
        self.revert_btn = ttk.Button(right, text="Discard changes", command=self.reload)
        self.revert_btn.pack(side="right")

        mid = ttk.Frame(head, style="Header.TFrame")
        mid.pack(side="left", padx=(32, 0), fill="x", expand=True)
        r1 = ttk.Frame(mid, style="Header.TFrame")
        r1.pack(fill="x")
        ttk.Label(r1, text="Slot", style="Side.TLabel").pack(side="left")
        self.slot_var = tk.StringVar()
        self.slot_box = ttk.Combobox(r1, textvariable=self.slot_var, state="readonly", width=46)
        self.slot_box.pack(side="left", padx=(8, 8))
        self.slot_box.bind("<<ComboboxSelected>>", self.on_slot_pick)
        self.register_combo(self.slot_box)
        ttk.Button(r1, text="Open folder…", command=self.open_dialog).pack(side="left")
        r2 = ttk.Frame(mid, style="Header.TFrame")
        r2.pack(fill="x", pady=(6, 0))
        self.mirror_chk = ttk.Checkbutton(r2, text="Apply edits to this route's other saves",
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
        self.pages.add(self.units_page, text="Units")
        self.pages.add(self.convoy_page, text="Convoy")
        self.pages.add(self.gold_page, text="Gold")

        self._build_units()
        self._build_convoy()
        self._build_gold()
        self._style_trees()
        self._update_dirty()

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
        self._build_ranks_tab()
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
                                       ("EXP", self.exp_var, self.commit_exp, 0, 255)):
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

        ttk.Separator(tab).pack(fill="x", pady=16)

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
                  text="HP here is current HP — max HP isn't stored in the save; the game "
                       "derives it from class and stats. Stats are capped at 255. Changes "
                       "apply as you type (Enter / Tab) and are written when you Save."
                  ).pack(anchor="w", side="bottom")

    def _build_ranks_tab(self):
        tab = ttk.Frame(self.unit_tabs, style="Card.TFrame", padding=18)
        self.unit_tabs.add(tab, text="Weapon ranks")
        top = ttk.Frame(tab, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Set every rank to", style="Card.TLabel").pack(side="left")
        self.all_grade = tk.StringVar(value="A")
        cb = ttk.Combobox(top, textvariable=self.all_grade, values=GRADES, width=5,
                          state="readonly")
        cb.pack(side="left", padx=8)
        self.register_combo(cb)
        ttk.Button(top, text="Apply", command=self.apply_all_grades).pack(side="left")

        self.skill_frame = ttk.Frame(tab, style="Card.TFrame")
        self.skill_frame.pack(fill="x", pady=(16, 0))

        ttk.Label(tab, style="CardFaint.TLabel", wraplength=700, justify="left",
                  text="The stored number is cumulative rank EXP; the game turns it into a "
                       "letter (E 0 · D 100 · C 300 · B 680 · A 1320 · S 2520 · S+ 3600). "
                       "A unit only has rows for ranks it already owns — the rest read E in "
                       "game and can't be added from here."
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
        ttk.Label(left, text="Shared storage — what the convoy screen shows with no owner.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 8))
        ctl = ttk.Frame(left, style="Card.TFrame")
        ctl.pack(side="bottom", fill="x", pady=(10, 0))
        self.conv_tree = scrolled_tree(left, columns=("kind", "qty"), show="tree headings",
                                       selectmode="extended", height=6)
        self.conv_tree.heading("#0", text="Item", anchor="w")
        self.conv_tree.heading("kind", text="Type", anchor="w")
        self.conv_tree.heading("qty", text="Qty", anchor="e")
        self.conv_tree.column("#0", width=240)
        self.conv_tree.column("kind", width=90, stretch=False)
        self.conv_tree.column("qty", width=56, anchor="e", stretch=False)
        self.conv_tree.container.pack(fill="both", expand=True)
        self.conv_tree.bind("<<TreeviewSelect>>", self._conv_row_picked)
        self.conv_tree.bind("<Delete>", lambda e: self.clear_convoy())

        ttk.Label(ctl, text="Quantity", style="Card.TLabel").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Spinbox(ctl, from_=1, to=QTY_MAX, width=5, textvariable=self.qty_var,
                    validate="key", validatecommand=self._num_vcmd()
                    ).pack(side="left", padx=(8, 12))
        ttk.Button(ctl, text="Set qty", command=self.set_convoy_qty).pack(side="left")
        ttk.Button(ctl, text="Clear row", style="Danger.TButton",
                   command=self.clear_convoy).pack(side="right")

        right = ttk.Frame(pane, padding=(10, 0, 0, 0))
        pane.add(right, weight=1)
        self.conv_picker = ItemPicker(right, self, self.add_convoy, "Add to convoy")
        self.conv_picker.pack(fill="both", expand=True)
        self.conv_replace_btn = ttk.Button(self.conv_picker.action_btn.master,
                                           text="Replace selected row",
                                           command=self.replace_convoy)
        self.conv_replace_btn.pack(side="right", padx=(0, 8))

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

        find = ttk.Frame(wrap, style="Card.TFrame", padding=24)
        find.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(find, text="Locate gold in this slot", style="CardH3.TLabel").pack(anchor="w")
        ttk.Label(find, style="CardMuted.TLabel", wraplength=760, justify="left",
                  text="Gold has no fixed address. Type the amount the game is showing right "
                       "now, pick the match, and the editor remembers where it lives for "
                       "every later save. Only needed once — and it can't search for 0."
                  ).pack(anchor="w", pady=(4, 12))
        r = ttk.Frame(find, style="Card.TFrame")
        r.pack(anchor="w")
        ttk.Label(r, text="Gold shown in game", style="Card.TLabel").pack(side="left")
        self.gold_search = tk.StringVar()
        ge = ttk.Entry(r, textvariable=self.gold_search, width=14)
        ge.pack(side="left", padx=8)
        ge.bind("<Return>", lambda ev: self.find_gold())
        ttk.Button(r, text="Find", command=self.find_gold).pack(side="left")
        self.gold_tree = scrolled_tree(find, columns=("ctx",), show="tree headings",
                                       selectmode="browse", height=4)
        self.gold_tree.heading("#0", text="Offset", anchor="w")
        self.gold_tree.heading("ctx", text="Surrounding bytes", anchor="w")
        self.gold_tree.column("#0", width=120, stretch=False)
        self.gold_tree.column("ctx", width=500)
        self.gold_tree.container.pack(fill="both", expand=True, pady=(12, 0))
        self.gold_tree.bind("<<TreeviewSelect>>", self.on_gold_pick)

    # --------------------------------------------------------- keys / misc
    def _bind_keys(self):
        self.bind_all("<Control-s>", lambda e: self.save_all())
        self.bind_all("<Control-o>", lambda e: self.open_dialog())
        self.bind_all("<Control-f>", self._focus_search)
        self.bind_all("<F5>", lambda e: self.reload())

    def _focus_search(self, _e=None):
        page = self.pages.index(self.pages.select())
        if page == 0:
            tab = self.unit_tabs.index(self.unit_tabs.select())
            target = {2: self.inv_picker.search, 3: self.class_search}.get(tab, self.unit_search)
        elif page == 1:
            target = self.conv_picker.search
        else:
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
        out.sort(key=lambda pth: os.path.getmtime(pth), reverse=True)
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
            target = os.path.abspath(prefer) if prefer else self.slot_paths[0]
            self._populate_slot_box()
            self.load(target)
        finally:
            self.config(cursor="")

    def _populate_slot_box(self):
        labels = []
        newest = self.slot_paths[0] if self.slot_paths else None
        for pth in self.slot_paths:
            sv = self.files.get(pth)
            n = len({u.uid for u in sv.units if not is_enemy(u)}) if sv else 0
            mark = "● " if pth in self.dirty else ""
            tag = "   ★ newest" if pth == newest and len(self.slot_paths) > 1 else ""
            labels.append(f"{mark}{os.path.basename(pth)}  ·  {n} units  ·  "
                          f"{_fmt_time(os.path.getmtime(pth))}{tag}")
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
            text = "Apply edits to this route's other saves (off for chapter checkpoints)"
        elif peers:
            text = f"Apply edits to this route's other saves (also {', '.join(peers)})"
        else:
            text = "Apply edits to this route's other saves (none — this slot only)"
        self.mirror_chk.configure(text=text)
        self.refresh_units(keep=keep)
        self.refresh_convoy()
        self.locate_gold()
        self._update_dirty()
        self.flash(f"Opened {os.path.basename(path)} — {len(self._unit_map())} units.")

    def _update_file_label(self):
        if not self.sv:
            self.file_lbl.configure(text="")
            return
        bad = self.sv.verify() if self.sv.path not in self.dirty else []
        folder = os.path.normpath(self.folder or os.path.dirname(self.sv.path))
        parts = folder.split(os.sep)
        shown = folder if len(parts) <= 4 else os.sep.join(["…"] + parts[-3:])
        self.file_lbl.configure(text=f"{shown}" + (f"   ⚠ {', '.join(bad)}" if bad else ""))

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
                APP_NAME, f"Throw away unsaved changes in {len(self.dirty)} slot(s) and "
                          "re-read everything from disk?", parent=self):
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
            self.revert_btn.configure(state="normal")
        else:
            self.dirty_lbl.configure(text="All changes saved" if self.sv else "",
                                     style="Status.TLabel")
            self.save_btn.configure(text="Save", state="normal" if self.sv else "disabled")
            self.revert_btn.configure(state="disabled")
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
        for w in self.skill_frame.winfo_children():
            w.destroy()
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
        copies = [r for r in self.sv.units if r.uid == u.uid]
        variants = {(r.level, r.exp, tuple(r.stats)) for r in copies}
        self.sync_btn.pack_forget()
        enemy = is_enemy(u)
        for sp in self._stat_spins:
            sp.configure(state="disabled" if enemy else "normal")
        if enemy:
            self.copies_chip.configure(text="🔒 Enemy / NPC — read-only", style="ChipWarn.TLabel")
        elif len(copies) <= 1:
            self.copies_chip.configure(text="1 copy in slot", style="Chip.TLabel")
        elif len(variants) == 1:
            self.copies_chip.configure(text=f"✓ {len(copies)} copies in sync",
                                       style="ChipOk.TLabel")
        else:
            self.copies_chip.configure(text=f"⚠ {len(copies)} copies disagree",
                                       style="ChipWarn.TLabel")
            self.sync_btn.pack(anchor="e", pady=(6, 0))

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
        for key, widgets in self._skill_rows:
            self.apply_skill_value(key, widgets)

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
        v = self._num(self.exp_var, 0, 255)
        if v is None:
            return self._bad_input(self.exp_var, 0, 255, u.exp, "EXP")
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
            r.set_stat(i, v, sv.payload)
            r.stats[i] = v
        n, s = self._edit_units(fn)
        top = max(40, max(u.stats))
        for k, bar in enumerate(self.stat_bars):
            bar.set(u.stats[k] / top)
        if n:
            self._update_copies_chip(u)
            self.flash(f"{u.name}: {STAT_LONG[STAT_NAMES[i]]} → {v}  ({self._where(n, s)})")

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
        for w in self.skill_frame.winfo_children():
            w.destroy()
        self._skill_rows = []
        self._skill_shown = {}
        u = self._current()
        if not u:
            return
        tab = u.skills(bytes(self.sv.payload))
        if not tab:
            ttk.Label(self.skill_frame, text="No weapon-rank table found for this unit.",
                      style="CardMuted.TLabel").pack(anchor="w")
            return
        g = self.skill_frame
        for c, (txt, w) in enumerate((("RANK", 0), ("GRADE", 0), ("PROGRESS", 0),
                                      ("EXP", 0), ("SET GRADE", 0))):
            ttk.Label(g, text=txt, style="CardFaint.TLabel").grid(row=0, column=c, sticky="w",
                                                                  padx=(0, 16), pady=(0, 6))
        g.columnconfigure(2, weight=1)
        vcmd = self._num_vcmd()
        for row, key in enumerate(sorted(tab), start=1):
            _off, val = tab[key]
            ttk.Label(g, text=SKILL_NAMES.get(key, f"skill {key}"), style="CardBold.TLabel",
                      width=13).grid(row=row, column=0, sticky="w", pady=5)
            badge = tk.Label(g, text="", width=3, font=self.f_bold, fg="#10131a",
                             padx=4, pady=1)
            badge.grid(row=row, column=1, sticky="w", padx=(0, 16))
            bar = Bar(g, self, width=180, height=8)
            bar.grid(row=row, column=2, sticky="ew", padx=(0, 16))
            nxt = ttk.Label(g, text="", style="CardFaint.TLabel", width=12)
            vvar = tk.StringVar(value=str(val))
            spin = ttk.Spinbox(g, from_=0, to=SKILL_MAX, width=7, textvariable=vvar,
                               increment=10, validate="key", validatecommand=vcmd)
            spin.grid(row=row, column=3, sticky="w", padx=(0, 16))
            gvar = tk.StringVar(value=grade_label(val))
            box = ttk.Combobox(g, textvariable=gvar, values=GRADES, width=5, state="readonly")
            box.grid(row=row, column=4, sticky="w")
            self.register_combo(box)
            nxt.grid(row=row, column=5, sticky="w", padx=(12, 0))
            widgets = (vvar, gvar, badge, bar, nxt)
            for ev in ("<Return>", "<FocusOut>"):
                spin.bind(ev, lambda e, k=key, w=widgets: self.apply_skill_value(k, w))
            spin.configure(command=lambda k=key, w=widgets: self.apply_skill_value(k, w))
            box.bind("<<ComboboxSelected>>",
                     lambda e, k=key, w=widgets: self.apply_skill_grade(k, w))
            self._paint_skill(widgets, val)
            self._skill_shown[key] = val
            self._skill_rows.append((key, widgets))

    def _paint_skill(self, widgets, value):
        vvar, gvar, badge, bar, nxt = widgets
        idx = grade_of(value)
        gvar.set(GRADES[idx])
        badge.configure(text=GRADES[idx], bg=GRADE_COLORS[idx])
        lo = SKILL_THRESHOLDS[idx]
        hi = next_threshold(value)
        if hi is None:
            bar.set(1.0, GRADE_COLORS[idx])
            nxt.configure(text="max rank")
        else:
            bar.set((value - lo) / (hi - lo), GRADE_COLORS[idx])
            nxt.configure(text=f"{hi - value} to {GRADES[idx + 1]}")

    def _write_skill(self, key, value):
        def fn(r, sv):
            cur = r.skills(bytes(sv.payload)).get(key)
            if not cur or cur[1] == value:
                return False
            return r.set_skill(key, value, sv.payload)
        return self._edit_units(fn)

    def apply_skill_value(self, key, widgets):
        u = self._current()
        vvar = widgets[0]
        if not u or vvar.get() == "":
            return
        v = self._num(vvar, 0, SKILL_MAX)
        if v is None:
            cur = u.skills(bytes(self.sv.payload)).get(key, (0, 0))[1]
            vvar.set(str(cur))
            self.flash(f"Rank EXP must be 0 – {SKILL_MAX}.", "warn")
            return
        if v == self._skill_shown.get(key):
            return
        self._skill_shown[key] = v
        n, s = self._write_skill(key, v)
        self._paint_skill(widgets, v)
        if n:
            self.flash(f"{u.name}: {SKILL_NAMES.get(key, key)} → {grade_label(v)} "
                       f"(exp {v}, {self._where(n, s)})")

    def apply_skill_grade(self, key, widgets):
        u = self._current()
        g = widgets[1].get()
        if not u or g not in GRADES:
            return
        v = SKILL_THRESHOLDS[GRADES.index(g)]
        widgets[0].set(str(v))
        self._skill_shown[key] = v
        n, s = self._write_skill(key, v)
        self._paint_skill(widgets, v)
        if n:
            self.flash(f"{u.name}: {SKILL_NAMES.get(key, key)} → {g} "
                       f"(exp {v}, {self._where(n, s)})")

    def apply_all_grades(self):
        u = self._current()
        g = self.all_grade.get()
        if not u or g not in GRADES or not self._skill_rows:
            return
        v = SKILL_THRESHOLDS[GRADES.index(g)]
        total, slots = 0, 0
        for key, widgets in self._skill_rows:
            widgets[0].set(str(v))
            self._skill_shown[key] = v
            n, s = self._write_skill(key, v)
            total += n
            slots = max(slots, s)
            self._paint_skill(widgets, v)
        self.flash(f"{u.name}: every listed rank → {g}  ({total} values"
                   + (f" across {slots} slots)" if slots > 1 else ")"))

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
        u = self._current()
        idx = self._inv_slot()
        sel = self.inv_tree.selection()
        if sel and sel[0][:1] == "s":
            self.flash("Spells are read-only — pick one of the carried items.", "warn")
            return
        if not u or idx is None or idx >= len(self._inv_items):
            self.flash("Select one of the carried items on the left first.", "warn")
            return
        old_id = self._inv_items[idx][1]
        if new_id == old_id:
            self.flash("That slot already holds this item.")
            return

        def fn(r, sv):
            # each copy is parsed on its own, so a copy laid out a byte
            # differently is still hit at the right place
            inv = r.inventory(bytes(sv.payload))
            if inv is None or idx >= len(inv.items):
                return False
            struct.pack_into("<I", sv.payload, inv.items[idx][0], new_id)
        n, s = self._edit_units(fn)
        name = item_label(new_id)
        if n:
            self.flash(f"{u.name}: slot {idx + 1} → {name}  ({self._where(n, s)})")
        else:
            self.flash("Nothing changed — the slot could not be matched in any copy.", "warn")
        self.refresh_inventory()

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
    @staticmethod
    def _primary_block(payload) -> list:
        """The list the game is using: the last one in the payload."""
        blocks = convoy_blocks(bytes(payload))
        return max(blocks, key=lambda b: b[0][0]) if blocks else []

    def refresh_convoy(self, select: list[int] | None = None):
        tree = self.conv_tree
        prev = select if select is not None else [int(i) for i in tree.selection()
                                                  if i.isdigit()]
        tree.delete(*tree.get_children())
        self._conv_rows = self._primary_block(self.sv.payload) if self.sv else []
        names = item_ids()
        filled = 0
        for k, (off, qty, iid) in enumerate(self._conv_rows):
            meta = names.get(iid, {})
            kind = item_kind(meta) if meta else "Item"
            tree.insert("", "end", iid=str(k), text=" " + item_label(iid, meta),
                        image=self.item_icon(iid, meta, kind),
                        values=(kind, qty if qty else "—"), tags=("empty",) if not qty else ())
            filled += 1 if qty else 0
        if not self._conv_rows:
            tree.insert("", "end", iid="none", text="  No convoy list found in this slot",
                        tags=("empty",))
        self.conv_count.configure(text=f"{filled} stacks" if self._conv_rows else "")
        keep = [str(i) for i in prev if tree.exists(str(i))]
        if keep:
            tree.selection_set(keep)
            tree.see(keep[-1])

    def _conv_selected(self) -> list[int]:
        return sorted(int(i) for i in self.conv_tree.selection() if i.isdigit())

    def _conv_row_picked(self, _e=None):
        rows = self._conv_selected()
        if len(rows) == 1 and rows[0] < len(self._conv_rows):
            qty = self._conv_rows[rows[0]][1]
            if qty:
                self.qty_var.set(str(qty))

    def _qty(self) -> int | None:
        v = self._num(self.qty_var, 1, QTY_MAX)
        if v is None:
            self.flash(f"Quantity must be 1 – {QTY_MAX}.", "warn")
        return v

    def _convoy_edit(self, fn) -> int:
        touched = []
        for sv in self._targets():
            block = self._primary_block(sv.payload)
            if block and fn(sv.payload, block):
                touched.append(sv)
        self._touch(touched)
        return len(touched)

    def add_convoy(self, iid: int):
        if not self.sv:
            return
        if not self._conv_rows:
            self.flash("This slot has no convoy list to add to.", "warn")
            return
        qty = self._qty()
        if qty is None:
            return
        name = item_label(iid)
        existing = [k for k, (_o, _q, i) in enumerate(self._conv_rows) if i == iid]
        if existing:
            self.refresh_convoy(select=existing)
            self.flash(f"{name} is already in the convoy — selected its row; use "
                       "“Set qty” to change how many.", "warn")
            return
        n = self._convoy_edit(lambda p, b: add_convoy_item(p, iid, [b], qty))
        self.refresh_convoy(select=[len(self._conv_rows)])
        self.flash(f"Added {name} ×{qty} to the convoy" + (f" in {n} slots" if n > 1 else ""))

    def replace_convoy(self):
        rows = self._conv_selected()
        iid = self.conv_picker.selected()
        if len(rows) != 1 or iid is None:
            self.flash("Select one convoy row and one catalogue item to replace it with.",
                       "warn")
            return
        qty = self._qty()
        if qty is None:
            return
        k = rows[0]

        def fn(payload, block):
            if k >= len(block):
                return False
            set_convoy_row(payload, block[k][0], iid, qty)
            return True
        n = self._convoy_edit(fn)
        self.refresh_convoy(select=[k])
        self.flash(f"Convoy row {k + 1} → {item_label(iid)} ×{qty}"
                   + (f" in {n} slots" if n > 1 else ""))

    def set_convoy_qty(self):
        rows = self._conv_selected()
        if not rows:
            self.flash("Select a convoy row first.", "warn")
            return
        qty = self._qty()
        if qty is None:
            return

        def fn(payload, block):
            hit = False
            for k in rows:
                if k < len(block):
                    struct.pack_into("<H", payload, block[k][0] - 2, qty)
                    hit = True
            return hit
        n = self._convoy_edit(fn)
        self.refresh_convoy(select=rows)
        self.flash(f"Quantity → {qty} on {len(rows)} row(s)" + (f" in {n} slots" if n > 1 else ""))

    def clear_convoy(self):
        rows = self._conv_selected()
        if not rows:
            self.flash("Select the convoy row(s) to clear.", "warn")
            return

        def fn(payload, block):
            hit = False
            for k in rows:
                if k < len(block):
                    struct.pack_into("<H", payload, block[k][0] - 2, 0)
                    hit = True
            return hit
        n = self._convoy_edit(fn)
        self.refresh_convoy(select=rows)
        self.flash(f"Cleared {len(rows)} row(s) (quantity 0)" + (f" in {n} slots" if n > 1 else ""))

    # ============================================================ gold
    def _show_gold(self, val: int | None, hint: str):
        self.gold_now.configure(text="—" if val is None else f"{val:,}")
        self.gold_hint.configure(text=hint)

    def locate_gold(self):
        self.money_off = None
        self.gold_tree.delete(*self.gold_tree.get_children())
        sig = load_money_sig()
        if not self.sv:
            return self._show_gold(None, "")
        if not sig:
            return self._show_gold(None, "Not located yet — use the search below once.")
        off = locate_money(self.sv.payload, sig)
        if off is None:
            return self._show_gold(None, "The remembered location isn't in this slot — "
                                         "search for the amount below.")
        self.money_off = off
        val = struct.unpack_from("<I", self.sv.payload, off)[0]
        self._show_gold(val, "Found automatically from the remembered location.")

    def find_gold(self):
        if not self.sv:
            return
        try:
            want = int(self.gold_search.get().replace(",", "").strip())
        except ValueError:
            self.flash("Type the gold amount as a number.", "warn")
            return
        if want <= 0:
            self.flash("Can't search for 0 — every empty field matches. Earn or spend a "
                       "little gold in game first.", "warn")
            return
        cands = find_money_candidates(bytes(self.sv.payload), want)
        self._gold_cands = cands
        self.gold_tree.delete(*self.gold_tree.get_children())
        for k, off in enumerate(cands[:60]):
            ctx = bytes(self.sv.payload[max(0, off - 8):off + 12]).hex(" ")
            self.gold_tree.insert("", "end", iid=str(k), text=f"0x{off:06x}", values=(ctx,),
                                  tags=("ctx",))
        if len(cands) == 1:
            self.gold_tree.selection_set("0")
        if not cands:
            self.flash(f"No match for {want:,}. Double-check the amount shown in game for "
                       "this slot.", "warn")
        else:
            self.flash(f"{len(cands)} match(es) for {want:,}"
                       + (" — pick one, then Set gold." if len(cands) > 1 else "."))

    def on_gold_pick(self, _e=None):
        sel = self.gold_tree.selection()
        if not sel or not self._gold_cands:
            return
        self.money_off = self._gold_cands[int(sel[0])]
        val = struct.unpack_from("<I", self.sv.payload, self.money_off)[0]
        self._show_gold(val, f"Using the match at 0x{self.money_off:06x}.")

    def set_gold(self):
        if not self.sv:
            return
        if self.money_off is None:
            self.flash("Locate gold first: type the amount shown in game and press Find.",
                       "warn")
            return
        try:
            val = int(self.gold_new.get().replace(",", "").strip())
        except ValueError:
            self.flash("Type the new gold amount as a number.", "warn")
            return
        if not 0 <= val <= 0xFFFFFFFF:
            self.flash("Gold must be between 0 and 4,294,967,295.", "warn")
            return
        sig = money_signature(bytes(self.sv.payload), self.money_off)
        save_money_sig(sig)
        touched = []
        for sv in self._targets():
            off = self.money_off if sv is self.sv else locate_money(sv.payload, sig)
            if off is None:
                continue
            struct.pack_into("<I", sv.payload, off, val)
            touched.append(sv)
        self._touch(touched)
        self._show_gold(val, "Location remembered for future saves.")
        self.flash(f"Gold → {val:,}" + (f" in {len(touched)} slots" if len(touched) > 1 else ""))


def _dpi_aware():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            pass


def main():
    _dpi_aware()
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and os.path.isfile(arg):
        arg = os.path.dirname(arg)
    App(arg).mainloop()


if __name__ == "__main__":
    main()
