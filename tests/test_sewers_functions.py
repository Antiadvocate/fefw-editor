"""Sewers history identity, atomic batches and chapter-entry integration."""
from pathlib import Path
import hashlib
import os
import struct
import tempfile
import unittest

import facilities as fac
import fefw_core as core
import fefw_save as container
import story_start as start
from test_story import StoryHarness, box_for
from test_facility_page import FacilityHarness
from test_facilities import EXAM, ARMORER
from test_tutorials import raw_map


def maps(f):
    return [raw_map(f, m) for m in core.flag_maps(f)]


class SewersFunctionsTest(unittest.TestCase):
    def test_exact_identity_and_empty_history_add_remove_roundtrip(self):
        self.assertEqual(core.id_hash(fac.SEWERS_DIALOGUE), fac.SEWERS)
        f = StoryHarness(1).core_of(); original = bytes(f.payload)
        self.assertEqual(fac.locate_history(f).flags, [])
        g = core.SaveFile(fac.edited(f, {fac.SEWERS: True}))
        self.assertEqual(fac.read(g)[fac.SEWERS], 1)
        self.assertNotIn(fac.SEWERS, {v.hash for v in fac.locate(g).flags})
        self.assertEqual(fac.edited(g, {fac.SEWERS: True}), g.payload)
        restored = core.SaveFile(fac.edited(g, {fac.SEWERS: False}))
        self.assertEqual(start.normalized_blocks(restored), start.normalized_blocks(f))
        self.assertEqual(f.payload, original)

    def test_mixed_maps_preserve_wide_records_and_undo_redo(self):
        f = StoryHarness(1).core_of()
        f = core.SaveFile(core.flag_add(f, fac.locate_history(f), 0xdeadbeef, -70000))
        f = core.SaveFile(core.flag_add(f, fac.locate_history(f), fac.SEWERS, 0))
        before = raw_map(f, fac.locate_history(f)); original = bytes(f.payload)
        app = FacilityHarness();app.sv.payload=f.payload;app.sv._core_cache=None
        app.selected=tuple(f'{h:08x}' for h in (fac.SEWERS, EXAM, ARMORER))
        app.set_facilities(True); g=app.core_of()
        self.assertEqual(fac.read(g)[fac.SEWERS],1)
        self.assertEqual(fac.read(g)[EXAM],1)
        self.assertEqual(raw_map(g,fac.locate_history(g))[0xdeadbeef],before[0xdeadbeef])
        after=bytes(g.payload)
        app.undo();self.assertEqual(app.sv.payload,original)
        app.redo();self.assertEqual(app.sv.payload,after)
        app.set_facilities(False)
        self.assertNotIn(fac.SEWERS,fac.read(app.core_of()))
        self.assertEqual(fac.read(app.core_of())[ARMORER],1)

    def test_unknown_value_refuses_both_maps_and_chapter_atomically(self):
        for value in (2, -1, 1000):
            f=StoryHarness(1).core_of()
            f=core.SaveFile(core.flag_add(f,fac.locate_history(f),fac.SEWERS,value))
            original=bytes(f.payload)
            with self.assertRaises(core.SaveError):fac.edited(f,{EXAM:True,fac.SEWERS:True})
            with self.assertRaises(core.SaveError):start.edited(f,4)
            self.assertEqual(f.payload,original)

    def test_wrong_member_duplicate_keys_and_wrong_map_record_are_not_used(self):
        f=StoryHarness(1).core_of()
        g=core.SaveFile(core.flag_add(f,fac.locate(f),fac.SEWERS,1))
        self.assertNotIn(fac.SEWERS,fac.read(g))
        result=core.SaveFile(fac.edited(g,{fac.SEWERS:True}))
        self.assertEqual([v.value for v in fac.locate_history(result).flags if v.hash==fac.SEWERS],[1])
        self.assertEqual(raw_map(g,fac.locate(g)),raw_map(result,fac.locate(result)))
        tree=core.SaveTree(f.payload);node=tree.node_at(fac.locate_history(f).start)
        parent=tree.nodes[tree.nodes[node].parent];table=f.ptr(parent.start)
        row=next(table+8*i for i in range(f.u32(parent.start)>>24) if f.u32(table+8*i)==fac.HISTORY_MEMBER)
        for key in (0xdeadbeef, 0x972fa7ee):
            p=bytearray(f.payload);struct.pack_into('<I',p,row,key);bad=core.SaveFile(p)
            self.assertEqual(fac.read(bad)[fac.SEWERS],fac.UNAVAILABLE)
            with self.assertRaises(core.SaveError):fac.edited(bad,{EXAM:True,fac.SEWERS:True})
            self.assertEqual(bad.payload,p)
        history=fac.locate_history(f)
        body=b'\0'+struct.pack('<H',2)+struct.pack('<IBIB',fac.SEWERS,1,fac.SEWERS,1)
        bad=core.SaveFile(core.replace_content(f,history.start,body))
        with self.assertRaises(core.SaveError):fac.edited(bad,{fac.SEWERS:False})

    def test_all_supported_cai_chapters_enable_only_history_prerequisite(self):
        for route in (1,4):
            f=StoryHarness(route).core_of()
            for chapter in start.TARGETS[route]:
                with self.subTest(route=route,chapter=chapter):
                    base=core.SaveFile(start._edited_at_entry(f,chapter,start.ENTRY_YEARS[chapter],start.target(chapter,route)))
                    g=core.SaveFile(start.edited(f,chapter))
                    if route==1 and chapter>=3:
                        self.assertEqual(fac.read(g)[fac.SEWERS],1)
                        restored=core.SaveFile(fac.edited(g,{fac.SEWERS:False}))
                        self.assertEqual(start.normalized_blocks(restored),start.normalized_blocks(base))
                    else:self.assertEqual(g.payload,base.payload)
                    self.assertEqual(start.edited(g,chapter),g.payload)
        enabled=core.SaveFile(fac.edited(StoryHarness(1).core_of(),{fac.SEWERS:True}))
        self.assertEqual(fac.read(core.SaveFile(start.edited(enabled,2)))[fac.SEWERS],1)

    def test_manual_disable_survives_save_and_same_chapter_selection_reenables(self):
        app=StoryHarness(1);original=bytes(app.sv.payload)
        app.apply_story_chapter(3);changed=bytes(app.sv.payload)
        self.assertEqual(fac.read(app.core_of())[fac.SEWERS],1)
        app.undo();self.assertEqual(app.sv.payload,original)
        app.redo();self.assertEqual(app.sv.payload,changed)
        disabled=core.SaveFile(fac.edited(app.core_of(),{fac.SEWERS:False}))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Auto';box=box_for(disabled);path.write_bytes(box.to_bytes())
            box=container.SaveFile(str(path));box.save();reopened=container.SaveFile(str(path))
            self.assertEqual(reopened.verify(),[])
            self.assertNotIn(fac.SEWERS,fac.read(core.SaveFile(reopened.payload)))
            self.assertEqual(fac.read(core.SaveFile(start.edited(core.SaveFile(reopened.payload),3)))[fac.SEWERS],1)


