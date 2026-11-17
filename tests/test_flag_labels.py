"""Known English labels survive regeneration and occupy the correct UI columns."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import boons
import deeds
import editor_advanced as advanced
import flag_labels
import fefw_core as core
from test_fast_travel import fixture


class FlagLabelsTest(unittest.TestCase):
    def test_shipped_dictionary_and_runtime_share_all_known_labels(self):
        raw = json.loads((Path(__file__).resolve().parents[1] / 'flag_names.json').read_text(encoding='utf8'))
        names = {int(h, 16): row for h, row in raw.items()}
        original = dict(names)
        flag_labels.apply_labels(names)
        self.assertEqual(names, original)
        self.assertEqual(advanced.flag_names(), names)
        for h, row in deeds.catalog().items():
            self.assertEqual(names[h]['name'], row['name'])
            self.assertTrue(names[h]['label'].startswith('Deed progress: '))
            for tier in row['milestones']:
                self.assertEqual(names[int(tier['hash'], 16)]['name'], tier['name'])
        for h, (key, label) in flag_labels.KNOWN_FLAGS.items():
            self.assertEqual(core.id_hash(key), h)
            self.assertEqual((names[h]['name'], names[h]['label']), (key, label))

    def test_boon_labels_use_actual_skill_aliases_and_do_not_invent_off_names(self):
        names = {}; boons.apply_labels(names)
        self.assertEqual(len(names), 62)
        for group in boons.catalog():
            level, off = boons.group_keys(group['name'])
            self.assertEqual(core.id_hash(names[level]['name']), level)
            self.assertTrue(names[level]['label'].startswith('Boon tier: '))
            self.assertEqual(names[off]['name'], '')
            self.assertTrue(names[off]['label'].startswith('Boon disabled: '))
        self.assertEqual(names[0x45409cb9]['name'], '因果報酬_レベル_技能経験格')
        bad = {0x45409cb9: {'name': 'wrong'}}; original = dict(bad)
        with self.assertRaises(boons.BoonError): boons.apply_labels(bad)
        self.assertEqual(bad, original)
        with patch('deeds.apply_labels', side_effect=deeds.DeedError('bad catalogue')):
            fallback = {}; flag_labels.apply_labels(fallback, strict=False)
        self.assertIn(boons.EXP_CANDIDATE, fallback)

    def test_flags_search_displays_english_name_and_exact_original_key(self):
        f = fixture([[(0xeb92a0f6, 20, False), (0x45409cb9, 1, False),
                      (0x79b46b58, 1, False), (0xdeadbeef, 1, False)]])
        output = []
        tree = SimpleNamespace(get_children=lambda: (), delete=lambda *a: output.clear(),
                               insert=lambda *a, **kw: output.append(kw) or str(len(output)),
                               tag_configure=lambda *a, **kw: None)
        app = SimpleNamespace(flag_tree=tree, core_of=lambda: f, flag_filter='', p={'muted': 'gray'},
                              flag_count=SimpleNamespace(configure=lambda **kw: None))
        for query in ('Hours played', '実績_プレイ時間', 'eb92a0f6'):
            app.flag_search = SimpleNamespace(get=lambda: query)
            advanced.AdvancedMixin.refresh_flags(app)
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0]['text'], 'Deed progress: Hours played')
            self.assertEqual(output[0]['values'][0], '実績_プレイ時間')
        app.flag_search = SimpleNamespace(get=lambda: '79b46b58')
        advanced.AdvancedMixin.refresh_flags(app)
        self.assertTrue(output[0]['text'].startswith('Boon disabled: '))
        self.assertEqual(output[0]['values'][0], '')
        app.flag_search = SimpleNamespace(get=lambda: 'deadbeef')
        advanced.AdvancedMixin.refresh_flags(app)
        self.assertEqual(output[0]['text'], 'unknown 0xdeadbeef')
