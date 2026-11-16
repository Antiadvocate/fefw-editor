"""Warning-gated chapter selector on Player; Leda Part 1 only."""
import tkinter as tk
from tkinter import ttk

import fefw_core as core
import fefw_layer as layer
import story

WARNING_TITLE = 'CAUTION - UNEXPECTED CONSEQUENCES POSSIBLE'
WARNING_POINTS = (
    "This feature currently only works with Leda's Part 1.",
    'It will start you at the applicable chapter. It WILL NOT unlock facilities, features, tutorials, map points, side quests from previous chapters or give you units that should be in your party. That will need to be managed separately.',
    'This has only been tested that the chapter starts and can be progressed to the next story sequence or battle. Long term testing has not been carried out.',
    'Skipping chapters will lock them out of being present in the Obelisk Chamber as this relies on chapter save files.',
    'Back up your save into a fresh directory NOW before proceeding.',
)
EVIDENCE_NOTE = ('The earlier Chapter 9 restoration progressed, but Tests 1 and 2 did not establish working chapter transitions. '
                 'Chapter editing is paused while the supplied Test 3 saves investigate a separate resume identifier and hub state.')


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
            self.story_status.configure(text='Open a Leda Part 1 save. Other routes remain read-only.')
            return
        route = layer.route_info(self.sv.payload)
        label = f'{route[0]} · Part {route[1]} · Chapter {route[2]}\n' if route else ''
        if route and (route[0], route[1]) != ('Leda', 1):
            self.story_status.configure(text=label + 'Read-only. Story editing supports Leda Part 1 only.')
            return
        try:
            info = story.require_leda(self.core_of())
            story.check_outer(self.sv.raw, info)
        except core.SaveError as exc:
            self.story_status.configure(text=label + str(exc)); return
        self.story_status.configure(text=info.label + '\nEditing paused after failed game tests; Test 3 diagnostics supplied separately.')
        self.story_button.state(['!disabled'])

    def _story_ready(self):
        if not self.sv:
            self.flash('Open a Leda Part 1 save first.', 'warn'); return False
        if self.mirror.get():
            self.flash('Turn off “Also edit this route’s other saves” before editing story progression.', 'warn')
            return False
        try:
            info = story.require_leda(core.SaveFile(self.sv.payload))
            story.check_outer(self.sv.raw, info)
        except core.SaveError as exc:
            self.flash(str(exc), 'error'); return False
        return True

    def open_story_progression(self):
        if not self._story_ready():
            return
        slot = self.sv
        if not self._confirm_story_warning():
            return
        if self.sv is not slot or not self._story_ready():
            return
        chapter = self._choose_story_chapter()
        if chapter is not None and self.sv is slot:
            self.apply_story_chapter(chapter)

    def _confirm_story_warning(self):
        win = tk.Toplevel(self); win.title(WARNING_TITLE); win.transient(self)
        self.place_dialog(win, 720, 510)
        win.configure(background=self.p['bg']); win.resizable(False, False)
        frame = ttk.Frame(win, padding=20); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=WARNING_TITLE, style='CardH3.TLabel', wraplength=670).pack(anchor='w', pady=(0, 12))
        for point in WARNING_POINTS:
            ttk.Label(frame, text='• ' + point, wraplength=665, justify='left').pack(anchor='w', pady=(0, 10))
        ttk.Label(frame, text=EVIDENCE_NOTE, wraplength=665, justify='left',
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
        win = tk.Toplevel(self); win.title('Leda · Part 1 — choose chapter'); win.transient(self)
        self.place_dialog(win, 680, 470); win.configure(background=self.p['bg'])
        frame = ttk.Frame(win, padding=18); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Chapter research · editing paused', style='CardH3.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Chapters 4–12 are the next research scope. Chapters 1–3 need location work. Use the supplied Test 3 saves first.',
                  wraplength=625, justify='left').pack(anchor='w', pady=(4, 10))
        buttons = ttk.Frame(frame); buttons.pack(side='bottom', fill='x', pady=(12, 0))
        tree = ttk.Treeview(frame, columns=('evidence',), show='tree headings', height=12, selectmode='browse')
        tree.heading('#0', text='Leda Part 1', anchor='w'); tree.column('#0', width=150, stretch=False)
        tree.heading('evidence', text='Evidence / limits', anchor='w'); tree.column('evidence', width=450)
        tree.pack(fill='both', expand=True)
        for chapter in range(4, 13):
            text = 'Progression unverified; entry setup under investigation'
            tree.insert('', 'end', iid=str(chapter), text=f'Chapter {chapter}', values=(text,))
        current = str(max(4, story.require_leda(self.core_of()).chapter))
        tree.selection_set(current); tree.see(current); tree.focus(current)
        result = [None]
        ttk.Button(buttons, text='Apply chapter start', state='disabled').pack(side='right')
        ttk.Button(buttons, text='Cancel', command=win.destroy).pack(side='right', padx=8)
        win.bind('<Escape>', lambda e: win.destroy()); win.grab_set(); self.wait_window(win)
        return result[0]

    def apply_story_chapter(self, chapter):
        if not self._story_ready():
            return
        self.flash('Story editing is paused after failed progression tests. Use the supplied Test 3 diagnostic saves.', 'warn')
