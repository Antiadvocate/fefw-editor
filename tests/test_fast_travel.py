"""Synthetic saves exercise targeted edits and preservation, never game dumps."""
import struct
import unittest
from unittest.mock import patch

import fast_travel as ft
import fefw_core as core
from test_tutorials import raw_map, AUTO

ARENA = 0x5a48ce35
SHOPPING = 0xbb86129f
UPPER = 0x387f1e5a
STABLES = 0x2478dd30
TAVERN = 0xc1c872f8
UNKNOWN = 0xdeadbeef


def fixture(maps):
    """Maps live inside a struct group directly below GameUserData."""
    p = bytearray(4)

    def obj(body):
        at = len(p)
        p.extend(bytes(4) + body)
        p.extend(bytes((-len(p)) % 4))
        struct.pack_into('<I', p, at, len(p) + 32)
        return at

    user = len(p); p.extend(bytes(4))
    group = len(p); p.extend(bytes(4))
    members = [obj(b'\xee' * 4)]
    for entries in maps:
        body = bytearray(b'\0' + struct.pack('<H', len(entries)))
        for h, v, wide in entries:
            body += struct.pack('<I', h)
            body += b'\xff' + struct.pack('<i', v) if wide else bytes([v])
        members.append(obj(body))
    table = len(p)
    for i, at in enumerate(members): p += struct.pack('<II', 0x1000+i, at+32)
    struct.pack_into('<I', p, group, (len(members) << 24) | (table+32))
    table = len(p)
    p += struct.pack('<II', 0xabcdef01, group+32)
    struct.pack_into('<I', p, user, (1 << 24) | (table+32))
    other = obj(b'\xaa' * 24)
    table = len(p)
    p += struct.pack('<IIII', core.fnv1_32(b'GameUserData'), user+32,
                     core.fnv1_32(b'GmapSpotMgr'), other+32)
    struct.pack_into('<I', p, 0, (2 << 24) | (table+32))
    return core.SaveFile(p)


def rows():
    return [(ARENA, 1, False), (SHOPPING, 1, True), (UPPER, 1, False),
            (STABLES, 1, False), (UNKNOWN, -70000, True), (0xfaceabcd, 0, False)]


def outside_list(f):
    tree = core.SaveTree(f.payload)
    node = tree.nodes[tree.node_at(ft.locate(f).start)]
    p = bytearray(f.payload)
    for ref in tree.refs:
        struct.pack_into('<I', p, ref.at, f.u32(ref.at) & 0xff000000)
    return bytes(p[:node.start] + p[node.end:])


class FastTravelTest(unittest.TestCase):
    def test_catalog_uses_full_scoped_names_and_flags_labels(self):
        cat = ft.catalog()
        self.assertEqual(len(cat), 16)
        self.assertEqual(cat[STABLES]['name'], '拠点_FT_Hub_000_A1_ファストトラベル_厩舎前')
        self.assertEqual(cat[STABLES]['label'], 'Stables')
        self.assertNotIn(core.id_hash('ファストトラベル_厩舎前'), cat)
        names = {}; ft.apply_labels(names)
        self.assertEqual(names[STABLES]['name'], cat[STABLES]['name'])
        self.assertIn('(translated)', names[STABLES]['label'])
        names[STABLES]['name'] = 'conflicting_identity'
        before = dict(names)
        with self.assertRaises(ft.FastTravelError): ft.apply_labels(names)
        self.assertEqual(names, before)

    def test_reordered_shifted_maps_and_unscoped_decoy(self):
        decoy = [(core.id_hash('ファストトラベル_厩舎前'), 1, False)]
        for maps in ([rows()], [decoy, rows()[::-1]], [[], decoy, rows()]):
            f = fixture(maps)
            self.assertEqual(ft.read(f)[STABLES], 1)

    def test_add_remove_and_restore_preserve_every_other_record_and_block(self):
        f = fixture([[(AUTO, 2, False)], rows()]); original = bytes(f.payload)
        old = raw_map(f, ft.locate(f)); outside = outside_list(f)
        g = core.SaveFile(ft.edited(f, {STABLES: None, TAVERN: 1}))
        actual = raw_map(g, ft.locate(g))
        self.assertEqual(bytes(f.payload), original)
        self.assertNotIn(STABLES, actual)
        self.assertEqual(ft.read(g)[TAVERN], 1)
        for h in old.keys() - {STABLES}: self.assertEqual(actual[h], old[h])
        self.assertEqual(outside_list(g), outside)
        restored = core.SaveFile(ft.edited(g, {STABLES: 1, TAVERN: None}))
        self.assertEqual(raw_map(restored, ft.locate(restored)), old)
        self.assertEqual(outside_list(restored), outside)

    def test_noops_are_byte_identical_including_wide_known_flags(self):
        f = fixture([rows()])
        for edits in ({}, {SHOPPING: 1}, {TAVERN: None}):
            self.assertEqual(ft.edited(f, edits), f.payload)
        g = core.SaveFile(ft.edited(f, {TAVERN: 1}))
        self.assertTrue(next(r for r in ft.locate(g).flags if r.hash == SHOPPING).wide)

    def test_unknown_states_and_invalid_requests_fail_atomically(self):
        for value in (0, 2, 255, -1, 1000):
            data = [(h, value if h == STABLES else v, True if h == STABLES else w)
                    for h, v, w in rows()]
            f = fixture([data]); original = bytes(f.payload)
            self.assertIn('Unknown', ft.state_label(ft.read(f)[STABLES]))
            for edit in (None, 1):
                with self.assertRaises(ft.FastTravelError):
                    ft.edited(f, {TAVERN: 1, STABLES: edit})
            self.assertEqual(bytes(f.payload), original)
        f = fixture([rows()])
        for edits in ({STABLES: 0}, {STABLES: 2}, {STABLES: True}, {STABLES: 1.0},
                      {UNKNOWN: 1}, {UNKNOWN: None}):
            with self.assertRaises(ft.FastTravelError): ft.edited(f, edits)

    def test_ambiguous_missing_duplicate_sparse_and_last_anchors_rejected(self):
        for maps in ([], [[]], [rows()[:2]], [rows(), rows()],
                     [rows(), [(TAVERN, 1, False)]], [rows()+[rows()[0]]]):
            with self.subTest(maps=maps), self.assertRaises(ft.FastTravelError):
                ft.edited(fixture(maps), {TAVERN: 1})
        with self.assertRaises(ft.FastTravelError):
            ft.edited(fixture([rows()]), {ARENA: None, STABLES: None})

    def test_map_outside_live_flag_group_is_rejected(self):
        f = fixture([rows()]); tree = core.SaveTree(f.payload)
        tree.nodes[tree.node_at(ft.locate(f).start)].parent = -1
        with patch.object(ft.core, 'SaveTree', return_value=tree):
            with self.assertRaises(ft.FastTravelError): ft.read(f)

    def test_absent_is_distinct_from_zero(self):
        self.assertEqual(ft.state_label(None), 'Absent')
        self.assertEqual(ft.state_label(1), 'Available (1)')
        self.assertIn('Unknown', ft.state_label(0))
