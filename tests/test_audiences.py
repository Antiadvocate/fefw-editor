"""Synthetic shared maps: exact identities, isolation and pointer relocation."""
import struct
import unittest
from unittest.mock import patch

import audiences as au
import fefw_core as core
from test_fast_travel import fixture, rows as travel_rows
from test_tutorials import raw_map

GODS = (0xa1e2e07e81a0a45b, 0x976774b9a9818925, 0xf4fe5a5c9aab9f81,
        0xb980ecffb61b6541, 0xbdafb8af054f07e0, 0x72fc44e0a9217c6a)
FLAGS = (0xdb6908aa, 0x19d34a8a, 0xf1a2fc34, 0x4af1cfb8, 0x067eec7d, 0xb8ccf6c9)
FORTUNA = 0xd2fdff3fa4a597ed


def rows():
    return [(0xd9941983, 1, False), (0xe268cf4c, 1, True),
            (FLAGS[0], 1, True), (FLAGS[2], 1, False), (0xdeadbeef, -70000, True)]


def outside_map(f):
    tree = core.SaveTree(f.payload)
    node = tree.nodes[tree.node_at(au.locate(f).start)]
    p = bytearray(f.payload)
    for ref in tree.refs:
        struct.pack_into('<I', p, ref.at, f.u32(ref.at) & 0xff000000)
    return bytes(p[:node.start] + p[node.end:])


class AudienceTest(unittest.TestCase):
    def test_exact_condition_keys_and_no_fortuna_flag(self):
        self.assertEqual(tuple(au.HASHES), GODS)
        self.assertEqual(tuple(au.HASHES.values()), FLAGS)
        self.assertNotIn(FORTUNA, au.KEYS)
        self.assertEqual(au.state_label(FORTUNA, {}), 'Not required')
        names = {}; au.apply_labels(names)
        self.assertEqual(names[FLAGS[0]]['name'], '共有_行動_初めてマーズと話した')
        self.assertIn('Mars', names[FLAGS[0]]['label'])
        names[FLAGS[-1]]['name'] = 'different_identity'; before = dict(names)
        with self.assertRaises(au.AudienceError): au.apply_labels(names)
        self.assertEqual(names, before)

    def test_all_six_toggle_both_directions_preserving_other_bytes(self):
        initial = fixture([travel_rows(), rows()]); original = bytes(initial.payload)
        for god, h in zip(GODS, FLAGS):
            f = initial; old = raw_map(f, au.locate(f)); outside = outside_map(f)
            for value in ((None, 1) if h in old else (1, None)):
                g = core.SaveFile(au.edited(f, {god: value}))
                self.assertEqual(au.read(g).get(h), value)
                actual = raw_map(g, au.locate(g))
                for other in old.keys() - {h}:
                    self.assertEqual(actual[other], old[other])
                self.assertEqual(outside_map(g), outside)
                f = g
            self.assertEqual(au.read(f), au.read(initial))
        self.assertEqual(bytes(initial.payload), original)

    def test_noop_keeps_wide_encoding_and_all_off_remains_identifiable(self):
        f = fixture([rows()])
        for edits in ({}, {GODS[0]: 1}, {GODS[-1]: None}):
            self.assertEqual(au.edited(f, edits), f.payload)
        off = core.SaveFile(au.edited(f, {g: None for g in GODS}))
        self.assertFalse(set(au.read(off)) & set(FLAGS))
        on = core.SaveFile(au.edited(off, {g: 1 for g in GODS}))
        self.assertTrue(all(au.read(on)[h] == 1 for h in FLAGS))

    def test_unknown_states_invalid_and_fortuna_writes_rejected_atomically(self):
        for value in (0, 2, -1, 255):
            rr = [(h, value if h == FLAGS[0] else v, True) for h, v, w in rows()]
            f = fixture([rr]); before = bytes(f.payload)
            for target in (None, 1):
                with self.assertRaises(au.AudienceError):
                    au.edited(f, {GODS[-1]: 1, GODS[0]: target})
            self.assertEqual(bytes(f.payload), before)
            self.assertIn('Unknown', au.state_label(GODS[0], au.read(f)))
        f = fixture([rows()])
        for edits in ({GODS[0]: 0}, {GODS[0]: True}, {GODS[0]: 1.0},
                      {FORTUNA: 1}, {FLAGS[0]: 1}, {True: None}):
            with self.assertRaises(au.AudienceError): au.edited(f, edits)

    def test_sparse_ambiguous_duplicate_and_wrong_parent_fail_closed(self):
        for maps in ([], [[]], [rows()[1:]], [rows(), rows()],
                     [rows()+[rows()[0]]], [rows(), [(FLAGS[-1], 1, False)]]):
            with self.subTest(maps=maps), self.assertRaises(au.AudienceError):
                au.edited(fixture(maps), {GODS[-1]: 1})
        f = fixture([rows()]); tree = core.SaveTree(f.payload)
        tree.nodes[tree.node_at(au.locate(f).start)].parent = -1
        with patch.object(core.SaveFile, 'tree', return_value=tree):
            with self.assertRaises(au.AudienceError): au.read(f)

    def test_reordered_shifted_and_unscoped_decoy_maps(self):
        decoy = [(core.id_hash('初めてマーズと話した'), 1, False)]
        for maps in ([rows()], [decoy, rows()[::-1]], [[], travel_rows(), rows()]):
            self.assertEqual(au.read(fixture(maps))[FLAGS[0]], 1)
