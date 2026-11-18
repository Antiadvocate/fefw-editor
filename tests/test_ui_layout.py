"""Display-dependent layout checks; skipped when Tk has no display."""
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import editor
from ui_util import ScrollableFrame
from test_unit_entries import fixture


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class LayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
            root.destroy()
        except tk.TclError as exc:
            raise unittest.SkipTest(f'Tk display unavailable: {exc}')

    def setUp(self):
        for name, value in (('_load_settings', {}), ('_save_settings', None),
                            ('_show_welcome', None)):
            mock = patch.object(editor.App, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        mock = patch.object(editor, 'default_save_dir', return_value=None)
        mock.start()
        self.addCleanup(mock.stop)
        self.app = editor.App()
        def close():
            for job in self.app.tk.call('after', 'info'):
                self.app.after_cancel(job)
            self.app.destroy()
        self.addCleanup(close)
        self.app.update()

    def inside(self, widget, viewport):
        self.assertTrue(widget.winfo_ismapped())
        for axis in ('x', 'y'):
            start = getattr(widget, 'winfo_root' + axis)()
            origin = getattr(viewport, 'winfo_root' + axis)()
            size = 'width' if axis == 'x' else 'height'
            self.assertGreaterEqual(start, origin)
            self.assertLessEqual(start + getattr(widget, 'winfo_' + size)(),
                                 origin + getattr(viewport, 'winfo_' + size)())

    def test_sidebar_and_tab_menu_remain_visible(self):
        for size in ('1360x900', '1234x768', '1000x640'):
            with self.subTest(size=size):
                self.app.geometry(size)
                self.app.update()
                actions = [w for w in descendants(self.app.units_page)
                           if isinstance(w, ttk.Button) and w.cget('text') in
                           ('Add unit…', 'Change unit number…', 'Copy unit in…', 'Remove unit')]
                self.assertEqual(len(actions), 4)
                for button in actions:
                    self.inside(button, self.app.units_page)
                self.app.status_lbl.configure(text='Long status message ' * 100)
                self.app.update()
                self.inside(self.app.tab_menu_button, self.app)
                menu = self.app.nametowidget(self.app.tab_menu_button.cget('menu'))
                menu.invoke(menu.index('end'))
                self.assertEqual(self.app.pages.select(), str(self.app.flags_page))
                self.app.pages.select(self.app.units_page)

    def test_stats_and_story_controls_can_be_reached(self):
        self.app.geometry('1000x640')
        self.app.update()
        last = self.app._stat_spins[-1]
        last.focus_force()
        self.app.update()
        self.inside(last, self.app.stats_scroll.canvas)
        self.app.pages.select(self.app.player_page)
        self.app.update()
        self.app.player_scroll.see(self.app.troubleshoot_button)
        self.app.update()
        for button in (self.app.story_button, self.app.part2_button,
                       self.app.troubleshoot_button):
            self.inside(button, self.app.player_scroll.canvas)

    def test_wheel_is_local_and_preserves_field_value(self):
        win = tk.Toplevel(self.app)
        win.geometry('360x200')
        form = ScrollableFrame(win)
        form.pack(fill='both', expand=True)
        value = tk.StringVar(value='7')
        spin = ttk.Spinbox(form.body, textvariable=value, from_=0, to=99)
        spin.pack()
        ttk.Label(form.body, text='Line\n' * 80).pack()
        self.app.update()
        other = self.app.stats_scroll.canvas.yview()
        spin.event_generate('<Button-5>')
        self.app.update()
        self.assertGreater(form.canvas.yview()[0], 0)
        self.assertEqual(value.get(), '7')
        self.assertEqual(self.app.stats_scroll.canvas.yview(), other)
        native = ttk.Treeview(form.body, height=2)
        native.pack()
        for i in range(30):
            native.insert('', 'end', text=str(i))
        self.app.update()
        form.see(native)
        self.app.update()
        before = form.canvas.yview()
        native.event_generate('<MouseWheel>', delta=-120)
        self.app.update()
        self.assertGreater(native.yview()[0], 0)
        self.assertEqual(form.canvas.yview(), before)
        self.app.p = editor.PALETTES['light']
        self.app.apply_theme()
        self.app.update()
        self.assertEqual(form.canvas.cget('background'), self.app.p['bg'])
        win.destroy()
        self.app.update()  # No stale scrolling callbacks after closing a dialog.

    def test_add_unit_footer_and_long_preview_at_small_sizes(self):
        f = fixture()
        original = bytes(f.payload)
        self.app.sv = SimpleNamespace(payload=f.payload)
        def inspect(win):
            tree = next(w for w in descendants(win) if isinstance(w, ttk.Treeview))
            anna = next(i for i in tree.get_children() if tree.item(i, 'text') == 'Anna')
            tree.selection_set(anna)
            for size in ('920x760', '640x480', '580x420'):
                win.geometry(size)
                win.update()
                for button in (w for w in descendants(win) if isinstance(w, ttk.Button)):
                    self.inside(button, win)
                details = next(w for w in descendants(win) if isinstance(w, ScrollableFrame))
                details.canvas.yview_moveto(1)
                win.update()
                self.assertAlmostEqual(details.canvas.yview()[1], 1, delta=.03)
            win.destroy()
        with patch.object(self.app, '_unit_entry_ready', return_value=True), \
                patch.object(self.app, 'core_of', return_value=f), \
                patch.object(self.app, 'wait_window', side_effect=inspect):
            self.app.open_add_unit()
        self.assertEqual(bytes(f.payload), original)
        self.app.sv = None
