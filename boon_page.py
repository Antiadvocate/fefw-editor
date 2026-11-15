"""Read-only catalogue and evidence display while Boon save fields are mapped."""
from tkinter import ttk

import boons
import fefw_core as core


class BoonPageMixin:
    def _build_boons(self):
        page = self.boons_page
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        ttk.Label(top, text="Boons of Salvation · reference catalogue", style="CardH3.TLabel").pack(anchor="w")
        self.boon_count = ttk.Label(top, style="CardMuted.TLabel", wraplength=950)
        self.boon_count.pack(anchor="w", pady=(8, 0))
        self.boon_observation = ttk.Label(top, style="CardMuted.TLabel", wraplength=950)
        self.boon_observation.pack(anchor="w", pady=(4, 0))
        self.boon_search = ttk.Entry(top)
        self.boon_search.pack(fill="x", pady=(8, 0))
        self.boon_search.bind("<KeyRelease>", lambda e: self.refresh_boons())
        ttk.Label(page, style="CardFaint.TLabel", justify="left", wraplength=950, text=(
            "Read-only research build. English names describe the data; purchase and activation are not decoded.\n"
            "Listed value and clear count are reference fields, not your current bonus or completed runs. "
            "Search English/Japanese with Ctrl+F. Follow docs/testing-boons.md for the controlled save captures."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        self.boon_detail = ttk.Label(page, style="CardMuted.TLabel", wraplength=950, justify="left",
                                     padding=(14, 10), text="Select a reference tier for its evidence limits.")
        self.boon_detail.pack(side="bottom", fill="x", pady=(8, 0))
        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = self.boon_tree = ttk.Treeview(frame, columns=("tier", "value", "cost", "clears", "jp"),
                                             show="tree headings", selectmode="browse")
        for col, label, width in (("#0", "Effect (descriptive)", 320), ("tier", "Tier", 55),
                                  ("value", "Value (data)", 90), ("cost", "Listed cost", 95),
                                  ("clears", "Clear count (data)", 135), ("jp", "Reads as", 230)):
            tree.heading(col, text=label, anchor="w")
            tree.column(col, width=width, stretch=col in ("#0", "jp"))
        tree.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree.bind("<<TreeviewSelect>>", lambda e: self._select_boon())

    def refresh_boons(self):
        if not hasattr(self, "boon_tree"):
            return
        tree = self.boon_tree
        keep = tree.selection()
        tree.delete(*tree.get_children())
        self._boon_rows = {}
        self.boon_detail.configure(text="Select a reference tier for its evidence limits.")
        self.boon_observation.configure(text="Open a save to inspect the EXP-associated reference record.")
        try:
            groups = boons.catalog()
            rows = boons.matching_rows(self.boon_search.get())
        except core.SaveError as exc:
            self.boon_count.configure(text=str(exc))
            return
        for iid, group, tier in rows:
            self._boon_rows[iid] = (group, tier)
            tree.insert("", "end", iid=iid, text=group["label"], values=(
                tier["tier"], tier["value"], tier["cost"], tier["clear_count"], group["name"]))
        total = sum(len(g["tiers"]) for g in groups)
        summary = f"{len(rows)} of {total} reference tiers · {len(groups)} groups · No Boon edits"
        try:
            f = self.core_of()
            if f is not None:
                observation = boons.read_observation(f)
                summary += f" · Karma Shards: {observation['karma_shards']:,} (read-only here)"
                self.boon_observation.configure(text=(
                    f"EXP-associated record {boons.EXP_CANDIDATE:08x}: "
                    + boons.observation_label(observation["exp_candidate"])))
        except core.SaveError as exc:
            self.boon_observation.configure(text=str(exc))
        self.boon_count.configure(text=summary)
        tree.selection_set([i for i in keep if tree.exists(i)])
        self._select_boon()

    def _select_boon(self):
        picked = self.boon_tree.selection()
        if len(picked) != 1 or picked[0] not in self._boon_rows:
            return
        group, tier = self._boon_rows[picked[0]]
        note = "Ownership, activation and stacking are not yet mapped."
        if group["name"] == "経験値" and tier["tier"] == 1:
            note = "This is the +10% EXP reference tier. The candidate record alone does not prove it is purchased or active."
        self.boon_detail.configure(text=(
            f"{group['label']} · tier {tier['tier']} · {group['name']}\n"
            f"Listed cost: {tier['cost']} Karma Shards. Clear-count field: {tier['clear_count']}; "
            "eligibility still needs game confirmation.\n" + note))
