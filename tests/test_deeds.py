"""Counter edits preserve claim states, currency and every unrelated record."""
import struct
import unittest
from unittest.mock import patch

import deeds
import fefw_core as core
from test_fast_travel import fixture
from test_tutorials import raw_map

TRAIN = core.id_hash('実績_訓練回数')
FOES = core.id_hash('実績_敵撃破数')
GIFTS = core.id_hash('実績_贈り物回数')
GAMBITS = core.id_hash('実績_計略回数')
TIME = core.id_hash('実績_プレイ時間')
CLAIM = core.id_hash('実績状態_訓練を実行')
READY = core.id_hash('実績状態_訓練を実行_1')
BOON = 0x3b6429de


def rows():
    return [(TRAIN, 65, False), (FOES, 281, True), (GIFTS, 35, True),
            (TIME, 17, False), (CLAIM, 4, False), (READY, 2, True),
            (0xdeadbeef, -40000, True)]


def outside_map(f):
    tree = core.SaveTree(f.payload)
    node = tree.nodes[tree.node_at(deeds.locate(f).start)]
    p = bytearray(f.payload)
    for ref in tree.refs:
        struct.pack_into('<I', p, ref.at, f.u32(ref.at) & 0xff000000)
    return bytes(p[:node.start] + p[node.end:])


class DeedTest(unittest.TestCase):
    def test_catalog_and_english_flag_labels(self):
        cat = deeds.catalog()
        self.assertEqual(len(cat), 47)
        self.assertEqual(sum(r['editable'] for r in cat.values()), 32)
        self.assertEqual(sum(len(r['milestones']) for r in cat.values()), 350)
        self.assertEqual([(t['target'], t['reward']) for t in cat[TRAIN]['milestones']],
                         [(n, 10) for n in (10, 20, 30, 40, 50, 75, 100)])
        names = {}; deeds.apply_labels(names)
        self.assertEqual(len(names), 397)
        self.assertEqual(names[TRAIN]['name'], '実績_訓練回数')
        self.assertEqual(names[CLAIM]['name'], '実績状態_訓練を実行')
        self.assertIn('Training sessions', names[CLAIM]['label'])
        names[CLAIM]['name'] = 'bad'; before = dict(names)
        with self.assertRaises(deeds.DeedError): deeds.apply_labels(names)
        self.assertEqual(names, before)

    def test_map_index_order_and_zero_omission_are_not_assumptions(self):
        for maps in ([rows()], [[], [(BOON, 1, False)], rows()[::-1]]):
            self.assertEqual(deeds.read(fixture(maps))[TRAIN], 65)
        f = fixture([rows()])
        self.assertEqual(deeds.edited(f, GAMBITS, 0), f.payload)
        g = core.SaveFile(deeds.edited(f, GAMBITS, 1))
        self.assertEqual(deeds.read(g)[GAMBITS], 1)
        self.assertEqual(outside_map(f), outside_map(g))

    def test_one_counter_changes_with_claims_and_currency_untouched(self):
        f = fixture([[(BOON, 1, False), (0x12345678, 710, True)], rows()])
        original = bytes(f.payload); before = raw_map(f, deeds.locate(f))
        for h, value in ((TRAIN, 75), (TRAIN, 0), (FOES, 1000), (GIFTS, 40), (GAMBITS, 300)):
            g = core.SaveFile(deeds.edited(f, h, value))
            self.assertEqual(outside_map(g), outside_map(f))
            after = raw_map(g, deeds.locate(g))
            for k in before.keys() - {h}: self.assertEqual(after[k], before[k])
            self.assertEqual(deeds.read(g)[h], value)
            self.assertEqual(deeds.read(g)[CLAIM], 4)
            self.assertEqual(deeds.read(g)[READY], 2)
        self.assertEqual(bytes(f.payload), original)

    def test_short_wide_boundary_and_existing_wide_encoding(self):
        f = fixture([[(h, 254, False) if h == FOES else (h, v, w) for h, v, w in rows()]])
        g = core.SaveFile(deeds.edited(f, FOES, 255))
        self.assertTrue(next(x for x in deeds.locate(g).flags if x.hash == FOES).wide)
        back = core.SaveFile(deeds.edited(g, FOES, 1))
        self.assertTrue(next(x for x in deeds.locate(back).flags if x.hash == FOES).wide)
        self.assertEqual(deeds.edited(g, FOES, 255), g.payload)
        self.assertEqual(outside_map(f), outside_map(g))

    def test_invalid_readonly_unknown_claim_and_negative_progress_fail_atomically(self):
        f = fixture([rows()]); before = bytes(f.payload)
        for h, value in ((TRAIN, -1), (TRAIN, 101), (TRAIN, True), (TRAIN, 1.5),
                         (TRAIN, '75'), (TIME, 18), (CLAIM, 2), (0xdeadbeef, 1)):
            with self.subTest(h=h, value=value), self.assertRaises(deeds.DeedError):
                deeds.edited(f, h, value)
        self.assertEqual(bytes(f.payload), before)
        for data in ([ (h, 1 if h == CLAIM else v, w) for h, v, w in rows()],
                     [(h, -1, True) if h == TRAIN else (h, v, w) for h, v, w in rows()]):
            g = fixture([data])
            with self.assertRaises(deeds.DeedError): deeds.edited(g, TRAIN, 75)
        high = fixture([[(h, 1001, True) if h == FOES else (h, v, w) for h, v, w in rows()]])
        self.assertEqual(deeds.edited(high, FOES, 1001), high.payload)
        with self.assertRaises(deeds.DeedError): deeds.edited(high, FOES, 1002)
        self.assertEqual(deeds.read(core.SaveFile(deeds.edited(high, FOES, 999)))[FOES], 999)

    def test_missing_ambiguous_duplicate_and_invalid_ancestry_rejected(self):
        for maps in ([], [[]], [rows()[:2]], [rows(), rows()],
                     [rows(), [(CLAIM, 4, False)]], [rows() + [rows()[0]]]):
            with self.subTest(maps=maps), self.assertRaises(deeds.DeedError): deeds.read(fixture(maps))
        f = fixture([rows()]); tree = core.SaveTree(f.payload)
        tree.nodes[tree.node_at(deeds.locate(f).start)].parent = -1
        with patch.object(deeds.core, 'SaveTree', return_value=tree):
            with self.assertRaises(deeds.DeedError): deeds.read(f)

    def test_state_labels_do_not_infer_claims_from_progress(self):
        self.assertEqual(deeds.claim_label(None), 'Not stored')
        self.assertEqual(deeds.claim_label(2), 'Complete, unclaimed (2)')
        self.assertEqual(deeds.claim_label(4), 'Claimed (4)')
        for v in (0, 1, 3, 5, -1): self.assertIn('Unknown', deeds.claim_label(v))
