"""Theodora repair scope, map guards and chapter-action history."""
import struct
import unittest
import facilities as fac
import fefw_core as core
import story_start as start
import story_theodora_prerequisites as pre
import worldmap
from research.dietrich_retry_kit import flag_snapshot
from test_story import StoryHarness, box_for


def fixture():
    f=StoryHarness(3).core_of();tree=f.tree();p=bytearray(4);rows=[]
    for b in f.blocks:
        at=len(p);p.extend(tree.copy_object(tree.node_at(b.start),at));rows.append((b.hash,at))
    at=len(p);p.extend(bytes(4));spots=worldmap.catalog().spots
    p.extend(b'\0'+struct.pack('<H',len(spots)))
    for i,s in enumerate(spots):
        p.extend(struct.pack('<I',s.key))
        if i==0:p.append(0)
        leaf=len(p);p.extend(struct.pack('<I',leaf+44)+bytes((2,3,1))+bytes(5))
    struct.pack_into('<I',p,at,len(p)+32);rows.append((core.fnv1_32(b'GmapSpotMgr'),at))
    table=len(p)
    for key,pos in rows:p.extend(struct.pack('<II',key,pos+32))
    struct.pack_into('<I',p,0,(len(rows)<<24)|(table+32))
    f=core.SaveFile(p)
    return core.SaveFile(fac._edit_map(f,fac.locate_member(f,fac.PROGRESSION_MEMBER),{h:1 for h in fac.MOVEMENT}))


class TheodoraPrerequisiteTest(unittest.TestCase):
    def test_exact_repairs_and_other_chapters_preserve_all_unrelated_data(self):
        f=fixture();before=bytes(f.payload);flags=flag_snapshot(f);recs=worldmap.read(f)
        for chapter in range(1,13):
            g=core.SaveFile(pre.edited(f,chapter));after=flag_snapshot(g)
            changed={k for k in flags.keys()|after.keys() if flags.get(k)!=after.get(k)}
            self.assertEqual(changed,{f'4ad575a2:{k:08x}' for k in pre.CITY.get(chapter,())})
            if chapter==9:
                allowed={recs[k].at+4 for k in pre.TROY_EXIT}
                self.assertEqual({i for i,(a,b) in enumerate(zip(f.payload,g.payload)) if a!=b},allowed)
            else:
                a,b=start.normalized_blocks(f),start.normalized_blocks(g)
                for key in a.keys()-{'GameUserData'}:self.assertEqual(a[key],b[key])
            self.assertEqual(pre.edited(g,chapter),g.payload)
        self.assertEqual(bytes(f.payload),before)

    def test_map_missing_unknown_and_wrong_route_refuse_atomically(self):
        f=fixture();r=worldmap.read(f)[pre.TROY_EXIT[0]]
        for at,value in ((r.at+4,9),(r.at+5,9)):
            g=core.SaveFile(f.payload);g.payload[at]=value;before=bytes(g.payload)
            with self.assertRaises(core.SaveError):start.edited(g,9)
            self.assertEqual(bytes(g.payload),before)
        g=core.SaveFile(f.payload)
        struct.pack_into('<I',g.payload,r.at-4,0x12345678)  # Troy is not the first map record.
        before=bytes(g.payload)
        with self.assertRaises(core.SaveError):start.edited(g,9)
        self.assertEqual(bytes(g.payload),before)
        for route in (1,2,4):
            with self.assertRaises(core.SaveError):pre.edited(StoryHarness(route).core_of(),6)
        for chapter in (0,13,True,'6'):
            with self.assertRaises(core.SaveError):pre.edited(f,chapter)
        with self.assertRaises(core.SaveError):start.edited(StoryHarness(3).core_of(),9)

    def test_chapter_repairs_share_one_history_step_and_restore_on_reapply(self):
        for chapter in (4,6,8,9):
            a=StoryHarness(3);f=fixture();a.sv.payload=f.payload;a.sv.raw=box_for(f).raw;a.sv._core_cache=None
            before=bytes(a.sv.payload);a.apply_story_chapter(chapter);changed=bytes(a.sv.payload)
            self.assertNotEqual(changed,before);self.assertEqual(len(a._undo_stack),1)
            a.undo();self.assertEqual(bytes(a.sv.payload),before)
            a.redo();self.assertEqual(bytes(a.sv.payload),changed)
            a.apply_story_chapter(chapter);self.assertEqual(len(a._undo_stack),1)
            g=a.core_of()
            if chapter==9:worldmap.apply(g,{pre.TROY_EXIT[0]:(worldmap.HIDDEN,None)})
            else:g=core.SaveFile(fac.edited(g,{pre.CITY[chapter][0]:False}))
            a.sv.payload=g.payload;a.sv._core_cache=None;a.apply_story_chapter(chapter)
            self.assertEqual(bytes(a.sv.payload),changed)
