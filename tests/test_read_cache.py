"""Cache invalidation must follow bytes, including mutations outside UI helpers."""
import struct
import unittest
from unittest.mock import patch
import fefw_core as core
import facilities
import story_start as start
from editor_advanced import AdvancedMixin
from test_story import StoryHarness


class ReadCacheTest(unittest.TestCase):
    def test_tree_reuses_snapshot_but_revalidates_direct_edits_and_replacement(self):
        f=StoryHarness(3).core_of();before=bytes(f.payload)
        a=f.tree();self.assertIs(a,f.tree());self.assertIsInstance(a.payload,bytes)
        at=f.block('GameSound').start+4;f.payload[at]^=1
        b=f.tree();self.assertIsNot(a,b);self.assertEqual(a.payload,before)
        f.payload=bytearray(before);c=f.tree();self.assertIsNot(b,c)
        self.assertEqual(c.payload,before)
        # Reusing an identity must not hide invalid object boundaries.
        struct.pack_into('<I',f.payload,0,0)
        with self.assertRaises(core.SaveError):f.tree()
        self.assertEqual(c.payload,before)
        f.payload=bytearray(before);self.assertEqual(f.tree().payload,before)
        copy=f.copy();self.assertIsNot(copy.tree(),f.tree())

    def test_flag_values_widths_and_returned_objects_never_stale_or_shared(self):
        f=StoryHarness(3).core_of();maps=core.flag_maps(f);chosen=maps[0].flags[0]
        expected=chosen.value;chosen.value=77;maps[0].flags.clear();maps.clear()
        fresh=core.flag_maps(f);chosen=fresh[0].flags[0]
        self.assertEqual(chosen.value,expected)
        with patch.object(core,'_scan_flag_maps',wraps=core._scan_flag_maps) as scan:
            core.flag_maps(f);self.assertEqual(scan.call_count,0)
            f.payload[chosen.offset]=0
            self.assertEqual(core.flag_maps(f)[0].flags[0].value,0);self.assertEqual(scan.call_count,1)
            f.payload[chosen.offset]=expected
            self.assertEqual(core.flag_maps(f)[0].flags[0].value,expected);self.assertEqual(scan.call_count,2)
        # Resizing the flag map relocates subsequent records; a copied file has
        # no inherited offset cache, and parse results match an uncached scan.
        g=core.SaveFile(facilities._edit_map(f,facilities.locate(f),{0x12345678:255}))
        self.assertEqual(core.flag_maps(g),core._scan_flag_maps(g))
        self.assertEqual(core.flag_maps(f),core._scan_flag_maps(f))

    def test_editor_core_cache_detects_pack_into_and_same_size_slice_mutations(self):
        app=StoryHarness(3);first=AdvancedMixin.core_of(app);before=bytes(app.sv.payload)
        self.assertIs(first,AdvancedMixin.core_of(app))
        at=first.block('GameSound').start+4;app.sv.payload[at:at+4]=b'abcd'
        second=AdvancedMixin.core_of(app);self.assertIsNot(first,second)
        self.assertEqual(second.payload,app.sv.payload);self.assertEqual(bytes(first.payload),before)
        struct.pack_into('<I',app.sv.payload,at,0x01020304)
        self.assertEqual(AdvancedMixin.core_of(app).payload,app.sv.payload)
        app.sv.payload[:]=before;self.assertEqual(AdvancedMixin.core_of(app).payload,before)

    def test_restart_noops_are_skipped_after_full_validation(self):
        f=StoryHarness(3).core_of();g=core.SaveFile(start.clear_restart(f))
        with patch.object(core,'replace_content',side_effect=AssertionError('empty blob rebuilt')):
            self.assertEqual(start.clear_restart(g),g.payload)
        leaf=start.restart_leaves(g)[0]
        broken=core.SaveFile(g.payload);struct.pack_into('<I',broken.payload,leaf+4,8)
        with self.assertRaises(core.SaveError):start.clear_restart(broken)
