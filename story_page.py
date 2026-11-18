"""Warning-gated chapter selector with route-specific validation evidence."""
import tkinter as tk
from tkinter import ttk, messagebox

import fefw_core as core
import fefw_layer as layer
import story
import story_start
import story_troubleshoot

WARNING_TITLE = 'CAUTION - UNEXPECTED CONSEQUENCES POSSIBLE'
WARNING_POINTS = (
    "This is a Leda Part 1 save. Chapters 2–12 are available. Chapter 1 cannot be selected because its first objective cannot be progressed.",
    'It will start you at the applicable chapter. It WILL NOT unlock facilities, features, tutorials, map points, side quests from previous chapters or give you units that should be in your party. That will need to be managed separately.',
    'This has only been tested that the chapter starts and can be progressed to the next story sequence or battle. Long term testing has not been carried out.',
    'The Obelisk Chamber relies on chapter save files. Select “Create a chapter start file using this state” to write the chosen chapter’s file when you Save. Other skipped chapters still need their own files. Existing files require overwrite confirmation and are backed up first.',
    'Back up your save into a fresh directory NOW before proceeding.',
)
EVIDENCE_NOTE = ('Chapters 2–12 passed opening and next-story-beat tests. Editor-created chapter files passed Obelisk tests for Chapters 8 and 9; other chapters are untested through the Obelisk. Entry resets the clock and internal restart state.')


def warning_points(route, part=1):
    if part == 3 and route == 9:
        return ('Eshmel Part 3: Chapters 2–5 passed opening and progression checks. Chapter 6 reached its opening battle only. Chapter 1 is unavailable; start it through the Obelisk door.',
                'Chapter selection keeps the current party, stored carryover data, flags and inventory. It does not perform the native Part 3 transition or create missing route-completion state.',
                'Entry resets the clock and internal restart state. The game can regroup the party or reset unit stats during the opening. No Part 3 unlock repairs have been established.',
                *WARNING_POINTS[3:])
    if part == 2:
        if route not in story.PREFIXES:
            raise story.StoryError('Part 2 supports the four main routes only.')
        if route != 1:
            return (f'{story.ROUTES[route]} Part 2 Chapters 1–6 reached the next battle from the tested Part 1 baseline. Theodora Chapter 6 also passed with automatic midtown access.',
                    'Chapter 5 enables upper-city movement. Chapter 6 enables middle-city movement; the automatic Theodora entry repair passed its focused retest. Other prerequisites may still block progress.',
                    'Party, items and prior progression are retained. Missing units, rewards, facilities and map unlocks are not granted. Other source saves, Obelisk loading and long-term progression need testing.',
                    f'This does not create the separate Part_{story.FILE_CODES[route]}_2 handoff file. Optional chapter files are different.',
                    *WARNING_POINTS[3:])
        return ('Cai Part 2 Chapters 1–6 passed opening and next-battle checks from a natural Part 2 baseline.',
                'Chapter 5 enables upper-city movement to reach Dagda’s temple. Both repairing the blocked save and entering the chapter afresh passed.',
                'Separate conversion from Cai Part 1 Chapter 4 to Part 2 Chapter 1 passed its opening and next-battle checks. Other starting states, Obelisk loading and long-term progression remain untested. Party and prior progression are retained; missing prerequisites can still block objectives.',
                *WARNING_POINTS[3:])
    if route == 4:
        return WARNING_POINTS
    if route == 1:
        return ('This is a Cai Part 1 save. Chapters 1–12 passed opening and progression tests.',
                'For Cai Chapter 3 and later, Sewers access is enabled automatically. Other facilities, features, tutorials, map points, side quests and party units from previous chapters must still be managed separately.',
                'Direct Chapter 4 entry passed with the Sewers fix. Editor-created Cai chapter files have not been tested through the Obelisk. Long term testing has not been carried out.',
                *WARNING_POINTS[3:])
    if route == 2:
        return ('This is a Dietrich Part 1 save. Chapters 3–12 are available and passed short-session checks. Chapters 1 and 2 are unavailable: Chapter 2 replay blocks at the rescue, and Chapter 1 leads into it.',
                'Chapter 5 clears the upper movement restriction. Chapter 6 clears the lower restriction and enables upper/lower access and Vandahl Trading Company. Chapter 7 permits Hidden Windpierce teaching. Other unlocks and party units must be managed separately.',
                'Direct entry and progression for Chapters 5/6 passed with these prerequisites. Chapter 7 teaching and its next checkpoint also passed. Obelisk and long term progression remain untested.',
                *WARNING_POINTS[3:])
    if route == 3:
        return ('This is a Theodora Part 1 save. Chapters 1–12 passed short-session checks, including repaired access for Chapters 4, 6, 8 and 9.',
                'Chapters 1–2 return to 1446; Chapter 3 and later use 1449. Chapter 4 enables middle movement; 6/8 enable middle, lower and district movement; 9 shows the three-point Troy exit. Other earlier unlocks and party units must be managed separately.',
                'Chapter 6 passed via an alternate city route: the NPC barrier can remain. Chapter 8 cleared that barrier. The cause of this difference is unresolved. City controls remain available in Functions. Obelisk use and long term progression remain untested.',
                *WARNING_POINTS[3:])
    raise story.StoryError('Unsupported story route.')


