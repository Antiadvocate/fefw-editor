"""Synthetic tests for polarity, atomic edits, identity and raw preservation."""
import struct
import unittest
from unittest.mock import patch

import facilities as fac
import fefw_core as core
from test_fast_travel import fixture
from test_tutorials import raw_map

ARMORER = 0xb9a0e16b
ITEMS = 0x5e9748e0
EXAM = 0x0be47d8b
STABLES = 0x63fc6b22
KALLA = 0x3fdd2f30
UNKNOWN = 0xdeadbeef


def rows():
    return [(h, 1, False) for h in sorted(fac.ANCHORS)] + [
        (ARMORER, 1, True), (EXAM, 1, True), (UNKNOWN, -70000, True), (0xfaceabcd, 0, False)]


def outside(f):
    tree = core.SaveTree(f.payload); node = tree.nodes[tree.node_at(fac.locate(f).start)]
    p = bytearray(f.payload)
    for ref in tree.refs: struct.pack_into('<I', p, ref.at, f.u32(ref.at) & 0xff000000)
    return bytes(p[:node.start] + p[node.end:])


class FacilityTest(unittest.TestCase):
    def test_catalog_and_labels_preserve_original_identity(self):
        cat = fac.catalog()
        self.assertEqual(len(cat), 41)
        self.assertEqual(sum(r['polarity'] == 'restriction' for r in cat.values()), 7)
        self.assertEqual(sum(r['kind'] == 'Gate registration' for r in cat.values()), 7)
        self.assertEqual(cat[KALLA]['name'], '神殿_転移_カーラ神殿')
        self.assertNotIn(0xb482d5dc, cat)  # Ordinary Kalla travel is a different map.
        names = {}; fac.apply_labels(names)
        self.assertEqual(names[STABLES]['name'], '機能開放_厩舎')
        self.assertEqual(names[ARMORER]['label'], 'Disabled: Armorer')
        names[KALLA]['name'] = 'wrong'; before = dict(names)
        with self.assertRaises(fac.FacilityError): fac.apply_labels(names)
        self.assertEqual(names, before)

    def test_every_switch_both_directions_only_changes_selected_raw_record(self):
        for h, row in fac.catalog().items():
            if fac.member_for(h) != fac.GENERAL_MEMBER: continue  # Separate sibling-map tests.
            with self.subTest(h=f'{h:08x}'):
                f = fixture([[(0x99887766, 2, False)], rows()])
                for state in (False, True, False):
                    old = raw_map(f, fac.locate(f)); preserved = outside(f); unchanged = bytes(f.payload)
                    g = core.SaveFile(fac.edited(f, {h: state}))
                    self.assertEqual(bytes(f.payload), unchanged)
                    self.assertEqual(fac.enabled(h, fac.read(g).get(h)), state)
                    expected = (not state) if row['polarity'] == 'restriction' else state
                    self.assertEqual(fac.read(g).get(h), 1 if expected else None)
                    actual = raw_map(g, fac.locate(g))
                    self.assertEqual({k:v for k,v in old.items() if k != h}, {k:v for k,v in actual.items() if k != h})
                    self.assertEqual(outside(g), preserved)
                    self.assertEqual(fac.edited(g, {h: state}), g.payload)
                    f = g

    def test_mixed_polarity_batch_preserves_travel_and_stables(self):
        f = fixture([rows(), [(0xb482d5dc, 1, False), (0x2478dd30, 1, False)]])
        g = core.SaveFile(fac.edited(f, {ARMORER: True, ITEMS: False, EXAM: False, KALLA: True}))
        v = fac.read(g)
        self.assertNotIn(ARMORER, v); self.assertEqual(v[ITEMS], 1)
        self.assertNotIn(EXAM, v); self.assertEqual(v[KALLA], 1)
        self.assertNotIn(STABLES, v); self.assertEqual(outside(f), outside(g))
        self.assertEqual(raw_map(f, core.flag_maps(f)[1]), raw_map(g, core.flag_maps(g)[1]))

    def test_zero_and_wide_noops_preserved_and_unknown_batch_refused(self):
        for h in (EXAM, ARMORER):
            data = [(k,v,w) for k,v,w in rows() if k != h] + [(h,0,True)]
            f = fixture([data]); before = bytes(f.payload)
            self.assertEqual(fac.edited(f, {h: h == ARMORER}), before)
            g = core.SaveFile(fac.edited(f, {h: h != ARMORER}))
            self.assertEqual(fac.read(g)[h], 1)
        for value in (2,255,-1,1000):
            f = fixture([rows()+[(STABLES,value,True)]]); before = bytes(f.payload)
            for state in (True,False):
                with self.assertRaises(fac.FacilityError): fac.edited(f,{ARMORER:True,STABLES:state})
            self.assertEqual(bytes(f.payload), before)
            self.assertIn('Unknown', fac.state_label(STABLES,value))
        f=fixture([rows()])
        for edits in ({UNKNOWN:True},{EXAM:1},{EXAM:None},{EXAM:'yes'},{str(EXAM):True}):
            with self.assertRaises(fac.FacilityError): fac.edited(f,edits)
        self.assertEqual(fac.edited(f,{}),f.payload)

    def test_map_reordering_ambiguity_duplicates_sparse_and_structure(self):
        for maps in ([rows()], [[],rows()[::-1]], [[(0x99887766,1,False)],[],rows()]):
            self.assertEqual(fac.read(fixture(maps))[ARMORER],1)
        for maps in ([],[[]],[rows(),rows()],[rows(),[(KALLA,1,False)]],
                     [rows()+[rows()[0]]], [[rows()[0],(EXAM,1,False)]]):
            with self.assertRaises(fac.FacilityError): fac.edited(fixture(maps),{EXAM:False})
        f=fixture([rows()]);tree=core.SaveTree(f.payload)
        tree.nodes[tree.node_at(fac.locate(f).start)].parent=-1
        with patch.object(fac.core,'SaveTree',return_value=tree):
            with self.assertRaises(fac.FacilityError):fac.read(f)
