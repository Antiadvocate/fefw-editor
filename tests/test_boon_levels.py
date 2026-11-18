"""General Boon edits preserve unrelated state and reject ambiguous requests."""
import unittest
from unittest.mock import patch

import audiences
import boons
import fefw_core as core
from test_audiences import outside_map, rows
from test_fast_travel import fixture
from test_tutorials import raw_map
from test_weapon_boon import weapon_save
from test_boon_page import BoonHarness


class BoonLevelTest(unittest.TestCase):
    def test_key_pattern_matches_independent_captures_and_has_no_collisions(self):
        self.assertEqual(boons.group_keys('経験値'), (boons.EXP_CANDIDATE, boons.EXP_DISABLED))
        self.assertEqual(boons.group_keys('武器割引'), (boons.WEAPONS_PURCHASE, boons.WEAPONS_DISABLED))
        keys = [h for g in boons.catalog() for h in boons.group_keys(g['name'])]
        self.assertEqual(len(keys), 62)
        self.assertEqual(len(set(keys)), 62)
        self.assertFalse(set(keys) & audiences.ANCHORS)
        with self.assertRaises(boons.BoonError): boons.group_keys('unknown')

    def test_all_81_tiers_toggle_and_remove_without_other_changes(self):
        source = weapon_save(exp_disabled=1)
        original = bytes(source.payload)
        records = raw_map(source, audiences.locate(source))
        outside = outside_map(source)
        for group in boons.catalog():
            name = group['name']; keys = set(boons.group_keys(name))
            for tier in group['tiers']:
                with self.subTest(name=name, tier=tier['tier']):
                    f = core.SaveFile(boons.edited_groups(source, levels={name: tier['tier']}))
                    initial_disabled = boons.read_state(source)['groups'][name]['disabled']
                    self.assertEqual(boons.read_state(f)['groups'][name],
                                     {'level': tier['tier'], 'disabled': initial_disabled})
                    for active in (False, True):
                        f = core.SaveFile(boons.edited_groups(f, active={name: active}))
                        state = boons.read_state(f)['groups'][name]
                        self.assertEqual(state, {'level': tier['tier'], 'disabled': None if active else 1})
                        self.assertEqual(boons.row_state(group, tier, state), 'On' if active else 'Off')
                    f = core.SaveFile(boons.edited_groups(f, levels={name: 0}))
                    self.assertIsNone(boons.read_state(f)['groups'][name]['level'])
                    actual = raw_map(f, audiences.locate(f))
                    self.assertEqual({h: v for h, v in actual.items() if h not in keys},
                                     {h: v for h, v in records.items() if h not in keys})
                    self.assertEqual(outside_map(f), outside)
                    self.assertEqual(boons.read_state(f)['karma_shards'], 410)
        self.assertEqual(bytes(source.payload), original)

    def test_bulk_max_is_atomic_and_preserves_switches_and_unknown_other_records(self):
        source = weapon_save(exp_disabled=1)
        before = raw_map(source, audiences.locate(source))
        edited = core.SaveFile(boons.edited_groups(source, levels=boons.max_levels()))
        state = boons.read_state(edited)
        self.assertEqual({n: s['level'] for n, s in state['groups'].items()}, boons.max_levels())
        self.assertEqual(state['groups']['経験値']['disabled'], 1)
        self.assertIsNone(state['groups']['武器割引']['disabled'])
        after = raw_map(edited, audiences.locate(edited))
        level_keys = {boons.group_keys(n)[0] for n in boons.max_levels()}
        self.assertEqual({h: v for h, v in before.items() if h not in level_keys},
                         {h: v for h, v in after.items() if h not in level_keys})
        self.assertEqual(outside_map(edited), outside_map(source))
        self.assertEqual(boons.edited_groups(edited, levels=boons.max_levels()), edited.payload)
        # Removal preserves the independent Off marker for a later re-add.
        removed = core.SaveFile(boons.edited_groups(edited, levels={'経験値': 0}))
        self.assertEqual(boons.read_state(removed)['groups']['経験値'], {'level': None, 'disabled': 1})

    def test_invalid_or_unknown_batch_never_partially_changes_a_save(self):
        f = weapon_save(); before = bytes(f.payload)
        bad = ({'経験値': 6}, {'経験値': -1}, {'経験値': True}, {'経験値': 1.0},
               {'not a boon': 1}, {'経験値': 2, '武器割引': 4})
        for levels in bad:
            with self.assertRaises(boons.BoonError): boons.edited_groups(f, levels=levels)
        for active in ({'経験値': 1}, {'経験値': 'On'}, {'unknown': True}, {'道具割引': True}):
            with self.assertRaises(boons.BoonError): boons.edited_groups(f, active=active)
        with self.assertRaises(boons.BoonError):
            boons.edited_groups(f, levels={'経験値': 0}, active={'経験値': True})
        self.assertEqual(bytes(f.payload), before)
        for bad_save in (weapon_save(owner=99), weapon_save(disabled=0), weapon_save(disabled=-1, wide=True)):
            before = bytes(bad_save.payload)
            with self.assertRaises(boons.BoonError): boons.edited_groups(bad_save, levels=boons.max_levels())
            self.assertEqual(bytes(bad_save.payload), before)
            # Unrelated valid group remains editable without normalizing the unknown record.
            g = core.SaveFile(boons.edited_groups(bad_save, levels={'道具割引': 2}))
            self.assertEqual(boons.read_observation(g), boons.read_observation(bad_save))

    def test_wide_encodings_zero_noops_and_request_order(self):
        f = weapon_save(owner=2, disabled=1, wide=True)
        self.assertEqual(boons.edited_groups(f, levels={'武器割引': 2}, active={'武器割引': False}), f.payload)
        g = core.SaveFile(boons.edited_groups(f, levels={'武器割引': 3}))
        marker = next(fl for fl in audiences.locate(g).flags if fl.hash == boons.WEAPONS_PURCHASE)
        self.assertTrue(marker.wide); self.assertEqual(marker.value, 3)
        zero = weapon_save(owner=0)
        self.assertEqual(boons.edited_groups(zero, levels={'武器割引': 0}), zero.payload)
        levels = boons.max_levels()
        self.assertEqual(boons.edited_groups(f, levels=levels),
                         boons.edited_groups(f, levels=dict(reversed(list(levels.items())))))
        both = core.SaveFile(boons.edited_groups(zero, levels={'武器割引': 2}, active={'武器割引': False}))
        self.assertEqual(boons.read_state(both)['groups']['武器割引'], {'level': 2, 'disabled': 1})

    def test_sparse_duplicate_ambiguous_parent_and_header_refused(self):
        for maps in ([[]], [rows(), rows()], [rows() + [rows()[0]]]):
            f = fixture(maps); before = bytes(f.payload)
            with self.assertRaises(boons.BoonError): boons.edited_groups(f, levels=boons.max_levels())
            self.assertEqual(bytes(f.payload), before)
        f = weapon_save(); tree = core.SaveTree(f.payload)
        tree.nodes[tree.node_at(audiences.locate(f).start)].parent = -1
        with patch.object(core.SaveFile, 'tree', return_value=tree):
            with self.assertRaises(boons.BoonError): boons.edited_groups(f, levels=boons.max_levels())
        with patch.object(boons.core, 'user_data', return_value=-1):
            with self.assertRaises(boons.BoonError): boons.edited_groups(f, levels=boons.max_levels())


