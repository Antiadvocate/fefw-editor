"""Observed EXP toggles preserve ownership, currency and unrelated save data."""
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


class BoonEditingTest(unittest.TestCase):
    @staticmethod
    def save(owner=1, disabled=None, wide=False):
        rr = rows() + [(boons.WEAPONS_PURCHASE, 1, True)]
        if owner is not None: rr.append((boons.EXP_CANDIDATE, owner, True))
        if disabled is not None: rr.append((boons.EXP_DISABLED, disabled, wide))
        return fixture([[(0x12345678, 9, False)], rr],
                       user_body=b'\x17' + bytes(14) + struct.pack('<I', 710) + bytes(1))

    def test_off_on_preserves_every_other_record_currency_and_outside_bytes(self):
        import audiences
        import fefw_core as core
        from test_audiences import outside_map
        from test_tutorials import raw_map
        for wide in (False, True):
            f = self.save(disabled=1 if wide else None, wide=wide)
            initial = f; original = bytes(f.payload)
            records = raw_map(f, audiences.locate(f)); outside = outside_map(f)
            for active in (False, True, False, True):
                g = core.SaveFile(boons.edited_exp_active(f, active))
                state = boons.read_observation(g)
                self.assertEqual(state['exp_disabled'], None if active else 1)
                self.assertEqual(boons.exp_state_label(state), 'On' if active else 'Off')
                self.assertEqual(state['exp_candidate'], 1)
                self.assertEqual(state['karma_shards'], 710)
                actual = raw_map(g, audiences.locate(g))
                for h in records.keys() - {boons.EXP_DISABLED}:
                    self.assertEqual(actual[h], records[h])
                self.assertEqual(outside_map(g), outside)
                f = g
            self.assertEqual(bytes(initial.payload), original)

    def test_unknown_states_and_invalid_requests_rejected_without_mutation(self):
        for owner in (None, 0, 2, 5, 255, -1):
            for disabled in (None, 1):
                f = self.save(owner, disabled); original = bytes(f.payload)
                self.assertIn('read-only', boons.exp_state_label(boons.read_observation(f)))
                for active in (False, True):
                    with self.assertRaises(boons.BoonError): boons.edited_exp_active(f, active)
                self.assertEqual(bytes(f.payload), original)
        for disabled in (0, 2, -1, 255):
            f = self.save(disabled=disabled, wide=True); original = bytes(f.payload)
            for active in (False, True):
                with self.assertRaises(boons.BoonError): boons.edited_exp_active(f, active)
            self.assertEqual(bytes(f.payload), original)
        f = self.save(); original = bytes(f.payload)
        for active in (None, 0, 1, 'on', [], 1.0):
            with self.assertRaises(boons.BoonError): boons.edited_exp_active(f, active)
        self.assertEqual(bytes(f.payload), original)

    def test_noops_preserve_wide_encodings_and_raw_zero_is_not_absence(self):
        for disabled, active in ((None, True), (1, False)):
            f = self.save(disabled=disabled, wide=True)
            self.assertEqual(boons.edited_exp_active(f, active), f.payload)
        absent = boons.read_observation(self.save())
        zero = boons.read_observation(self.save(disabled=0))
        self.assertEqual(boons.exp_state_label(absent), 'On')
        self.assertEqual(boons.exp_state_label(zero), 'Unknown / read-only')

    def test_ambiguous_sparse_duplicate_and_wrong_parent_maps_reject_edits(self):
        import audiences
        import fefw_core as core
        rr = rows() + [(boons.EXP_CANDIDATE, 1, False)]
        for maps in ([rr, rr], [[(boons.EXP_CANDIDATE, 1, False)]],
                     [rr + [(boons.EXP_DISABLED, 1, False)] * 2]):
            f = fixture(maps); original = bytes(f.payload)
            with self.assertRaises(boons.BoonError): boons.edited_exp_active(f, False)
            self.assertEqual(bytes(f.payload), original)
        f = self.save(); tree = core.SaveTree(f.payload)
        tree.nodes[tree.node_at(audiences.locate(f).start)].parent = -1
        with patch.object(core.SaveFile, 'tree', return_value=tree):
            with self.assertRaises(boons.BoonError): boons.edited_exp_active(f, False)
        with patch.object(boons.core, 'user_data', return_value=-1):
            with self.assertRaises(boons.BoonError): boons.edited_exp_active(f, False)

    def test_confirmed_names_are_searchable_without_losing_descriptive_or_japanese_names(self):
        self.assertEqual(boons.matching_rows('Increased Exp'), boons.matching_rows('経験値'))
        self.assertEqual(boons.matching_rows('Weapons Discount'), boons.matching_rows('武器割引'))
        self.assertEqual(boons.matching_rows('weapon discount'), boons.matching_rows('武器割引'))
        self.assertEqual(boons.display_name(boons.matching_rows('経験値')[0][1]), 'Increased Exp')


if __name__ == '__main__':
    unittest.main()
