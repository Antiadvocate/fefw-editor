"""Movement restrictions are sibling-map controls, not general unlock flags."""
import struct
import tempfile
from pathlib import Path
import unittest

import facilities as fac
import fefw_core as core
import fefw_save as container
import story_start as start
from test_story import StoryHarness, box_for
from test_facility_page import FacilityHarness
from test_facilities import EXAM
from test_tutorials import raw_map


class MovementFunctionsTest(unittest.TestCase):
    def source(self):
        f=StoryHarness(3).core_of()
        return core.SaveFile(fac._edit_map(f,fac.locate_member(f,fac.PROGRESSION_MEMBER),{h:1 for h in fac.MOVEMENT}))

    def test_each_switch_both_directions_preserves_other_stores_and_roots(self):
        source=self.source();before=bytes(source.payload)
        for h in fac.MOVEMENT:
            f=source
            for state in (True,False,True):
                a=start.normalized_blocks(f);old=raw_map(f,fac.locate_member(f,fac.PROGRESSION_MEMBER))
                g=core.SaveFile(fac.edited(f,{h:state}));b=start.normalized_blocks(g)
                self.assertEqual(fac.enabled(h,fac.read(g).get(h)),state)
                self.assertEqual(fac.read(g).get(h),None if state else 1)
                for k in a.keys()-{'GameUserData'}:self.assertEqual(a[k],b[k])
                for member in (fac.GENERAL_MEMBER,fac.HISTORY_MEMBER):
                    self.assertEqual(raw_map(f,fac.locate_member(f,member)),raw_map(g,fac.locate_member(g,member)))
                new=raw_map(g,fac.locate_member(g,fac.PROGRESSION_MEMBER))
                self.assertEqual({k:v for k,v in old.items() if k!=h},{k:v for k,v in new.items() if k!=h})
                self.assertEqual(fac.edited(g,{h:state}),g.payload);f=g
        self.assertEqual(bytes(source.payload),before)

    def test_mixed_three_store_batch_history_and_roundtrip(self):
        f=self.source();app=FacilityHarness();app.sv.payload=f.payload;app.sv.raw=box_for(f).raw;app.sv._core_cache=None
        app.selected=tuple(f'{h:08x}' for h in (*fac.MOVEMENT,fac.SEWERS,EXAM))
        original=bytes(app.sv.payload);app.set_facilities(True);after=bytes(app.sv.payload)
        self.assertEqual(len(app._undo_stack),1)
        for h in fac.MOVEMENT:self.assertNotIn(h,fac.read(app.core_of()))
        self.assertEqual(fac.read(app.core_of())[EXAM],1)
        self.assertEqual(fac.read(app.core_of())[fac.SEWERS],1)
        app.undo();self.assertEqual(bytes(app.sv.payload),original)
        app.redo();self.assertEqual(bytes(app.sv.payload),after)
        with tempfile.TemporaryDirectory() as tmp:
            box=box_for(app.core_of());path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes())
            check=container.SaveFile(str(path));self.assertEqual(check.verify(),[]);self.assertEqual(check.payload,app.sv.payload)

    def test_wrong_store_unknown_encoding_and_missing_member_are_atomic(self):
        h=next(iter(fac.MOVEMENT));f=StoryHarness(3).core_of()
        f=core.SaveFile(fac._edit_map(f,fac.locate(f),{h:1}))
        self.assertNotIn(h,fac.read(f))
        g=core.SaveFile(fac.edited(f,{h:False}))
        self.assertEqual(raw_map(f,fac.locate(f)),raw_map(g,fac.locate(g)))
        self.assertEqual(fac.read(g)[h],1)
        for raw in (struct.pack('<IB',h,9),struct.pack('<IBI',h,255,1),struct.pack('<IBIB',h,1,h,1)):
            fm=fac.locate_member(f,fac.PROGRESSION_MEMBER);count=2 if len(raw)==10 else 1
            bad=core.SaveFile(core.replace_content(f,fm.start,b'\0'+struct.pack('<H',count)+raw));before=bytes(bad.payload)
            with self.assertRaises(core.SaveError):fac.edited(bad,{EXAM:True,fac.SEWERS:True,h:True})
            self.assertEqual(bytes(bad.payload),before)
        bad=core.SaveFile(f.payload);tree,group,_=fac.flag_group(bad);table=bad.ptr(tree.nodes[group].start)
        at=next(table+8*i for i in range(bad.u32(tree.nodes[group].start)>>24) if bad.u32(table+8*i)==fac.PROGRESSION_MEMBER)
        struct.pack_into('<I',bad.payload,at,0xabcdef09)
        self.assertEqual(fac.read(bad)[h],fac.UNAVAILABLE)
        before=bytes(bad.payload)
        with self.assertRaises(core.SaveError):fac.edited(bad,{EXAM:True,h:True})
        self.assertEqual(bytes(bad.payload),before)
