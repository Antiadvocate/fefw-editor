from types import SimpleNamespace
import unittest

import facilities as fac
from test_tutorial_page import PageHarness
from test_fast_travel import fixture
from test_facilities import rows, ARMORER, ITEMS, EXAM, STABLES


class FacilityHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload=fixture([rows()]).payload
        self.selected=(f'{ARMORER:08x}',f'{EXAM:08x}')
        self.facility_tree=SimpleNamespace(selection=lambda:self.selected)


class FacilityPageTest(unittest.TestCase):
    def test_mixed_selection_undo_redo_and_unrelated_switches(self):
        app=FacilityHarness();before=bytes(app.sv.payload);app.core_of()
        app.set_facilities(True);after=bytes(app.sv.payload)
        self.assertNotIn(ARMORER,fac.read(app.core_of()))
        self.assertEqual(fac.read(app.core_of())[EXAM],1)
        self.assertNotIn(STABLES,fac.read(app.core_of()))
        self.assertEqual(len(app._undo_stack),1)
        app.undo();self.assertEqual(bytes(app.sv.payload),before)
        app.redo();self.assertEqual(bytes(app.sv.payload),after)
        app.set_facilities(False)
        self.assertEqual(fac.read(app.core_of())[ARMORER],1)
        self.assertNotIn(EXAM,fac.read(app.core_of()))
        self.assertEqual(app.refreshes,4)

    def test_refusal_noop_and_invalid_batch_leave_no_history(self):
        app=FacilityHarness();before=bytes(app.sv.payload)
        app.mirrored=False;app.selected=();app.set_facilities(True)
        app.selected=(f'{ITEMS:08x}',);app.set_facilities(True)
        app.selected=(f'{EXAM:08x}','deadbeef');app.set_facilities(False)
        self.assertEqual(app.messages[-1][1],'error')
        app.selected=('not-an-id',);app.set_facilities(False)
        self.assertEqual(app.messages[-1][1],'error')
        self.assertEqual(bytes(app.sv.payload),before)
        self.assertFalse(hasattr(app,'_undo_stack'))
        self.assertEqual(app.refreshes,0)
