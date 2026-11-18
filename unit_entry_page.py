"""Recruit preview and identity controls with same-route mirroring."""
import tkinter as tk
from tkinter import ttk, simpledialog

import fefw_core as core
import unit_entries as entries


class UnitEntryPageMixin:
    def _unit_entry_ready(self):
        if not self.sv: return False
        self._commit_form()
        try: entries.require_context(self.core_of())
        except core.SaveError as exc:
            self.flash(str(exc), 'error');return False
        return True

    def apply_unit_entry(self, action, person, number=None, expected=None):
        if not self._unit_entry_ready():return False
        if expected is not None and (self.sv is not expected[0] or bytes(self.sv.payload)!=expected[1]):
            self.flash('The selected save changed. Reopen the unit preview.', 'warn');return False
        def edit(f):
            entries.require_context(f)
            if action in ('add', 'restore'):
                state = entries.status(f, person)
                if state == 'Already in party':
                    return f.payload
                if state.startswith('Existing inactive'):
                    return entries.restore(f, person)
                return entries.add(f, person)  # Reject duplicates/unknown states.
            if action == 'renumber':
                return entries.renumber(f, person, number)
            raise core.SaveError('Unknown unit action.')
        # The preview action is exact for the selected slot. Peers may need
        # creation, flag restoration, or no change, and allocate numbers locally.
        try:
            if action == 'add': entries.add(self.core_of(), person)
            elif action == 'restore': entries.restore(self.core_of(), person)
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return False
        label = {'add':'Unit added where missing', 'restore':'Recruitment restored',
                 'renumber':'Unit number and mapped ownership references updated'}.get(action, 'Unit edit')
        if not self._core_edit(edit, label):
            return False
        self.uid=person;self.show_unit()
        return True

    def open_add_unit(self):
        if not self._unit_entry_ready():return
        f=self.core_of();expected=(self.sv,bytes(self.sv.payload))
        try:
            rows=entries.roster(f);flags=entries.flag_values(f);cat=entries.catalog()
            states={h:entries.status(f,h,rows,flags) for h in cat}
            try:number=entries.next_number(f);allocation_error=''
            except core.SaveError as exc:number=None;allocation_error=str(exc)
        except core.SaveError as exc:self.flash(str(exc),'error');return
        from editor_advanced import class_label
        win=tk.Toplevel(self);win.title('Add unit — preview');win.transient(self)
        self.place_dialog(win,850,640)
        top=ttk.Frame(win,padding=12);top.pack(fill='x')
        ttk.Label(top,text='Choose a character',style='CardH3.TLabel').pack(anchor='w')
        context=entries.context(f)
        note = {'mid-battle': 'Mid-battle: adds a reserve for a later deployment; does not spawn a unit into the current fight. Game test pending.',
                'pre-battle': 'Pre-battle: deployment and retention need game testing.',
                'chapter-start': 'Chapter-start: opening scripts may reset or replace units. Game test pending.'}.get(context, '')
        if note: ttk.Label(top,text=note,wraplength=805).pack(anchor='w',pady=(6,0))
        search=ttk.Entry(top);search.pack(fill='x',pady=(8,0))
        frame=ttk.Frame(win,padding=(12,0));frame.pack(fill='both',expand=True)
        tree=ttk.Treeview(frame,columns=('class','status'),show='tree headings',selectmode='browse')
        tree.heading('#0',text='Character');tree.column('#0',width=180)
        tree.heading('class',text='Starting class');tree.column('class',width=155)
        tree.heading('status',text='Status');tree.column('status',width=370)
        scroll=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        detail=ttk.Label(win,wraplength=805,justify='left',padding=12)
        detail.pack(fill='x')
        bar=ttk.Frame(win,padding=12);bar.pack(fill='x')
        selected={'person':None,'action':None}
        def choose(*_):
            picked=tree.selection();selected.update(person=None,action=None)
            apply.state(['disabled'])
            if not picked:detail.configure(text='Select a character to preview the change.');return
            h=int(picked[0],16);r=cat[h];state=states[h]
            action=('add' if state.startswith('Not present') and number is not None else
                    'restore' if state.startswith('Existing inactive') else None)
            selected.update(person=h,action=action)
            if action=='restore':preview='Restore recruitment/met flags; keep the existing unit and its number.'
            else:preview=f"Level 1 · {class_label(int(r['class'],16))} · HP {r['hp']} · Unit number {number if number is not None else 'unavailable'}\n{len(r['items'])} starting items · {len(r['magic'])} spells · {len(r['skills'][5])} learned abilities. No mount or battalion is copied."
            if action=='add':preview+='\nNo existing unit record to restore; this creates a new unit.'
            preview+=f"\nRecruitment flag (Reads As): {r['recruit_flag']}"
            mirror_note = ('\nMirroring: each target keeps existing records or restores recruitment; missing characters get a free local unit number. All targets are checked before editing.' if self.mirror.get() else '')
            detail.configure(text=f"{r['name']} — {state}\n{preview}\n{r['evidence']}. {r['route_scope']}\nRecruitment may interact with later story events. Undo/Redo is available; changes are written on Save."+mirror_note+(f'\n{allocation_error}' if allocation_error and action!='restore' else ''))
            apply.configure(text='Restore recruitment' if action=='restore' else 'Add unit')
            if action:apply.state(['!disabled'])
        def fill(*_):
            keep=tree.selection();tree.delete(*tree.get_children());q=search.get().strip().casefold()
            for h,r in sorted(cat.items(),key=lambda item:item[1]['name'].casefold()):
                label=class_label(int(r['class'],16))
                if q and q not in f"{r['name']} {r['pid']} {label} {states[h]}".casefold():continue
                tree.insert('','end',iid=f'{h:08x}',text=r['name'],values=(label,states[h]))
            if keep and tree.exists(keep[0]):tree.selection_set(keep)
            choose()
        def commit():
            if selected['action'] and self.apply_unit_entry(selected['action'],selected['person'],expected=expected):win.destroy()
        apply=ttk.Button(bar,text='Add unit',style='Accent.TButton',command=commit);apply.pack(side='right')
        ttk.Button(bar,text='Cancel',command=win.destroy).pack(side='right',padx=8)
        search.bind('<KeyRelease>',fill);tree.bind('<<TreeviewSelect>>',choose)
        fill();search.focus_set();win.grab_set();self.wait_window(win)

    def open_unit_number(self):
        if not self._unit_entry_ready() or self.uid is None:return
        person=self.uid;expected=(self.sv,bytes(self.sv.payload))
        try:
            if entries.context(self.core_of()) != 'free-time':
                raise core.SaveError('Renumbering requires a free-time save; battle references are not rewritten.')
            rows=[g for u,g in entries.roster(self.core_of()) if u.person==person]
            if len(rows)!=1:raise core.SaveError('No unique character record is selected.')
            old=rows[0].unit_number
        except core.SaveError as exc:self.flash(str(exc),'error');return
        number=simpledialog.askinteger('Change unit number',
            f'Current unit_number: {old}\nEnter an unused number (1–254).\nMapped mount and battalion ownership will move with the unit.\nThis action is experimental until its in-game checks pass.',
            initialvalue=old,minvalue=1,maxvalue=254,parent=self)
        if number is not None:self.apply_unit_entry('renumber',person,number,expected)
