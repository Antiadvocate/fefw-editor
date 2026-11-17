"""Exact prerequisite deltas, unrelated-record preservation and atomic guards."""
import struct
import unittest

import fefw_core as core
import facilities
import story_start
import story_prerequisites as pre
from research.dietrich_retry_kit import flag_snapshot
from test_story import StoryHarness


class PrerequisiteTest(unittest.TestCase):
    def source(self):
        f = StoryHarness(2).core_of()
        fm = pre.member_map(f, pre.PROGRESSION)
        body = b'\0' + struct.pack('<H', 3)
        body += struct.pack('<IBIBIB', 0x89dc5a51, 1, 0x8386d712, 1, 0x11223344, 7)
        return core.SaveFile(core.replace_content(f, fm.start, body))

    def test_named_deltas_preserve_all_other_flags_and_roots(self):
        f = self.source(); before = bytes(f.payload); original = flag_snapshot(f)
        expected = {
            5: {'4ad575a2:89dc5a51': None},
            6: {'4ad575a2:8386d712': None, '972fa7ee:948de8dd': [1,False],
                '972fa7ee:9402533e': [1,False], '972fa7ee:a78e9de8': [1,False]},
            7: {'4ad575a2:d2cbe499': [1,False]},
        }
        for chapter in range(1, 13):
            g = core.SaveFile(pre.edited(f, chapter)); after = flag_snapshot(g)
            delta = {k:after.get(k) for k in original.keys()|after.keys()
                     if original.get(k) != after.get(k)}
            self.assertEqual(delta, expected.get(chapter, {}))
            a,b = story_start.normalized_blocks(f),story_start.normalized_blocks(g)
            self.assertEqual(a.keys(), b.keys())
            for key in a.keys()-{'GameUserData'}: self.assertEqual(a[key], b[key])
            self.assertEqual(pre.edited(g,chapter), g.payload)
            self.assertEqual(bytes(f.payload), before)
        # Chapter 6 must keep the upper restriction set by its own introduction.
        self.assertEqual(flag_snapshot(core.SaveFile(pre.edited(f,6)))['4ad575a2:89dc5a51'], [1,False])

    def test_unknown_values_duplicate_keys_missing_map_and_route_refused(self):
        f = self.source()
        for raw in (struct.pack('<IB',0x8386d712,9),
                    struct.pack('<IBI',0x8386d712,255,1),
                    struct.pack('<IBIB',0x8386d712,1,0x8386d712,1)):
            count = 2 if len(raw)==10 else 1
            fm = pre.member_map(f,pre.PROGRESSION)
            g = core.SaveFile(core.replace_content(f,fm.start,b'\0'+struct.pack('<H',count)+raw))
            before = bytes(g.payload)
            with self.assertRaises(core.SaveError): pre.edited(g,6)
            self.assertEqual(bytes(g.payload),before)
        g = self.source(); tree,group,_=facilities.flag_group(g);table=g.ptr(tree.nodes[group].start)
        for i in range(g.u32(tree.nodes[group].start)>>24):
            if g.u32(table+i*8)==pre.PROGRESSION:
                struct.pack_into('<I',g.payload,table+i*8,0x12345678)
        before=bytes(g.payload)
        with self.assertRaises(core.SaveError): pre.edited(g,6)
        self.assertEqual(bytes(g.payload),before)
        with self.assertRaises(core.SaveError): pre.edited(StoryHarness(1).core_of(),7)

    def test_same_hash_in_another_map_is_not_a_prerequisite(self):
        f = self.source(); fm=facilities.locate_history(f)
        f=core.SaveFile(facilities._edit_map(f,fm,{pre.SECRET:1,pre.LOWER:1}))
        original=facilities.locate_history(f).flags
        for chapter in (6,7):
            g=core.SaveFile(pre.edited(f,chapter))
            self.assertEqual([(v.hash,v.value) for v in facilities.locate_history(g).flags],
                             [(v.hash,v.value) for v in original])
