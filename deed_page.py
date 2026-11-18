"""Single-counter Notable Deeds edits with normal save and undo controls."""
from tkinter import messagebox, ttk

import deeds
import fefw_core as core


class DeedPageMixin:
    def _build_deeds(self):
        page = self.deeds_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 10))
        top.pack(fill="x")
        ttk.Label(top, text="Notable Deeds", style="CardH3.TLabel").pack(anchor="w")
        self.deed_count = ttk.Label(top, style="CardMuted.TLabel")
        self.deed_count.pack(anchor="w", pady=(6, 0))
        self.deed_search = ttk.Entry(top)
        self.deed_search.pack(fill="x", pady=(8, 0))
        self.deed_search.bind("<KeyRelease>", lambda e: self.refresh_deeds())

        ttk.Label(page, style="CardFaint.TLabel", wraplength=980, justify="left", text=(
            "Edit one activity total; it feeds every milestone for that activity. Claim rewards in game. "
            "The game can clear claimed rewards if their progress falls below target. Unlisted milestones may have game conditions.\n"
            "Uses the same-route mirroring selection. Apply changes memory; Ctrl+S saves, Ctrl+Z undoes."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        form = ttk.Frame(page, style="Card.TFrame", padding=(14, 10))
        form.pack(side="bottom", fill="x", pady=(8, 0))
        self.deed_detail = ttk.Label(form, style="CardMuted.TLabel", wraplength=960, justify="left")
        self.deed_detail.pack(anchor="w")
        controls = ttk.Frame(form, style="Card.TFrame")
        controls.pack(fill="x", pady=(8, 0))
        ttk.Label(controls, text="New total", style="Card.TLabel").pack(side="left")
        self.deed_value = ttk.Entry(controls, width=14)
        self.deed_value.pack(side="left", padx=(8, 8))
        self.deed_apply = ttk.Button(controls, text="Apply progress", command=self.set_deed)
        self.deed_apply.pack(side="left")
        self.deed_target = ttk.Button(controls, text="Use selected target", command=self.fill_deed_target)
        self.deed_target.pack(side="left", padx=(8, 0))
        self.deed_value.bind("<Return>", lambda e: self.set_deed())

        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = self.deed_tree = ttk.Treeview(frame, columns=("progress", "reward", "claim", "access", "jp", "hash"),
                                           show="tree headings", selectmode="browse")
        for col, label, width in (("#0", "Activity · milestone target", 300), ("progress", "Progress", 170),
                                  ("reward", "Karma Shards", 105), ("claim", "Claim state (stored)", 200),
                                  ("access", "Counter editing", 125), ("jp", "Reads as · milestone key", 420),
                                  ("hash", "Milestone hash", 125)):
            tree.heading(col, text=label, anchor="w")
            tree.column(col, width=width, minwidth=width, stretch=col == "jp")
        vs = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        tree.bind("<<TreeviewSelect>>", self._deed_selected)
        self._deed_rows = {}
        self._deed_selected()

    def refresh_deeds(self):
        if not hasattr(self, "deed_tree"):
            return
        tree = self.deed_tree
        keep = tree.selection()
        view = tree.yview()
        tree.delete(*tree.get_children())
        self._deed_rows = {}
        try:
            cat = deeds.catalog()
            f = self.core_of()
            if f is None:
                self.deed_count.configure(text="Open a save to see its Notable Deeds.")
                self._deed_selected()
                return
            values = deeds.read(f)
        except core.SaveError as exc:
            self.deed_count.configure(text=str(exc))
            self._deed_selected()
            return
        q = self.deed_search.get().strip().casefold()
        claimed = unclaimed = total = 0
        for h, row in cat.items():
            value = values.get(h, 0)
            for tier in row["milestones"]:
                total += 1
                state = values.get(int(tier["hash"], 16))
                claimed += state == 4
                unclaimed += state == 2
                if q and q not in f"{row['label']} {row['category']} {row['name']} {h:08x} {tier['name']} {tier['hash']} {tier['target']}".casefold():
                    continue
                iid = tier["hash"]
                self._deed_rows[iid] = (h, tier)
                reached = " · reached" if value >= tier["target"] else ""
                progress = f"{min(value, tier['target']):,}/{tier['target']:,}{reached}"
                tree.insert("", "end", iid=iid, text=f"{row['label']} · {tier['target']:,}", values=(
                    progress, tier["reward"], deeds.claim_label(state),
                    deeds.editing_label(h, values), tier["name"], tier["hash"]))
        tree.selection_set([i for i in keep if tree.exists(i)])
        if view:
            tree.yview_moveto(view[0])
        editable = sum(not deeds.read_only_reason(h, values) for h in cat)
        inferred = sum(bool(row.get('inferred')) for row in cat.values())
        self.deed_count.configure(text=(f"{len(self._deed_rows)} of {total} milestones · {editable} of {len(cat)} counters editable · "
                                        f"{inferred} inferred · "
                                        f"{claimed} claimed · {unclaimed} complete, unclaimed (stored)"))
        self._deed_selected()

    def _deed_selected(self, _event=None):
        for widget in (self.deed_value, self.deed_apply, self.deed_target):
            widget.state(["disabled"])
        self.deed_detail.configure(text="Select a milestone to view its activity total. Rewards and claim states are read-only.")
        picked = self.deed_tree.selection()
        if len(picked) != 1 or picked[0] not in self._deed_rows:
            return
        h, tier = self._deed_rows[picked[0]]
        try:
            f = self.core_of()
            if f is None:
                return
            values = deeds.read(f)
            row = deeds.catalog()[h]
            reason = deeds.read_only_reason(h, values)
        except core.SaveError as exc:
            self.deed_detail.configure(text=str(exc))
            return
        value = values.get(h, 0)
        stored = f"{value:,}" if h in values else "0 (not stored)"
        note = reason or f"Allowed total: 0–{deeds.maximum(h, values):,}. Updates all {len(row['milestones'])} milestones' progress. The game may clear claims below target."
        if not reason and row.get('editing_note'):
            note = row['editing_note'] + '\n' + note
        self.deed_detail.configure(text=f"{row['label']} · current total: {stored}\n{row['name']} · {h:08x}\n{note}")
        self.deed_value.state(["!disabled"])
        self.deed_value.delete(0, "end")
        self.deed_value.insert(0, str(value))
        for widget in (self.deed_value, self.deed_apply, self.deed_target):
            widget.state(["disabled" if reason else "!disabled"])

    def fill_deed_target(self):
        picked = self.deed_tree.selection()
        if len(picked) == 1 and picked[0] in self._deed_rows and not self.deed_target.instate(["disabled"]):
            self.deed_value.delete(0, "end")
            self.deed_value.insert(0, str(self._deed_rows[picked[0]][1]["target"]))

    def _confirm_deed_unclaim(self, h, value, affected):
        targets = ", ".join(f"{tier['target']:,}" for tier in affected)
        return messagebox.askokcancel(
            "Previously claimed rewards",
            "You are about to unclaim some previously claimed rewards. Continue anyway?",
            detail=(f"{deeds.catalog()[h]['label']}: new total {value:,}.\n"
                    f"Affected claimed targets: {targets}.\n\n"
                    "The game can clear these claims when it loads the edited save. "
                    "The editor keeps the stored claim flags and Karma Shards unchanged."),
            icon="warning", default="cancel", parent=self)

    def set_deed(self):
        if not self.sv:
            return
        picked = self.deed_tree.selection()
        if len(picked) != 1 or picked[0] not in self._deed_rows:
            self.flash("Select one milestone first.", "info")
            return
        h, _tier = self._deed_rows[picked[0]]
        try:
            value = int(self.deed_value.get().strip())
        except ValueError:
            self.flash("Enter a whole-number activity total.", "error")
            return
        self._commit_form()
        try:
            before = self.core_of()
            after = deeds.edited(before, h, value)
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            return
        try:
            risks = {}
            for sv in self._targets():
                for tier in deeds.claims_at_risk(h, value, deeds.read(self.core_of(sv))):
                    risks[tier['target']] = tier
            affected = list(risks.values())
        except core.SaveError as exc:
            from os.path import basename
            self.flash(f'Nothing changed: {basename(sv.path)} — {exc}', 'error'); return
        if affected and not self._confirm_deed_unclaim(h, value, affected):
            self.flash("Progress edit cancelled; no deed changes applied.", "info")
            return
        self._core_edit(lambda f: deeds.edited(f, h, value), f"Set {deeds.catalog()[h]['label']} to {value:,}")
