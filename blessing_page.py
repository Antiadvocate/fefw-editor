"""Single-god EXP controls, using the editor's selected-slot undo history."""
from tkinter import ttk

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
            frame, columns=("exp", "level", "selected", "key"),
            show="tree headings", selectmode="browse", height=7)
        for col, title, width in (("#0", "God", 150), ("exp", "Stored EXP", 100),
                                  ("level", "Level preview", 160),
                                  ("selected", "Selected (stored)", 145),
                                  ("key", "Reads as", 235)):
            tree.heading(col, text=title, anchor="w")
            tree.column(col, width=width, stretch=col in ("#0", "key"))
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
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
        ttk.Label(page, style="CardFaint.TLabel", wraplength=980, justify="left", text=(
            "Edit one god at a time. Level previews use game-data thresholds; Photon is special. "
            "EXP alone does not grant an audience or unlock a temple. Selection and Divine Sand stay as stored.\n"
            "Turn off ‘Also edit this route’s other saves’. Apply EXP changes memory; "
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
        try:
            f = self.core_of()
            if f is None:
                self.blessing_summary.configure(text="Open a save to see its blessings.")
                return
            table = blessings.read(f)
            self._blessing_records = {r.hash: r for r in table.records}
            for god in blessings.GODS:
                record = self._blessing_records[god.hash]
                level = blessings.level_preview(god.hash, record.exp)
                selected = {0: "No (0)", 1: "Yes (1)"}.get(
                    record.selected, f"Unknown ({record.selected})")
                tree.insert("", "end", iid=f"{god.hash:016x}", text=god.name,
                            values=(record.exp, "Special / unknown" if level is None else level,
                                    selected, god.key))
            tree.selection_set([i for i in keep if tree.exists(i)])
            self.blessing_summary.configure(text=(
                f"All 7 gods · Divine Sand: {table.divine_sand:,} (read-only) · "
                "Level previews need confirmation in game."))
        except core.SaveError as exc:
            self.blessing_summary.configure(text=str(exc))
        finally:
            self._blessing_selected()

    def _blessing_selected(self, _event=None):
        selected = self.blessing_tree.selection()
        self.blessing_apply.state(["disabled"])
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
        self.blessing_exp.insert(0, str(record.exp))
        self.blessing_apply.state(["!disabled"])
        if god.thresholds:
            detail = "Threshold buttons fill New EXP; click Apply EXP to use that value."
            for i, (button, value) in enumerate(zip(self.blessing_presets, god.thresholds)):
                button.configure(text=f"Level {i + 1}: {value}")
                button.state(["!disabled"])
        else:
            detail = "Photon has zero-valued threshold fields; its EXP effect is unverified."
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
        if self.mirror.get():
            self.flash("Turn off ‘Also edit this route’s other saves’ for blessing edits.", "warn")
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
        if after == before.payload:
            self.flash("This blessing already has the requested EXP.", "info")
            return
        self.push_undo()
        self._core_edit(lambda f: blessings.edited(f, {h: value}),
                        f"{blessings.BY_HASH[h].name} EXP → {value}")
