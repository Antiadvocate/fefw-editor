"""editor_advanced.py - Player / Classes / Flags pages for the save editor.

These pages are driven by fefw_core (the save's own object tree), so they
can add and remove records: classes, weapon masteries, named
flags.  Everything else in the app keeps working on the same payload; after a
resizing edit the records are re-scanned, so no offsets go stale.

The class owns no state of its own beyond widget caches: the App supplies
self.sv (SaveFile), self.core (fefw_core.SaveFile for the shown slot),
self._targets(), self._touch(), self.flash().
"""
from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

import fefw_core as core
import supports
from fefw_save import item_ids, item_label, unit_ids
from ui_util import enable_multi_select

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "Fortune's Weave Save Editor"

# the 13 weapon masteries, in the order the save stores them
MASTERIES = [
    ("Sword", "剣"), ("Lance", "槍"), ("Axe", "斧"), ("Bow", "弓"),
    ("Fist", "格闘"), ("Black Magic", "黒魔"), ("White Magic", "白魔"),
    ("Special", "特殊"), ("Foot", "歩兵"), ("Cavalry", "騎馬"),
    ("Heavy", "重装"), ("Fly", "飛行"), ("Tactics", "指揮"),
]
RANKS = ["E", "E+", "D", "D+", "C", "C+", "B", "B+", "A", "A+", "S", "S+"]
from fefw_save import SKILL_THRESHOLDS as RANK_EXP  # noqa: E402  (one table for both tabs)
DIFFICULTIES = ["Normal", "Hard", "Maddening"]
MODES = ["Casual", "Classic"]

# what the Japanese name prefixes mean (the part after them is a game-internal
# name; there is no English table for those, so it stays as the game writes it)
PREFIX_EN = [
    ("面識_", "Met"),
    ("加入_", "Recruited"),
    ("支援会話_", "Support conversation"),
    ("実績_", "Achievement"),
    ("機能開放_", "Feature unlocked"),
    ("兵種解放_", "Class unlocked"),
    ("禁止_", "Disabled"),
    ("因果報酬_", "Boon"),
    ("状況_", "Situation"),
    ("環境設定_", "Settings"),
    ("既読_", "Read"),
    ("共有_", "Shared"),
    ("チュートリアル_", "Tutorial"),
    ("ファストトラベル_", "Fast travel"),
    ("会話_", "Talk"),
]


def friendly(name: str) -> str:
    for prefix, en in PREFIX_EN:
        if name.startswith(prefix):
            rest = name[len(prefix):]
            return f"{en} · {rest}" if rest else en
    return name

_JOBS = None
_FLAG_NAMES = None


def scrolled_tree(master, **kw) -> ttk.Treeview:
    """Treeview with its own scrollbar, in a Card frame (same as editor.py)."""
    frame = ttk.Frame(master, style="Card.TFrame")
    tree = ttk.Treeview(frame, **kw)
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    tree.container = frame
    return tree


def jobs() -> dict:
    global _JOBS
    if _JOBS is None:
        raw = json.load(open(os.path.join(HERE, "job_ids.json"), encoding="utf8"))
        _JOBS = {int(k, 16): v for k, v in raw.items()}
    return _JOBS


def flag_names() -> dict:
    global _FLAG_NAMES
    if _FLAG_NAMES is None:
        try:
            raw = json.load(open(os.path.join(HERE, "flag_names.json"), encoding="utf8"))
            _FLAG_NAMES = {int(k, 16): v for k, v in raw.items()}
        except Exception:                     # noqa: BLE001 — the page still works
            _FLAG_NAMES = {}
    return _FLAG_NAMES


def class_label(cid: int) -> str:
    meta = jobs().get(cid & 0xFFFFFFFF)
    if not meta:
        return "unknown 0x%08X" % (cid & 0xFFFFFFFF)
    return meta.get("en") or meta.get("jp") or "unknown 0x%08X" % (cid & 0xFFFFFFFF)


def class_jp(cid: int) -> str:
    return (jobs().get(cid & 0xFFFFFFFF) or {}).get("jp", "")


def unit_name(person: int) -> str:
    meta = unit_ids().get(person & 0xFFFFFFFF) or {}
    return meta.get("name") or meta.get("pid") or "unknown 0x%08X" % (person & 0xFFFFFFFF)


def rank_of(exp: int) -> int:
    r = 0
    while r + 1 < len(RANK_EXP) and exp >= RANK_EXP[r + 1]:
        r += 1
    return r


