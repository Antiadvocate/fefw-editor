from types import SimpleNamespace
import unittest

import deeds
from test_deeds import TRAIN, TIME, rows
from test_fast_travel import fixture
from test_tutorial_page import PageHarness


class DeedHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = fixture([rows()]).payload
        self.selected = ('milestone',)
        self._deed_rows = {'milestone': (TRAIN, deeds.catalog()[TRAIN]['milestones'][5])}
        self.deed_tree = SimpleNamespace(selection=lambda: self.selected)
        self.input = '75'
        self.deed_value = SimpleNamespace(get=lambda: self.input)


class DeedPageTest(unittest.TestCase):
    def test_edit_undo_redo_refresh_and_save_target(self):
        app = DeedHarness(); before = bytes(app.sv.payload)
        app.core_of(); app.set_deed(); after = bytes(app.sv.payload)
        self.assertEqual(deeds.read(app.core_of())[TRAIN], 75)
        self.assertEqual(app.dirty_slots, [app.sv])
        self.assertEqual(len(app._undo_stack), 1)
        app.undo(); self.assertEqual(bytes(app.sv.payload), before)
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        self.assertEqual(app.refreshes, 3)

    def test_mirroring_invalid_noop_readonly_and_missing_selection_make_no_history(self):
        app = DeedHarness(); original = bytes(app.sv.payload)
        app.mirrored = True; app.set_deed()
        self.assertEqual(app.messages[-1][1], 'warn')
        app.mirrored = False
        for value in ('bad', '1.5', '-1', '101', '65'):
            app.input = value; app.set_deed()
        app._deed_rows['milestone'] = (TIME, deeds.catalog()[TIME]['milestones'][0])
        app.input = '20'; app.set_deed()
        self.assertEqual(app.messages[-1][1], 'error')
        app.selected = (); app.set_deed()
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertFalse(hasattr(app, '_undo_stack'))