@unittest.skipUnless(os.environ.get('FEFW_SEWERS_RETURN_DIR'),'No successful Sewers returns supplied')
class SewersReturnsTest(unittest.TestCase):
    def test_successful_returns_preserve_prerequisite_and_advance_resume_state(self):
        root=Path(os.environ['FEFW_SEWERS_RETURN_DIR'])
        for name,sha,mode in (
                ('Auto-arrival','fd6b7904195f0a626303f19653459b789503bf2c55de64e1daa4090c78d8309d',b'\x12\x05'),
                ('Auto-after-progress','ddefc27a2390b729336bdae1d861f1ddb199148674960664c955d49212691565',b'\x12\x06')):
            path=root/name;raw=path.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
            box=container.SaveFile(str(path));self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);h=f.block('Header').start
            self.assertEqual(f.payload[h+12:h+15],bytes((1,1,4)))
            self.assertEqual(f.payload[h+20:h+22],mode)
            self.assertEqual([v.value for m in core.flag_maps(f) for v in m.flags if v.hash==fac.SEWERS],[1])
            if name=='Auto-arrival':self.assertEqual(fac.read(f)[fac.SEWERS],1)
            else:
                # This post-progress context is unsupported by the story writer.
                with self.assertRaises(core.SaveError):start.edited(f,4)
            self.assertEqual(path.read_bytes(),raw)
