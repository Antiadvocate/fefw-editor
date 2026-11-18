"""Eshmel Part 3 chapter entry; all fixtures are synthetic."""
from pathlib import Path
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
import story_start as start
import story_files
import story_page
from test_story_part2 import fixture
from test_story import StoryHarness, box_for


class Part3Test(unittest.TestCase):
    def test_entry_anchors_and_evidence(self):
        self.assertEqual(story.sequence(1,9,3),0xe1caa5330eae18c4)
        self.assertEqual(story.sequence(2,9,3),0xe1d565330eb7b38b)
        self.assertEqual(start.chapters_for(9,3),(1,2,3,4,5,6))
        self.assertIn('pending',story_page.chapter_evidence(9,1,3))
        self.assertIn('Inferred',story_page.chapter_evidence(9,6,3))
        self.assertIn('does not perform',story_page.warning_points(9,3)[1])

    def test_six_targets_preserve_entire_user_object_except_story_fields(self):
        f=fixture(9,3);before=bytes(f.payload);old=start.normalized_blocks(f)
        dates=((1,24,8,0),(2,1,12,0),(2,16,12,0),(3,7,12,0),(4,6,12,0),(5,16,12,0))
        for chapter,date in enumerate(dates,1):
            g=core.SaveFile(start.edited(f,chapter));info=start.validate(g)
            self.assertEqual((info.route,info.part,info.chapter),(9,3,chapter))
            self.assertEqual(struct.unpack_from('<H5B',g.payload,info.header+22),(1454,*date,0))
            now=start.normalized_blocks(g)
            for key in old.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
                self.assertEqual(now[key],old[key])
            expected=bytearray(old['GameUserData']);expected[9]=chapter
            struct.pack_into('<Q',expected,85,story.sequence(chapter,9,3))
            struct.pack_into('<Q',expected,4+start.RESUME_OFFSET,start.CHECKPOINT_ID)
            self.assertEqual(now['GameUserData'],expected)
            self.assertEqual(start.edited(g,chapter),g.payload)
        self.assertEqual(bytes(f.payload),before)

    def test_wrong_route_part_target_and_resume_are_refused(self):
        for route,part in ((1,3),(2,3),(3,3),(4,3),(9,1),(9,2),(9,0)):
            with self.assertRaises(core.SaveError):start.edited(fixture(route,part),1)
        for ch in (0,7,True,'2',None):
            with self.assertRaises(core.SaveError):start.edited(fixture(9,3),ch)
        f=fixture(9,3);i=story.read(f);f.payload[i.header+21]=6
        with self.assertRaises(core.SaveError):start.edited(f,1)
        with self.assertRaises(core.SaveError):start.enter_part2(fixture(9,3))

    def test_apply_history_file_roundtrip_and_story_mirror_refusal(self):
        app=StoryHarness();app.sv=box_for(fixture(9,3));before=bytes(app.sv.payload)
        app.mirrored=True;app.apply_story_chapter(4)
        self.assertEqual(app.sv.payload,before);self.assertFalse(hasattr(app,'_undo_stack'))
        app.mirrored=False;app.apply_story_chapter(4,True)
        changed=bytes(app.sv.payload)
        self.assertNotEqual(before,changed);self.assertEqual(app.sv._pending_story_chapter,story.ChapterFileRequest(9,4,3))
        app.undo();self.assertEqual(app.sv.payload,before)
        app.redo();self.assertEqual(app.sv.payload,changed)
        with tempfile.TemporaryDirectory() as tmp:
            app.sv.path=str(Path(tmp)/'Auto')
            plan=story_files.prepare({app.sv.path:app.sv},{app.sv.path})[app.sv.path]
            self.assertEqual(Path(plan.target).name,'Chapter_Ism_3_4')
            story_files.write(plan);reopened=container.SaveFile(plan.target)
            self.assertEqual(reopened.verify(),[])
            self.assertEqual(reopened.raw[40:43],bytes((9,3,4)))
            self.assertEqual(reopened.payload,changed)
