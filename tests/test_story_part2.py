"""Provisional Cai Part 2: part isolation, save mirrors and preservation."""
from pathlib import Path
import os
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
import story_start as start
import story_files
import story_page
from test_story import StoryHarness, box_for
from test_story_resume_probe import fixture as original_fixture


def fixture(route=1, part=2):
    f = original_fixture()
    i = story.read(f)
    for at in (i.header+12, i.user+3):
        f.payload[at:at+3] = bytes((route, part, 1))
    for at in (i.header+45, i.user+81):
        struct.pack_into('<Q', f.payload, at, 0xdca84ca7d2796ea4)
    return f


class Part2Test(unittest.TestCase):
    def test_observed_anchor_names_and_provisional_evidence(self):
        self.assertEqual(story.sequence(1, 1, 2), 0x3338b2abbb8cfa25)
        self.assertEqual(story.chapter_filename(1, 1, 2), 'Chapter_Kai_2_1')
        self.assertEqual(story.chapter_filename(1, 1), 'Chapter_Kai_1_1')
        self.assertIn('provisional', story_page.warning_points(1, 2)[0])
        self.assertIn('replay untested', story_page.chapter_evidence(1, 1, 2))
        self.assertIn('Inferred', story_page.chapter_evidence(1, 6, 2))

    def test_all_targets_preserve_unrelated_roots_and_all_flags(self):
        f = fixture(); before = bytes(f.payload)
        old = start.normalized_blocks(f)
        dates = ((1,1,12,0),(2,1,12,0),(3,1,12,0),(4,3,12,0),(4,30,9,30),(4,30,12,0))
        for chapter, date in enumerate(dates, 1):
            g = core.SaveFile(start.edited(f, chapter)); i = start.validate(g)
            self.assertEqual((i.route, i.part, i.chapter), (1,2,chapter))
            self.assertEqual(struct.unpack_from('<H5B', g.payload, i.header+22), (1450,*date,0))
            now = start.normalized_blocks(g)
            for name in old.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
                self.assertEqual(old[name], now[name])
            # Validate the complete user object except the three intended fields.
            expected = bytearray(old['GameUserData']); expected[9] = chapter
            struct.pack_into('<Q', expected, 85, story.sequence(chapter,1,2))
            struct.pack_into('<Q', expected, 4+start.RESUME_OFFSET, start.CHECKPOINT_ID)
            self.assertEqual(expected, now['GameUserData'])
            self.assertEqual(start.edited(g,chapter), g.payload)
        self.assertEqual(f.payload, before)

    def test_unsupported_routes_contexts_and_targets_refused(self):
        for route, part in ((2,2),(3,2),(4,2),(9,2),(1,3)):
            with self.assertRaises(core.SaveError): start.edited(fixture(route,part),1)
        for value in (0,7,True,'1',None):
            with self.assertRaises(core.SaveError): start.edited(fixture(),value)
        f=fixture(); i=story.read(f); f.payload[i.header+21]=2
        with self.assertRaises(core.SaveError): start.edited(f,1)
        for part in (0,3,True,'2'):
            with self.assertRaises(core.SaveError): story.sequence(1,1,part)

    def test_roundtrip_and_pending_files_are_part_bound(self):
        box=box_for(fixture()); original=bytes(box.payload)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Auto';box.path=str(path)
            for payload in (start.edited(fixture(),5),original):
                box.payload=bytearray(payload);path.write_bytes(box.to_bytes())
                reopened=container.SaveFile(str(path));i=story.read(core.SaveFile(reopened.payload))
                self.assertEqual(reopened.verify(),[])
                self.assertEqual(reopened.raw[40:43],bytes((1,2,i.chapter)))
                self.assertEqual(reopened.raw[48:57],reopened.payload[i.header+20:i.header+29])
                self.assertEqual(struct.unpack_from('<Q',reopened.raw,73)[0],i.sequence)
            box.payload=start.edited(fixture(),1)
            box._pending_story_chapter=story.ChapterFileRequest(1,1,2)
            plans=story_files.prepare({str(path):box},{str(path)})
            self.assertEqual(Path(plans[str(path)].target).name,'Chapter_Kai_2_1')
            box._pending_story_chapter=story.ChapterFileRequest(1,1,1)
            with self.assertRaises(core.SaveError): story_files.prepare({str(path):box},{str(path)})

    def test_ui_apply_undo_redo_and_part_swap_during_warning(self):
        a=StoryHarness(1);a.sv=box_for(fixture());before=bytes(a.sv.payload)
        a.apply_story_chapter(5,True)
        self.assertEqual(a.sv._pending_story_chapter,story.ChapterFileRequest(1,5,2))
        after=bytes(a.sv.payload)
        a.undo();self.assertEqual(a.sv.payload,before)
        a.redo();self.assertEqual(a.sv.payload,after)
        a=StoryHarness(1)
        def swap():
            box=box_for(fixture());a.sv.payload=box.payload;a.sv.raw=box.raw
            return True
        a._confirm_story_warning=swap
        a.open_story_progression()
        self.assertIn('part changed',a.messages[-1][0])
        self.assertFalse(hasattr(a,'_undo_stack'))


@unittest.skipUnless(os.environ.get('FEFW_PART2_SOURCE_DIR'),'No private Part 2 captures supplied')
class Part2PrivateTest(unittest.TestCase):
    def test_real_arrival_and_checkpoint_preservation_and_serialization(self):
        root=Path(os.environ['FEFW_PART2_SOURCE_DIR'])
        for name in ('Auto-Cai-Part-2','Chapter_Kai_2_1'):
            source=container.SaveFile(str(root/name));f=core.SaveFile(source.payload)
            self.assertEqual(source.verify(),[])
            for chapter in story.PART2_CHAPTERS:
                box=container.SaveFile(str(root/name));box.payload=start.edited(f,chapter)
                with tempfile.TemporaryDirectory() as tmp:
                    path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes())
                    reopened=container.SaveFile(str(path));g=core.SaveFile(reopened.payload)
                    self.assertEqual(reopened.verify(),[])
                    self.assertEqual((story.read(g).part,story.read(g).chapter),(2,chapter))
                    self.assertEqual(start.edited(g,chapter),g.payload)
                    old=start.normalized_blocks(f);new=start.normalized_blocks(g)
                    for key in old.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
                        self.assertEqual(old[key],new[key])
