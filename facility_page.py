"""Facility switches and read-only access diagnostics for the selected save."""
from tkinter import ttk

import facilities
import facility_access
import fefw_core as core


class FacilityPageMixin:
    def _build_facilities(self):
        self.facility_views = ttk.Notebook(self.facilities_page)
        self.facility_views.pack(fill='both', expand=True)
        switches = ttk.Frame(self.facility_views)
        access = ttk.Frame(self.facility_views)
        self.facility_views.add(switches, text='Saved switches')
        self.facility_views.add(access, text='Access conditions')
        top = ttk.Frame(switches, style='Card.TFrame', padding=(14, 10))
        top.pack(fill='x', pady=(8, 0))
        row = ttk.Frame(top, style='Card.TFrame'); row.pack(fill='x')
        ttk.Label(row, text='Function switches', style='CardH3.TLabel').pack(side='left')
        self.facility_buttons = []
        for label, state in (('Disable selected', False), ('Enable selected', True)):
            b = ttk.Button(row, text=label, style='Small.TButton',
                           command=lambda s=state: self.set_facilities(s))
            b.pack(side='right', padx=(6, 0)); self.facility_buttons.append(b)
        self.facility_count = ttk.Label(top, style='CardMuted.TLabel', wraplength=920)
        self.facility_count.pack(anchor='w', pady=(6, 0))
        search_row = ttk.Frame(top, style='Card.TFrame'); search_row.pack(fill='x', pady=(8, 0))
        self.facility_kind = ttk.Combobox(search_row, state='readonly', width=19,
                                        values=('All switches', 'Service', 'Gate registration', 'Journal', 'Area access'))
        self.facility_kind.current(0); self.facility_kind.pack(side='left', padx=(0, 8))
        self.facility_kind.bind('<<ComboboxSelected>>', lambda e: self.refresh_facilities())
        self.facility_search = ttk.Entry(search_row); self.facility_search.pack(fill='x', expand=True)
        self.facility_search.bind('<KeyRelease>', lambda e: self.refresh_facilities())
        ttk.Label(switches, style='CardFaint.TLabel', wraplength=950, justify='left', text=(
            'Enable/Disable changes only the selected saved switches. Enabling movement clears its restriction; area-unlock switches are separate. Route, story and NPC conditions may still limit access. '
            'Gate registrations are separate from ordinary fast travel.\n'
            'Stables stays unchanged unless selected. Uses the same-route mirroring selection. Ctrl+Z undoes; Ctrl+S saves.'
        )).pack(side='bottom', anchor='w', pady=(8, 0))
        self.facility_detail = ttk.Label(switches, style='CardMuted.TLabel', wraplength=950,
                                         justify='left', padding=(12, 8), text='Select a switch to see its evidence and limits.')
        self.facility_detail.pack(side='bottom', fill='x', pady=(8, 0))
        self.facility_tree = self._facility_table(switches, (
            ('#0', 'Function / facility', 245), ('kind', 'Kind', 125), ('state', 'Saved switch', 160),
            ('evidence', 'Evidence', 135), ('jp', 'Reads As', 390), ('hash', 'Hash', 90)))
        self.facility_tree.bind('<<TreeviewSelect>>', lambda e: self._facility_selected())

        top = ttk.Frame(access, style='Card.TFrame', padding=(14, 12)); top.pack(fill='x', pady=(8, 0))
        ttk.Button(top, text='Copy diagnostics', style='Small.TButton', command=self.copy_facility_diagnostics).pack(side='right')
        self.facility_route = ttk.Label(top, text='Open a save to inspect access conditions.', style='CardH3.TLabel')
        self.facility_route.pack(anchor='w')
        ttk.Label(top, text='Read-only data conditions. Arena has no verified saved switch yet. Recorded flags do not guarantee access.',
                  style='CardMuted.TLabel', wraplength=920).pack(anchor='w', pady=(6, 0))
        self.access_detail = ttk.Label(access, style='CardMuted.TLabel', wraplength=950, justify='left',
                                      padding=(12, 10), text='Select a destination for the known conditions.')
        self.access_detail.pack(side='bottom', fill='x', pady=(8, 0))
        self.facility_access_tree = self._facility_table(access, (
            ('#0', 'Destination', 200), ('stored', 'Saved evidence', 140),
            ('route', 'Route / prerequisite', 265), ('entry', 'Access / entrance', 330)))
        self.facility_access_tree.configure(selectmode='browse')
        self.facility_access_tree.bind('<<TreeviewSelect>>', lambda e: self._facility_access_selected())

    @staticmethod
    def _facility_table(page, columns):
        frame = ttk.Frame(page, style='Card.TFrame'); frame.pack(fill='both', expand=True, pady=(8, 0))
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=tuple(c[0] for c in columns[1:]), show='tree headings', selectmode='extended')
        for col, label, width in columns:
            tree.heading(col, text=label, anchor='w'); tree.column(col, width=width, minwidth=width, stretch=False)
        vs = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        hs = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky='nsew'); vs.grid(row=0, column=1, sticky='ns'); hs.grid(row=1, column=0, sticky='ew')
        return tree

    def refresh_facilities(self):
        if not hasattr(self, 'facility_tree'):
            return
        tree = self.facility_tree; keep = tree.selection(); view = tree.yview()
        tree.delete(*tree.get_children()); self.facility_detail.configure(text='Select a switch to see its evidence and limits.')
        for b in self.facility_buttons: b.state(['disabled'])
        self._refresh_facility_access()
        try:
            cat = facilities.catalog(); f = self.core_of()
            if f is None:
                self.facility_count.configure(text='Open a save to see its saved function switches.'); return
            values = facilities.read(f)
        except core.SaveError as exc:
            self.facility_count.configure(text=str(exc)); return
        q = self.facility_search.get().strip().casefold(); kind = self.facility_kind.get()
        for h, row in cat.items():
            if kind != 'All switches' and row['kind'] != kind: continue
            if q and q not in f"{row['label']} {row['name']} {h:08x}".casefold(): continue
            tree.insert('', 'end', iid=f'{h:08x}', text=row['label'], values=(row['kind'],
                facilities.state_label(h, values.get(h)), row['coverage'], row['name'], f'{h:08x}'))
        tree.selection_set([i for i in keep if tree.exists(i)])
        if keep and any(tree.exists(i) for i in keep) and view:
            tree.yview_moveto(view[0])
        self.facility_count.configure(text=f"{len(tree.get_children())} of {len(cat)} switches shown · {sum(r['coverage'] == 'Inferred' for r in cat.values())} inferred · select a row for its tested scope")
        for b in self.facility_buttons: b.state(['!disabled'])
        self._facility_selected()

    def _facility_selected(self):
        picked = self.facility_tree.selection()
        if not picked: return
        rows = facilities.catalog()
        if len(picked) == 1:
            row = rows[int(picked[0], 16)]
            text = f"{row['label']} · {row['coverage']}\n{row['note']}"
            if int(picked[0], 16) == facility_access.YU_PHAS_GATE:
                text += '\n' + facility_access.yu_phas_gate_status(self.core_of())
            self.facility_detail.configure(text=text)
        else:
            self.facility_detail.configure(text=f'{len(picked)} selected switches will change together. Other switches, ordinary destinations and story progress are preserved.')

    def set_facilities(self, state):
        if not self.sv: return
        picked = self.facility_tree.selection()
        if not picked:
            self.flash('Select one or more function switches first.', 'info'); return
        self._commit_form()
        try:
            edits = {int(i, 16): state for i in picked}
            before = self.core_of(); after = facilities.edited(before, edits)
        except (ValueError, core.SaveError) as exc:
            self.flash(str(exc), 'error'); return
        self._core_edit(lambda f: facilities.edited(f, edits),
                        f"{'Enabled' if state else 'Disabled'} {len(edits)} function switch(es)")

    def _refresh_facility_access(self):
        tree = self.facility_access_tree; keep = tree.selection(); tree.delete(*tree.get_children())
        self.access_detail.configure(text='Select a destination for the known conditions.')
        self._access_rows = {}
        f = self.core_of()
        if f is None:
            self.facility_route.configure(text='Open a save to inspect access conditions.'); return
        route = facility_access.route_info(f)
        self.facility_route.configure(text=(f'Access conditions · {route[0]} P{route[1]} Ch{route[2]}' if route else 'Access conditions · unknown route'))
        try:
            for row in facility_access.report(f):
                iid = row.get('id') or f"{row['hash']:08x}"; self._access_rows[iid] = row
                tree.insert('', 'end', iid=iid, text=row['label'], values=(row['stored'], row['route_check'], row['entry']))
        except core.SaveError as exc:
            self.access_detail.configure(text=str(exc)); return
        tree.selection_set([i for i in keep if tree.exists(i)])
        self._facility_access_selected()

    def _facility_access_selected(self):
        picked = self.facility_access_tree.selection()
        if picked:
            row = self._access_rows[picked[0]]
            self.access_detail.configure(text=row['detail'] + ('\n' + row['error'] if row['error'] else ''))

    def copy_facility_diagnostics(self):
        f = self.core_of()
        if f is None: return
        try:
            text = facility_access.diagnostics(f)
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return
        self.clipboard_clear(); self.clipboard_append(text)
        self.flash('Copied access conditions and related saved flags.', 'ok')
