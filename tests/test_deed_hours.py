"""Hours experiment is scoped, reversible, and never marks rewards claimed."""
import unittest
from unittest.mock import patch

import deeds
import fefw_core as core
from test_deeds import TIME, rows, outside_map
from test_fast_travel import fixture
from test_tutorials import raw_map
from test_deed_page import DeedHarness

TEN = 0xe0de8be2
TWENTY = 0x71725a0a


class DeedHoursTest(unittest.TestCase):
    def test_only_hours_is_experimental_and_other_restricted_counters_stay_readonly(self):
        cat = deeds.catalog(); values = {h: v for h, v, _ in rows()}
        self.assertEqual(TIME, 0xeb92a0f6)
        self.assertEqual(deeds.editing_label(TIME, values), 'Experimental')
        self.assertEqual(sum(r['editable'] for r in cat.values()), 33)
        blocked = [h for h, r in cat.items() if not r['editable']]
        self.assertEqual(len(blocked), 14)
        f = fixture([rows()])
        for h in blocked:
            with self.assertRaises(deeds.DeedError): deeds.edited(f, h, 1)

    def test_hours_changes_preserve_all_other_bytes_claims_and_unrelated_maps(self):
        f = fixture([[(0x12345678, 410, True)], rows() + [(TEN, 4, False)]])
        before = bytes(f.payload); records = raw_map(f, deeds.locate(f))
        for target in (0, 20, 254, 255, 300):
            g = core.SaveFile(deeds.edited(f, TIME, target))
            self.assertEqual(deeds.read(g)[TIME], target)
            self.assertEqual(outside_map(g), outside_map(f))
            after = raw_map(g, deeds.locate(g))
            self.assertEqual({h: r for h, r in after.items() if h != TIME},
                             {h: r for h, r in records.items() if h != TIME})
            self.assertNotIn(TWENTY, deeds.read(g))
            self.assertEqual(deeds.edited(g, TIME, target), g.payload)
        self.assertEqual(bytes(f.payload), before)

    def test_experimental_note_does_not_bypass_unknown_state_or_range_guards(self):
        for data in (rows() + [(TEN, 1, False)],
                     [(h, -1, True) if h == TIME else (h, v, w) for h, v, w in rows()]):
            f = fixture([data]); original = bytes(f.payload)
            self.assertEqual(deeds.editing_label(TIME, deeds.read(f)), 'Read-only')
            with self.assertRaises(deeds.DeedError): deeds.edited(f, TIME, 20)
            self.assertEqual(bytes(f.payload), original)
        f = fixture([rows()])
        for value in (-1, 301, True, 20.5):
            with self.assertRaises(deeds.DeedError): deeds.edited(f, TIME, value)

    @patch('deed_page.messagebox.askokcancel', return_value=False)
    def test_page_hours_undo_redo_and_claim_warning(self, confirm):
        app = DeedHarness()
        app.sv.payload = fixture([rows() + [(TEN, 4, False)]]).payload
        app._deed_rows['milestone'] = (TIME, deeds.catalog()[TIME]['milestones'][1])
        original = bytes(app.sv.payload)
        app.input = '20'; app.set_deed(); edited = bytes(app.sv.payload)
        self.assertEqual(deeds.read(app.core_of())[TIME], 20)
        self.assertEqual(deeds.read(app.core_of())[TEN], 4)
        self.assertNotIn(TWENTY, deeds.read(app.core_of()))
        confirm.assert_not_called()
        app.undo(); self.assertEqual(bytes(app.sv.payload), original)
        app.redo(); self.assertEqual(bytes(app.sv.payload), edited)
        history = len(app._undo_stack)
        app.input = '9'; app.set_deed()
        confirm.assert_called_once()
        self.assertIn('Affected claimed targets: 10.', confirm.call_args.kwargs['detail'])
        self.assertEqual(bytes(app.sv.payload), edited)
        self.assertEqual(len(app._undo_stack), history)