class AdvancedMixin:
    # ------------------------------------------------------------- helpers
    def core_of(self, sv=None):
        """fefw_core.SaveFile for a slot (cached on the payload object)."""
        sv = sv or self.sv
        if sv is None:
            return None
        key = (sv.path, id(sv.payload))
        cache = getattr(sv, "_core_cache", None)
        if cache and cache[0] == key:
            return cache[1]
        f = core.SaveFile(bytes(sv.payload))
        sv._core_cache = (key, f)
        return f

    def _core_edit(self, fn, what: str) -> bool:
        """fn(fefw_core.SaveFile) -> new payload; applied to every target slot."""
        if not self.sv:
            return False
        self._commit_form()
        touched, err = [], None
        for sv in self._targets():
            try:
                f = core.SaveFile(bytes(sv.payload))
                new = fn(f)
            except core.SaveError as exc:
                err = exc
                continue
            except Exception as exc:          # noqa: BLE001 — report, never crash
                err = exc
                continue
            if new is None or bytes(new) == bytes(sv.payload):
                continue
            sv.payload = bytearray(new)
            sv.scan()
            sv._core_cache = None
            touched.append(sv)
        if not touched:
            self.flash(f"Couldn't apply “{what}”" + (f": {err}" if err else "."), "error")
            return False
        self._touch(touched)
        self.refresh_after_core()
        where = f" in {len(touched)} slots" if len(touched) > 1 else ""
        self.flash(f"{what}{where} — Ctrl+S to write it.", "ok")
        return True

    def refresh_after_core(self):
        keep = self.uid
        self._shown = {}
        self.refresh_units(keep=keep)
        self.refresh_convoy()
        self.refresh_player()
        self.refresh_classes_page()
        self.refresh_flags()
        self.refresh_supports()

    def refresh_core_pages(self):
        self.refresh_player()
        self.refresh_classes_page()
        self.refresh_flags()

    # -------------------------------------------------------- pick a value
    def _picker(self, title: str, rows, current: int | None = None):
        """Modal searchable single-choice list. rows: [(key, primary, secondary)]."""
        win = tk.Toplevel(self)
        win.title(title)
        win.transient(self)
        self.place_dialog(win, 560, 460)
        win.configure(background=self.p["bg"])
        top = ttk.Frame(win, padding=10)
        top.pack(fill="x")
        ent = ttk.Entry(top)
        ent.pack(fill="x")
        tree = ttk.Treeview(win, columns=("sec",), show="tree headings", selectmode="browse")
        tree.heading("#0", text="Name", anchor="w")
        tree.heading("sec", text="Internal id", anchor="w")
        tree.column("#0", width=300)
        tree.column("sec", width=210)
        sb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0))
        sb.pack(side="left", fill="y", padx=(0, 10))
        result = {"key": None}
        iids: dict[str, object] = {}

        def fill(*_a):
            q = ent.get().strip().lower()
            tree.delete(*tree.get_children())
            iids.clear()
            n = 0
            for key, primary, secondary in rows:
                if q and q not in str(primary).lower() and q not in str(secondary).lower():
                    continue
                iid = tree.insert("", "end", text=primary, values=(secondary,))
                iids[iid] = key
                if current is not None and key == current:
                    tree.selection_set(iid)
                    tree.see(iid)
                n += 1
                if n > 4000:
                    break

        def ok(*_a):
            sel = tree.selection()
            if sel:
                result["key"] = iids[sel[0]]
                win.destroy()

        ent.bind("<KeyRelease>", fill)
        tree.bind("<Double-1>", ok)
        tree.bind("<Return>", ok)
        bar = ttk.Frame(win, padding=(10, 6))
        bar.pack(side="bottom", fill="x")
        ttk.Button(bar, text="Use this", style="Accent.TButton", command=ok).pack(side="right")
        ttk.Button(bar, text="Cancel", command=win.destroy).pack(side="right", padx=(0, 8))
        fill()
        ent.focus_set()
        self.wait_window(win)
        return result["key"]

    # ============================================================ PLAYER
    def _build_player(self):
        page = self.player_page
        card = ttk.Frame(page, style="Card.TFrame", padding=(16, 14))
        card.pack(fill="x")
        ttk.Label(card, text="Player", style="CardH3.TLabel").pack(anchor="w")
        ttk.Label(card, text="Army-wide values, stored in GameUserData at the start of the save.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 10))
        self.player_vars: dict[str, tk.StringVar] = {}
        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill="x")
        rows = [("gold", "Gold", 9_999_999), ("renown", "Renown exp", 999_999),
                ("karma", "Karma Shards", 999_999)]
        for i, (key, label, limit) in enumerate(rows):
            ttk.Label(grid, text=label, style="Card.TLabel", width=16).grid(
                row=i, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            self.player_vars[key] = var
            box = ttk.Entry(grid, textvariable=var, width=14, justify="right")
            box.grid(row=i, column=1, sticky="w", pady=4)
            box.bind("<Return>", lambda e, k=key, l=limit: self.apply_player(k, l))
            box.bind("<FocusOut>", lambda e, k=key, l=limit: self.apply_player(k, l))
            ttk.Label(grid, text=f"0 – {limit:,}", style="CardFaint.TLabel").grid(
                row=i, column=2, sticky="w", padx=(10, 0))
        self.player_note = ttk.Label(grid, text="", style="CardFaint.TLabel", wraplength=520,
                                     justify="left")
        self.player_note.grid(row=3, column=0, columnspan=3, sticky="w", pady=(10, 0))

        card2 = ttk.Frame(page, style="Card.TFrame", padding=(16, 14))
        card2.pack(fill="x", pady=(10, 0))
        ttk.Label(card2, text="Run settings", style="CardH3.TLabel").pack(anchor="w")
        ttk.Label(card2, text="Written into every copy the save keeps, and into every slot in this "
                             "folder (the run's difficulty is one setting).",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 8))
        row = ttk.Frame(card2, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Difficulty", style="Card.TLabel", width=12).pack(side="left")
        self.diff_var = tk.StringVar()
        cb = ttk.Combobox(row, textvariable=self.diff_var, values=DIFFICULTIES,
                          state="readonly", width=12)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.apply_settings())
        ttk.Label(row, text="Mode", style="Card.TLabel", width=9).pack(side="left", padx=(20, 0))
        self.mode_var = tk.StringVar()
        cb2 = ttk.Combobox(row, textvariable=self.mode_var, values=MODES, state="readonly",
                           width=10)
        cb2.pack(side="left")
        cb2.bind("<<ComboboxSelected>>", lambda e: self.apply_settings())
        self.play_lbl = ttk.Label(card2, text="", style="CardFaint.TLabel")
        self.play_lbl.pack(anchor="w", pady=(10, 0))

    def refresh_player(self):
        if not hasattr(self, "player_vars"):
            return
        f = self.core_of()
        if f is None:
            for v in self.player_vars.values():
                v.set("")
            return
        ud = core.user_data(f)
        if ud < 0:
            for v in self.player_vars.values():
                v.set("—")
            self.player_note.configure(text="This file's GameUserData isn't the known layout.")
            return
        self.player_vars["gold"].set(str(f.u32(ud + core.GOLD_AT)))
        self.player_vars["renown"].set(str(f.u32(ud + core.RENOWN_AT)))
        self.player_vars["karma"].set(str(f.u32(ud + core.KARMA_AT)))
        st = core.read_settings(f)
        if st:
            self.diff_var.set(DIFFICULTIES[st[1]] if st[1] < 3 else str(st[1]))
            self.mode_var.set(MODES[st[2]] if st[2] < 2 else str(st[2]))
            line = f"Playthrough {st[0]}"
            counts: dict[tuple[int, int], int] = {}
            for sv in getattr(self, "files", {}).values():
                q = sv.payload
                if len(q) > 15 and q[12] == 15:
                    counts[(q[15], q[14])] = counts.get((q[15], q[14]), 0) + 1   # (difficulty, mode)
            if len(counts) <= 1:
                line += (f" · every slot: {DIFFICULTIES[st[1]] if st[1] < 3 else st[1]}"
                         f" / {MODES[st[2]] if st[2] < 2 else st[2]}")
            else:
                bits = [f"{DIFFICULTIES[a] if a < 3 else a}/{MODES[b] if b < 2 else b} ×{n}"
                        for (a, b), n in sorted(counts.items())]
                line += " · slots disagree — " + " · ".join(bits)
            self.play_lbl.configure(text=line)
        self.player_note.configure(
            text="Renown exp is the army's total; the level itself follows the game's own "
                 "Reward.bin table, so set a value between two levels to land on a level.")

    def apply_player(self, key: str, limit: int):
        var = self.player_vars.get(key) if hasattr(self, "player_vars") else None
        if var is None or not self.sv:
            return
        text = var.get().strip().replace(",", "")
        if not text.isdigit():
            self.refresh_player()
            return
        value = min(int(text), limit)
        f = self.core_of()
        ud = core.user_data(f) if f else -1
        if ud < 0:
            return
        off = {"gold": core.GOLD_AT, "renown": core.RENOWN_AT, "karma": core.KARMA_AT}[key]
        if f.u32(ud + off) == value:
            return

        def edit(g, off=off, value=value):
            base = core.user_data(g)
            if base < 0:
                return None
            core.set_u32(g, base + off, value)
            return g.payload

        self._core_edit(edit, f"{key.title()} → {value:,}")

    def apply_settings(self):
        if not self.sv or not hasattr(self, "diff_var"):
            return
        try:
            d = DIFFICULTIES.index(self.diff_var.get())
            m = MODES.index(self.mode_var.get())
        except ValueError:
            return
        f0 = self.core_of()
        cur = core.read_settings(f0) if f0 is not None else None
        if cur and cur[1] == d and cur[2] == m:
            return

        # Difficulty and mode are properties of the run, not of one slot: the
        # game's save screen shows them for every slot, so write them into the
        # whole folder (Auto, Chapter_* and Route_*), not only the open one.
        touched, err = [], None
        for sv in list(getattr(self, "files", {}).values()):
            try:
                g = core.SaveFile(bytes(sv.payload))
                offs = settings_offsets(g)
                if not offs:
                    continue
                for at in offs:
                    g.payload[at] = m & 0xFF          # mode comes first
                    g.payload[at + 1] = d & 0xFF      # then difficulty
                core.fix_embedded_hashes(g.payload)
                if bytes(g.payload) == bytes(sv.payload):
                    continue
                sv.payload = bytearray(g.payload)
                sv.scan()
                sv._core_cache = None
                touched.append(sv)
            except Exception as exc:          # noqa: BLE001 — report, never crash
                err = exc
        if not touched:
            self.flash("Couldn't apply difficulty/mode" + (f": {err}" if err else "."), "error")
            return
        self._touch(touched)
        self.refresh_after_core()
        where = f"in {len(touched)} slots" if len(touched) > 1 else "in this slot"
        self.flash(f"{DIFFICULTIES[d]} / {MODES[m]} {where} — Ctrl+S to write it.", "ok")

    # ============================================================ CLASSES
    def _build_classes(self):
        pane = ttk.PanedWindow(self.classes_page, orient="horizontal")
        pane.pack(fill="both", expand=True)

        side = ttk.Frame(pane, style="Card.TFrame", padding=12)
        pane.add(side, weight=0)
        head = ttk.Frame(side, style="Card.TFrame")
        head.pack(fill="x")
        ttk.Label(head, text="Units", style="CardH3.TLabel").pack(side="left")
        self.cls_count = ttk.Label(head, text="", style="CardMuted.TLabel")
        self.cls_count.pack(side="right")
        self.cls_search = ttk.Entry(side)
        self.cls_search.pack(fill="x", pady=(6, 6))
        self.cls_search.bind("<KeyRelease>", lambda e: self.refresh_class_units())
        self.cls_unit_tree = ttk.Treeview(side, columns=("lv",), show="tree headings",
                                          selectmode="browse", height=20)
        self.cls_unit_tree.heading("#0", text="Name", anchor="w")
        self.cls_unit_tree.heading("lv", text="Lv", anchor="e")
        self.cls_unit_tree.column("#0", width=170)
        self.cls_unit_tree.column("lv", width=40, anchor="e", stretch=False)
        sb = ttk.Scrollbar(side, orient="vertical", command=self.cls_unit_tree.yview)
        self.cls_unit_tree.configure(yscrollcommand=sb.set)
        self.cls_unit_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.cls_unit_tree.bind("<<TreeviewSelect>>", lambda e: self.on_class_unit())

        main = ttk.Frame(pane)
        pane.add(main, weight=1)

        head = ttk.Frame(main, style="Card.TFrame", padding=(16, 12))
        head.pack(fill="x", padx=(10, 0))
        self.cls_name = ttk.Label(head, text="No unit selected", style="CardH1.TLabel")
        self.cls_name.pack(anchor="w")
        self.cls_sub = ttk.Label(head, text="", style="CardMuted.TLabel")
        self.cls_sub.pack(anchor="w", pady=(2, 0))

        cur = ttk.Frame(main, style="Card.TFrame", padding=(16, 10))
        cur.pack(fill="x", padx=(10, 0), pady=(8, 0))
        ttk.Label(cur, text="Current class", style="Card.TLabel", width=13).pack(side="left")
        self.cur_class_lbl = ttk.Label(cur, text="—", style="CardH3.TLabel")
        self.cur_class_lbl.pack(side="left")
        self.cur_class_jp = ttk.Label(cur, text="", style="CardFaint.TLabel")
        self.cur_class_jp.pack(side="left", padx=(10, 0))
        ttk.Button(cur, text="Change…", style="Small.TButton",
                   command=self.change_current_class).pack(side="right")

        body = ttk.PanedWindow(main, orient="vertical")
        body.pack(fill="both", expand=True, padx=(10, 0), pady=(8, 0))

        cbox = ttk.Frame(body, style="Card.TFrame", padding=(12, 10))
        body.add(cbox, weight=3)
        bar = ttk.Frame(cbox, style="Card.TFrame")
        bar.pack(fill="x")
        ttk.Label(bar, text="Classes this unit has", style="CardH3.TLabel").pack(side="left")
        for text, cmd in (("Set exp…", self.set_class_exp), ("Add…", self.add_class),
                          ("Swap…", self.swap_class), ("Remove", self.remove_class),
                          ("Set current", self.set_current_class)):
            ttk.Button(bar, text=text, style="Small.TButton", command=cmd).pack(side="right",
                                                                               padx=(6, 0))
        self.cls_tree = ttk.Treeview(cbox, columns=("value", "flags", "now"),
                                     show="tree headings", selectmode="extended")
        self.cls_tree.heading("#0", text="Class", anchor="w")
        self.cls_tree.heading("value", text="Class exp", anchor="e")
        self.cls_tree.heading("flags", text="Flags", anchor="e")
        self.cls_tree.heading("now", text="", anchor="center")
        self.cls_tree.column("#0", width=300)
        self.cls_tree.column("value", width=80, anchor="e", stretch=False)
        self.cls_tree.column("flags", width=70, anchor="e", stretch=False)
        self.cls_tree.column("now", width=40, anchor="center", stretch=False)
        cls_sb = ttk.Scrollbar(cbox, orient="vertical", command=self.cls_tree.yview)
        self.cls_tree.configure(yscrollcommand=cls_sb.set)
        self.cls_tree.pack(side="left", fill="both", expand=True, pady=(6, 0))
        cls_sb.pack(side="left", fill="y", pady=(6, 0))
        self.cls_tree.bind("<Double-1>", lambda e: self.set_current_class())
        enable_multi_select(self.cls_tree)

        mbox = ttk.Frame(body, style="Card.TFrame", padding=(12, 10))
        body.add(mbox, weight=3)
        bar2 = ttk.Frame(mbox, style="Card.TFrame")
        bar2.pack(fill="x")
        ttk.Label(bar2, text="Weapon masteries", style="CardH3.TLabel").pack(side="left")
        for text, cmd in (("Set rank…", self.set_mastery_rank), ("Set exp…", self.set_mastery_exp),
                          ("Add…", self.add_mastery), ("Remove", self.remove_mastery)):
            ttk.Button(bar2, text=text, style="Small.TButton", command=cmd).pack(side="right",
                                                                               padx=(6, 0))
        self.mas_tree = ttk.Treeview(mbox, columns=("rank", "exp", "next"),
                                     show="tree headings", selectmode="browse")
        self.mas_tree.heading("#0", text="Weapon", anchor="w")
        self.mas_tree.heading("rank", text="Rank", anchor="center")
        self.mas_tree.heading("exp", text="Exp", anchor="e")
        self.mas_tree.heading("next", text="Next rank at", anchor="e")
        self.mas_tree.column("#0", width=220)
        self.mas_tree.column("rank", width=60, anchor="center", stretch=False)
        self.mas_tree.column("exp", width=70, anchor="e", stretch=False)
        self.mas_tree.column("next", width=110, anchor="e", stretch=False)
        mas_sb = ttk.Scrollbar(mbox, orient="vertical", command=self.mas_tree.yview)
        self.mas_tree.configure(yscrollcommand=mas_sb.set)
        self.mas_tree.pack(side="left", fill="both", expand=True, pady=(6, 0))
        mas_sb.pack(side="left", fill="y", pady=(6, 0))
        self.mas_tree.bind("<Double-1>", lambda e: self.set_mastery_rank())

        note = ttk.Frame(main, style="Card.TFrame")
        note.pack(fill="x", padx=(10, 0), pady=(6, 0))
        ttk.Label(note, style="CardFaint.TLabel", justify="left", wraplength=900,
                  text="Classes and masteries are separate lists inside the unit's record; "
                       "adding one grows the record and every pointer after it is rewritten "
                       "(that is what the old editor could not do). Rank thresholds are the "
                       "game's: E 0 · E+ 20 · D 35 · D+ 80 · C 220 · C+ 440 · B 690 · B+ 910 "
                       "· A 1215 · A+ 1510 · S 1960 · S+ 2560."
                  ).pack(anchor="w")

    def _core_units(self):
        f = self.core_of()
        return f.units() if f else []

    def refresh_classes_page(self):
        if not hasattr(self, "cls_unit_tree"):
            return
        self.refresh_class_units()
        self.on_class_unit()

    def refresh_class_units(self):
        f = self.core_of()
        keep = getattr(self, "_cls_uid", None)
        self.cls_unit_tree.delete(*self.cls_unit_tree.get_children())
        self._cls_rows = {}
        if not f:
            return
        q = ""
        try:
            q = self.cls_search.get().strip().lower()
        except Exception:                     # noqa: BLE001
            pass
        first = None
        rows = []
        by_start = {u.start: u for u in f.units()}
        for u in f.units():
            meta = unit_ids().get(u.person & 0xFFFFFFFF) or {}
            name = meta.get("name") or meta.get("pid") or "unknown 0x%08X" % (u.person & 0xFFFFFFFF)
            kind = (meta.get("kind") or "char")
            label = name + ("" if kind == "char" else f"  · {kind}")
            rows.append((0 if kind == "char" else 1, label.lower(), u.start, label))
        rows.sort()
        for _k, _s, start, label in rows:
            if q and q not in label.lower():
                continue
            u = by_start[start]
            lv = f.payload[u.level_off]
            iid = self.cls_unit_tree.insert("", "end", text=label, values=(lv,))
            self._cls_rows[iid] = u.start
            if first is None:
                first = iid
            if keep is not None and u.start == keep:
                first = iid
        self.cls_count.configure(text=f"{len(self._cls_rows)} unit"
                                      f"{'' if len(self._cls_rows) == 1 else 's'}")
        if first:
            self.cls_unit_tree.selection_set(first)
            self.cls_unit_tree.see(first)

    def _cls_unit(self):
        sel = self.cls_unit_tree.selection() if hasattr(self, "cls_unit_tree") else ()
        start = getattr(self, "_cls_rows", {}).get(sel[0] if sel else None)
        if start is None:
            return None
        for u in self._core_units():
            if u.start == start:
                return u
        return None

    def on_class_unit(self):
        u = self._cls_unit()
        f = self.core_of()
        self.cls_tree.delete(*self.cls_tree.get_children())
        self.mas_tree.delete(*self.mas_tree.get_children())
        if u is None or f is None:
            self.cls_name.configure(text="No unit selected")
            self.cur_class_lbl.configure(text="—")
            return
        self._cls_uid = u.start
        self.cls_name.configure(text=unit_name(u.person))
        self.cls_sub.configure(text=f"Lv {f.payload[u.level_off]} · "
                                    f"{len(u.classes)} class{'es' if len(u.classes) != 1 else ''}"
                                    f" · {len(u.masteries)} masteries")
        cid = u.klass
        cur = class_label(cid)
        jp = class_jp(cid)
        self.cur_class_lbl.configure(text=cur)
        self.cur_class_jp.configure(text=jp if jp and jp != cur else "")
        for i, (klass, value, flags) in enumerate(u.classes):
            self.cls_tree.insert("", "end", text=class_label(klass),
                                 values=(value, flags, "●" if klass == cid else ""),
                                 iid=str(i))
        for i, (idx, exp) in enumerate(u.masteries):
            r = rank_of(exp)
            nxt = RANK_EXP[r + 1] if r + 1 < len(RANK_EXP) else None
            nm = MASTERIES[idx][0] if 0 <= idx < len(MASTERIES) else f"#{idx}"
            self.mas_tree.insert("", "end", text=nm,
                                 values=(RANKS[r], exp, nxt if nxt is not None else "max"),
                                 iid=str(i))

    # -- class actions
    def _class_rows(self):
        rows = []
        for cid, meta in jobs().items():
            rows.append((cid, meta.get("en") or meta.get("jp") or "unknown",
                         meta.get("jp", "")))
        rows.sort(key=lambda r: r[1].lower())
        return rows

    def change_current_class(self):
        u = self._cls_unit()
        if u is None:
            return
        cid = self._picker("Pick the unit's current class", self._class_rows(), u.klass)
        if cid is None:
            return
        self._set_current(u, cid)

    def set_current_class(self):
        u = self._cls_unit()
        sel = self.cls_tree.selection()
        if u is None or not sel:
            return
        klass = u.classes[int(sel[0])][0]
        self._set_current(u, klass)

    def _set_current(self, u, cid: int):
        if cid == u.klass:
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            if not any(c[0] == cid for c in v.classes):
                new = core.with_lists(g, v, v.masteries, list(v.classes) + [(cid, 0, 4)])
                g.payload = new
                v = next((x for x in g.units() if x.start == u.start), None)
            core.set_class(g, v, cid)
            return g.payload

        self._core_edit(edit, f"Current class → {class_label(cid)}")

    def _class_entries(self) -> list[int]:
        """Selected class rows (entry index), in list order."""
        sel = self.cls_tree.selection() if hasattr(self, "cls_tree") else ()
        out = sorted({int(i) for i in sel if str(i).isdigit()})
        return out

    def set_class_exp(self):
        """Set the class exp ("progress") saved with each selected class."""
        u = self._cls_unit()
        entries = self._class_entries()
        if u is None or not entries:
            self.flash("Pick a class row first.", "info")
            return
        cur = u.classes[entries[0]][1] if len(entries) == 1 else 0
        many = len(entries) > 1
        prompt = ("Class exp for the selected classes (0 – 255):" if many
                  else "Class exp saved with this class (0 – 255):")
        val = _ask_number(self, "Class exp", prompt, cur, 255)
        if val is None:
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            classes = list(v.classes)
            changed = False
            for i in entries:
                if classes[i][1] != val:
                    classes[i] = (classes[i][0], val, classes[i][2])
                    changed = True
            if not changed:
                return None
            return core.with_lists(g, v, v.masteries, classes)

        what = (f"{class_label(u.classes[entries[0]][0])} class exp → {val}" if not many
                else f"{len(entries)} classes' exp → {val}")
        self._core_edit(edit, what)

    def add_class(self):
        u = self._cls_unit()
        if u is None:
            return
        have = {c[0] for c in u.classes}
        rows = [r for r in self._class_rows() if r[0] not in have]
        cid = self._picker("Add a class", rows)
        if cid is None:
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None or any(c[0] == cid for c in v.classes):
                return None
            return core.with_lists(g, v, v.masteries, list(v.classes) + [(cid, 0, 4)])

        self._core_edit(edit, f"Added class {class_label(cid)}")

    def swap_class(self):
        u = self._cls_unit()
        sel = self.cls_tree.selection()
        if u is None or not sel:
            return
        entry = int(sel[0])
        old = u.classes[entry]
        have = {c[0] for c in u.classes}
        rows = [r for r in self._class_rows() if r[0] not in have]
        cid = self._picker(f"Swap {class_label(old[0])} for…", rows)
        if cid is None:
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            classes = list(v.classes)
            was_current = classes[entry][0] == v.klass
            classes[entry] = (cid, classes[entry][1], classes[entry][2])
            new = core.with_lists(g, v, v.masteries, classes)
            g.payload = new
            if was_current:
                w = next((x for x in g.units() if x.start == u.start), None)
                core.set_class(g, w, cid)
            return g.payload

        self._core_edit(edit, f"Class {class_label(old[0])} → {class_label(cid)}")

    def remove_class(self):
        u = self._cls_unit()
        entries = self._class_entries()
        if u is None or not entries:
            return
        if any(u.classes[i][0] == u.klass for i in entries):
            messagebox.showinfo("Save editor", "That is the unit's current class. Change the "
                                               "current class first, or use Swap.", parent=self)
            entries = [i for i in entries if u.classes[i][0] != u.klass]
            if not entries:
                return
        names = [class_label(u.classes[i][0]) for i in entries]

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            classes = [c for i, c in enumerate(v.classes) if i not in set(entries)]
            return core.with_lists(g, v, v.masteries, classes)

        what = (f"Removed class {names[0]}" if len(names) == 1
                else f"Removed {len(names)} classes")
        self._core_edit(edit, what)

    # -- mastery actions
    def set_mastery_rank(self):
        u = self._cls_unit()
        sel = self.mas_tree.selection()
        if u is None or not sel:
            return
        entry = int(sel[0])
        rows = [(i, RANKS[i], f"{RANK_EXP[i]} exp") for i in range(len(RANKS))]
        r = self._picker(f"Rank for {MASTERIES[u.masteries[entry][0]][0]}", rows)
        if r is None:
            return
        exp = RANK_EXP[r]

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            mas = list(v.masteries)
            mas[entry] = (mas[entry][0], exp)
            new = core.with_lists(g, v, mas, list(v.classes))
            return new

        self._core_edit(edit, f"{MASTERIES[u.masteries[entry][0]][0]} → {RANKS[r]}")

    def set_mastery_exp(self):
        u = self._cls_unit()
        sel = self.mas_tree.selection()
        if u is None or not sel:
            return
        entries = sorted({int(i) for i in sel if str(i).isdigit()})
        if not entries:
            return
        cur = u.masteries[entries[0]][1] if len(entries) == 1 else 0
        if len(entries) == 1:
            prompt = (f"Exp for {MASTERIES[u.masteries[entries[0]][0]][0]} "
                      f"(0 – 65535):")
        else:
            names = [MASTERIES[u.masteries[i][0]][0] for i in entries]
            shown = ", ".join(names[:4]) + (f" +{len(names) - 4} more" if len(names) > 4 else "")
            prompt = f"Exp for {len(entries)} masteries ({shown}) (0 – 65535):"
        val = _ask_number(self, "Mastery exp", prompt, cur, 65535)
        if val is None:
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            mas = list(v.masteries)
            changed = False
            for i in entries:
                if mas[i][1] != val:
                    mas[i] = (mas[i][0], val)
                    changed = True
            if not changed:
                return None
            return core.with_lists(g, v, mas, list(v.classes))

        if len(entries) == 1:
            what = f"{MASTERIES[u.masteries[entries[0]][0]][0]} exp → {val}"
        else:
            what = f"{len(entries)} masteries' exp → {val}"
        self._core_edit(edit, what)

    def add_mastery(self):
        u = self._cls_unit()
        if u is None:
            return
        have = {m[0] for m in u.masteries}
        rows = [(i, MASTERIES[i][0], MASTERIES[i][1]) for i in range(len(MASTERIES))
                if i not in have]
        if not rows:
            self.flash("The unit already has every weapon mastery.", "info")
            return
        idx = self._picker("Add a weapon mastery", rows)
        if idx is None:
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            mas = sorted(list(v.masteries) + [(idx, 0)])
            return core.with_lists(g, v, mas, list(v.classes))

        self._core_edit(edit, f"Added mastery {MASTERIES[idx][0]}")

    def remove_mastery(self):
        u = self._cls_unit()
        sel = self.mas_tree.selection()
        if u is None or not sel:
            return
        entry = int(sel[0])
        idx = u.masteries[entry][0]
        if not messagebox.askyesno("Save editor",
                                   f"Remove the {MASTERIES[idx][0]} mastery from "
                                   f"{unit_name(u.person)}?", parent=self):
            return

        def edit(g):
            v = next((x for x in g.units() if x.start == u.start), None)
            if v is None:
                return None
            mas = [m for i, m in enumerate(v.masteries) if i != entry]
            return core.with_lists(g, v, mas, list(v.classes))

        self._core_edit(edit, f"Removed mastery {MASTERIES[idx][0]}")

    # ============================================================== FLAGS
    def _build_flags(self):
        page = self.flags_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        row = ttk.Frame(top, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Saved flags", style="CardH3.TLabel").pack(side="left")
        self.flag_count = ttk.Label(row, text="", style="CardMuted.TLabel")
        self.flag_count.pack(side="left", padx=(10, 0))
        ttk.Button(row, text="Add flag…", style="Small.TButton",
                   command=self.add_flag).pack(side="right")
        ttk.Button(row, text="Set value…", style="Small.TButton",
                   command=self.set_flag_value).pack(side="right", padx=(6, 0))
        ttk.Button(row, text="Remove", style="Small.TButton",
                   command=self.remove_flag).pack(side="right", padx=(6, 0))
        self.flag_search = ttk.Entry(top)
        self.flag_search.pack(fill="x", pady=(8, 6))
        self.flag_search.bind("<KeyRelease>", lambda e: self.refresh_flags())
        quick = ttk.Frame(top, style="Card.TFrame")
        quick.pack(fill="x")
        for text, prefix in (("All", ""), ("Supports", "支援会話_"), ("Recruited", "加入_"),
                             ("Met", "面識_"), ("Achievements", "実績_"),
                             ("Expansion classes", "兵種解放_")):
            ttk.Button(quick, text=text, style="Small.TButton",
                       command=lambda p=prefix: self.set_flag_filter(p)).pack(side="left",
                                                                              padx=(0, 6))
        self.flag_filter = ""
        self.flag_tree = scrolled_tree(page, columns=("label", "value", "map"),
                                       show="tree headings", selectmode="browse")
        self.flag_tree.heading("#0", text="Name", anchor="w")
        self.flag_tree.heading("label", text="Reads as", anchor="w")
        self.flag_tree.heading("value", text="Value", anchor="e")
        self.flag_tree.heading("map", text="List", anchor="e")
        self.flag_tree.column("#0", width=260)
        self.flag_tree.column("label", width=360)
        self.flag_tree.column("value", width=80, anchor="e", stretch=False)
        self.flag_tree.column("map", width=60, anchor="e", stretch=False)
        self.flag_tree.container.pack(fill="both", expand=True, pady=(8, 0))
        ttk.Label(page, style="CardFaint.TLabel", justify="left", wraplength=980,
                  text="Flags are the game's named variables: 支援会話_<A>_<B>_<rank> marks a "
                       "support conversation as seen, 加入_ a recruited character, 面識_ a met "
                       "one, 実績_ an achievement counter. A name the data files don't contain "
                       "shows as its hash — that is a real flag, just one the editor can't name."
                  ).pack(anchor="w", pady=(8, 0))

    def set_flag_filter(self, prefix: str):
        self.flag_filter = prefix
        self.refresh_flags()

    def refresh_flags(self):
        if not hasattr(self, "flag_tree"):
            return
        f = self.core_of()
        self.flag_tree.delete(*self.flag_tree.get_children())
        self._flag_rows = {}
        if not f:
            self.flag_count.configure(text="")
            return
        names = flag_names()
        q = ""
        try:
            q = self.flag_search.get().strip().lower()
        except Exception:                     # noqa: BLE001
            pass
        shown = 0
        total = 0
        for m in core.flag_maps(f):
            for fl in m.flags:
                total += 1
                meta = names.get(fl.hash)
                name = meta["name"] if meta else ""
                label = meta.get("label") if meta else ""
                if self.flag_filter:
                    if not name.startswith(self.flag_filter):
                        continue
                if q:
                    hay = (name + " " + (label or "") + " %08x" % fl.hash).lower()
                    if q not in hay:
                        continue
                text = label or (friendly(name) if name else
                                 ("unknown 0x%08x" % fl.hash))
                sec = name if (name and name != text) else ""
                iid = self.flag_tree.insert("", "end", text=text,
                                            values=(sec, fl.value, m.index),
                                            tags=("flag_unknown",) if not meta else ())
                self._flag_rows[iid] = (m.index, fl.hash)
                shown += 1
        self.flag_count.configure(text=f"{shown:,} of {total:,} in this file"
                                       + (f" · {self.flag_filter}*" if self.flag_filter else ""))
        p = self.p
        self.flag_tree.tag_configure("flag_unknown", foreground=p["muted"])

    def _flag_sel(self):
        sel = self.flag_tree.selection() if hasattr(self, "flag_tree") else ()
        return getattr(self, "_flag_rows", {}).get(sel[0] if sel else None)

    def set_flag_value(self):
        key = self._flag_sel()
        if not key:
            return
        f = self.core_of()
        map_i, hash_ = key
        cur = next((fl.value for m in core.flag_maps(f) for fl in m.flags
                    if m.index == map_i and fl.hash == hash_), 0)
        val = _ask_number(self, "Flag value", "New value (0 – 2147483647):", cur, 2_147_483_647)
        if val is None or val == cur:
            return
        self._write_flag(map_i, hash_, val)

    def _write_flag(self, map_i: int, hash_: int, value: int):
        def edit(g):
            maps = core.flag_maps(g)
            m = next((x for x in maps if x.index == map_i), None)
            if m is None:
                return None
            fl = next((x for x in m.flags if x.hash == hash_), None)
            if fl is None:
                return core.flag_add(g, m, hash_, value)
            start = fl.offset - 5 if fl.wide else fl.offset - 4
            size = 9 if fl.wide else 5
            b = bytearray(g.payload[start:start + size])
            if fl.wide:
                b[5:9] = core.struct.pack("<i", value)
            else:
                b[4] = value & 0xFF
            return core.replace_content(g, m.start, bytes(b))

        name = (flag_names().get(hash_) or {}).get("label") or "0x%08x" % hash_
        self._core_edit(edit, f"{name} = {value}")

    def remove_flag(self):
        key = self._flag_sel()
        if not key:
            return
        map_i, hash_ = key
        name = (flag_names().get(hash_) or {}).get("label") or "0x%08x" % hash_
        if not messagebox.askyesno("Save editor", f"Remove the flag {name}?", parent=self):
            return

        def edit(g):
            for m in core.flag_maps(g):
                if m.index != map_i:
                    continue
                fl = next((x for x in m.flags if x.hash == hash_), None)
                if fl is None:
                    return None
                return core.flag_remove(g, m, fl)
            return None

        self._core_edit(edit, f"Removed {name}")

    def add_flag(self):
        names = flag_names()
        rows = [(h, v.get("label") or v["name"], v["name"]) for h, v in names.items()]
        rows.sort(key=lambda r: str(r[1]).lower())
        hash_ = self._picker("Add a flag", rows)
        if hash_ is None:
            return
        val = _ask_number(self, "Flag value", "Value to store (0 – 254, or anything wider):",
                          1, 2_147_483_647)
        if val is None:
            return
        f = self.core_of()
        maps = core.flag_maps(f)
        if not maps:
            self.flash("This save has no flag list to add to.", "error")
            return
        target = maps[0].index

        def edit(g):
            ms = core.flag_maps(g)
            if not ms:
                return None
            return core.flag_add(g, ms[0], hash_, val)

        name = (names.get(hash_) or {}).get("label") or "0x%08x" % hash_
        self._core_edit(edit, f"Added {name} = {val}")

    # ====================================================== support unlock
    def _map_for_prefix(self, f, prefix: str) -> int:
        """The flag list that already holds flags named like `prefix`."""
        names = flag_names()
        best, best_n = None, 0
        for m in core.flag_maps(f):
            n = sum(1 for x in m.flags
                    if (names.get(x.hash) or {}).get("name", "").startswith(prefix))
            if n > best_n:
                best, best_n = m, n
        if best is not None:
            return best.index
        maps = core.flag_maps(f)
        return maps[0].index if maps else -1

    def sup_set_rank(self, rank: str):
        """Mark the <rank> conversation as seen for every selected pair."""
        sel = self.sup_tree.selection() if hasattr(self, "sup_tree") else ()
        rows = getattr(self, "_sup_pairs", {})
        picked = [rows[i] for i in sel if i in rows]
        if not picked:
            self.flash("Pick a support partner on the Supports page first.", "info")
            return
        if not any((fl or {}).get(rank) for _p, fl in picked):
            self.flash(("This pair has" if len(picked) == 1 else "None of these pairs have")
                       + f" a {rank} conversation in the game data.", "error")
            return
        f = self.core_of()
        have = {x.hash for m in core.flag_maps(f) for x in m.flags}
        todo = [(pair, fl[rank]) for pair, fl in picked
                if (fl or {}).get(rank) and fl[rank] not in have]
        if not todo:
            self.flash(f"Already recorded ({rank}).")
            return
        target = self._map_for_prefix(f, "支援会話_")
        hashes = [h for _p, h in todo]

        def edit(g):
            for h in hashes:
                ms = core.flag_maps(g)
                m = next((x for x in ms if x.index == target), ms[0] if ms else None)
                if m is None:
                    return None
                out = core.flag_add(g, m, h, 1)
                if out is None:
                    return None
                g = core.SaveFile(out)
            return g.payload

        pair = todo[0][0]
        who = pair["b_en"] if len(todo) == 1 else f"{len(todo)} partners"
        self._core_edit(edit, f"Support {pair['a_en']} – {who} ({rank}) seen")
        self.refresh_support_chars()

    def sup_forget_rank(self):
        sel = self.sup_tree.selection() if hasattr(self, "sup_tree") else ()
        rows = getattr(self, "_sup_pairs", {})
        if not sel or sel[0] not in rows:
            self.flash("Pick a support partner on the Supports page first.", "info")
            return
        pair, fl = rows[sel[0]]
        ranks = [(r, r, "") for r in ("C", "B", "A") if fl.get(r)]
        if not ranks:
            self.flash("This pair has no conversations in the game data.", "error")
            return
        rank = self._picker("Forget which conversation?", ranks)
        if rank:
            self.sup_clear_rank(rank)

    def sup_clear_rank(self, rank: str):
        sel = self.sup_tree.selection() if hasattr(self, "sup_tree") else ()
        rows = getattr(self, "_sup_pairs", {})
        if not sel or sel[0] not in rows:
            return
        pair, fl = rows[sel[0]]
        hash_ = (fl or {}).get(rank)
        if not hash_:
            return
        if not messagebox.askyesno("Save editor",
                                   f"Forget the {rank} conversation between "
                                   f"{pair['a_en']} and {pair['b_en']}?", parent=self):
            return

        def edit(g):
            for m in core.flag_maps(g):
                for x in m.flags:
                    if x.hash == hash_:
                        return core.flag_remove(g, m, x)
            return None

        self._core_edit(edit, f"Support {pair['a_en']} – {pair['b_en']} ({rank}) cleared")
        self.refresh_support_chars()


    # ====================================================== support points
    def sup_apply_points(self):
        """Write the number in the points box onto the selected pair."""
        raw = (self.sup_pt_var.get() or "").strip().replace(",", "").replace(" ", "")
        if not raw.isdigit():
            self.flash(f"Type a support point value between 0 and "
                       f"{supports.max_points():,}.", "error")
            return
        self.sup_set_points(int(raw))

    def sup_set_points(self, value: int):
        """Set support points (the save's own value) on every selected pair."""
        sel = self.sup_tree.selection() if hasattr(self, "sup_tree") else ()
        pt = getattr(self, "_sup_pt", {})
        rows = [i for i in sel if i in pt]
        if not rows:
            self.flash("Pick a support partner on the Supports page first.", "info")
            return
        value = max(0, min(int(value), supports.max_points()))
        a_en = self.sup_name.cget("text")
        todo = [(pt[i][0], self.sup_tree.item(i, "text")) for i in rows if pt[i][1] != value]
        if not todo:
            who = (self.sup_tree.item(rows[0], "text") if len(rows) == 1
                   else f"all {len(rows)} partners")
            self.flash(f"{a_en} – {who} already at {value:,} points.", "info")
            return
        hashes = [h for h, _n in todo]

        def edit(g):
            blk = g.block("GameUserData")
            if not blk:
                return None
            table = supports.find_table(g.payload, blk.start, blk.end) or {}
            changed = False
            for h in hashes:
                entry = table.get(h)
                if entry is None or entry[0] == value:
                    continue
                supports.set_points(g.payload, entry[2], value)
                changed = True
            return g.payload if changed else None

        who = todo[0][1] if len(todo) == 1 else f"{len(todo)} partners"
        # _core_edit re-reads the save and refreshes every page, which rebuilds
        # this one with the same character and partners still selected.
        self._core_edit(edit, f"Support points {a_en} – {who} → {value:,}")

def settings_offsets(f: core.SaveFile) -> list[int]:
    """Offsets of the (mode, difficulty) byte pairs, everywhere the save keeps them."""
    out = []

    def collect(start: int, length: int, depth: int):
        if depth > 6:
            return
        sub = core.SaveFile(bytes(f.payload[start:start + length]))
        hdr = sub.block("Header")
        if hdr is not None and hdr.start == 4 and sub.payload[12] == 15:
            out.append(start + 14)
        ud = sub.block("GameUserData")
        if ud is not None and ud.start + 7 <= len(sub.payload) and sub.payload[ud.start + 4] == 23:
            out.append(start + ud.start + 5)
        for node in sub.tree().nodes:
            if not node.leaf:
                continue
            at = node.start + 4
            body = None
            for probe in (node.start + 4, node.start + 8):
                if probe + 32 <= node.end and \
                        sub.u32(probe) == core.MAGIC:
                    size = sub.u32(probe + 4)
                    if sub.u32(probe + 12) == 1 and 0 < size and probe + 32 + size <= node.end:
                        body = (probe + 32, size)
                        break
            if body and sub.payload[body[0] + 4] == 15:
                out.append(start + body[0] + 6)
            elif body:
                try:
                    collect(start + body[0], body[1], depth + 1)
                except Exception:             # noqa: BLE001
                    pass

    collect(0, len(f.payload), 0)
    return sorted(set(out))


def _ask_number(parent, title: str, prompt: str, current: int, limit: int):
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.resizable(False, False)
    win.configure(background=parent.p["bg"])
    ttk.Label(win, text=prompt, padding=(16, 14, 16, 6)).pack(anchor="w")
    var = tk.StringVar(value=str(current))
    ent = ttk.Entry(win, textvariable=var, width=18, justify="right")
    ent.pack(padx=16)
    out = {"v": None}

    def ok(*_a):
        t = var.get().strip().replace(",", "")
        if t.isdigit():
            out["v"] = min(int(t), limit)
        win.destroy()

    bar = ttk.Frame(win, padding=12)
    bar.pack(fill="x")
    ttk.Button(bar, text="OK", style="Accent.TButton", command=ok).pack(side="right")
    ttk.Button(bar, text="Cancel", command=win.destroy).pack(side="right", padx=(0, 8))
    ent.bind("<Return>", ok)
    if hasattr(parent, "place_dialog"):
        parent.place_dialog(win)
    ent.focus_set()
    ent.select_range(0, "end")
    parent.wait_window(win)
    return out["v"]



# ==========================================================================
# part 2 — the pages that replace the guessing code
# (appended to editor_advanced.py; every method here uses fefw_layer, which
#  answers unit / item / skill / convoy / gold questions from fefw_core)
# ==========================================================================
import fefw_layer as layer          # noqa: E402


def _slot_payload(app):
    return app.sv.payload if app.sv else None


# ---------------------------------------------------------------- undo/redo
def push_undo(self):
    """Snapshot the payload before an edit, so Ctrl+Z can take it back."""
    if not self.sv:
        return
    stack = getattr(self, "_undo_stack", None)
    if stack is None:
        stack = self._undo_stack = []
        self._redo_stack = []
    stack.append(bytes(self.sv.payload))
    del stack[:-60]
    self._redo_stack.clear()


def undo(self):
    stack = getattr(self, "_undo_stack", None)
    if not stack or not self.sv:
        self.flash("Nothing to undo.", "info")
        return
    self._redo_stack.append(bytes(self.sv.payload))
    self.sv.payload = bytearray(stack.pop())
    self.sv.scan()
    self.sv._core_cache = None
    self._touch([self.sv])
    self.refresh_after_core()
    self.flash("Undone — Ctrl+Y puts it back.", "ok")


def redo(self):
    stack = getattr(self, "_redo_stack", None)
    if not stack or not self.sv:
        self.flash("Nothing to redo.", "info")
        return
    self._undo_stack.append(bytes(self.sv.payload))
    self.sv.payload = bytearray(stack.pop())
    self.sv.scan()
    self.sv._core_cache = None
    self._touch([self.sv])
    self.refresh_after_core()
    self.flash("Redone.", "ok")


# --------------------------------------------------------------- snapshots
def snapshot_root(self) -> str:
    import os
    return os.path.join(os.path.dirname(os.path.abspath(self.sv.path)), "_snapshots")


def take_snapshot(self, name: str | None = None):
    import os
    import shutil
    import time
    if not self.folder:
        return
    stamp = time.strftime("%Y%m%d_%H%M%S")
    label = (name or "").strip()
    safe = "".join(c if c not in '\\/:*?"<>|' else "_" for c in label)
    dest = os.path.join(self.snapshot_root(), stamp + ((" " + safe) if safe else ""))
    os.makedirs(dest, exist_ok=True)
    saved = 0
    for p in self.slot_paths:
        if os.path.exists(p):
            shutil.copy2(p, dest)
            saved += 1
    self.flash(f"Snapshot of {saved} slots saved to {os.path.basename(dest)}", "ok")


def restore_snapshot(self):
    import os
    import shutil
    from tkinter import filedialog, messagebox
    root = self.snapshot_root()
    if not os.path.isdir(root):
        self.flash("No snapshots yet — press Snapshot first.", "warn")
        return
    pick = filedialog.askdirectory(parent=self, initialdir=root,
                                   title="Pick a snapshot to restore")
    if not pick:
        return
    n = len([f for f in os.listdir(pick) if os.path.isfile(os.path.join(pick, f))])
    if not messagebox.askyesno(
            APP_NAME, f"Copy the {n} slot files from\n{pick}\nover the save folder?\n\n"
                      "Everything in the editor is reloaded from those files.", parent=self):
        return
    for name in os.listdir(pick):
        src = os.path.join(pick, name)
        if os.path.isfile(src) and is_slot_name(name):
            shutil.copy2(src, os.path.join(self.folder, name))
    self.dirty.clear()
    self.reload()
    self.flash(f"Restored {n} slots from {os.path.basename(pick)}.", "ok")


# ------------------------------------------------------------- arts/skills
def _build_skill_tab(self):
    """The record's skill lists (all six), each with add / remove."""
    tab = ttk.Frame(self.unit_tabs, style="Card.TFrame", padding=16)
    self.unit_tabs.add(tab, text="Arts & skills")
    grid = ttk.Frame(tab, style="Card.TFrame")
    grid.pack(fill="both", expand=True)
    self._skill_trees = {}
    for idx, name in enumerate(layer.SKILL_LIST_NAMES):
        box = ttk.Frame(grid, style="Card.TFrame", padding=(0, 0, 10, 10))
        box.grid(row=idx // 3, column=idx % 3, sticky="nsew")
        grid.columnconfigure(idx % 3, weight=1, uniform="skills")
        grid.rowconfigure(idx // 3, weight=1)
        head = ttk.Frame(box, style="Card.TFrame")
        head.pack(fill="x")
        ttk.Label(head, text=name, style="CardH3.TLabel").pack(side="left")
        for text, fn in (("Remove", lambda i=idx: self.remove_skill(i)),
                         ("Add…", lambda i=idx: self.add_skill(i))):
            ttk.Button(head, text=text, style="Small.TButton", width=7,
                       command=fn).pack(side="right", padx=(4, 0))
        tree = scrolled_tree(box, show="tree", selectmode="browse", height=5)
        tree.container.pack(fill="both", expand=True, pady=(4, 0))
        self._skill_trees[idx] = tree
    ttk.Label(tab, style="CardFaint.TLabel", justify="left", wraplength=820,
              text="Equipped arts and skills are what the unit takes into battle; "
                   "“Learned (all)” is everything it has learned. Adding or removing an "
                   "entry rewrites the list safely."
              ).pack(anchor="w", pady=(8, 0))


def refresh_skill_lists(self):
    if not hasattr(self, "_skill_trees") or not self.sv or self.uid is None:
        return
    lists = layer.skill_lists(self.sv.payload, self.uid)
    for idx, tree in self._skill_trees.items():
        tree.delete(*tree.get_children())
        ids = lists[idx] if idx < len(lists) else []
        for k, sid in enumerate(ids):
            tree.insert("", "end", iid=str(k), text="  " + layer.skill_label(sid))
        if not ids:
            tree.insert("", "end", iid="none", text="  (empty)", tags=("empty",))


def add_skill(self, index: int):
    if not self.sv or self.uid is None:
        return
    # every entry in these lists is a skill / combat art id (SID_…), never an item
    rows = [(h, m.get("en") or m.get("jp") or m.get("sid"), m.get("sid", ""))
            for h, m in layer._skills().items()
            if not (m.get("sid") or "").startswith("SID_>") and (m.get("en") or m.get("jp"))]
    # skills with an English name first; internal / enemy-only entries after
    eng = {h for h, m in layer._skills().items() if m.get("en")}
    rows.sort(key=lambda r: (r[0] not in eng, str(r[1]).lower()))
    if not rows:
        self.flash("No skill names available (skill_ids.json is missing).", "warn")
        return
    sid = self._picker("Add to " + layer.SKILL_LIST_NAMES[index], rows)
    if sid is None:
        return
    self.push_undo()

    def edit(g):
        u = layer.unit_in(g, self.uid)
        if u is None:
            return None
        try:
            ids = core.skill_list(g, u, index + 1)
        except Exception:                     # noqa: BLE001
            return None
        if sid in ids:
            return None
        return core.with_skill_list(g, u, index + 1, ids + [sid])

    self._core_edit(edit, f"{layer.SKILL_LIST_NAMES[index]}: added {layer.skill_label(sid)}")


def remove_skill(self, index: int):
    tree = getattr(self, "_skill_trees", {}).get(index)
    sel = tree.selection() if tree else ()
    if not self.sv or self.uid is None or not sel or sel[0] == "none":
        return
    k = int(sel[0])

    def edit(g):
        u = layer.unit_in(g, self.uid)
        if u is None:
            return None
        try:
            ids = core.skill_list(g, u, index + 1)
        except Exception:                     # noqa: BLE001
            return None
        if k >= len(ids):
            return None
        return core.with_skill_list(g, u, index + 1, [x for i, x in enumerate(ids) if i != k])

    self.push_undo()
    self._core_edit(edit, f"{layer.SKILL_LIST_NAMES[index]}: removed entry {k + 1}")


# ------------------------------------------------------------------ mounts
def _build_mounts(self):
    pane = ttk.PanedWindow(self.mounts_page, orient="horizontal")
    pane.pack(fill="both", expand=True)
    left = ttk.Frame(pane, style="Card.TFrame", padding=12)
    pane.add(left, weight=3)
    ttk.Label(left, text="Battalions & mounts", style="CardH3.TLabel").pack(anchor="w")
    ttk.Label(left, style="CardMuted.TLabel", wraplength=520, justify="left",
              text="Each unit carries one battalion (and, for mounted classes, one mount) at "
                   "the end of its record. Pick from the pool this save holds.").pack(
        anchor="w", pady=(2, 8))
    self.mount_tree = scrolled_tree(left, columns=("bat", "mount"), show="tree headings",
                                    selectmode="browse")
    self.mount_tree.heading("#0", text="Unit", anchor="w")
    self.mount_tree.heading("bat", text="Battalion", anchor="w")
    self.mount_tree.heading("mount", text="Mount", anchor="w")
    self.mount_tree.column("#0", width=190)
    self.mount_tree.column("bat", width=230)
    self.mount_tree.column("mount", width=140)
    self.mount_tree.container.pack(fill="both", expand=True)

    right = ttk.Frame(pane, style="Card.TFrame", padding=12)
    pane.add(right, weight=2)
    ttk.Label(right, text="This save's pool", style="CardH3.TLabel").pack(anchor="w")
    self.pool_tree = scrolled_tree(right, columns=("kind", "id"), show="tree headings",
                                   selectmode="browse")
    self.pool_tree.heading("#0", text="Entry", anchor="w")
    self.pool_tree.heading("kind", text="Kind", anchor="w")
    self.pool_tree.heading("id", text="Record id", anchor="w")
    self.pool_tree.column("#0", width=90)
    self.pool_tree.column("kind", width=80)
    self.pool_tree.column("id", width=190)
    self.pool_tree.container.pack(fill="both", expand=True, pady=(6, 6))
    row = ttk.Frame(right, style="Card.TFrame")
    row.pack(fill="x")
    ttk.Button(row, text="Assign to unit", style="Small.TButton",
               command=self.assign_battalion).pack(side="left")
    ttk.Button(row, text="Clear unit's", style="Small.TButton",
               command=lambda: self.assign_battalion(clear=True)).pack(side="left", padx=(6, 0))
    ttk.Button(row, text="Remove from pool", style="Small.TButton",
               command=self.remove_battalion).pack(side="left", padx=(6, 0))


def refresh_mounts(self):
    if not hasattr(self, "mount_tree"):
        return
    self.mount_tree.delete(*self.mount_tree.get_children())
    self.pool_tree.delete(*self.pool_tree.get_children())
    self._mount_rows, self._pool_rows = {}, {}
    if not self.sv:
        return
    bat_by_unit = {}
    for l in layer.battalions(self.sv.payload):
        bat_by_unit.setdefault(l.owner, l)
    for u in layer.find_units(self.sv.payload):
        g = layer.unit_gear(self.sv.payload, u.uid)
        bat = bat_by_unit.get((g.unit_number if g else -1))
        bat_txt = ("Battalion row %d" % bat.row) if bat else "—"
        mnt = ("Mount #%d" % g.ride.serial) if (g and g.ride) else "—"
        iid = self.mount_tree.insert("", "end", text=u.name,
                                     values=(bat_txt, mnt))
        self._mount_rows[iid] = u.uid
    for i, l in enumerate(layer.battalions(self.sv.payload)):
        iid = self.pool_tree.insert("", "end", text=f"#{i + 1}", values=("Battalion", hex(l.id)),
                                    iid="b%d" % i)
        self._pool_rows[iid] = ("battalion", i)
    for i, r in enumerate(layer.mounts(self.sv.payload)):
        iid = self.pool_tree.insert("", "end", text=f"#{i + 1}", values=("Mount", hex(r.id)),
                                    iid="m%d" % i)
        self._pool_rows[iid] = ("mount", i)


def assign_battalion(self, clear: bool = False):
    sel = self.mount_tree.selection() if hasattr(self, "mount_tree") else ()
    uid = getattr(self, "_mount_rows", {}).get(sel[0] if sel else None)
    if uid is None or not self.sv:
        self.flash("Pick a unit on the Mounts page first.", "info")
        return
    legion = None
    ride = None
    g = layer.unit_gear(self.sv.payload, uid)
    if g is None:
        self.flash("This unit's record has no battalion slot (the game gives it one when "
                   "the unit actually joins a battle) — nothing to write.", "warn")
        return
    if g.ride:
        ride = g.ride
    if not clear:
        psel = self.pool_tree.selection()
        if not psel:
            self.flash("Pick a battalion in the pool first.", "info")
            return
        kind, idx = self._pool_rows.get(psel[0], (None, None))
        if kind != "battalion":
            self.flash("Only battalions can be assigned here.", "warn")
            return
        legion = layer.battalions(self.sv.payload)[idx]
        legion = core.Legion(legion.row, g.unit_number if g else 0, legion.id)
    self.push_undo()

    def edit(f):
        u = layer.unit_in(f, uid)
        gg = core.gear(f, u)
        if gg is None:
            return None
        return core.with_gear(f, u, gg, ride, legion)

    self._core_edit(edit, "Battalion cleared" if clear
                    else ("Battalion → row %d" % legion.row))


def remove_battalion(self):
    psel = self.pool_tree.selection() if hasattr(self, "pool_tree") else ()
    if not psel or not self.sv:
        return
    kind, idx = self._pool_rows.get(psel[0], (None, None))
    if kind != "battalion":
        self.flash("Pick a battalion in the pool first.", "info")
        return
    self.push_undo()
    self._core_edit(lambda f: layer_del_battalion(f, idx), "Removed battalion from the pool")


def layer_del_battalion(f, idx: int):
    st = core.party_store(f)
    if not st:
        return None
    pool = core.legions(f, st[2])
    if not (0 <= idx < len(pool)):
        return None
    return core.with_legions(f, st[2], [l for i, l in enumerate(pool) if i != idx])


# ------------------------------------------------------- units: copy / remove
def copy_unit_in(self):
    """Bring a unit over from another slot of the same folder."""
    import os
    from tkinter import filedialog
    if not self.sv:
        return
    others = [p for p in self.slot_paths if p != self.sv.path]
    start = self.folder or os.path.dirname(self.sv.path)
    pick = filedialog.askopenfilename(
        parent=self, initialdir=start, title="Copy a unit from which save?",
        filetypes=[("Save slots", "Auto Chapter_* Route_*"), ("All files", "*.*")])
    if not pick:
        return
    try:
        src = layer.SaveFile(pick)
    except Exception as exc:                  # noqa: BLE001
        self.flash(f"Can't read {os.path.basename(pick)}: {exc}", "error")
        return
    rows = [(u.uid, u.name, f"Lv {u.level} · {u.job}") for u in src.units]
    rows.sort(key=lambda r: r[1].lower())
    uid = self._picker(f"Copy a unit from {os.path.basename(pick)}", rows)
    if uid is None:
        return
    self.push_undo()
    name = next(r[1] for r in rows if r[0] == uid)
    self._core_edit(lambda f: (layer.copy_unit_in(f.payload, pick, uid) and f.payload) or None,
                    f"Copied {name} in")


def remove_current_unit(self):
    if not self.sv or self.uid is None:
        return
    from tkinter import messagebox
    u = self._current()
    if u is None:
        return
    if not messagebox.askyesno(
            APP_NAME, f"Remove {u.name} from this save?\n\n"
                      "The game may still refer to them (join flags, battalions, supports), "
                      "which can confuse it. Undo (Ctrl+Z) brings them back; nothing is "
                      "written until you save.", parent=self):
        return
    self.push_undo()
    self._core_edit(lambda f: (layer.remove_unit(f.payload, self.uid) and f.payload) or None,
                    f"Removed {u.name}")
    self.uid = None


# ------------------------------------------------------------ convoy extras
def add_convoy_item_ui(self):
    if not self.sv:
        return
    rows = [(h, layer.item_label(h, m), m.get("jp", "")) for h, m in layer.item_ids().items()]
    rows.sort(key=lambda r: str(r[1]).lower())
    iid = self._picker("Add to the convoy", rows)
    if iid is None:
        return
    qty = _ask_number(self, "Quantity", "How many?", 1, 999)
    if not qty:
        return
    conv = layer.live_convoy(bytes(self.sv.payload))
    home = layer.convoy_home(iid, conv.slots) if conv else None
    if home is None:
        self.flash(f"{layer.item_label(iid)} has no convoy slot of its own.", "warn")
        return
    other = next((r for r in conv.rows if r.slot == home and r.qty and r.iid != iid), None)
    if other:
        self.flash(f"Slot {home + 1}, {layer.item_label(iid)}'s own slot, holds "
                   f"{layer.item_label(other.iid)} — remove that first.", "warn")
        return
    self.push_undo()
    self._core_edit(lambda f: (layer.add_convoy_slot(f.payload, iid, qty) and f.payload) or None,
                    f"Convoy: added {layer.item_label(iid)} ×{qty}")
    self.refresh_convoy()


def fill_materials_ui(self):
    """Put every forging/cooking material in the convoy at one quantity."""
    if not self.sv:
        return
    mats = layer.material_ids()
    if not mats:
        self.flash("No materials found in the item list.", "error")
        return
    try:
        start = int(self.qty_var.get())
    except (AttributeError, ValueError):
        start = 99
    qty = _ask_number(self, "All materials",
                      f"Quantity for each of the {len(mats)} materials\n"
                      "(ores, meat, fish, plants, leaves, manure).\n"
                      "Each goes into its own convoy slot; stacks you\n"
                      "already have are set to it.", max(1, start), 999)
    if not qty:
        return
    self.push_undo()
    got = {}

    def run(f):
        res = layer.fill_materials(f.payload, qty)
        got.setdefault("r", res)
        return f.payload if any(res[:3]) else None

    if self._core_edit(run, f"Convoy: all materials ×{qty}"):
        kept, added, moved, blocked = got.get("r", (0, 0, 0, 0))
        msg = f"Materials ×{qty}: {added} added, {kept} set"
        if moved:
            msg += f", {moved} moved into their own slots"
        if blocked:
            msg += f" — {blocked} skipped (their slot holds another item)"
        self.flash(msg + " — Ctrl+S to write it.", "warn" if blocked else "ok")
    self.refresh_convoy()


def remove_convoy_item_ui(self):
    slots = self._conv_selected() if hasattr(self, "_conv_selected") else []
    if not slots:
        self.flash("Pick a convoy row first.", "info")
        return
    self.push_undo()
    for slot in sorted(slots, reverse=True):
        self._core_edit(
            lambda f, s=slot: (layer.remove_convoy_slot(f.payload, s) and f.payload) or None,
            f"Convoy: removed slot {slot + 1}")
    self.refresh_convoy()


# everything above is a plain function taking the app; attach it to the mixin
for _name in ("push_undo", "undo", "redo", "snapshot_root", "take_snapshot",
              "restore_snapshot", "_build_skill_tab", "refresh_skill_lists",
              "add_skill", "remove_skill", "_build_mounts", "refresh_mounts",
              "assign_battalion", "remove_battalion", "copy_unit_in",
              "remove_current_unit", "add_convoy_item_ui", "remove_convoy_item_ui",
              "fill_materials_ui"):
    setattr(AdvancedMixin, _name, globals()[_name])
