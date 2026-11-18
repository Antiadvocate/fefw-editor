"""Tutorials page; mirrored edits with grouped Undo/Redo."""
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
        for label, value in (("Remove selected", None), ("Add to save", tutorials.AVAILABLE)):
            button = ttk.Button(row, text=label, style="Small.TButton",
                                command=lambda v=value: self.set_tutorials(v))
            button.pack(side="right", padx=(6, 0))
            self.tutorial_buttons.append(button)
        ttk.Button(row, text='Select shown', style='Small.TButton',
                   command=lambda: self.tutorial_tree.selection_set(self.tutorial_tree.get_children())).pack(side='right', padx=(6, 0))
        filters = ttk.Frame(top, style='Card.TFrame'); filters.pack(fill='x', pady=(8, 0))
        self.tutorial_category = ttk.Combobox(filters, state='readonly', width=19,
                                              values=('All categories', *tutorials.CATEGORIES))
        self.tutorial_state = ttk.Combobox(filters, state='readonly', width=16,
                                         values=('All states', 'Absent', 'Stored (2)', 'Present (1)', 'Unknown'))
        self.tutorial_evidence = ttk.Combobox(filters, state='readonly', width=19,
                                            values=('All names', 'Game title checked', 'Provisional name'))
        for combo in (self.tutorial_category, self.tutorial_state, self.tutorial_evidence):
            combo.current(0); combo.pack(side='left', padx=(0, 6))
            combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_tutorials())
        self.tutorial_search = ttk.Entry(filters)
        self.tutorial_search.pack(fill="x", expand=True)
        self.tutorial_search.bind("<KeyRelease>", lambda e: self.refresh_tutorials())
        ttk.Label(page, style="CardFaint.TLabel", wraplength=920, justify="left", text=(
            "Search English, Japanese or hash. Add to save stores the selected records; "
            "the game controls menu visibility and can unlock tutorials again during play. "
            "Select shown uses the current filters; "
            "other entries stay saved. Unknown states are preserved. "
            "Uses the same-route mirroring selection. "
            "Ctrl+Z undoes an edit; Ctrl+S writes it."
        )).pack(side="bottom", anchor="w", pady=(8, 0))
        self.tutorial_detail = ttk.Label(page, style='CardMuted.TLabel', wraplength=950,
                                         justify='left', padding=(12, 8), text='Select a tutorial for its naming evidence.')
        self.tutorial_detail.pack(side='bottom', fill='x', pady=(8, 0))
        frame = ttk.Frame(page, style="Card.TFrame")
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = self.tutorial_tree = ttk.Treeview(frame, columns=("category", "state", "evidence", "jp", "hash"),
                                                show="tree headings", selectmode="extended")
        for col, label, width in (("#0", "Name", 285), ('category', 'Category', 145),
                                  ("state", "Stored state", 155), ('evidence', 'Name evidence', 145),
                                  ("jp", "Reads as", 310), ("hash", "Hash", 95)):
            tree.heading(col, text=label, anchor="w")
            tree.column(col, width=width, minwidth=width, stretch=False)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=sb.set, xscrollcommand=hs.set)
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky='nsew'); sb.grid(row=0, column=1, sticky='ns')
        hs.grid(row=1, column=0, sticky='ew')
        enable_multi_select(tree)
        tree.bind('<<TreeviewSelect>>', lambda e: self._tutorial_selected(), add='+')

    def refresh_tutorials(self):
        if not hasattr(self, "tutorial_tree"):
            return
        tree = self.tutorial_tree
        keep = tree.selection(); view = tree.yview()
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
        category = self.tutorial_category.get(); state = self.tutorial_state.get()
        evidence = self.tutorial_evidence.get()
        for h, row in cat.items():
            label = tutorials.state_label(values.get(h)); name_evidence = tutorials.evidence_label(row)
            if category != 'All categories' and row['category'] != category: continue
            if evidence != 'All names' and name_evidence != evidence: continue
            if state != 'All states' and not (label.startswith('Unknown') if state == 'Unknown' else label == state): continue
            if q and q not in f"{row['label']} {row['name']} {h:08x}".casefold():
                continue
            tree.insert("", "end", iid=f"{h:08x}", text=row["label"],
                        values=(row['category'], label, name_evidence, row["name"], f"{h:08x}"))
        tree.selection_set([i for i in keep if tree.exists(i)])
        if any(tree.exists(i) for i in keep) and view: tree.yview_moveto(view[0])
        present = sum(h in values for h in cat)
        shown_present = sum(int(i, 16) in values for i in tree.get_children())
        unknown = len(values.keys() - cat.keys())
        self.tutorial_count.configure(text=(
            f"{len(tree.get_children())} shown ({shown_present} saved) · "
            f"{present} of {len(cat)} catalogue entries saved overall "
            f"({present - shown_present} outside filters) · "
            f"{sum(r['evidence'] == 'provisional-translation' for r in cat.values())} provisional names · "
            f"{unknown} unlisted records preserved"))
        for button in self.tutorial_buttons:
            button.state(["!disabled"])
        self._tutorial_selected()

    def _tutorial_selected(self):
        picked = self.tutorial_tree.selection()
        if len(picked) == 1:
            row = tutorials.catalog()[int(picked[0], 16)]
            note = ('English title is provisional and absent from the supplied screenshots. If it appears during normal play, a title screenshot would help confirm it.'
                    if row['evidence'] == 'provisional-translation' else
                    'English title, category and order match the supplied in-game screenshots. This verifies the name, not feature unlocks or availability on every route.')
            text = (row['label'] + ' · ' + tutorials.evidence_label(row) + '\n' + note
                    + '\n' + tutorials.visibility_note(row))
        elif picked:
            text = f'{len(picked)} tutorials selected. The whole selection changes together; unknown saved states are preserved by refusing the batch.'
        else:
            text = 'Select a tutorial for its naming evidence. New English titles are marked Provisional name.'
        self.tutorial_detail.configure(text=text)

    def set_tutorials(self, value):
        if not self.sv:
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
        count = len((tutorials.read(before).keys() - edits.keys()) |
                    {h for h, v in edits.items() if v is not None})
        what = f"{'Removed' if value is None else 'Stored'} {len(edits)} tutorial(s); {count} records remain in this save"
        self._core_edit(lambda f: tutorials.edited(f, edits), what)
