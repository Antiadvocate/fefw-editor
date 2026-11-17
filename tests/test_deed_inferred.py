"""Newly enabled counters preserve game progress and retain all edit guards."""
import unittest
from unittest.mock import patch

import deeds
import fefw_core as core
from test_deed_page import DeedHarness
from test_deeds import rows, outside_map
from test_fast_travel import fixture
from test_tutorials import raw_map


INFERRED = {0xac891429, 0x6e05ea11, 0xcc4a3b3a, 0x01aca43b, 0xc6f4cfe6,
            0x05413e55, 0x69c3bd94, 0x0c174336, 0x0cd50d11, 0xda109aa3,
            0xb8892bfd, 0x84f61022, 0x550f13b3, 0xe203feff}


class InferredDeedTest(unittest.TestCase):
    def test_every_new_counter_changes_only_its_total_and_preserves_claims(self):
        self.assertEqual({h for h, r in deeds.catalog().items() if r.get('inferred')}, INFERRED)
        for h in sorted(INFERRED):
            with self.subTest(counter=f'{h:08x}'):
                row = deeds.catalog()[h]
                claim = int(row['milestones'][0]['hash'], 16)
                f = fixture([[(0x12345678, 410, True)], rows() + [(claim, 4, True)]])
                original = bytes(f.payload)
                before = raw_map(f, deeds.locate(f))
                self.assertEqual(deeds.editing_label(h, deeds.read(f)), 'Inferred')
                self.assertEqual(deeds.edited(f, h, 0), f.payload)
                target = row['milestones'][-1]['target']
                g = core.SaveFile(deeds.edited(f, h, target))
                self.assertEqual(deeds.read(g), deeds.read(f) | {h: target})
                self.assertEqual(outside_map(g), outside_map(f))
                after = raw_map(g, deeds.locate(g))
                self.assertEqual({k: v for k, v in after.items() if k != h}, before)
                self.assertEqual(deeds.edited(g, h, target), g.payload)
                zero = core.SaveFile(deeds.edited(g, h, 0))
                self.assertEqual(deeds.read(zero)[claim], 4)
                self.assertEqual(deeds.claims_at_risk(h, 0, deeds.read(g)), [row['milestones'][0]])
                self.assertEqual(bytes(f.payload), original)

    def test_inference_does_not_bypass_unknown_claims_negative_progress_or_bounds(self):
        for h in sorted(INFERRED):
            row = deeds.catalog()[h]; claim = int(row['milestones'][0]['hash'], 16)
            for extra in ([(claim, 1, False)], [(h, -1, True)]):
                f = fixture([rows() + extra]); original = bytes(f.payload)
                self.assertEqual(deeds.editing_label(h, deeds.read(f)), 'Read-only')
                with self.assertRaises(deeds.DeedError): deeds.edited(f, h, 1)
                self.assertEqual(bytes(f.payload), original)
            f = fixture([rows()])
            with self.assertRaises(deeds.DeedError):
                deeds.edited(f, h, row['milestones'][-1]['target'] + 1)

    @patch('deed_page.messagebox.askokcancel', return_value=False)
    def test_inferred_support_counter_uses_existing_warning_and_history(self, confirm):
        h = 0x6e05ea11; tier = deeds.catalog()[h]['milestones'][0]
        claim = int(tier['hash'], 16)
        app = DeedHarness()
        app.sv.payload = fixture([rows() + [(h, tier['target'], False), (claim, 4, False)]]).payload
        app._deed_rows['milestone'] = (h, tier)
        original = bytes(app.sv.payload)
        app.input = '0'; app.set_deed()
        confirm.assert_called_once()
        self.assertEqual(bytes(app.sv.payload), original)
        app.input = str(tier['target'] + 1); app.set_deed()
        changed = bytes(app.sv.payload)
        self.assertNotEqual(changed, original)
        app.undo(); self.assertEqual(bytes(app.sv.payload), original)
        app.redo(); self.assertEqual(bytes(app.sv.payload), changed)
