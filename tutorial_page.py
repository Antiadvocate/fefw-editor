"""Tutorials page; conservative, single-slot edits with the existing undo stack."""
from tkinter import ttk

import tutorials
import fefw_core as core
from ui_util import enable_multi_select


class TutorialPageMixin:
    def _build_tutorials(self):
        page = self.tutorials_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        row = ttk.Frame(top, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Tutorials", style="CardH3.TLabel").pack(side="left")
        self.tutorial_count = ttk.Label(top, style="CardMuted.TLabel", wraplength=950)
        self.tutorial_count.pack(anchor="w", pady=(8, 0))
        self.tutorial_buttons = []
        for label, value in (("Remove selected", None), ("Make available", tutorials.AVAILABLE)):
            button = ttk.Button(row, text=label, style="Small.TButton",
                                command=lambda v=value: self.set_tutorials(v))
            button.pack(side="right", padx=(6, 0))
            self.tutorial_buttons.append(button)
        self.tutorial_search = ttk.Entry(top)
        self.tutorial_search.pack(fill="x", pady=(8, 0))
        self.tutorial_search.bind("<KeyRelease>", lambda e: self.refresh_tutorials())
        ttk.Label(page, style="CardFaint.TLabel", wraplength=980, justify="left", text=(
            "Search English, Japanese or hash. Make available adds the selected help entries; "
            "it does not unlock the features they describe. Unknown states are preserved. "
            "This page edits only the selected save: turn off ‘Also edit this route’s other saves’. "
            "Ctrl+Z undoes an edit; Ctrl+S writes it."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = self.tutorial_tree = ttk.Treeview(frame, columns=("jp", "state", "hash"),
                                                show="tree headings", selectmode="extended")
        for col, label, width in (("#0", "Name", 310), ("jp", "Reads as", 310),
                                  ("state", "State", 190), ("hash", "Hash", 95)):
            tree.heading(col, text=label, anchor="w")
            tree.column(col, width=width, stretch=col in ("#0", "jp"))
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        enable_multi_select(tree)

    def refresh_tutorials(self):
        if not hasattr(self, "tutorial_tree"):
            return
        tree = self.tutorial_tree
        keep = tree.selection()
        tree.delete(*tree.get_children())
        for button in self.tutorial_buttons:
            button.state(["disabled"])
        try:
            cat = tutorials.catalog()
            f = self.core_of()
            if f is None:
                self.tutorial_count.configure(text="Open a save to see its tutorials.")
                return
            values = tutorials.read(f)
        except core.SaveError as exc:
            self.tutorial_count.configure(text=str(exc))
            return
        q = self.tutorial_search.get().strip().casefold()
        for h, row in cat.items():
            if q and q not in f"{row['label']} {row['name']} {h:08x}".casefold():
                continue
            tree.insert("", "end", iid=f"{h:08x}", text=row["label"],
                        values=(row["name"], tutorials.state_label(values.get(h)), f"{h:08x}"))
        tree.selection_set([i for i in keep if tree.exists(i)])
        present = sum(h in values for h in cat)
        unknown = len(values.keys() - cat.keys())
        self.tutorial_count.configure(text=(
            f"{present} of {len(cat)} identified tutorials present · "
            f"{unknown} unlisted records preserved · catalogue is not exhaustive"))
        for button in self.tutorial_buttons:
            button.state(["!disabled"])

    def set_tutorials(self, value):
        if not self.sv:
            return
        # Upstream undo snapshots only the shown slot. Do not silently mirror
        # a multi-slot edit that Ctrl+Z cannot completely reverse.
        if self.mirror.get():
            self.flash("Turn off ‘Also edit this route’s other saves’ for tutorial edits.", "warn")
            return
        picked = self.tutorial_tree.selection()
        if not picked:
            self.flash("Select one or more tutorials first.", "info")
            return
        edits = {int(i, 16): value for i in picked}
        self._commit_form()
        try:
            before = self.core_of()
            after = tutorials.edited(before, edits)
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            return
        if after == before.payload:
            self.flash("Selected tutorials already have the requested state.", "info")
            return
        self.push_undo()
        what = f"{'Removed' if value is None else 'Made available'} {len(edits)} tutorial(s)"
        self._core_edit(lambda f: tutorials.edited(f, edits), what)
