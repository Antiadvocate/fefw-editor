"""Warning-gated chapter selector with route-specific validation evidence."""
import tkinter as tk
from tkinter import ttk

import fefw_core as core
import fefw_layer as layer
import story
import story_start

WARNING_TITLE = 'CAUTION - UNEXPECTED CONSEQUENCES POSSIBLE'
WARNING_POINTS = (
    "This is a Leda Part 1 save. Chapters 2–12 are available. Chapter 1 cannot be selected because its first objective cannot be progressed.",
    'It will start you at the applicable chapter. It WILL NOT unlock facilities, features, tutorials, map points, side quests from previous chapters or give you units that should be in your party. That will need to be managed separately.',
    'This has only been tested that the chapter starts and can be progressed to the next story sequence or battle. Long term testing has not been carried out.',
    'The Obelisk Chamber relies on chapter save files. Select “Create a chapter start file using this state” to write the chosen chapter’s file when you Save. Other skipped chapters still need their own files. Existing files require overwrite confirmation and are backed up first.',
    'Back up your save into a fresh directory NOW before proceeding.',
)
EVIDENCE_NOTE = ('Chapters 2–12 passed opening and next-story-beat tests. Editor-created chapter files passed Obelisk tests for Chapters 8 and 9; other chapters are untested through the Obelisk. Entry resets the clock and internal restart state.')


def warning_points(route):
    if route == 4:
        return WARNING_POINTS
    if route == 1:
        return ('This is a Cai Part 1 save. Chapters 1–12 are available. Chapters 1, 5–8 and 10–12 are Inferred targets awaiting game tests.',
                'For Cai Chapter 3 and later, Sewers access is enabled automatically. Other facilities, features, tutorials, map points, side quests and party units from previous chapters must still be managed separately.',
                'Cai Chapters 2 and 9 passed initial progression tests; Chapter 3 was completed. Chapter 4 Sewers entry and progression passed after natural Chapter 3 completion. Direct Chapter 4 entry with this fix still needs a game test. Editor-created Cai chapter files have not been tested through the Obelisk. Long term testing has not been carried out.',
                *WARNING_POINTS[3:])
    raise story.StoryError('Unsupported story route.')


def evidence_note(route):
    if route == 4:
        return EVIDENCE_NOTE
    return ('Cai Chapters 2/3/9 passed. Chapter 4: Sewers fix passed after natural Chapter 3; direct entry remains untested. Cai Chapter 3+ enables Sewers access. Entry resets the clock and internal restart state. Cai Obelisk use remains untested.')