def evidence_note(route, part=1):
    if part == 3 and route == 9:
        return 'Eshmel Part 3: Chapters 2–5 passed opening and progression checks. Chapter 6 reached its opening battle; progression is untested. Chapter 1 is unavailable; start it through the Obelisk door. Obelisk loading and longer-term progression remain untested.'
    if part == 2:
        if route != 1:
            return f'{story.ROUTES[route]} Part 2 Chapters 1–6 reached the next battle from the tested Part 1 baseline. Theodora 6 passed both manual repair and fresh entry with automatic middle-city access. Other baselines, Obelisk loading and long-term progression remain untested.'
        return 'Cai only: Chapters 1–6, Chapter 5 repair and editor checks passed. Part 1 Chapter 4 → Part 2 Chapter 1 passed short-session checks. Obelisk loading, other conversion starting states and long-term progression remain untested.'
    if route == 4:
        return EVIDENCE_NOTE
    if route == 1:
        return ('Cai Chapters 1–12 passed opening and progression tests, including direct Chapter 4 entry. Cai Chapter 3+ enables Sewers access. Entry resets the clock and internal restart state. Cai Obelisk use remains untested.')
    if route == 2:
        return ('Dietrich Chapters 3–12 and Test 1 UI passed. Only the native Chapter 2 control worked; replay repairs failed. Targeted prerequisites for 5–7 preserve party and tutorials.')
    if route == 3:
        return ('Theodora Chapters 1–12 and Test 1 UI passed. Chapter 6 uses alternate traversal; 9 needs only the small Troy-exit repair. Exact prerequisites for 4/6/8/9 preserve party, tutorials and unrelated flags/map points.')
    raise story.StoryError('Unsupported story route.')


def chapter_evidence(route, chapter, part=1):
    if part == 3 and route == 9:
        if chapter == 1:
            return 'Unavailable — start through the Obelisk door'
        if chapter == 6:
            return 'Opening battle reached — progression untested'
        return 'Game-tested opening and next battle'
    if part == 2:
        if route == 3 and chapter == 6:
            return 'Game-tested opening and progression with automatic midtown access'
        return ('Game-tested opening and progression' if chapter in story_start.PART2_TESTED_BY_ROUTE.get(route, ())
                else 'Inferred — game test pending')
    if route == 3 and chapter in story_start.THEODORA_REPAIRS:
        return story_start.THEODORA_REPAIRS[chapter]
    if route == 2 and chapter in story_start.DIETRICH_BLOCKERS:
        return 'Unavailable — ' + story_start.DIETRICH_BLOCKERS[chapter]
    if route == 2 and chapter in (5, 6):
        return 'Game-tested direct entry and progression'
    if route == 2 and chapter == 7:
        return 'Teaching and next checkpoint passed with permission fix'
    if chapter in story_start.TESTED_BY_ROUTE[route]:
        return 'Game-tested opening and progression'
    return 'Inferred — game test pending'


