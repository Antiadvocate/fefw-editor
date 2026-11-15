"""Exercise real apply/undo methods with lightweight widget substitutes."""
from types import SimpleNamespace
import unittest

import blessings
from test_blessings import fixture, HASHES
from test_tutorial_page import PageHarness


class BlessingHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = fixture().payload
        self.selected = (f'{HASHES[1]:016x}',)
        self.entered = '60'
        self.blessing_tree = SimpleNamespace(selection=lambda: self.selected)
        self.blessing_exp = SimpleNamespace(get=lambda: self.entered)


class BlessingPageTest(unittest.TestCase):
    def test_apply_undo_redo_and_cache_refresh(self):
        app = BlessingHarness()
        before = bytes(app.sv.payload)
        app.core_of()
        app.apply_blessing_exp()
        after = bytes(app.sv.payload)
        self.assertNotEqual(before, after)
        self.assertEqual(blessings.read(app.core_of()).records[1].exp, 60)
        self.assertEqual(len(app._undo_stack), 1)
        self.assertEqual(app.dirty_slots, [app.sv])
        app.undo()
        self.assertEqual(bytes(app.sv.payload), before)
        app.redo()
        self.assertEqual(bytes(app.sv.payload), after)
        self.assertEqual(app.refreshes, 3)

    def test_mirroring_blocks_before_mutation(self):
        app = BlessingHarness(); app.mirrored = True
        before = bytes(app.sv.payload)
        app.apply_blessing_exp()
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.messages[-1][1], 'warn')

    def test_invalid_values_and_selection_leave_history_and_payload_alone(self):
        for value in ('', '-1', '1.5', '65536', 'nan', '0x10', '１２'):
            with self.subTest(value=value):
                app = BlessingHarness(); app.entered = value
                before = bytes(app.sv.payload)
                app.apply_blessing_exp()
                self.assertEqual(bytes(app.sv.payload), before)
                self.assertFalse(hasattr(app, '_undo_stack'))
                self.assertEqual(app.messages[-1][1], 'error')
        for selected in ((), tuple(f'{h:016x}' for h in HASHES[:2])):
            app = BlessingHarness(); app.selected = selected
            app.apply_blessing_exp()
            self.assertFalse(hasattr(app, '_undo_stack'))
            self.assertEqual(app.refreshes, 0)

    def test_same_value_does_not_create_undo_or_dirty_slot(self):
        app = BlessingHarness(); app.entered = ' 25 '
        before = bytes(app.sv.payload)
        app.apply_blessing_exp()
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.dirty_slots, [])

    def test_reloaded_layout_does_not_reuse_stale_exp_offsets(self):
        app = BlessingHarness()
        app.core_of()
        app.sv.payload = fixture(prefix=b'\xee' * 64).payload
        before = bytes(app.sv.payload)
        expected = blessings.edited(app.core_of(), {HASHES[1]: 60})
        app.apply_blessing_exp()
        self.assertNotEqual(bytes(app.sv.payload), before)
        self.assertEqual(app.sv.payload, expected)