class StoryPageMixin:
    def _build_story(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=(16, 8))
        card.pack(fill='x', pady=(10, 0))
        self.story_button = ttk.Button(card, text='Story progression…',
                                       command=self.open_story_progression)
        self.story_button.pack(side='right', padx=(12, 0))
        ttk.Label(card, text='Story progression · Experimental', style='CardH3.TLabel').pack(anchor='w')
        self.story_status = ttk.Label(card, style='CardMuted.TLabel', wraplength=690, justify='left')
        self.story_status.pack(anchor='w', pady=(4, 0))
        self.refresh_story()

    def refresh_story(self):
        if not hasattr(self, 'story_button'):
            return
        self.story_button.state(['disabled'])
        if not self.sv:
            self.story_status.configure(text='Open a Leda or Cai Part 1 save. Other routes remain read-only.')
            return
        route = layer.route_info(self.sv.payload)
        label = f'{route[0]} · Part {route[1]} · Chapter {route[2]}\n' if route else ''
        if route and (route[0], route[1]) not in (('Leda', 1), ('Cai', 1)):
            self.story_status.configure(text=label + 'Read-only. Story editing supports Leda and Cai Part 1 only.')
            return
        try:
            info = story_start.validate(self.core_of())
            story.check_outer(self.sv.raw, info)
        except core.SaveError as exc:
            self.story_status.configure(text=label + str(exc)); return
        pending = getattr(self.sv, '_pending_story_chapter', None)
        note = f'\n{story.chapter_filename(pending.route, pending.chapter)} will be created on Save.' if pending else ''
        evidence = 'Chapters 2–12 game-tested; Chapter 1 unavailable.' if info.route == 4 else 'Chapters 2/3/9 game-tested; Chapter 4 Sewers fix passed after natural Chapter 3.'
        self.story_status.configure(text=info.label + '\n' + evidence + note)
        self.story_button.state(['!disabled'])

    def _story_ready(self):
        if not self.sv:
            self.flash('Open a Leda or Cai Part 1 save first.', 'warn'); return False
        if self.mirror.get():
            self.flash('Turn off “Also edit this route’s other saves” before editing story progression.', 'warn')
            return False
        try:
            info = story_start.validate(core.SaveFile(self.sv.payload))
            story.check_outer(self.sv.raw, info)
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return False
        return True

    def open_story_progression(self):
        if not self._story_ready():
            return
        slot = self.sv
        route = story.read(core.SaveFile(slot.payload)).route
        if not self._confirm_story_warning():
            return
        if self.sv is not slot or not self._story_ready():
            return
        if story.read(core.SaveFile(slot.payload)).route != route:
            self.flash('The route changed while the warning was open. Open Story progression again.', 'warn'); return
        choice = self._choose_story_chapter()
        if choice is not None and self.sv is slot and self._story_ready():
            if story.read(core.SaveFile(slot.payload)).route != route:
                self.flash('The route changed while choosing a chapter. Open Story progression again.', 'warn'); return
            self.apply_story_chapter(*choice)

    def _confirm_story_warning(self):
        route = story.read(core.SaveFile(self.sv.payload)).route
        win = tk.Toplevel(self); win.title(WARNING_TITLE); win.transient(self)
        self.place_dialog(win, 720, 570)
        win.configure(background=self.p['bg']); win.resizable(False, False)
        frame = ttk.Frame(win, padding=20); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=WARNING_TITLE, style='CardH3.TLabel', wraplength=670).pack(anchor='w', pady=(0, 12))
        for point in warning_points(route):
            ttk.Label(frame, text='• ' + point, wraplength=665, justify='left').pack(anchor='w', pady=(0, 10))
        ttk.Label(frame, text=evidence_note(route), wraplength=665, justify='left',
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
        chapters = story_start.TARGETS[info.route]
        win = tk.Toplevel(self); win.title(f'{lord} · Part 1 — choose chapter'); win.transient(self)
        self.place_dialog(win, 680, 540); win.configure(background=self.p['bg'])
        frame = ttk.Frame(win, padding=18); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Choose a chapter start', style='CardH3.TLabel').pack(anchor='w')
        limit = 'Chapter 1 is unavailable.' if info.route == 4 else 'Cai Chapter 3+ also enables Sewers access.'
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
        tree.heading('#0', text=f'{lord} Part 1', anchor='w'); tree.column('#0', width=150, stretch=False)
        tree.heading('evidence', text='Evidence / limits', anchor='w'); tree.column('evidence', width=450)
        scroll = ttk.Scrollbar(table, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky='nsew'); scroll.grid(row=0, column=1, sticky='ns')
        for chapter in chapters:
            if chapter in story_start.TESTED_BY_ROUTE[info.route]:
                text = 'Game-tested opening and progression'
            elif info.route == 1 and chapter == 4:
                text = 'Conditional pass — Sewers fixed after natural Chapter 3'
            else:
                text = 'Inferred — game test pending'
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
            route = story_start.validate(core.SaveFile(self.sv.payload)).route
            story_start.target(chapter, route)
            self._commit_form()
            if not self._story_ready():
                return
            if story.read(core.SaveFile(self.sv.payload)).route != route:
                raise story.StoryError('The route changed; reopen Story progression.')
            new = story_start.edited(core.SaveFile(self.sv.payload), chapter)
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return
        pending = story.ChapterFileRequest(route, chapter) if create_file else None
        if bytes(new) == bytes(self.sv.payload) and pending == getattr(self.sv, '_pending_story_chapter', None):
            self.flash('This chapter-start setup is already staged.', 'info'); return
        self.push_undo()
        self.sv.payload = bytearray(new); self.sv.scan(); self.sv._core_cache = None
        self.sv._pending_story_chapter = pending
        self._touch([self.sv]); self.refresh_after_core()
        self.flash(f'{story.ROUTES[route]} Part 1 Chapter {chapter} start staged — Ctrl+S saves; Ctrl+Z undoes.', 'ok')