class BoonLevelPageTest(unittest.TestCase):
    def test_set_remove_toggle_and_bulk_are_reversible_single_history_steps(self):
        app = BoonHarness(); original = bytes(app.sv.payload)
        app.selected = (boons.matching_rows('道具割引')[1][0],); app.refresh_boons()
        self.assertEqual(app.actions['set'], 'normal')
        app.set_boon_tier()
        self.assertEqual(boons.read_state(app.core_of())['groups']['道具割引']['level'], 2)
        app.set_boon_active(False)
        self.assertEqual(boons.read_state(app.core_of())['groups']['道具割引']['disabled'], 1)
        app.set_boon_tier(remove=True)
        self.assertIsNone(boons.read_state(app.core_of())['groups']['道具割引']['level'])
        for _ in range(3): app.undo()
        self.assertEqual(bytes(app.sv.payload), original)
        count = len(app._undo_stack); app.max_boons(); after = bytes(app.sv.payload)
        self.assertEqual(len(app._undo_stack), count + 1)
        self.assertEqual({n:s['level'] for n,s in boons.read_state(app.core_of())['groups'].items()}, boons.max_levels())
        self.assertEqual(app.actions['max'], 'disabled')
        app.undo(); self.assertEqual(bytes(app.sv.payload), original)
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        app.max_boons(); self.assertEqual(len(app._undo_stack), count + 1)

    def test_bulk_revalidates_new_payload(self):
        app = BoonHarness(); original = bytes(app.sv.payload)
        app.mirrored = False; app.sv.payload = weapon_save(owner=99).payload
        original = bytes(app.sv.payload); app.max_boons()
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.actions['max'], 'disabled')
        self.assertEqual(app.messages[-1][1], 'error')
