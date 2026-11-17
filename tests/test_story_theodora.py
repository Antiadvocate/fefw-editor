"""Theodora route isolation, early-year replay, preservation and private exports."""
from pathlib import Path
import os
import struct
import tempfile
import unittest
from unittest.mock import patch

import editor
import fefw_core as core
import fefw_save as container
import story
import story_start as start
import story_page
import story_files
from test_story import StoryHarness, box_for
from test_story_files import SaveHarness
from test_story_theodora_prerequisites import fixture as repaired_fixture
from research.theodora_test_kit import build, flags, SOURCES, NATIVE_CLOCKS

# Recorded independently from native checkpoints and timeline title rows.
NATIVE_IDS = (0xe51103b9b4fbaeb2, 0xe50d03b9b4f7c59d, 0xe509c3b9b4f52324)
DATES = ((2,1,12),(2,13,12),(2,4,7),(3,1,12),(3,7,20),(3,21,23),
         (4,21,5),(6,1,12),(7,1,12),(8,25,12),(9,17,12),(10,16,10))


class TheodoraStoryTest(unittest.TestCase):
    def test_native_anchors_and_reported_evidence(self):
        self.assertEqual(tuple(story.sequence(n,3) for n in range(1,4)), NATIVE_IDS)
        self.assertEqual(start.TARGETS[3], tuple(range(1,13)))
        self.assertEqual(start.TESTED_BY_ROUTE[3], frozenset(range(1,13)))
        for ch in start.TARGETS[3]:
            if ch in (4,6,8,9):self.assertIn('passed',story_page.chapter_evidence(3,ch))
            else:self.assertEqual(story_page.chapter_evidence(3,ch), 'Game-tested opening and progression')
        self.assertIn('Chapters 1–12 passed', story_page.warning_points(3)[0])
        self.assertIn('1446', story_page.warning_points(3)[1])
        self.assertIn('UI passed', story_page.evidence_note(3))
        self.assertEqual(story.chapter_filename(3,12), 'Chapter_Seo_1_12')

    def test_forward_backward_years_preserve_party_flags_roots_and_roundtrip(self):
        f = repaired_fixture(); before = bytes(f.payload)
        # Test from both sides of the year transition, independent of source year.
        sources = (f, core.SaveFile(start.edited(f,1)))
        with tempfile.TemporaryDirectory() as tmp:
            for source in sources:
                original = start.normalized_blocks(source)
                for chapter, (month,day,hour) in enumerate(DATES,1):
                    # Dietrich prerequisites must never run for Theodora.
                    with patch.object(start.story_prerequisites,'edited',side_effect=AssertionError('Dietrich prerequisite')):
                        g = core.SaveFile(start.edited(source,chapter))
                    i = start.validate(g); year = 1446 if chapter <= 2 else 1449
                    self.assertEqual((i.route,i.part,i.chapter,i.sequence),(3,1,chapter,story.sequence(chapter,3)))
                    self.assertEqual(struct.unpack_from('<H5B',g.payload,i.header+22),(year,month,day,hour,0,0))
                    self.assertEqual(flags(g),flags(core.SaveFile(start.story_theodora_prerequisites.edited(source,chapter))))
                    after = start.normalized_blocks(g)
                    for key in original.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData','GmapSpotMgr'}:
                        self.assertEqual(original[key],after[key])
                    self.assertEqual(start.edited(g,chapter),g.payload)
                    box=box_for(source);box.payload=g.payload;path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes())
                    reopened=container.SaveFile(str(path));self.assertEqual(reopened.verify(),[])
                    self.assertEqual(reopened.payload,g.payload)
                    self.assertEqual(reopened.raw[40:43],bytes((3,1,chapter)))
                    self.assertEqual(int.from_bytes(reopened.raw[73:81],'little'),i.sequence)
                    self.assertEqual(reopened.raw[48:57],g.payload[i.header+20:i.header+29])
        self.assertEqual(bytes(f.payload),before)

    def test_routes_parts_contexts_and_bad_targets_refused_without_mutation(self):
        f=StoryHarness(3).core_of();before=bytes(f.payload)
        for ch in (0,13,True,'2',None):
            with self.assertRaises(core.SaveError):start.edited(f,ch)
        for route in (1,2,4):
            with self.assertRaises(core.SaveError):story.edited(f,4,route=route)
            with self.assertRaises(core.SaveError):story.edited(StoryHarness(route).core_of(),4,route=3)
        i=story.read(f)
        for part in (0,2,3):
            g=core.SaveFile(f.payload);g.payload[i.header+13]=g.payload[i.user+4]=part
            with self.assertRaises(core.SaveError):start.edited(g,4)
        for mode in (b'\x12\x06',b'\x12\x02'):
            g=core.SaveFile(f.payload);g.payload[i.header+20:i.header+22]=mode
            with self.assertRaises(core.SaveError):start.edited(g,4)
        self.assertEqual(bytes(f.payload),before)

    def test_theodora_checkpoint_save_history_backup_and_stale_route_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=SaveHarness(tmp);path=Path(a.sv.path);box=box_for(StoryHarness(3).core_of())
            path.write_bytes(box.to_bytes());a.sv=container.SaveFile(str(path));a.files[str(path)]=a.sv
            before=bytes(a.sv.payload);target=Path(tmp)/'Chapter_Seo_1_2';target.write_bytes(path.read_bytes());old=target.read_bytes()
            other=Path(tmp)/'Chapter_Dit_1_2';other.write_bytes(b'untouched')
            a.apply_story_chapter(2,True);changed=bytes(a.sv.payload)
            self.assertEqual(target.read_bytes(),old)
            a.undo();self.assertEqual(bytes(a.sv.payload),before);self.assertIsNone(a.sv._pending_story_chapter)
            a.redo();self.assertEqual(bytes(a.sv.payload),changed)
            self.assertEqual(a.sv._pending_story_chapter,story.ChapterFileRequest(3,2))
            with patch.object(editor.messagebox,'askyesno',return_value=False):self.assertFalse(a.save_all())
            self.assertEqual(target.read_bytes(),old)
            with patch.object(editor.messagebox,'askyesno',return_value=True):self.assertTrue(a.save_all())
            self.assertEqual(target.read_bytes(),path.read_bytes())
            self.assertEqual(Path(str(target)+'.bak').read_bytes(),old)
            self.assertEqual(other.read_bytes(),b'untouched')
            self.assertEqual(container.SaveFile(str(target)).verify(),[])
            a.sv._pending_story_chapter=story.ChapterFileRequest(2,3)
            with self.assertRaises(core.SaveError):story_files.prepare(a.files,{str(path)})

    def test_route_change_during_dialog_requires_fresh_warning(self):
        for phase in ('warning','picker'):
            a=StoryHarness(3);other=StoryHarness(1).sv;before=bytes(other.payload)
            def swap():
                a.sv.payload=bytearray(other.payload);a.sv.raw=other.raw;a.sv._core_cache=None
                return True if phase=='warning' else (9,True)
            if phase=='warning':a._confirm_story_warning=swap
            else:a._choose_story_chapter=swap
            a.open_story_progression()
            self.assertEqual(bytes(a.sv.payload),before);self.assertFalse(hasattr(a,'_undo_stack'))
            self.assertIn('route changed',a.messages[-1][0])


