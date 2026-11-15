"""The weapon toggle edits its own marker and never purchases or changes EXP."""
import struct
import unittest
from unittest.mock import patch

import audiences
import boons
import fefw_core as core
from test_audiences import rows, outside_map
from test_fast_travel import fixture
from test_tutorials import raw_map


def weapon_save(owner=1, disabled=None, wide=False, exp_disabled=None):
    rr = rows() + [(boons.EXP_CANDIDATE, 1, True)]
    if owner is not None: rr.append((boons.WEAPONS_PURCHASE, owner, True))
    if disabled is not None: rr.append((boons.WEAPONS_DISABLED, disabled, wide))
    if exp_disabled is not None: rr.append((boons.EXP_DISABLED, exp_disabled, True))
    return fixture([[(0x12345678, 128, False)], rr],
                   user_body=b'\x17' + bytes(14) + struct.pack('<I', 410) + bytes(1))


class WeaponBoonTest(unittest.TestCase):
    def test_repeated_toggles_preserve_other_records_encodings_and_outside_bytes(self):
        for exp_disabled in (None, 1, 0, -5):
            for wide in (False, True):
                f = weapon_save(disabled=1 if wide else None, wide=wide, exp_disabled=exp_disabled)
                original = bytes(f.payload)
                records = raw_map(f, audiences.locate(f)); outside = outside_map(f)
                g = f
                for active in (False, True, False, True):
                    g = core.SaveFile(boons.edited_weapons_active(g, active))
                    state = boons.read_observation(g)
                    self.assertEqual(state['weapons_disabled'], None if active else 1)
                    self.assertEqual(boons.weapons_state_label(state), 'On' if active else 'Off')
                    self.assertEqual(state['weapons_purchase'], 1)
                    self.assertEqual(state['karma_shards'], 410)
                    self.assertEqual(state['exp_disabled'], exp_disabled)
                    actual = raw_map(g, audiences.locate(g))
                    expected_keys = records.keys() - {boons.WEAPONS_DISABLED}
                    self.assertEqual(actual.keys() - {boons.WEAPONS_DISABLED}, expected_keys)
                    for h in expected_keys: self.assertEqual(actual[h], records[h])
                    self.assertEqual(outside_map(g), outside)
                self.assertEqual(bytes(f.payload), original)

    def test_unowned_unknown_and_invalid_requests_fail_without_mutation(self):
        cases = [weapon_save(owner=v) for v in (None, 0, 2, -1, 255)]
        cases += [weapon_save(disabled=v, wide=True) for v in (0, 2, -1, 255)]
        for f in cases:
            before = bytes(f.payload)
            self.assertEqual(boons.weapons_state_label(boons.read_observation(f)), 'Unknown / read-only')
            for active in (True, False):
                with self.assertRaises(boons.BoonError): boons.edited_weapons_active(f, active)
            self.assertEqual(bytes(f.payload), before)
        f = weapon_save(); before = bytes(f.payload)
        for active in (None, 0, 1, 'on', [], 1.0):
            with self.assertRaises(boons.BoonError): boons.edited_weapons_active(f, active)
        self.assertEqual(bytes(f.payload), before)

    def test_noops_preserve_wide_marker_and_stored_zero_is_not_absence(self):
        for disabled, active in ((None, True), (1, False)):
            f = weapon_save(disabled=disabled, wide=True)
            self.assertEqual(boons.edited_weapons_active(f, active), f.payload)
        self.assertEqual(boons.weapons_state_label(boons.read_observation(weapon_save())), 'On')
        self.assertEqual(boons.weapons_state_label(boons.read_observation(weapon_save(disabled=0))),
                         'Unknown / read-only')

    def test_wrong_parent_ambiguous_duplicate_sparse_and_unknown_header_rejected(self):
        rr = rows() + [(boons.WEAPONS_PURCHASE, 1, False)]
        for maps in ([rr, rr], [[(boons.WEAPONS_PURCHASE, 1, False)]],
                     [rr + [(boons.WEAPONS_DISABLED, 1, False)] * 2]):
            f = fixture(maps); before = bytes(f.payload)
            with self.assertRaises(boons.BoonError): boons.edited_weapons_active(f, False)
            self.assertEqual(bytes(f.payload), before)
        f = weapon_save(); before = bytes(f.payload); tree = core.SaveTree(f.payload)
        tree.nodes[tree.node_at(audiences.locate(f).start)].parent = -1
        with patch.object(audiences.core, 'SaveTree', return_value=tree):
            with self.assertRaises(boons.BoonError): boons.edited_weapons_active(f, False)
        with patch.object(boons.core, 'user_data', return_value=-1):
            with self.assertRaises(boons.BoonError): boons.edited_weapons_active(f, False)
        self.assertEqual(bytes(f.payload), before)

    def test_interleaved_exp_and_weapon_edits_remain_independent(self):
        f = weapon_save()
        f = core.SaveFile(boons.edited_weapons_active(f, False))
        f = core.SaveFile(boons.edited_exp_active(f, False))
        f = core.SaveFile(boons.edited_weapons_active(f, True))
        self.assertEqual(boons.read_observation(f)['exp_disabled'], 1)
        f = core.SaveFile(boons.edited_exp_active(f, True))
        self.assertEqual(boons.read_observation(f), boons.read_observation(weapon_save()))

