"""Single-god EXP and first-audience controls with selected-slot undo."""
import tkinter as tk
from tkinter import ttk

import audiences
import blessings
import fefw_core as core


class BlessingPageMixin:
    def _build_blessings(self):
        page = self.blessings_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        ttk.Label(top, text="Blessings", style="CardH3.TLabel").pack(anchor="w")
        self.blessing_summary = ttk.Label(top, style="CardMuted.TLabel", wraplength=950)
        self.blessing_summary.pack(anchor="w", pady=(6, 0))

        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = self.blessing_tree = ttk.Treeview(
            frame, columns=("exp", "level", "selected", "audience", "key"),
            show="tree headings", selectmode="browse", height=7)
        for col, title, width in (("#0", "God", 125), ("exp", "Stored EXP", 90),
                                  ("level", "Level preview", 140),
                                  ("selected", "Selected (stored)", 125),
                                  ("audience", "First audience", 175),
                                  ("key", "Reads as", 235)):
            tree.heading(col, text=title, anchor="w")
            tree.column(col, width=width, minwidth=width, stretch=col == "key")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sb.set, xscrollcommand=hs.set)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        tree.bind("<<TreeviewSelect>>", self._blessing_selected)

        form = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        form.pack(fill="x", pady=(8, 0))
        self.blessing_detail = ttk.Label(form, style="CardMuted.TLabel", wraplength=950)
        self.blessing_detail.pack(anchor="w")
        row = ttk.Frame(form, style="Card.TFrame")
        row.pack(fill="x", pady=(8, 0))
        ttk.Label(row, text="New EXP", style="Card.TLabel").pack(side="left")
        self.blessing_exp = ttk.Entry(row, width=12)
        self.blessing_exp.pack(side="left", padx=(8, 8))
        self.blessing_apply = ttk.Button(row, text="Apply EXP", style="Small.TButton",
                                         command=self.apply_blessing_exp)
        self.blessing_apply.pack(side="left", padx=(0, 14))
        self.blessing_presets = []
        for level in range(3):
            button = ttk.Button(row, text=f"Level {level + 1} EXP", style="Small.TButton",
                                command=lambda i=level: self._blessing_preset(i))
            button.pack(side="left", padx=(0, 6))
            self.blessing_presets.append(button)
        audience_row = ttk.Frame(form, style="Card.TFrame")
        audience_row.pack(fill="x", pady=(12, 0))
        self.blessing_audience = tk.BooleanVar(value=False)
        self.blessing_audience_toggle = ttk.Checkbutton(
            audience_row, text="First audience recorded",
            variable=self.blessing_audience, command=self.toggle_blessing_audience)
        self.blessing_audience_toggle.pack(anchor="w")
        self.blessing_audience_detail = ttk.Label(
            audience_row, style="CardMuted.TLabel", wraplength=950, justify="left")
        self.blessing_audience_detail.pack(anchor="w", pady=(5, 0))
        ttk.Label(page, style="CardFaint.TLabel", wraplength=980, justify="left", text=(
            "Edit one god at a time. Level previews use game-data thresholds; Fortuna is special. "
            "The audience toggle changes only the first-talk flag; other access conditions may still apply. "
            "Audience edits leave EXP, selected blessings, Divine Sand and travel destinations unchanged.\n"
            "Uses the same-route mirroring selection. Apply EXP and the toggle change memory; "
            "Ctrl+S saves, Ctrl+Z undoes, Ctrl+Y redoes."
        )).pack(anchor="w", pady=(8, 0))
        self._blessing_selected()

    def refresh_blessings(self):
        if not hasattr(self, "blessing_tree"):
            return
        tree = self.blessing_tree
        keep = tree.selection()
        tree.delete(*tree.get_children())
        self._blessing_records = {}
        self._audience_values = None
        self._audience_error = "Open a save first."
        try:
            f = self.core_of()
            if f is None:
                self.blessing_summary.configure(text="Open a save to see its blessings.")
                return
            table = blessings.read(f)
            self._blessing_records = {r.hash: r for r in table.records}
            try:
                self._audience_values = audiences.read(f)
            except core.SaveError as exc:
                self._audience_error = str(exc)
            for god in blessings.GODS:
                record = self._blessing_records[god.hash]
                level = blessings.level_preview(god.hash, record.exp)
                selected = {0: "No (0)", 1: "Yes (1)"}.get(
                    record.selected, f"Unknown ({record.selected})")
                tree.insert("", "end", iid=f"{god.hash:016x}", text=god.name,
                            values=(record.exp, "Special / unknown" if level is None else level,
                                    selected,
                                    audiences.state_label(god.hash, self._audience_values or {})
                                    if self._audience_values is not None or god.hash not in audiences.KEYS
                                    else "Unavailable",
                                    god.key))
            tree.selection_set([i for i in keep if tree.exists(i)])
            self.blessing_summary.configure(text=(
                f"All 7 gods · Divine Sand: {table.divine_sand:,} (read-only) · "
                "First audience: tested at Leda Chapter 9 · Fortuna: not required."))
        except core.SaveError as exc:
            self.blessing_summary.configure(text=str(exc))
        finally:
            self._blessing_selected()

    def _blessing_selected(self, _event=None):
        selected = self.blessing_tree.selection()
        self.blessing_apply.state(["disabled"])
        self.blessing_audience_toggle.state(["disabled"])
        self.blessing_audience.set(False)
        self.blessing_audience_detail.configure(text="Select a god to inspect its first-audience condition.")
        self.blessing_exp.state(["!disabled"])
        self.blessing_exp.delete(0, "end")
        for i, button in enumerate(self.blessing_presets):
            button.configure(text=f"Level {i + 1} EXP")
            button.state(["disabled"])
        records = getattr(self, "_blessing_records", {})
        if len(selected) != 1 or int(selected[0], 16) not in records:
            self.blessing_detail.configure(text="Select a god to edit its stored EXP.")
            self.blessing_exp.state(["disabled"])
            return
        h = int(selected[0], 16)
        god, record = blessings.BY_HASH[h], records[h]
        values = getattr(self, "_audience_values", None)
        if h not in audiences.KEYS:
            audience_detail = "Fortuna has no first-audience condition in the game data; no flag is written."
        elif values is None:
            audience_detail = getattr(self, "_audience_error", "Audience data is unavailable.")
        else:
            value = values.get(audiences.HASHES[h])
            self.blessing_audience.set(value == 1)
            if value in (None, 1):
                self.blessing_audience_toggle.state(["!disabled"])
            audience_detail = (f"{audiences.state_label(h, values)} · Reads as: {audiences.KEYS[h]} "
                               f"· {audiences.HASHES[h]:08x}\n"
                               "On records the first audience; off removes that record. Save to write the change.")
        self.blessing_audience_detail.configure(text=audience_detail)
        self.blessing_exp.insert(0, str(record.exp))
        self.blessing_apply.state(["!disabled"])
        if god.thresholds:
            detail = "Threshold buttons fill New EXP; click Apply EXP to use that value."
            for i, (button, value) in enumerate(zip(self.blessing_presets, god.thresholds)):
                button.configure(text=f"Level {i + 1}: {value}")
                button.state(["!disabled"])
        else:
            detail = "EXP effect unknown; no Blessings-screen change reported at EXP 1 or 65535."
        self.blessing_detail.configure(text=f"{god.name} · EXP range 0–65535. {detail}")

    def _blessing_preset(self, index):
        selected = self.blessing_tree.selection()
        if len(selected) != 1:
            return
        god = blessings.BY_HASH.get(int(selected[0], 16))
        if god and god.thresholds:
            self.blessing_exp.delete(0, "end")
            self.blessing_exp.insert(0, str(god.thresholds[index]))

    def apply_blessing_exp(self):
        if not self.sv:
            return
        selected = self.blessing_tree.selection()
        if len(selected) != 1:
            self.flash("Select one god first.", "info")
            return
        try:
            raw = self.blessing_exp.get().strip()
            if not raw.isascii() or not raw.isdecimal():
                raise ValueError
            value = int(raw)
            h = int(selected[0], 16)
        except ValueError:
            self.flash("EXP must be a whole number from 0 to 65535.", "error")
            return
        self._commit_form()
        try:
            before = self.core_of()
            after = blessings.edited(before, {h: value})
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            return
        self._core_edit(lambda f: blessings.edited(f, {h: value}),
                        f"{blessings.BY_HASH[h].name} EXP → {value}")

    def toggle_blessing_audience(self):
        """Checkbox applies immediately in memory, like other page actions."""
        if not self.sv:
            self._blessing_selected()
            return
        selected = self.blessing_tree.selection()
        if len(selected) != 1:
            self.flash("Select one god first.", "info")
            self._blessing_selected()
            return
        h = int(selected[0], 16)
        value = 1 if self.blessing_audience.get() else None
        self._commit_form()
        try:
            before = self.core_of()
            after = audiences.edited(before, {h: value})
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            self._blessing_selected()
            return
        self._core_edit(lambda f: audiences.edited(f, {h: value}),
                        f"{blessings.BY_HASH[h].name} first audience → {'recorded' if value else 'not recorded'}")
