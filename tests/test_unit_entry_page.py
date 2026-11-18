from types import SimpleNamespace
import unittest

import unit_entries
from test_tutorial_page import PageHarness
from test_unit_entries import fixture, CAI, CATANIA


class Harness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload=fixture().payload
        self.uid=CAI

    def show_unit(self): pass


class UnitEntryPageTest(unittest.TestCase):
    def test_add_renumber_restore_undo_redo_selected_slot_only(self):
        a=Harness();original=bytes(a.sv.payload)
        other=Harness().sv;other_before=bytes(other.payload)
        self.assertTrue(a.apply_unit_entry('add',CATANIA))
        added=bytes(a.sv.payload)
        self.assertEqual(unit_entries.status(a.core_of(),CATANIA),'Already in party')
        self.assertEqual(a.dirty_slots,[a.sv])
        a.undo();self.assertEqual(a.sv.payload,original)
        a.redo();self.assertEqual(a.sv.payload,added)
        self.assertTrue(a.apply_unit_entry('renumber',CATANIA,30))
        a.undo();self.assertEqual(a.sv.payload,added)
        a.redo();self.assertEqual(unit_entries.roster(a.core_of())[-1][1].unit_number,30)
        self.assertEqual(other.payload,other_before)
        self.assertTrue(a.apply_unit_entry('restore',CAI))

    def test_duplicate_stale_preview_and_noop_do_not_add_history(self):
        a=Harness();expected=(a.sv,bytes(a.sv.payload))
        self.assertFalse(a.apply_unit_entry('add',CAI))
        self.assertFalse(a.apply_unit_entry('renumber',CAI,12))
        self.assertFalse(hasattr(a,'_undo_stack'))
        a.sv=SimpleNamespace(path='different',payload=bytearray(expected[1]),scan=lambda:None)
        self.assertFalse(a.apply_unit_entry('add',CATANIA,expected=expected))
        self.assertFalse(hasattr(a,'_undo_stack'))
        self.assertEqual(a.sv.payload,expected[1])
