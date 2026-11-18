"""Single-save fast-travel edits with the editor's normal undo/save controls."""
from tkinter import ttk

import fast_travel
import fefw_core as core


class FastTravelPageMixin:
    def _build_fast_travel(self):
        page = self.fast_travel_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        row = ttk.Frame(top, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Fast travel · Dagsion", style="CardH3.TLabel").pack(side="left")
        self.fast_travel_buttons = []
        for label, value in (("Remove selected", None), ("Make available", fast_travel.AVAILABLE)):
            button = ttk.Button(row, text=label, style="Small.TButton",
                                command=lambda v=value: self.set_fast_travel(v))
            button.pack(side="right", padx=(6, 0))
            self.fast_travel_buttons.append(button)
        self.fast_travel_count = ttk.Label(top, style="CardMuted.TLabel", wraplength=950)
        self.fast_travel_count.pack(anchor="w", pady=(8, 0))
        self.fast_travel_search = ttk.Entry(top)
        self.fast_travel_search.pack(fill="x", pady=(8, 0))
        self.fast_travel_search.bind("<KeyRelease>", lambda e: self.refresh_fast_travel())
        ttk.Label(page, style="CardFaint.TLabel", wraplength=980, justify="left", text=(
            "Aurora’s room/garden require Cai for their travel locators; Salamis Guesthouse requires Theodora. Yu Phas travel/exit passed on Leda Chapter 9; its entrance remains restricted. See Facilities > Access conditions. "
            "Search by name, Japanese key or hash. "
            "Edits update destination lists in the selected save and enabled mirror targets. Travel still depends on game conditions; "
            "the Stables destination does not unlock the stable facility. Keep at least three original destinations.\n"
            "Uses the same-route mirroring selection. Ctrl+Z undoes; Ctrl+S saves."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = self.fast_travel_tree = ttk.Treeview(frame, columns=("state", "evidence", "jp", "hash"),
                                                   show="tree headings", selectmode="extended")
        for col, label, width in (("#0", "Destination", 220), ("state", "State", 175),
                                  ("evidence", "Coverage", 150),
                                  ("jp", "Reads as", 570), ("hash", "Hash", 95)):
            tree.heading(col, text=label, anchor="w")
            tree.column(col, width=width, minwidth=width, stretch=col == "jp")
        vs = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")

    def refresh_fast_travel(self):
        if not hasattr(self, "fast_travel_tree"):
            return
        tree = self.fast_travel_tree
        keep = tree.selection()
        tree.delete(*tree.get_children())
        for button in self.fast_travel_buttons:
            button.state(["disabled"])
        try:
            cat = fast_travel.catalog()
            f = self.core_of()
            if f is None:
                self.fast_travel_count.configure(text="Open a save to see its destinations.")
                return
            values = fast_travel.read(f)
        except core.SaveError as exc:
            self.fast_travel_count.configure(text=str(exc))
            return
        q = self.fast_travel_search.get().strip().casefold()
        for h, row in cat.items():
            if q and q not in f"{row['label']} {row['name']} {h:08x}".casefold():
                continue
            tree.insert("", "end", iid=f"{h:08x}", text=row["label"], values=(
                fast_travel.state_label(values.get(h)),
                row["coverage"],
                row["name"], f"{h:08x}"))
        tree.selection_set([i for i in keep if tree.exists(i)])
        available = sum(values.get(h) == fast_travel.AVAILABLE for h in cat)
        unlisted = len(values.keys() - cat.keys())
        self.fast_travel_count.configure(text=(
            f"{available} of {len(cat)} known destinations available · "
            f"{sum(row['coverage'] == 'Effect unknown' for row in cat.values())} effects unknown · "
            f"{unlisted} other list records preserved"))
        for button in self.fast_travel_buttons:
            button.state(["!disabled"])

    def set_fast_travel(self, value):
        if not self.sv:
            return
        picked = self.fast_travel_tree.selection()
        if not picked:
            self.flash("Select one or more destinations first.", "info")
            return
        edits = {int(i, 16): value for i in picked}
        self._commit_form()
        try:
            before = self.core_of()
            after = fast_travel.edited(before, edits)
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            return
        what = f"{'Removed' if value is None else 'Made available'} {len(edits)} destination(s)"
        self._core_edit(lambda f: fast_travel.edited(f, edits), what)
