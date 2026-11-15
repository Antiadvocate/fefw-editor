"""Independent game-capture hashes guard against self-consistent wrong keys."""
import unittest

import audiences
import boons
import fefw_core as core
from test_audiences import outside_map
from test_tutorials import raw_map
from test_weapon_boon import weapon_save


# Literal identities from isolated game purchases/toggles, not group_keys().
CAPTURED = {
    '技能経験格闘': (0x45409cb9, 0x79b46b58, 0xad9326cb),
    '技能経験黒魔法': (0x45227c65, 0x79c9024c, 0xd440c259),
}


class BoonSkillKeyTest(unittest.TestCase):
    def test_captured_keys_read_game_records_and_switch_only_the_actual_marker(self):
        for name, (level_key, off_key, _) in CAPTURED.items():
            with self.subTest(name=name):
                f = weapon_save()
                f = core.SaveFile(core.flag_add(f, audiences.locate(f), level_key, 1))
                self.assertEqual(boons.group_keys(name), (level_key, off_key))
                self.assertEqual(boons.read_state(f)['groups'][name], {'level': 1, 'disabled': None})
                g = core.SaveFile(boons.edited_groups(f, active={name: False}))
                self.assertEqual(audiences.read(g), audiences.read(f) | {off_key: 1})
                self.assertEqual(outside_map(g), outside_map(f))
                h = core.SaveFile(boons.edited_groups(g, active={name: True}))
                self.assertEqual(audiences.read(h), audiences.read(f))

    def test_stale_test3_level_is_ignored_and_preserved_when_correct_record_is_written(self):
        for name, (level_key, off_key, wrong_key) in CAPTURED.items():
            with self.subTest(name=name):
                f = weapon_save()
                f = core.SaveFile(core.flag_add(f, audiences.locate(f), wrong_key, 3))
                before = raw_map(f, audiences.locate(f))
                self.assertEqual(boons.read_state(f)['groups'][name], {'level': None, 'disabled': None})
                g = core.SaveFile(boons.edited_groups(f, levels={name: 3}))
                self.assertEqual(audiences.read(g)[level_key], 3)
                self.assertEqual(raw_map(g, audiences.locate(g))[wrong_key], before[wrong_key])
                self.assertNotIn(off_key, audiences.read(g))
                self.assertEqual(outside_map(g), outside_map(f))
                h = core.SaveFile(boons.edited_groups(g, levels={name: 0}))
                self.assertEqual(audiences.read(h), audiences.read(f))
                self.assertIsNone(boons.read_state(h)['groups'][name]['level'])

    def test_aliases_are_scoped_and_evidence_does_not_claim_untested_gameplay(self):
        self.assertEqual(len(boons.SKILL_KEY_NAMES), 8)
        self.assertEqual(boons.evidence_label('技能経験格闘', 1), 'Save-verified')
        self.assertEqual(boons.evidence_label('技能経験黒魔法', 1), 'Save-verified')
        self.assertEqual(boons.evidence_label('技能経験格闘', 3), 'Inferred')
        self.assertEqual(boons.evidence_label('技能経験白魔法', 1), 'Inferred')
        self.assertEqual(boons.evidence_label('武器割引', 2), 'Game-tested')
        # A skill alias is not evidence for shortening unrelated long names.
        self.assertEqual(boons.group_keys('加護消費_アウロラ')[0], 0x54eb2cb2)
        self.assertEqual(core.id_hash('因果報酬_レベル_技能経験格闘'), 0xad9326cb)