class StoryPageMixin:
    def _build_story(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=(16, 8))
        card.pack(fill='x', pady=(10, 0))
        ttk.Label(card, text='Story progression · Experimental', style='CardH3.TLabel').pack(anchor='w')
        self.story_status = ttk.Label(card, style='CardMuted.TLabel', wraplength=690, justify='left')
        self.story_status.pack(anchor='w', pady=(4, 0))
        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(8, 0))
        self.story_button = ttk.Button(actions, text='Story progression…',
                                       command=self.open_story_progression)
        self.story_button.pack(side='left')
        self.part2_button = ttk.Button(actions, text='Try Part 2 entry…',
                                      command=self.open_part2_entry)
        self.part2_button.pack(side='left', padx=12)
        self.troubleshoot_button = ttk.Button(actions, text='Troubleshoot Progress',
                                              command=self.open_progress_troubleshooter)
        self.troubleshoot_button.pack(side='left')
        self.refresh_story()

    def refresh_story(self):
        if not hasattr(self, 'story_button'):
            return
        self.story_button.state(['disabled'])
        if hasattr(self, 'part2_button'):
            self.part2_button.state(['disabled'])
        if hasattr(self, 'troubleshoot_button'):
            self.troubleshoot_button.state(['!disabled'] if self.sv else ['disabled'])
        if not self.sv:
            self.story_status.configure(text='Open a supported Part 1/2 save or an Eshmel Part 3 save (provisional).')
            return
        route = layer.route_info(self.sv.payload)
        label = f'{route[0]} · Part {route[1]} · Chapter {route[2]}\n' if route else ''
        if route and (route[0], route[1]) not in (('Leda', 1), ('Cai', 1), ('Dietrich', 1), ('Theodora', 1), ('Cai', 2), ('Leda', 2), ('Dietrich', 2), ('Theodora', 2), ('Eshmel', 3)):
            self.story_status.configure(text=label + 'Read-only. Supported: the four Part 1/2 routes and Eshmel Part 3.')
            return
        try:
            info = story_start.validate(self.core_of())
            story.check_outer(self.sv.raw, info, allow_part_change=
                              getattr(self.sv, "_allow_part_transition", False))
        except core.SaveError as exc:
            self.story_status.configure(text=label + str(exc)); return
        pending = getattr(self.sv, '_pending_story_chapter', None)
        note = f'\n{story.chapter_filename(pending.route, pending.chapter, pending.part)} will be created on Save.' if pending else ''
        evidence = {4: 'Chapters 2–12 game-tested; Chapter 1 unavailable.',
                    1: 'Chapters 1–12 game-tested; Chapter 3+ enables Sewers access.',
                    2: 'Chapters 3–12 game-tested, including direct entry for 5/6. Chapters 1/2 unavailable because of the Chapter 2 rescue block.',
                    3: 'Chapters 1–12 passed; targeted repairs for 4/6/8/9. Chapter 6 uses alternate traversal.'}.get(info.route, '')
        if info.part in (2, 3):
            evidence = evidence_note(info.route, info.part)
        if info.part == 2 and getattr(self.sv, '_allow_part_transition', False):
            evidence += ' This session used experimental Part 1-to-2 entry.'
        self.story_status.configure(text=info.label + '\n' + evidence + note)
        self.story_button.state(['!disabled'])
        if hasattr(self, 'part2_button') and info.route in story.PREFIXES and info.part == 1:
            self.part2_button.state(['!disabled'])

    def _story_ready(self):
        if not self.sv:
            self.flash('Open a supported Part 1/2 save or an Eshmel Part 3 save first.', 'warn'); return False
        if self.mirror.get():
            self.flash('Turn off “Also edit this route’s other saves” before editing story progression.', 'warn')
            return False
        try:
            info = story_start.validate(core.SaveFile(self.sv.payload))
            story.check_outer(self.sv.raw, info, allow_part_change=
                              getattr(self.sv, "_allow_part_transition", False))
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return False
        return True

    def open_progress_troubleshooter(self):
        if not self.sv:
            self.flash('Open a save first.', 'warn'); return
        slot, snapshot = self.sv, bytes(self.sv.payload)
        try:
            report = story_troubleshoot.diagnose(core.SaveFile(snapshot))
            story.check_outer(slot.raw, report.progress, allow_part_change=
                              getattr(slot, '_allow_part_transition', False))
        except core.SaveError as exc:
            messagebox.showerror('Troubleshoot Progress', str(exc) + '\n\nNo safe suggestion is available. '
                                 'Please report the save state and blocked objective at:\n' +
                                 story_troubleshoot.ISSUES_URL, parent=self); return
        win = tk.Toplevel(self); win.title('Troubleshoot Progress'); win.transient(self)
        self.place_dialog(win, 740, 570); win.configure(background=self.p['bg'])
        frame = ttk.Frame(win, padding=18); frame.pack(fill='both', expand=True)
        buttons = ttk.Frame(frame); buttons.pack(side='bottom', fill='x')
        ttk.Label(frame, text=report.progress.label, style='CardH3.TLabel').pack(anchor='w')
        ttk.Label(frame, text=report.note, wraplength=690, justify='left').pack(anchor='w', pady=(8, 10))
        table = ttk.Treeview(frame, columns=('state',), show='tree headings', height=5,
                             selectmode='none')
        table.heading('#0', text='Known prerequisite', anchor='w'); table.column('#0', width=420)
        table.heading('state', text='Current state / suggestion', anchor='w'); table.column('state', width=260)
        for row in report.checks:
            table.insert('', 'end', text=row.label, values=(row.state,))
        if report.checks:
            table.pack(fill='both', expand=True, pady=(0, 10))
        status = report.blocked
        if not status and report.checks and not report.actionable:
            status = 'All known prerequisites are already enabled. These checks cannot identify every cause of a blocked objective.'
        if self.mirror.get():
            status += '\nTurn off “Also edit this route’s other saves” to apply a repair to this slot.'
        if status:
            ttk.Label(frame, text=status.strip(), wraplength=690, justify='left').pack(anchor='w', pady=(0, 10))
        ttk.Label(frame, text='Only the listed missing unlocks are staged. Your current chapter, story checkpoint, '
                  'date, party and inventory are kept. Ctrl+S saves; Ctrl+Z undoes.',
                  wraplength=690, justify='left', style='CardMuted.TLabel').pack(anchor='w', pady=(0, 10))
        if not report.actionable:
            ttk.Label(frame, text='Still blocked? Please raise an issue with your character, part, chapter, '
                      'objective and what blocks the path. Include a screenshot and, if you are comfortable sharing it, a save.',
                      wraplength=690, justify='left').pack(anchor='w', pady=(0, 4))
            def open_issues():
                import webbrowser
                webbrowser.open(story_troubleshoot.ISSUES_URL)
            ttk.Button(frame, text='Open Antiadvocate/fefw-editor issues',
                       command=open_issues).pack(anchor='w', pady=(0, 10))
        def apply():
            if self.apply_progress_repair(slot, snapshot):
                win.destroy()
        apply_button = ttk.Button(buttons, text='Apply suggested unlocks', command=apply)
        apply_button.pack(side='right')
        if not report.actionable or self.mirror.get():
            apply_button.state(['disabled'])
        ttk.Button(buttons, text='Close', command=win.destroy).pack(side='right', padx=8)
        win.bind('<Escape>', lambda e: win.destroy()); win.grab_set(); self.wait_window(win)

    def apply_progress_repair(self, slot, snapshot):
        if self.sv is not slot or bytes(slot.payload) != snapshot:
            self.flash('The selected save changed. Reopen Troubleshoot Progress.', 'warn'); return False
        if not self._story_ready():
            return False
        self._commit_form()
        # Form edits can invalidate the diagnosis; never apply a stale plan.
        if self.sv is not slot or bytes(slot.payload) != snapshot:
            self.flash('Pending edits changed the save. Reopen Troubleshoot Progress.', 'warn'); return False
        try:
            new = story_troubleshoot.edited(core.SaveFile(slot.payload))
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return False
        if new == slot.payload:
            self.flash('No missing known unlocks to apply.', 'info'); return False
        self.push_undo()
        slot.payload = bytearray(new); slot.scan(); slot._core_cache = None
        self._touch([slot]); self.refresh_after_core()
        self.flash('Suggested progress unlocks staged — Ctrl+S saves; Ctrl+Z undoes.', 'ok')
        return True

    def open_story_progression(self):
        if not self._story_ready():
            return
        slot = self.sv
        initial = story.read(core.SaveFile(slot.payload))
        route, part = initial.route, initial.part
        if not self._confirm_story_warning():
            return
        if self.sv is not slot or not self._story_ready():
            return
        current = story.read(core.SaveFile(slot.payload))
        if (current.route, current.part) != (route, part):
            self.flash('The route changed or the part changed while the warning was open. Open Story progression again.', 'warn'); return
        choice = self._choose_story_chapter()
        if choice is not None and self.sv is slot and self._story_ready():
            current = story.read(core.SaveFile(slot.payload))
            if (current.route, current.part) != (route, part):
                self.flash('The route changed or the part changed while choosing a chapter. Open Story progression again.', 'warn'); return
            self.apply_story_chapter(*choice)

    def _confirm_story_warning(self):
        info = story.read(core.SaveFile(self.sv.payload))
        route, part = info.route, info.part
        win = tk.Toplevel(self); win.title(WARNING_TITLE); win.transient(self)
        self.place_dialog(win, 720, 570)
        win.configure(background=self.p['bg']); win.resizable(False, False)
        frame = ttk.Frame(win, padding=20); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=WARNING_TITLE, style='CardH3.TLabel', wraplength=670).pack(anchor='w', pady=(0, 12))
        for point in warning_points(route, part):
            ttk.Label(frame, text='• ' + point, wraplength=665, justify='left').pack(anchor='w', pady=(0, 10))
        ttk.Label(frame, text=evidence_note(route, part), wraplength=665, justify='left',
                  style='CardMuted.TLabel').pack(anchor='w', pady=(0, 8))
        result = [False]
        def finish(value):
            result[0] = value; win.destroy()
        buttons = ttk.Frame(frame); buttons.pack(side='bottom', fill='x', pady=(10, 0))
        ttk.Button(buttons, text='Continue', command=lambda: finish(True)).pack(side='right')
        cancel = ttk.Button(buttons, text='Cancel', command=lambda: finish(False))
        cancel.pack(side='right', padx=8); cancel.focus_set()
        win.bind('<Escape>', lambda e: finish(False)); win.protocol('WM_DELETE_WINDOW', lambda: finish(False))
        win.grab_set(); self.wait_window(win)
        return result[0]

    def _choose_story_chapter(self):
        info = story_start.validate(core.SaveFile(self.sv.payload))
        lord = story.ROUTES[info.route]
        chapters = story_start.chapters_for(info.route, info.part)
        win = tk.Toplevel(self); win.title(f'{lord} · Part {info.part} — choose chapter'); win.transient(self)
        self.place_dialog(win, 680, 540); win.configure(background=self.p['bg'])
        frame = ttk.Frame(win, padding=18); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Choose a chapter start', style='CardH3.TLabel').pack(anchor='w')
        limit = {4: 'Chapter 1 is unavailable.', 1: 'Cai Chapter 3+ also enables Sewers access.',
                 2: 'Dietrich Chapters 1/2 are unavailable because of the Chapter 2 rescue block. Chapters 5–7 apply targeted prerequisites; party and tutorials are preserved.',
                 3: 'Theodora 4/6/8/9 apply targeted access repairs. Chapter 6 uses an alternate route around the NPC barrier. Chapters 1–2 use 1446; Chapter 3+ uses 1449. Party and tutorials are preserved.'}.get(info.route, '')
        if info.part in (2, 3):
            limit = evidence_note(info.route, info.part)
        ttk.Label(frame, text='Selected save only. Apply stages the chapter start and date; Ctrl+S saves and Ctrl+Z undoes. ' + limit,
                  wraplength=625, justify='left').pack(anchor='w', pady=(4, 10))
        buttons = ttk.Frame(frame); buttons.pack(side='bottom', fill='x', pady=(12, 0))
        options = ttk.Frame(frame); options.pack(side='bottom', fill='x', pady=(10, 0))
        create_file = tk.BooleanVar(value=getattr(self.sv, '_pending_story_chapter', None) is not None)
        ttk.Checkbutton(options, text='Create a chapter start file using this state',
                        variable=create_file).pack(anchor='w')
        ttk.Label(options, text='Written beside the selected save only when you Save. Existing chapter files require confirmation; a .bak (or numbered .bak) is kept first.',
                  wraplength=625, justify='left', style='CardMuted.TLabel').pack(anchor='w', pady=(4, 0))
        table = ttk.Frame(frame); table.pack(fill='both', expand=True)
        table.rowconfigure(0, weight=1); table.columnconfigure(0, weight=1)
        tree = ttk.Treeview(table, columns=('evidence',), show='tree headings', height=12, selectmode='browse')
        tree.heading('#0', text=f'{lord} Part {info.part}', anchor='w'); tree.column('#0', width=150, stretch=False)
        tree.heading('evidence', text='Evidence / limits', anchor='w'); tree.column('evidence', width=450)
        scroll = ttk.Scrollbar(table, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky='nsew'); scroll.grid(row=0, column=1, sticky='ns')
        for chapter in chapters:
            text = chapter_evidence(info.route, chapter, info.part)
            tree.insert('', 'end', iid=str(chapter), text=f'Chapter {chapter}', values=(text,))
        current = str(info.chapter if info.chapter in chapters else chapters[0])
        tree.selection_set(current); tree.see(current); tree.focus(current)
        result = [None]
        def apply():
            picked = tree.selection()
            if picked:
                result[0] = (int(picked[0]), create_file.get()); win.destroy()
        ttk.Button(buttons, text='Apply chapter start', command=apply).pack(side='right')
        ttk.Button(buttons, text='Cancel', command=win.destroy).pack(side='right', padx=8)
        win.bind('<Escape>', lambda e: win.destroy()); win.grab_set(); self.wait_window(win)
        return result[0]

    def apply_story_chapter(self, chapter, create_file=False):
        if not self._story_ready():
            return
        try:
            info = story_start.validate(core.SaveFile(self.sv.payload))
            route, part = info.route, info.part
            story_start.target(chapter, route, part)
            self._commit_form()
            if not self._story_ready():
                return
            current = story.read(core.SaveFile(self.sv.payload))
            if (current.route, current.part) != (route, part):
                raise story.StoryError('The route changed or the part changed; reopen Story progression.')
            new = story_start.edited(core.SaveFile(self.sv.payload), chapter)
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return
        pending = story.ChapterFileRequest(route, chapter, part) if create_file else None
        if bytes(new) == bytes(self.sv.payload) and pending == getattr(self.sv, '_pending_story_chapter', None):
            self.flash('This chapter-start setup is already staged.', 'info'); return
        self.push_undo()
        self.sv.payload = bytearray(new); self.sv.scan(); self.sv._core_cache = None
        self.sv._pending_story_chapter = pending
        self._touch([self.sv]); self.refresh_after_core()
        self.flash(f'{story.ROUTES[route]} Part {part} Chapter {chapter} start staged — Ctrl+S saves; Ctrl+Z undoes.', 'ok')


    def open_part2_entry(self):
        if not self._story_ready():
            return
        info = story_start.validate(self.core_of())
        if info.route not in story.PREFIXES or info.part != 1:
            self.flash('Use a supported Part 1 free-time or chapter-start save.', 'warn'); return
        slot = self.sv
        snapshot = bytes(slot.payload)
        if not messagebox.askyesno('Experimental Part 2 entry',
                f'Start this {story.ROUTES[info.route]} Part 1 save at Part 2 Chapter 1?\n\n'
                'Part 2 Chapter 1 entry and progression passed from Cai Chapter 4, '
                'Leda Chapter 9, Dietrich Chapter 4 and Theodora Chapter 3 saves. '
                'Other starting states and long-term progression remain untested. '
                'It keeps your current units, items, '
                'flags and world state; it does not grant missing transition rewards '
                'or unlocks. Objectives may be blocked.\n\n'
                'This changes the selected save to Part 2, but does not create the '
                f'separate Part_{story.FILE_CODES[info.route]}_2 handoff file. An optional '
                f'Chapter_{story.FILE_CODES[info.route]}_2_N '
                'chapter file is different and does not replace it.\n\n'
                'Use a disposable copy. Apply changes only this slot; Ctrl+S saves '
                'and Ctrl+Z undoes. Chapter files are not created automatically.', parent=self):
            return
        if self.sv is not slot or bytes(slot.payload) != snapshot:
            self.flash('The selected save changed. Reopen Part 2 entry.', 'warn'); return
        self.apply_part2_entry()

    def apply_part2_entry(self):
        if not self._story_ready():
            return
        try:
            self._commit_form()
            if not self._story_ready():
                return
            new = story_start.enter_part2(self.core_of())
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return
        self.push_undo()
        # Session-only permission for the explicit conversion and its Undo/Redo.
        # Keep raw untouched: serialization derives the part mirror from payload.
        self.sv._allow_part_transition = True
        self.sv.payload = bytearray(new); self.sv.scan(); self.sv._core_cache = None
        self.sv._pending_story_chapter = None
        self._touch([self.sv]); self.refresh_after_core()
        self.flash(f'Experimental {story.ROUTES[story.read(self.core_of()).route]} Part 2 Chapter 1 entry staged — Ctrl+S saves; Ctrl+Z undoes.', 'ok')
