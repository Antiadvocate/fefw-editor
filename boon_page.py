"""Single-save EXP activation control and the wider read-only Boon catalogue."""
from tkinter import ttk

import boons
import fefw_core as core


class BoonPageMixin:
    def _build_boons(self):
        page = self.boons_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        ttk.Label(top, text="Boons of Salvation", style="CardH3.TLabel").pack(anchor="w")
        self.boon_count = ttk.Label(top, style="CardMuted.TLabel", wraplength=900)
        self.boon_count.pack(anchor="w", pady=(6, 0))
        self.boon_observation = ttk.Label(top, style="CardMuted.TLabel", wraplength=900)
        self.boon_observation.pack(anchor="w", pady=(4, 0))
        self.boon_search = ttk.Entry(top)
        self.boon_search.pack(fill="x", pady=(8, 0))
        self.boon_search.bind("<KeyRelease>", lambda e: self.refresh_boons())

        ttk.Label(page, style="CardFaint.TLabel", justify="left", wraplength=900, text=(
            "The already-owned EXP +10% Boon can be switched on/off. "
            "Purchases, tiers and other Boons remain read-only.\n"
            "Turn off ‘Also edit this route’s other saves’. Ctrl+S saves, Ctrl+Z undoes, Ctrl+Y redoes."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        form = ttk.Frame(page, style="Card.TFrame", padding=(14, 10))
        form.pack(side="bottom", fill="x", pady=(8, 0))
        self.boon_detail = ttk.Label(form, style="CardMuted.TLabel", wraplength=880, justify="left")
        self.boon_detail.pack(anchor="w")
        actions = ttk.Frame(form, style="Card.TFrame")
        actions.pack(fill="x", pady=(8, 0))
        self.boon_on = ttk.Button(actions, text="Turn on", style="Small.TButton",
                                  command=lambda: self.set_boon_active(True), state="disabled")
        self.boon_on.pack(side="left", padx=(0, 8))
        self.boon_off = ttk.Button(actions, text="Turn off", style="Small.TButton",
                                   command=lambda: self.set_boon_active(False), state="disabled")
        self.boon_off.pack(side="left")
        ttk.Label(actions, text="Existing EXP +10% only · Save to write changes",
                  style="CardMuted.TLabel").pack(side="left", padx=(14, 0))

        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = self.boon_tree = ttk.Treeview(frame, columns=("tier", "state", "value", "cost", "clears", "jp"),
                                             show="tree headings", selectmode="browse")
        for col, label, width in (("#0", "Effect", 260), ("tier", "Tier", 50),
                                  ("state", "Saved state", 170), ("value", "Value (data)", 90),
                                  ("cost", "Listed cost", 95), ("clears", "Clear count (data)", 135),
                                  ("jp", "Reads as", 230)):
            tree.heading(col, text=label, anchor="w")
            tree.column(col, width=width, minwidth=width, stretch=col in ("#0", "jp"))
        tree.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree.bind("<<TreeviewSelect>>", lambda e: self._select_boon())
        self._boon_rows = {}
        self._boon_observed = None
        self._boon_error = "Open a save first."
        self._select_boon()

    def refresh_boons(self):
        if not hasattr(self, "boon_tree"):
            return
        tree = self.boon_tree
        keep = tree.selection()
        tree.delete(*tree.get_children())
        self._boon_rows = {}
        self._boon_observed = None
        self._boon_error = "Open a save first."
        self.boon_observation.configure(text="Open a save to inspect its Boons.")
        self._select_boon()
        try:
            groups = boons.catalog()
            rows = boons.matching_rows(self.boon_search.get())
        except core.SaveError as exc:
            self.boon_count.configure(text=str(exc))
            return
        summary = f"{len(rows)} of {sum(len(g['tiers']) for g in groups)} reference tiers · {len(groups)} groups"
        try:
            f = self.core_of()
            if f is not None:
                self._boon_observed = observation = boons.read_observation(f)
                summary += f" · Karma Shards: {observation['karma_shards']:,}"
                reason = boons.exp_edit_reason(observation)
                self.boon_observation.configure(text=(
                    "Increased Exp 10%: " + boons.exp_state_label(observation)
                    + (f" · {reason}" if reason else "")))
        except core.SaveError as exc:
            self._boon_error = str(exc)
            self.boon_observation.configure(text=str(exc))
        for iid, group, tier in rows:
            self._boon_rows[iid] = (group, tier)
            state = "Not mapped"
            if group['name'] == '経験値' and tier['tier'] == 1:
                state = boons.exp_state_label(self._boon_observed) if self._boon_observed else "Unavailable"
            elif group['name'] == '武器割引' and tier['tier'] == 1 and self._boon_observed:
                value = self._boon_observed['weapons_purchase']
                state = "Purchase recorded" if value == 1 else "Not recorded" if value is None else f"Unknown ({value})"
            tree.insert("", "end", iid=iid, text=boons.display_name(group), values=(
                tier['tier'], state, tier['value'], tier['cost'], tier['clear_count'], group['name']))
        self.boon_count.configure(text=summary)
        tree.selection_set([i for i in keep if tree.exists(i)])
        self._select_boon()

    def _select_boon(self):
        self.boon_on.configure(state="disabled")
        self.boon_off.configure(state="disabled")
        picked = self.boon_tree.selection()
        if len(picked) != 1 or picked[0] not in self._boon_rows:
            self.boon_detail.configure(text="Select Increased Exp, tier 1, to switch an existing +10% Boon on/off.\n"
                                            "Other rows show reference values; they do not indicate a current bonus.")
            return
        group, tier = self._boon_rows[picked[0]]
        note = "Read-only: ownership, activation and stacking are not mapped for this tier."
        if group['name'] == '経験値' and tier['tier'] == 1:
            observation = self._boon_observed
            reason = boons.exp_edit_reason(observation) if observation else self._boon_error
            if reason:
                note = "Read-only: " + reason
            else:
                state = boons.exp_state_label(observation)
                note = f"Existing +10% Boon: {state}. Switching preserves ownership and Karma Shards."
                self.boon_on.configure(state="normal" if state == "Off" else "disabled")
                self.boon_off.configure(state="normal" if state == "On" else "disabled")
        elif group['name'] == '武器割引' and tier['tier'] == 1:
            note = "Read-only: purchase and off/on captures recorded; shop-price effect unverified and editor control unavailable."
        self.boon_detail.configure(text=(
            f"{boons.display_name(group)} · tier {tier['tier']} · {group['name']}\n"
            f"Reference value: {tier['value']}; listed cost: {tier['cost']} Karma Shards; "
            f"clear-count field: {tier['clear_count']}. These are catalogue data.\n" + note))

    def set_boon_active(self, active):
        if not self.sv:
            self._select_boon()
            return
        if self.mirror.get():
            self.flash("Turn off ‘Also edit this route’s other saves’ for Boon edits.", "warn")
            self._select_boon()
            return
        selected = self.boon_tree.selection()
        row = self._boon_rows.get(selected[0]) if len(selected) == 1 else None
        if not row or row[0]['name'] != '経験値' or row[1]['tier'] != 1:
            self.flash("Select Increased Exp, tier 1; other Boons are read-only.", "info")
            self._select_boon()
            return
        self._commit_form()
        try:
            before = self.core_of()
            after = boons.edited_exp_active(before, active)
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            self.refresh_boons()
            return
        if after == before.payload:
            self.flash("This Boon already has the requested state.", "info")
            self.refresh_boons()
            return
        self.push_undo()
        self._core_edit(lambda f: boons.edited_exp_active(f, active),
                        f"Increased Exp 10% → {'On' if active else 'Off'}")
