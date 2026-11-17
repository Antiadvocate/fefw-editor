"""The new page uses the existing cache, dirty state and undo mechanisms."""
from types import SimpleNamespace
import unittest

import fast_travel as ft
from test_tutorial_page import PageHarness
from test_fast_travel import fixture, rows, STABLES, TAVERN


class FastTravelHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = fixture([rows()]).payload
        self.selected = (f'{STABLES:08x}',)
        self.fast_travel_tree = SimpleNamespace(selection=lambda: self.selected)


class FastTravelPageTest(unittest.TestCase):
    def test_remove_add_undo_redo_refreshes_cached_save(self):
        app = FastTravelHarness(); before = bytes(app.sv.payload)
        app.core_of()
        app.set_fast_travel(None)
        after = bytes(app.sv.payload)
        self.assertNotIn(STABLES, ft.read(app.core_of()))
        self.assertEqual(app.dirty_slots, [app.sv])
        app.undo(); self.assertEqual(bytes(app.sv.payload), before)
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        app.set_fast_travel(1)
        self.assertEqual(ft.read(app.core_of())[STABLES], 1)
        self.assertEqual(app.refreshes, 4)

    def test_mirroring_refused_no_selection_noop_and_invalid_batch(self):
        app = FastTravelHarness(); before = bytes(app.sv.payload)
        app.mirrored = True; app.set_fast_travel(None)
        self.assertEqual(app.messages[-1][1], 'warn')
        app.mirrored = False; app.selected = (); app.set_fast_travel(None)
        app.selected = (f'{STABLES:08x}',); app.set_fast_travel(1)
        app.selected = (f'{TAVERN:08x}', 'deadbeef'); app.set_fast_travel(1)
        self.assertEqual(app.messages[-1][1], 'error')
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.refreshes, 0)
