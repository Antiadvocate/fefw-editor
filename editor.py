"""
FEFW Save Editor — Fire Emblem: Fortune's Weave (Eden / eglantine slots).

Opens ONE slot file at a time, exactly as it exists on disk, so what you see is
everything that file holds. Edits go back into that same file only.

Tabs: Units (level / EXP / max HP / nine stats) and Money (gold).
"""

from __future__ import annotations

import os
import struct
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fefw_save import (CONVOY_ENTRY, GRADES, SKILL_NAMES, SKILL_THRESHOLDS, STAT_NAMES,
                       SaveError, SaveFile, add_convoy_item, convoy_blocks, convoy_items,
                       default_save_dir, find_money_candidates, grade_label, is_enemy,
                       is_shadow, item_category, item_ids, job_ids, job_name, load_money_sig,
                       locate_money, money_signature, next_threshold, pick_live,
                       remove_convoy_item, save_money_sig, set_convoy_row)


def slot_files(folder: str) -> list[str]:
    out = []
    for name in sorted(os.listdir(folder)):
        if "." in name:
            continue
        if name == "Auto" or name.startswith(("Chapter_", "Route_")):
            out.append(os.path.join(folder, name))
    return out


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fortune's Weave — Save Editor")
        self.geometry("940x600")
        self.minsize(800, 500)

        self.sv: SaveFile | None = None
        self.uid: int | None = None
        self.money_off: int | None = None

        self._build()
        folder = default_save_dir()
        if folder:
            slots = slot_files(folder)
            if slots:
                self.populate_slots(slots)
                self.load(slots[0])

    # ------------------------------------------------------------------ ui
    def _build(self):
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(fill="x")
        ttk.Label(bar, text="Slot").pack(side="left")
        self.slot_var = tk.StringVar()
        self.slot_box = ttk.Combobox(bar, textvariable=self.slot_var, width=34,
                                     state="readonly")
        self.slot_box.pack(side="left", padx=(6, 10))
        self.slot_box.bind("<<ComboboxSelected>>", self.on_slot_pick)
        ttk.Button(bar, text="Browse…", command=self.open_dialog).pack(side="left")
        ttk.Button(bar, text="Save file", command=self.write).pack(side="right")
        ttk.Button(bar, text="Reload", command=self.reload).pack(side="right", padx=6)

        self.file_lbl = ttk.Label(self, text="", padding=(10, 0), foreground="#444")
        self.file_lbl.pack(fill="x")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=(4, 6))

        left = ttk.Frame(body)
        body.add(left, weight=1)
        ttk.Label(left, text="Units in this file").pack(anchor="w")
        self.show_enemies = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="show enemies / NPCs (EN_ units)",
                        variable=self.show_enemies,
                        command=self.refresh_tree).pack(anchor="w")
        self.tree = ttk.Treeview(left, columns=("name", "lv", "hp"), show="headings", height=14)
        for c, w in (("name", 170), ("lv", 45), ("hp", 60)):
            self.tree.heading(c, text={"name": "Unit", "lv": "Lv", "hp": "HP"}[c])
            self.tree.column(c, width=w, anchor="w" if c == "name" else "center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right = ttk.Notebook(body)
        body.add(right, weight=2)

        # ---- unit tab
        tab = ttk.Frame(right, padding=10)
        right.add(tab, text="Unit")
        self.name_lbl = ttk.Label(tab, text="", font=("Segoe UI", 12, "bold"))
        self.name_lbl.pack(anchor="w", pady=(0, 8))

        crow = ttk.Frame(tab)
        crow.pack(fill="x", pady=(0, 6))
        ttk.Label(crow, text="Class").pack(side="left")
        self.class_box = ttk.Combobox(crow, width=40, state="readonly")
        self.class_box.pack(side="left", padx=6)
        ttk.Button(crow, text="Apply class", command=self.apply_class).pack(side="left")
        self.job_lbl = ttk.Label(crow, text="", foreground="#246")
        self.job_lbl.pack(side="left", padx=8)

        ttk.Label(tab, foreground="#555", wraplength=470,
                  text="The class is stored per unit as a hash of the game's job id, so it is "
                       "editable — but the game derives movement, usable weapons, class skills and "
                       "max HP from it, and this tool only changes the id. Save, reload the game "
                       "and check the unit screen; if the game shows something inconsistent, "
                       "change class in game instead."
                  ).pack(anchor="w", pady=(0, 6))

        self.show_bad_classes = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="show internal / enemy class ids (monsters, props)",
                        variable=self.show_bad_classes,
                        command=lambda: self.on_select()).pack(anchor="w", pady=(0, 6))

        row = ttk.Frame(tab)
        row.pack(fill="x", pady=(0, 10))
        self.lvl_var = tk.StringVar()
        self.exp_var = tk.StringVar()
        for label, var, apply, hi in (("Level", self.lvl_var, self.apply_level, 99),
                                      ("EXP", self.exp_var, self.apply_exp, 255)):
            ttk.Label(row, text=label).pack(side="left")
            sp = ttk.Spinbox(row, from_=0, to=hi, width=6, textvariable=var, command=apply)
            sp.pack(side="left", padx=(6, 14))
            sp.bind("<Return>", lambda e, f=apply: f())
            sp.bind("<FocusOut>", lambda e, f=apply: f())

        grid = ttk.Frame(tab)
        grid.pack(fill="x")
        self.stat_vars = []
        for i, name in enumerate(STAT_NAMES):
            cell = ttk.Frame(grid)
            cell.grid(row=i // 3, column=i % 3, sticky="w", padx=6, pady=6)
            ttk.Label(cell, text=name, width=4).pack(side="left")
            v = tk.StringVar()
            sp = ttk.Spinbox(cell, from_=0, to=255, width=6, textvariable=v,
                             command=lambda i=i: self.apply_stat(i))
            sp.pack(side="left")
            sp.bind("<Return>", lambda e, i=i: self.apply_stat(i))
            sp.bind("<FocusOut>", lambda e, i=i: self.apply_stat(i))
            self.stat_vars.append(v)

        ttk.Button(tab, text="Sync every copy to these values",
                   command=self.sync_copies).pack(anchor="w", pady=(10, 0))

        self.unit_note = ttk.Label(tab, wraplength=470, foreground="#555",
                                   text="Level, EXP and the stat block are confirmed. The nine values are "
                                        "HP, Str, Mag, Dex, Spd, Lck, Def, Res, Cha — the game's own "
                                        "order, taken from a cheat table that exposes the same struct in "
                                        "memory. There is no stored max HP: the game derives it from "
                                        "class and stats. A fresh level-1 unit reads all zeros. "
                                        "Nothing is written until “Save file”.")
        self.unit_note.pack(anchor="w", pady=(12, 0))

        # ---- skills / aptitude tab
        tabs = ttk.Frame(right, padding=10)
        right.add(tabs, text="Aptitude")
        ttk.Label(tabs, wraplength=470, foreground="#246",
                  text="Weapon aptitude / skill ranks, stored per unit (E → E+ → D … → S+). "
                       "The value is the unit's cumulative skill experience for that skill and "
                       "the game derives the letter from a threshold ladder (B+ starts at 960, "
                       "A at 1320, S+ at 3600). Pick a letter to write the start of that grade, "
                       "or type an exact exp value. Writes go into every copy of the unit in this "
                       "file; nothing is saved until “Save file”."
                  ).pack(anchor="w", pady=(0, 6))
        self.skill_frame = ttk.Frame(tabs)
        self.skill_frame.pack(fill="x")
        self.skill_rows = []
        ttk.Label(tabs, foreground="#555", wraplength=470,
                  text="Skill families, in the game's own order: Swords, Lances, Axes, Bows, "
                       "Fists, Black Magic, White Magic, Infantry, Riding, Heavy Armor, Flying, "
                       "Authority. A unit only has rows for the skills it owns — the rest show "
                       "E in game and cannot be added here."
                  ).pack(anchor="w", pady=(6, 0))

        row = ttk.Frame(tabs)
        row.pack(fill="x", pady=(10, 0))
        ttk.Label(row, text="Set every skill to").pack(side="left")
        self.all_grade = tk.StringVar(value="E")
        ttk.Combobox(row, textvariable=self.all_grade, values=GRADES, width=5,
                     state="readonly").pack(side="left", padx=6)
        ttk.Button(row, text="Apply to all listed skills",
                   command=self.apply_all_grades).pack(side="left")
        ttk.Button(tabs, text="Write these grades into every slot file",
                   command=self.sync_skills_to_slots).pack(anchor="w", pady=(8, 0))
        ttk.Label(tabs, foreground="#555", wraplength=470,
                  text="Mid-chapter the game resumes from a Chapter_* slot, so an edit made in "
                       "Auto alone can look like it did nothing. This copies the grades shown "
                       "here into the same unit in every other slot of this folder."
                  ).pack(anchor="w", pady=(2, 0))

        # ---- money tab
        tab2 = ttk.Frame(right, padding=10)
        right.add(tab2, text="Money")
        ttk.Label(tab2, wraplength=460, foreground="#555",
                  text="Gold is found by searching for the amount the game shows. Enter it once, "
                       "pick the match, and this tool remembers the spot for future saves."
                  ).pack(anchor="w", pady=(0, 8))

        f1 = ttk.Frame(tab2)
        f1.pack(fill="x", pady=4)
        ttk.Label(f1, text="Gold shown in game").pack(side="left")
        self.gold_search = tk.StringVar()
        ttk.Entry(f1, textvariable=self.gold_search, width=12).pack(side="left", padx=6)
        ttk.Button(f1, text="Find", command=self.find_gold).pack(side="left")

        self.gold_list = tk.Listbox(tab2, height=6, exportselection=False)
        self.gold_list.pack(fill="x", pady=6)
        self.gold_list.bind("<<ListboxSelect>>", self.on_gold_pick)

        f2 = ttk.Frame(tab2)
        f2.pack(fill="x", pady=4)
        self.gold_now = tk.StringVar(value="—")
        ttk.Label(f2, text="Current").pack(side="left")
        ttk.Label(f2, textvariable=self.gold_now, width=12).pack(side="left", padx=(6, 18))
        ttk.Label(f2, text="New").pack(side="left")
        self.gold_new = tk.StringVar()
        ttk.Entry(f2, textvariable=self.gold_new, width=12).pack(side="left", padx=6)
        ttk.Button(f2, text="Set", command=self.set_gold).pack(side="left")

        # ---- items tab
        tab3 = ttk.Frame(right, padding=10)
        right.add(tab3, text="Items")
        ttk.Label(tab3, foreground="#555",
                  text="Item ids found next to this unit's record. Pick a slot, then pick a "
                       "replacement item.").pack(anchor="w", pady=(0, 6))
        self.item_list = tk.Listbox(tab3, height=6, exportselection=False)
        self.item_list.pack(fill="x")
        self.item_list.bind("<<ListboxSelect>>", self.on_item_pick)

        ttk.Label(tab3, text="Search item").pack(anchor="w", pady=(8, 2))
        self.item_search = tk.StringVar()
        e = ttk.Entry(tab3, textvariable=self.item_search)
        e.pack(fill="x")
        e.bind("<KeyRelease>", lambda ev: self.filter_items())
        self.show_all = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab3, text="show every category (may break the game)",
                        variable=self.show_all,
                        command=self.filter_items).pack(anchor="w", pady=(0, 2))
        self.show_internal = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab3, text="show internal ids (duplicates the game ignores)",
                        variable=self.show_internal,
                        command=self.filter_items).pack(anchor="w", pady=(0, 2))
        self.item_choices = tk.Listbox(tab3, height=7, exportselection=False)
        self.item_choices.pack(fill="both", expand=True, pady=4)
        ttk.Button(tab3, text="Replace selected slot", command=self.replace_item).pack(anchor="w")

        # ---- convoy tab
        tab4 = ttk.Frame(right, padding=10)
        right.add(tab4, text="Convoy")
        ttk.Label(tab4, wraplength=460, foreground="#555",
                  text="The shared storage list — what the convoy screen shows with no owner. "
                       "Entries are appended after the last one; there is free space for them.").pack(anchor="w")
        self.conv_list = tk.Listbox(tab4, height=8, exportselection=False)
        self.conv_list.pack(fill="both", expand=True, pady=4)
        self.conv_list.bind("<<ListboxSelect>>", lambda ev: self.filter_convoy_items())
        ttk.Label(tab4, text="Search item (any category)").pack(anchor="w", pady=(6, 2))
        self.conv_search = tk.StringVar()
        ce = ttk.Entry(tab4, textvariable=self.conv_search)
        ce.pack(fill="x")
        ce.bind("<KeyRelease>", lambda ev: self.filter_convoy_items())
        ttk.Checkbutton(tab4, text="show internal ids (duplicates the game ignores)",
                        variable=self.show_internal,
                        command=self.filter_convoy_items).pack(anchor="w")
        self.conv_choices = tk.Listbox(tab4, height=8, exportselection=False)
        self.conv_choices.pack(fill="both", expand=True, pady=4)
        cf = ttk.Frame(tab4)
        cf.pack(fill="x")
        ttk.Button(cf, text="Append row", command=self.add_convoy).pack(side="left")
        ttk.Label(cf, text="  qty:").pack(side="left")
        self.type_code = tk.StringVar(value="1")
        ttk.Entry(cf, textvariable=self.type_code, width=4).pack(side="left")
        ttk.Button(cf, text="Replace row", command=self.replace_convoy).pack(side="left", padx=6)
        ttk.Button(cf, text="Remove row", command=self.remove_convoy).pack(side="left")

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, anchor="w", padding=(10, 4)).pack(fill="x")

    # ---------------------------------------------------------------- files
    def populate_slots(self, paths):
        self._slot_paths = paths
        labels = []
        for p in paths:
            try:
                sv = SaveFile(p)
                units = len(sv.units)
            except Exception:
                units = "?"
            labels.append(f"{os.path.basename(p)}  ({units}u, "
                          f"{time.strftime('%H:%M', time.localtime(os.path.getmtime(p)))})")
        self.slot_box.configure(values=labels)
        self._slot_labels = labels

    def on_slot_pick(self, _e=None):
        idx = self.slot_box.current()
        if 0 <= idx < len(self._slot_paths):
            self.load(self._slot_paths[idx])

    def open_dialog(self):
        folder = default_save_dir() or os.path.expanduser("~")
        path = filedialog.askopenfilename(initialdir=folder, title="Open one save slot",
                                          filetypes=[("Slots", "Auto Chapter_* Route_*"),
                                                     ("All files", "*.*")])
        if not path:
            return
        self.populate_slots(slot_files(os.path.dirname(path)) or [path])
        self.load(path)

    def load(self, path: str):
        prev_uid = self.uid
        try:
            self.sv = SaveFile(path)
        except SaveError as e:
            messagebox.showerror("Cannot open", str(e))
            return
        self.uid = None
        self.money_off = None
        self.gold_now.set("—")
        paths = getattr(self, "_slot_paths", []) or []
        for i, p in enumerate(paths):
            if os.path.abspath(p) == os.path.abspath(path):
                self.slot_box.current(i)
                break
        st = os.stat(path)
        self.file_lbl.configure(
            text=f"{path}\n{st.st_size:,} bytes · payload {len(self.sv.payload):,} · "
                 f"modified {time.strftime('%H:%M:%S', time.localtime(st.st_mtime))} · "
                 f"checksums: {', '.join(self.sv.verify()) or 'OK'}")
        self.refresh_tree()
        if prev_uid is not None and self.tree.exists(str(prev_uid)):
            self.tree.selection_set(str(prev_uid))
            self.on_select()
        self.locate_gold()
        self.filter_convoy_items()
        self.refresh_convoy()

    def reload(self):
        if self.sv and self.sv.path:
            self.load(self.sv.path)

    def write(self):
        if not self.sv:
            return
        prior = getattr(self.status, "get", lambda: "")()
        prior = prior.split("  ·  ")[0]
        try:
            self.sv.save(self.sv.path)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Write failed", str(e))
            return
        name = os.path.basename(self.sv.path)
        self.load(self.sv.path)
        self.status.set(f"Saved {name} (first write leaves a .bak)"
                        + (f"  —  {prior}" if prior and prior != "Ready" else ""))

    # ---------------------------------------------------------------- units
    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        seen = {}
        for u in (self.sv.units if self.sv else []):
            if not self.show_enemies.get() and is_enemy(u):
                continue
            best = seen.get(u.uid)
            if best is None or (u.base, u.level, u.exp) > (best.base, best.level, best.exp):
                seen[u.uid] = u
        for u in seen.values():
            self.tree.insert("", "end", iid=str(u.uid),
                             values=(u.name, u.level, u.stats[0]))
        if self.tree.get_children():
            self.tree.selection_set(self.tree.get_children()[0])
        self.on_select()

    def _current(self):
        sel = self.tree.selection()
        if not sel or not self.sv:
            return None
        self.uid = int(sel[0])
        recs = [r for r in self.sv.units if r.uid == self.uid]
        if not recs:
            return None
        return pick_live(recs)

    def _apply(self, fn):
        """Apply an edit to every copy of the selected unit in this file."""
        n = 0
        for u in self.sv.units:
            if u.uid == self.uid:
                fn(u)
                n += 1
        return n

    def on_select(self, _e=None):
        u = self._current()
        if not u:
            return
        self.name_lbl.configure(text=f"{u.name}   ({u.pid})")
        self._refresh_class_box(u)
        self.lvl_var.set(str(u.level))
        self.exp_var.set(str(u.exp))
        for i, v in enumerate(self.stat_vars):
            v.set(str(u.stats[i]))
        self.refresh_items(u)
        self.refresh_skills(u)
        copies = [r for r in self.sv.units if r.uid == u.uid]
        variants = {(r.level, r.exp, tuple(r.stats)) for r in copies}
        if len(copies) > 1:
            note = (f"{len(copies)} copies of this unit in the file"
                    if len(variants) == 1 else
                    f"{len(copies)} copies, and they DISAGREE — editing writes all of them")
            self.status.set(note)

    def sync_copies(self):
        u = self._current()
        if not u:
            return
        lv = self._num(self.lvl_var, 1, 99)
        ex = self._num(self.exp_var, 0, 255)
        stats = [self._num(v, 0, 255) for v in self.stat_vars]
        if None in (lv, ex) or None in stats:
            messagebox.showerror("Sync", "One of the fields is not a valid number.")
            return
        n = 0
        for r in self.sv.units:
            if r.uid != self.uid:
                continue
            r.set_level(lv, self.sv.payload)
            r.set_exp(ex, self.sv.payload)
            r.level, r.exp = lv, ex
            for i, v in enumerate(stats):
                r.set_stat(i, v, self.sv.payload)
                r.stats[i] = v
            n += 1
        self._edited(f"{u.name}: {n} copies synced to lv{lv}")
        self.refresh_tree()

    def _num(self, var, lo, hi):
        try:
            v = int(var.get())
        except (TypeError, ValueError):
            return None
        return v if lo <= v <= hi else None

    def _edited(self, msg):
        self.status.set(msg + f"  ·  {os.path.basename(self.sv.path)}  (not saved yet)")

    def apply_level(self):
        u = self._current()
        v = u and self._num(self.lvl_var, 1, 99)
        if not (u and v is not None):
            return
        n = self._apply(lambda r: r.set_level(v, self.sv.payload))
        self._edited(f"{u.name}: level → {v} ({n} copies)")
        self.refresh_tree()

    def apply_exp(self):
        u = self._current()
        v = u and self._num(self.exp_var, 0, 255)
        if not (u and v is not None):
            return
        n = self._apply(lambda r: r.set_exp(v, self.sv.payload))
        self._edited(f"{u.name}: EXP → {v} ({n} copies)")

    def apply_stat(self, i):
        u = self._current()
        v = u and self._num(self.stat_vars[i], 0, 255)
        if not (u and v is not None):
            return
        def write(r):
            r.set_stat(i, v, self.sv.payload)
            r.stats[i] = v
        n = self._apply(write)
        self._edited(f"{u.name}: {STAT_NAMES[i]} → {v} ({n} copies)")

    # ----------------------------------------------------------------- class
    def _job_names(self):
        """hash -> {"jp","en"} for every class the game data knows."""
        return job_ids()

    def _job_label(self, h):
        meta = self._job_names().get(h, {})
        en = meta.get("en") or "?"
        jp = (meta.get("jp") or "").replace("JID_", "")
        return f"{en}  [{jp}]" if jp else en

    def _refresh_class_box(self, u):
        jobs = self._job_names()
        show_all = self.show_bad_classes.get()
        rows = [(h, m) for h, m in jobs.items() if show_all or m.get("en")]
        rows.sort(key=lambda kv: ((kv[1].get("en") or "~"), kv[1].get("jp") or ""))
        self._job_choices = [h for h, _m in rows]
        self.class_box["values"] = [self._job_label(h) for h in self._job_choices]
        cur = u.job_hash
        if cur in self._job_choices:
            self.class_box.current(self._job_choices.index(cur))
        else:
            self.class_box.set(f"unknown class {cur:08x}")
        self.job_lbl.configure(text=f"now: {u.job}")

    def apply_class(self):
        if not (self.sv and self.uid is not None):
            return
        sel = self.class_box.current()
        if sel < 0 or sel >= len(getattr(self, "_job_choices", [])):
            return
        new_hash = self._job_choices[sel]
        u = self._current()
        if new_hash == u.job_hash:
            return
        name = job_name(new_hash)
        if not messagebox.askyesno(
                "Change class",
                f"Set {u.name}'s class to {name}?\n\n"
                "Only the class id is written: the game keeps movement, usable weapons, "
                "class skills and max HP derived from it, and those are not rewritten here. "
                "Keep the .bak and check the unit screen after reloading."):
            return
        n = self.sv.set_class(self.uid, new_hash)

        # the game loads whichever slot matches the active state, so write the
        # class into every sibling slot that holds this unit as well
        others = 0
        cur = os.path.abspath(self.sv.path) if self.sv.path else None
        for path in getattr(self, "_slot_paths", []) or []:
            if os.path.abspath(path) == cur:
                continue
            try:
                sv = SaveFile(path)
            except Exception:
                continue
            hit = sv.set_class(self.uid, new_hash)
            if hit:
                try:
                    sv.save(path)
                    others += 1
                except Exception:
                    pass
        self._edited(f"{u.name}: class -> {name} ({n} ids, {others} other slots)")
        self.on_select()

    # ---------------------------------------------------------------- skills
    def refresh_skills(self, u):
        for w in self.skill_frame.winfo_children():
            w.destroy()
        self.skill_rows = []
        tab = u.skills(bytes(self.sv.payload))
        if not tab:
            ttk.Label(self.skill_frame,
                      text="(no aptitude table found for this unit)").pack(anchor="w")
            return
        hdr = ttk.Frame(self.skill_frame)
        hdr.pack(fill="x", pady=(0, 2))
        ttk.Label(hdr, text="Skill", width=15).pack(side="left")
        ttk.Label(hdr, text="Exp", width=8).pack(side="left")
        ttk.Label(hdr, text="Grade", width=18).pack(side="left")
        ttk.Label(hdr, text="Set grade to").pack(side="left")
        for key in sorted(tab):
            _off, val = tab[key]
            cell = ttk.Frame(self.skill_frame)
            cell.pack(fill="x", pady=1)
            ttk.Label(cell, text=SKILL_NAMES.get(key, f"skill {key}"), width=15).pack(side="left")
            vvar = tk.StringVar(value=str(val))
            spin = ttk.Spinbox(cell, from_=0, to=9999, width=7, textvariable=vvar)
            spin.pack(side="left", padx=(0, 6))
            glbl = ttk.Label(cell, text=self._grade_text(val), width=18)
            glbl.pack(side="left")
            gvar = tk.StringVar(value=grade_label(val))
            box = ttk.Combobox(cell, textvariable=gvar, values=GRADES, width=5,
                               state="readonly")
            box.pack(side="left")
            for ev in ("<Return>", "<FocusOut>"):
                spin.bind(ev, lambda e, k=key, v=vvar, g=gvar, l=glbl: self.apply_skill_value(k, v, g, l))
            box.bind("<<ComboboxSelected>>",
                     lambda e, k=key, v=vvar, g=gvar, l=glbl: self.apply_skill_grade(k, v, g, l))
            self.skill_rows.append((key, vvar, gvar, glbl))

    @staticmethod
    def _grade_text(value):
        nxt = next_threshold(value)
        return grade_label(value) + (f"  (next {nxt})" if nxt is not None else "  (max)")

    def _write_skill(self, key, value):
        u = self._current()
        if not u:
            return 0
        cur = u.skills(bytes(self.sv.payload)).get(key)
        if cur and cur[1] == value:
            return 0
        n = 0
        for r in self.sv.units:
            if r.uid != self.uid:
                continue
            if r.set_skill(key, value, self.sv.payload):
                n += 1
        return n

    def apply_skill_value(self, key, vvar, gvar, glbl):
        if not (self.sv and self.uid is not None):
            return
        v = self._num(vvar, 0, 9999)
        if v is None:
            return
        n = self._write_skill(key, v)
        gvar.set(grade_label(v))
        glbl.configure(text=self._grade_text(v))
        u = self._current()
        self._edited(f"{u.name}: {SKILL_NAMES.get(key, 'skill ' + str(key))} exp -> {v} "
                     f"= {grade_label(v)} ({n} copies)")

    def apply_skill_grade(self, key, vvar, gvar, glbl):
        if not (self.sv and self.uid is not None):
            return
        name = (gvar.get() or "").strip()
        if name not in GRADES:
            return
        v = SKILL_THRESHOLDS[GRADES.index(name)]
        vvar.set(str(v))
        n = self._write_skill(key, v)
        glbl.configure(text=self._grade_text(v))
        u = self._current()
        self._edited(f"{u.name}: {SKILL_NAMES.get(key, 'skill ' + str(key))} -> {name} "
                     f"(exp {v}, {n} copies)")

    def apply_all_grades(self):
        if not (self.sv and self.uid is not None):
            return
        g = (self.all_grade.get() or "").strip()
        if g not in GRADES:
            return
        v = SKILL_THRESHOLDS[GRADES.index(g)]
        u = self._current()
        n = 0
        for key, vvar, gvar, glbl in self.skill_rows:
            gvar.set(g)
            vvar.set(str(v))
            glbl.configure(text=self._grade_text(v))
            n += self._write_skill(key, v)
        if u:
            self._edited(f"{u.name}: every listed skill -> {g} (exp {v}, {n} values)")

    def sync_skills_to_slots(self):
        """Copy the grades currently shown into the same unit in every other slot."""
        if not (self.sv and self.uid is not None and self.skill_rows):
            return
        u = self._current()
        wanted = {}
        for key, vvar, _gvar, _glbl in self.skill_rows:
            v = self._num(vvar, 0, 9999)
            if v is not None:
                wanted[key] = v
        if not wanted:
            return
        cur = os.path.abspath(self.sv.path)
        others = written = 0
        for path in getattr(self, "_slot_paths", []) or []:
            if os.path.abspath(path) == cur:
                continue
            try:
                sv = SaveFile(path)
            except Exception:
                continue
            hits = 0
            for r in sv.units:
                if r.uid != self.uid:
                    continue
                for k, v in wanted.items():
                    if r.set_skill(k, v, sv.payload):
                        hits += 1
            if hits:
                try:
                    sv.save(path)
                    written += 1
                except Exception:
                    continue
                others += hits
        self._edited(f"{u.name}: grades copied into {written} other slot(s) "
                     f"({others} values); this file still needs “Save file”")

    # ---------------------------------------------------------------- items
    # --------------------------------------------------------------- convoy
    def _convoy_primary(self):
        """The list the game is using: the last one in the payload."""
        if not self.sv:
            return []
        blocks = convoy_blocks(bytes(self.sv.payload))
        if not blocks:
            return []
        return [max(blocks, key=lambda b: b[0][0])]

    def refresh_convoy(self):
        self.conv_list.delete(0, "end")
        self._conv_rows = []
        if not self.sv:
            return
        blocks = self._convoy_primary()
        if not blocks:
            self.conv_list.insert("end", "  (no convoy list found in this slot)")
            return
        items = item_ids()
        for k, (off, qty, iid) in enumerate(blocks[0]):
            self._conv_rows.append(off)
            meta = items.get(iid, {})
            name = ((meta.get("en") or meta.get("jp")) if meta else f"unknown item {iid:08x}")
            self.conv_list.insert("end", f"{k:3d}  {name}" + (f"  x{qty}" if qty != 1 else ""))

    def filter_convoy_items(self):
        q = (self.conv_search.get() or "").strip().lower()
        self.conv_choices.delete(0, "end")
        self._conv_pick = []
        items = item_ids()
        hits = []
        for iid, meta in items.items():
            if not self.show_internal.get() and is_shadow(meta):
                continue
            blob = (meta["en"] + " " + meta["jp"]).lower()
            if not q or q in blob:
                hits.append((meta["en"], iid))
        hits.sort()
        for name, iid in hits:
            self._conv_pick.append(iid)
            self.conv_choices.insert("end", f"{name}   ({iid:08x})")
        if not hits:
            self.conv_choices.insert("end", "  (no match)")

    def _row_qty(self):
        try:
            return max(1, int(self.type_code.get().strip() or "1", 0))
        except ValueError:
            return 1

    def add_convoy(self):
        if not (self.sv and getattr(self, "_conv_pick", None)):
            return
        sel = self.conv_choices.curselection()
        if not sel:
            self.status.set("Pick an item to add first.")
            return
        iid = self._conv_pick[sel[0]]
        qty = self._row_qty()
        blocks = self._convoy_primary()
        n = add_convoy_item(self.sv.payload, iid, blocks, qty)
        others = self.sync_convoy_to_slots(
            lambda p: add_convoy_item(p, iid, [max(convoy_blocks(bytes(p)), key=lambda b: b[0][0])]
                                      if convoy_blocks(bytes(p)) else [], qty))
        name = item_ids().get(iid, {}).get("en") or hex(iid)
        if not n and not others:
            self.status.set(f"{name} is already in the convoy on every slot.")
        else:
            self._edited(f"added {name} x{qty} to convoy ({n} here, {others} other slots)")
        self.refresh_convoy()

    def replace_convoy(self):
        if not self.sv or not getattr(self, "_conv_rows", None):
            return
        row = self.conv_list.curselection()
        pick = self.conv_choices.curselection()
        if not row or not pick:
            self.status.set("Pick a convoy row and a replacement item first.")
            return
        iid = self._conv_pick[pick[0]]
        qty = self._row_qty()
        off = self._conv_rows[row[0]]
        set_convoy_row(self.sv.payload, off, iid, qty)

        def swap(payload):
            blocks = convoy_blocks(bytes(payload))
            if not blocks:
                return 0
            block = max(blocks, key=lambda b: b[0][0])
            if row[0] >= len(block):
                return 0
            set_convoy_row(payload, block[row[0]][0], iid, qty)
            return 1

        others = self.sync_convoy_to_slots(swap)
        name = item_ids().get(iid, {}).get("en") or hex(iid)
        self._edited(f"convoy row {row[0]} -> {name} x{qty} ({others} other slots)")
        self.refresh_convoy()

    def remove_convoy(self):
        if not self.sv or not getattr(self, "_conv_rows", None):
            return
        row = self.conv_list.curselection()
        if not row:
            self.status.set("Pick a convoy row to clear.")
            return
        off = self._conv_rows[row[0]]
        struct.pack_into("<H", self.sv.payload, off - 2, 0)
        self._edited(f"convoy row {row[0]} cleared (qty 0)")
        self.refresh_convoy()

    @staticmethod
    def _convoy_blocks_of(payload):
        return convoy_blocks(payload)

    def sync_convoy_to_slots(self, fn):
        done = 0
        cur = os.path.abspath(self.sv.path) if self.sv and self.sv.path else None
        for path in getattr(self, "_slot_paths", []) or []:
            if os.path.abspath(path) == cur:
                continue
            try:
                sv = SaveFile(path)
            except Exception:
                continue
            try:
                if fn(sv.payload):
                    sv.save(path)
                    done += 1
            except Exception:
                pass
        return done

    def refresh_items(self, u):
        self.item_list.delete(0, "end")
        self._slots = u.item_slots(bytes(self.sv.payload))
        names = item_ids()
        for off, iid in self._slots:
            meta = names.get(iid, {})
            label = f"{meta.get('en', hex(iid))}  ·  {meta.get('jp', '')}".strip(" ·")
            cat = item_category(meta) if meta else "?"
            self.item_list.insert("end", f"0x{off:06x}   [{cat}] {label}")
        self._all_items = sorted((v["en"], k, v["jp"]) for k, v in names.items())
        self.filter_items()

    def filter_items(self):
        q = self.item_search.get().strip().lower()
        self.item_choices.delete(0, "end")
        self._choices = []
        names = item_ids()
        allowed = None
        if not self.show_all.get():
            idx = getattr(self, "_chosen_slot", None)
            sel = self.item_list.curselection()
            if sel:
                idx = sel[0]
                self._chosen_slot = idx
            if idx is not None and idx < len(self._slots):
                _, iid = self._slots[idx]
                allowed = item_category(names.get(iid, {}))
        for name, iid, jp in self._all_items:
            if not self.show_internal.get() and is_shadow(names.get(iid, {})):
                continue
            if allowed and allowed != "misc" and item_category(names.get(iid, {})) != allowed:
                continue
            if q and q not in name.lower() and q not in jp:
                continue
            self._choices.append((name, iid))
            self.item_choices.insert("end", f"{name}   ({iid:08x})")

    def on_item_pick(self, _e=None):
        sel = self.item_list.curselection()
        if sel:
            self._chosen_slot = sel[0]
        self.filter_items()

    def replace_item(self):
        if not self.sv or self.uid is None:
            return
        slot = self.item_list.curselection()
        if not slot and getattr(self, "_chosen_slot", None) is not None:
            slot = (self._chosen_slot,)
        choice = self.item_choices.curselection()
        if not slot or not choice:
            messagebox.showinfo("Items", "Pick a slot and a replacement item first.")
            return
        off, old_id = self._slots[slot[0]]
        name, new_id = self._choices[choice[0]]
        u = self._current()
        delta = off - u.base
        n = 0
        import struct as _s
        for r in self.sv.units:
            if r.uid != self.uid:
                continue
            target = r.base + delta
            if not (0 <= target < len(self.sv.payload) - 4):
                continue
            _s.pack_into("<I", self.sv.payload, target, new_id)
            n += 1
        self._edited(f"{u.name}: slot {slot[0] + 1} -> {name} ({n} copies)")
        self.refresh_items(u)
        self.refresh_skills(u)

    # ---------------------------------------------------------------- money
    def locate_gold(self):
        sig = load_money_sig()
        if not sig or not self.sv:
            return
        off = locate_money(self.sv.payload, sig)
        if off is not None:
            self.money_off = off
            val = struct.unpack_from("<I", self.sv.payload, off)[0]
            self.gold_now.set(f"{val:,}")
            self.status.set(f"Gold located automatically: {val:,}")

    def find_gold(self):
        if not self.sv:
            return
        try:
            want = int(self.gold_search.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("Money", "Enter the gold amount as a number.")
            return
        if want == 0:
            messagebox.showinfo(
                "Money", "Gold is 0, so there is nothing to search for — every empty field "
                         "matches. Earn or spend a little gold first, then use the amount the "
                         "game shows.")
            return
        cands = find_money_candidates(bytes(self.sv.payload), want)
        self._gold_cands = cands
        self.gold_list.delete(0, "end")
        for i, off in enumerate(cands[:40]):
            ctx = bytes(self.sv.payload[max(0, off - 8):off + 8]).hex(" ")
            self.gold_list.insert("end", f"0x{off:06x}  …{ctx}…")
        self.status.set(f"{len(cands)} match(es) for {want:,} — pick the one that looks like "
                        f"a plain counter, then Set.")

    def on_gold_pick(self, _e=None):
        sel = self.gold_list.curselection()
        if not sel or not getattr(self, "_gold_cands", None):
            return
        off = self._gold_cands[sel[0]]
        self.money_off = off
        val = struct.unpack_from("<I", self.sv.payload, off)[0]
        self.gold_now.set(f"{val:,}")

    def set_gold(self):
        if not self.sv or self.money_off is None:
            messagebox.showinfo("Money", "Find the gold value first.")
            return
        try:
            val = int(self.gold_new.get().replace(",", ""))
        except ValueError:
            return
        sig = money_signature(bytes(self.sv.payload), self.money_off)
        struct.pack_into("<I", self.sv.payload, self.money_off, val & 0xFFFFFFFF)
        save_money_sig(sig)
        self.gold_now.set(f"{val:,}")
        self._edited(f"gold → {val:,} (spot remembered)")


if __name__ == "__main__":
    App().mainloop()