@unittest.skipUnless(os.environ.get('FEFW_THEODORA_SOURCE_DIR'),'No native Theodora captures supplied')
class TheodoraPrivateTest(unittest.TestCase):
    def test_reference_year_transitions_and_twelve_independent_replay_exports(self):
        root=Path(os.environ['FEFW_THEODORA_SOURCE_DIR'])
        for name in SOURCES:
            box=container.SaveFile(str(root/name));self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);i=start.validate(f)
            if name!='Auto':
                self.assertEqual(i.sequence,NATIVE_IDS[i.chapter-1])
                self.assertEqual(struct.unpack_from('<H5B',f.payload,i.header+22),NATIVE_CLOCKS[i.chapter])
            # Natural early checkpoints can move into 1449 and then back to 1446.
            for chapter in (3,2):
                g=core.SaveFile(start.edited(f,chapter));j=start.validate(g)
                self.assertEqual(struct.unpack_from('<H',g.payload,j.header+22)[0],1446 if chapter==2 else 1449)
                self.assertEqual(flags(g),flags(f));f=g
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'cases';result=build(root,out)
            self.assertEqual([r['chapter'] for r in result['cases']],list(range(1,13)))
            for row in result['cases']:
                self.assertEqual(row['source'],'Auto')
                self.assertEqual(row['tutorial_records'],113)
                self.assertEqual(row['units'],[4,8,9])
            for name in SOURCES:self.assertEqual((out/'00-Native-Control'/name).read_bytes(),(root/name).read_bytes())
            for ch in (1,2,3):self.assertEqual((out/f'Control-Chapter-{ch:02d}'/'Auto').read_bytes(),(root/f'Chapter_Seo_1_{ch}').read_bytes())
            with self.assertRaises(ValueError):build(root,out)
        if os.environ.get('FEFW_GAMEDATA'):
            from research.story_timeline_report import report
            timeline=report(os.environ['FEFW_GAMEDATA'],'theodora')
            self.assertEqual(timeline['sha256'],'964da5cf80e6b5385c9bb8c21e706b201b1f6154aa62c26b600970dd852a6741')
            for row in timeline['chapters'][1:]:
                self.assertEqual(start.THEODORA_DATES[row['chapter']],(row['month'],row['day'],row['time']//100,row['time']%100))
