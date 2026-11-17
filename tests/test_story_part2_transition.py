"""Bounded Cai part conversion and the tested Chapter 5 access repair."""
from pathlib import Path
import os
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import facilities
import story
import story_start as start
import story_files
from test_story import StoryHarness, box_for
from test_story_part2 import fixture


class Part2TransitionTest(unittest.TestCase):
    def test_conversion_preserves_user_data_and_other_objects(self):
        f=fixture(part=1);before=bytes(f.payload);old=start.normalized_blocks(f)
        g=core.SaveFile(start.enter_cai_part2(f));i=start.validate(g)
        self.assertEqual((i.route,i.part,i.chapter,i.sequence),(1,2,1,0x3338b2abbb8cfa25))
        new=start.normalized_blocks(g)
        for key in old.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
            self.assertEqual(old[key],new[key])
        a,b=old['GameUserData'],new['GameUserData']
        allowed={8,9,*range(62,70),*range(85,93)}
        self.assertEqual(len(a),len(b))
        self.assertTrue(all(x==y or k in allowed for k,(x,y) in enumerate(zip(a,b))))
        self.assertEqual(f.payload,before)
        for other in (fixture(),fixture(route=4,part=1)):
            with self.assertRaises(core.SaveError):start.enter_cai_part2(other)
        f.payload[i.header+20:i.header+22]=b'\x12\x08'
        with self.assertRaises(core.SaveError):start.enter_cai_part2(f)

    def test_opt_in_is_required_and_only_cai_part_one_two_allowed(self):
        original=fixture(part=1);box=box_for(original)
        converted=core.SaveFile(start.enter_cai_part2(original));i=story.read(converted)
        with self.assertRaises(core.SaveError):story.check_outer(box.raw,i)
        story.check_outer(box.raw,i,allow_cai_part_change=True)
        for at,value in ((40,4),(41,3),(36,14)):
            raw=bytearray(box.raw);raw[at]=value
            with self.assertRaises(core.SaveError):story.check_outer(raw,i,allow_cai_part_change=True)

    def test_ui_save_undo_redo_keeps_outer_part_consistent_and_slot_isolated(self):
        a=StoryHarness(1);a.sv=box_for(fixture(part=1));original=bytes(a.sv.payload)
        raw=bytes(a.sv.raw)
        a.apply_cai_part2_entry();converted=bytes(a.sv.payload)
        self.assertNotEqual(original,converted);self.assertEqual(a.sv.raw,raw)
        self.assertTrue(a.sv._allow_cai_part_transition)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Auto';a.sv.path=str(path)
            for part,action in ((2,None),(1,a.undo),(2,a.redo)):
                if action:action()
                a.sv.save(backup=False)
                reopened=container.SaveFile(path);i=story.read(core.SaveFile(reopened.payload))
                self.assertEqual(reopened.verify(),[])
                self.assertEqual((i.part,reopened.raw[41]),(part,part))
                self.assertTrue(a._story_ready())
            a.apply_story_chapter(2,True)
            plan=story_files.prepare({str(path):a.sv},{str(path)})[str(path)]
            self.assertEqual(Path(plan.target).name,'Chapter_Kai_2_2')
        other=StoryHarness(1).sv;a.sv=other;a.undo();a.redo()
        self.assertFalse(getattr(other,'_allow_cai_part_transition',False))

    def test_chapter5_repair_changes_only_the_upper_restriction(self):
        f=core.SaveFile(start.edited(fixture(),5))
        f=core.SaveFile(facilities.edited(f,{start.PART2_UPPER_MOVEMENT:False}))
        low=core.id_hash('行動範囲制限_下層')
        f=core.SaveFile(facilities.edited(f,{low:False}))
        expected=facilities.edited(f,{start.PART2_UPPER_MOVEMENT:True})
        repaired=start.repair_cai_part2_chapter5(f)
        self.assertEqual(repaired,expected)
        fm=facilities.locate_member(core.SaveFile(repaired),facilities.PROGRESSION_MEMBER)
        values={v.hash:v.value for v in fm.flags}
        self.assertNotIn(start.PART2_UPPER_MOVEMENT,values)
        self.assertEqual(values[low],1)
        self.assertEqual(start.repair_cai_part2_chapter5(core.SaveFile(repaired)),repaired)
        with self.assertRaises(core.SaveError):start.repair_cai_part2_chapter5(fixture())


@unittest.skipUnless(os.environ.get('FEFW_PART2_RETURN_DIR'),'No private Part 2 returns supplied')
class Part2ReturnsTest(unittest.TestCase):
    def test_returns_cover_passed_arrivals_and_battles_and_one_blocked_arrival(self):
        root=Path(os.environ['FEFW_PART2_RETURN_DIR'])
        for chapter in range(1,7):
            folder=root/f'P2-{chapter:02d}-Chapter-{chapter:02d}'
            paths=[folder/'Auto']+([folder/'Auto-after-progress'] if chapter!=5 else [])
            for path in paths:
                box=container.SaveFile(path);f=core.SaveFile(box.payload);i=story.read(f)
                self.assertEqual(box.verify(),[])
                self.assertEqual((i.route,i.part,i.chapter),(1,2,chapter))
                self.assertEqual(f.payload[i.header+20:i.header+22],
                                 b'\x12\x05' if path.name=='Auto' else b'\x12\x02')
        box=container.SaveFile(root/'P2-05-Chapter-05/Auto');f=core.SaveFile(box.payload)
        fm=facilities.locate_member(f,facilities.PROGRESSION_MEMBER)
        self.assertEqual({v.hash:v.value for v in fm.flags}[start.PART2_UPPER_MOVEMENT],1)
        fixed=core.SaveFile(start.repair_cai_part2_chapter5(f))
        old=start.normalized_blocks(f);new=start.normalized_blocks(fixed)
        for key in old.keys()-{'GameUserData'}:self.assertEqual(old[key],new[key])
