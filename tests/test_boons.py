"""Read-only inspection must not promote a candidate into an unlock state."""
import struct
import unittest
from unittest.mock import patch

import boons
from test_audiences import rows
from test_fast_travel import fixture


class BoonTest(unittest.TestCase):
    def test_reference_counts_and_first_exp_and_discount_requirements(self):
        groups = boons.catalog()
        self.assertEqual(len(groups), 31)
        self.assertEqual(sum(len(g['tiers']) for g in groups), 81)
        exp = next(g for g in groups if g['name'] == '経験値')
        self.assertEqual([(t['value'], t['cost'], t['clear_count']) for t in exp['tiers']],
                         [(10, 500, 0), (20, 500, 1), (30, 1000, 1), (40, 1000, 2), (50, 1000, 3)])
        discount = next(g for g in groups if g['name'] == '武器割引')
        self.assertEqual(discount['tiers'][0], {'tier': 1, 'value': 10, 'clear_count': 0, 'cost': 300})
        # A reference group name is not a save key.
        self.assertTrue(all('hash' not in g for g in groups))

    def test_raw_values_absence_and_reordered_maps_are_read_without_mutation(self):
        for value in (None, 0, 1, 2, 255, -5):
            rr = rows() + ([] if value is None else [(boons.EXP_CANDIDATE, value, True)])
            for maps in ([rr], [[(0x12345678, 9, False)], rr[::-1]]):
                f = fixture(maps, user_body=b'\x17' + bytes(14) + struct.pack('<I', 710) + bytes(1)); before = bytes(f.payload)
                state = boons.read_observation(f)
                self.assertEqual(state['exp_candidate'], value)
                self.assertEqual(state['karma_shards'], 710)
                self.assertIn('unconfirmed', boons.observation_label(value))
                self.assertEqual(bytes(f.payload), before)
        self.assertNotEqual(boons.observation_label(None), boons.observation_label(0))

    def test_sparse_duplicate_and_ambiguous_maps_do_not_report_absent_or_owned(self):
        for maps in ([[]], [[(boons.EXP_CANDIDATE, 1, False)]], [rows(), rows()],
                     [rows() + [rows()[0]]]):
            f = fixture(maps); before = bytes(f.payload)
            with self.assertRaises(boons.BoonError):
                boons.read_observation(f)
            self.assertEqual(bytes(f.payload), before)

    def test_unrecognised_player_header_is_not_read_as_karma(self):
        f = fixture([rows()])
        with patch.object(boons.core, 'user_data', return_value=-1):
            with self.assertRaises(boons.BoonError):
                boons.read_observation(f)

    def test_english_and_original_group_search(self):
        english = boons.matching_rows('  weapon discount  ')
        original = boons.matching_rows('武器割引')
        self.assertEqual(english, original)
        self.assertEqual(len(original), 3)
        self.assertEqual(len(boons.matching_rows()), 81)
        self.assertFalse(boons.matching_rows('not a boon'))


if __name__ == '__main__':
    unittest.main()
