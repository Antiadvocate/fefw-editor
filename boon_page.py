"""Selected-save Boon tier and activation controls."""
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
            "Tier edits preserve Karma and progression. Set all to max preserves each On/Off switch.\n"
            "Uses the same-route mirroring selection. Ctrl+S saves, Ctrl+Z undoes, Ctrl+Y redoes."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        form = ttk.Frame(page, style="Card.TFrame", padding=(14, 10))
        form.pack(side="bottom", fill="x", pady=(8, 0))
        self.boon_detail = ttk.Label(form, style="CardMuted.TLabel", wraplength=880, justify="left")
        self.boon_detail.pack(anchor="w")
        actions = ttk.Frame(form, style="Card.TFrame")
        actions.pack(fill="x", pady=(8, 0))
        buttons = (
            ('boon_set', 'Set selected tier', self.set_boon_tier),
            ('boon_remove', 'Remove Boon', lambda: self.set_boon_tier(remove=True)),
            ('boon_on', 'Turn on', lambda: self.set_boon_active(True)),
            ('boon_off', 'Turn off', lambda: self.set_boon_active(False)),
            ('boon_max', 'Set all to max', self.max_boons),
        )
        for name, label, action in buttons:
            button = ttk.Button(actions, text=label, style="Small.TButton", command=action, state="disabled")
            button.pack(side="left", padx=(0, 8))
            setattr(self, name, button)
        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = self.boon_tree = ttk.Treeview(frame,
            columns=("tier", "state", "value", "evidence", "cost", "clears", "jp"),
            show="tree headings", selectmode="browse")
        for col, label, width in (("#0", "Effect", 240), ("tier", "Tier", 45),
                ("state", "Saved state", 145), ("value", "Value", 65),
                ("evidence", "Evidence", 105), ("cost", "Game cost", 85),
                ("clears", "Required clears", 115), ("jp", "Reads as", 230)):
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
        self._boon_state = None
        self._boon_error = "Open a save first."
        self._select_boon()

    def refresh_boons(self):
        if not hasattr(self, "boon_tree"):
            return
        tree = self.boon_tree
        keep = tree.selection()
        tree.delete(*tree.get_children())
        self._boon_rows = {}
        self._boon_state = None
        self._boon_error = "Open a save first."
        self.boon_observation.configure(text="Open a save to inspect its Boons.")
        self._select_boon()
        try:
            groups = boons.catalog()
            rows = boons.matching_rows(self.boon_search.get())
        except core.SaveError as exc:
            self.boon_count.configure(text=str(exc))
            return
        summary = f"{len(rows)} of {sum(len(g['tiers']) for g in groups)} tiers · {len(groups)} Boons"
        try:
            f = self.core_of()
            if f is not None:
                self._boon_state = state = boons.read_state(f)
                summary += f" · Karma Shards: {state['karma_shards']:,}"
                owned = sum(not boons.group_edit_reason(g, state['groups'][g['name']])
                            and (state['groups'][g['name']]['level'] or 0) > 0 for g in groups)
                self.boon_observation.configure(text=(
                    f"{owned} of {len(groups)} owned · Game-tested: EXP tier 1; Weapons Discount tiers 1–2. "
                    "Save-verified: Brawling and Black-Magic tier 1. Other tiers remain inferred."))
        except core.SaveError as exc:
            self._boon_error = str(exc)
            self.boon_observation.configure(text=str(exc))
        for iid, group, tier in rows:
            self._boon_rows[iid] = (group, tier)
            saved = boons.row_state(group, tier, self._boon_state['groups'][group['name']]) if self._boon_state else 'Unavailable'
            evidence = boons.evidence_label(group['name'], tier['tier'])
            tree.insert("", "end", iid=iid, text=boons.display_name(group), values=(
                tier['tier'], saved, tier['value'], evidence, tier['cost'], tier['clear_count'], group['name']))
        self.boon_count.configure(text=summary)
        tree.selection_set([i for i in keep if tree.exists(i)])
        self._select_boon()

    def _selected_boon(self):
        selected = self.boon_tree.selection()
        return self._boon_rows.get(selected[0]) if len(selected) == 1 else None

    def _select_boon(self):
        for button in (self.boon_set, self.boon_remove, self.boon_on, self.boon_off, self.boon_max):
            button.configure(state="disabled")
        if self._boon_state:
            states = self._boon_state['groups']
            valid = all(not boons.group_edit_reason(g, states[g['name']]) for g in boons.catalog())
            already_max = all(states[g['name']]['level'] == len(g['tiers']) for g in boons.catalog())
            if valid and not already_max:
                self.boon_max.configure(state="normal")
        row = self._selected_boon()
        if not row:
            self.boon_detail.configure(text="Select a tier, then Set selected tier. Each Boon has one owned tier and an independent On/Off switch.\n"
                "Set all to max affects all 31 Boons, including rows hidden by search. Undo restores the whole edit.")
            return
        group, tier = row
        state = self._boon_state['groups'][group['name']] if self._boon_state else None
        reason = boons.group_edit_reason(group, state) if state else self._boon_error
        if reason:
            note = 'Read-only: ' + reason
        else:
            level = state['level'] or 0
            self.boon_set.configure(state='normal' if level != tier['tier'] else 'disabled')
            self.boon_remove.configure(state='normal' if level else 'disabled')
            if level == tier['tier']:
                self.boon_on.configure(state='normal' if state['disabled'] == 1 else 'disabled')
                self.boon_off.configure(state='normal' if state['disabled'] is None else 'disabled')
            note = (f"Owned tier: {level} of {len(group['tiers'])}. Tier edits keep the current On/Off switch. "
                    "Select the owned tier to use Turn on/off.")
        self.boon_detail.configure(text=(
            f"{boons.display_name(group)} · selected tier {tier['tier']} · value {tier['value']}\n"
            f"Normal purchase: {tier['cost']} Karma, {tier['clear_count']} required clears (game data). "
            "Editing does not spend Karma or change clears.\n" + note))

    def _change_boons(self, edit, label):
        if not self.sv:
            self._select_boon()
            return
        self._commit_form()
        try:
            before = self.core_of()
            after = edit(before)
        except core.SaveError as exc:
            self.flash(str(exc), "error")
            self.refresh_boons()
            return
        self._core_edit(edit, label)

    def set_boon_tier(self, remove=False):
        row = self._selected_boon()
        if not row:
            self.flash('Select a Boon tier first.', 'info')
            return
        group, tier = row
        level = 0 if remove else tier['tier']
        self._change_boons(lambda f: boons.edited_groups(f, levels={group['name']: level}),
                           f"{boons.display_name(group)} → {'Not owned' if remove else 'tier ' + str(level)}")

    def max_boons(self):
        self._change_boons(lambda f: boons.edited_groups(f, levels=boons.max_levels()),
                           'All 31 Boons → maximum tiers (On/Off preserved)')

    def set_boon_active(self, active):
        row = self._selected_boon()
        if not row:
            self.flash('Select the owned Boon tier first.', 'info')
            return
        group, tier = row
        def edit(f):
            state = boons.read_state(f)['groups'][group['name']]
            if state['level'] != tier['tier']:
                raise boons.BoonError('Select the currently owned tier to switch this Boon On or Off.')
            return boons.edited_groups(f, active={group['name']: active})
        self._change_boons(edit, f"{boons.display_name(group)} → {'On' if active else 'Off'}")
