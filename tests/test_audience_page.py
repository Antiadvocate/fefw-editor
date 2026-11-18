"""Run real checkbox commit/undo handling with a small widget substitute."""
from types import SimpleNamespace
import unittest

import audiences as au
from test_audiences import GODS, FLAGS, FORTUNA, rows
from test_fast_travel import fixture, rows as travel_rows
from test_tutorial_page import PageHarness


class AudienceHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = fixture([rows()]).payload
        self.selected = (f'{GODS[0]:016x}',)
        self.checked = False
        self.blessing_tree = SimpleNamespace(selection=lambda: self.selected)
        self.blessing_audience = SimpleNamespace(get=lambda: self.checked)

    def _blessing_selected(self, _event=None):
        # A rejected checkbox action resets it to the actual stored state.
        if self.selected:
            h = au.HASHES.get(int(self.selected[0], 16))
            self.checked = au.read(self.core_of()).get(h) == 1


class AudiencePageTest(unittest.TestCase):
    def test_toggle_undo_redo_and_relocated_map_cache(self):
        app = AudienceHarness(); original = bytes(app.sv.payload)
        app.core_of(); app.toggle_blessing_audience()
        self.assertNotIn(FLAGS[0], au.read(app.core_of()))
        self.assertEqual(len(app._undo_stack), 1)
        self.assertEqual(app.dirty_slots, [app.sv])
        after = bytes(app.sv.payload)
        app.undo(); self.assertEqual(bytes(app.sv.payload), original)
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        app.sv.payload = fixture([travel_rows(), rows()]).payload
        expected = au.edited(app.core_of(), {GODS[0]: None})
        app.toggle_blessing_audience()
        self.assertEqual(app.sv.payload, expected)

    def test_noop_fortuna_and_no_selection_do_not_create_undo(self):
        app = AudienceHarness(); original = bytes(app.sv.payload)
        app.checked = True; app.toggle_blessing_audience()  # unchanged on
        app.selected = (f'{FORTUNA:016x}',); app.toggle_blessing_audience()
        self.assertEqual(app.messages[-1][1], 'error')
        app.selected = (); app.toggle_blessing_audience()
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertFalse(hasattr(app, '_undo_stack'))
