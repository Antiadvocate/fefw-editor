"""Dietrich sequence anchors, route guards, preservation and private exports."""
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
import story_prerequisites as prerequisites
import story_page
import story_files
from test_story import StoryHarness, box_for
from test_story_files import SaveHarness
from research.dietrich_test_kit import build, flags, SOURCES

# Independently recorded native checkpoints and timeline title rows.
NATIVE_IDS = (0x8e49b736a62418c8,0x8e547736a62db38f,0x8e50b736a62a3796,0x8e3fb736a61bc445)
DATES = ((2,10,9),(2,10,14),(2,11,12),(3,8,12),(4,11,6),(5,4,12),
         (5,29,20),(6,21,12),(8,10,12),(9,29,12),(10,5,12),(11,4,12))


class DietrichStoryTest(unittest.TestCase):
    def test_native_sequence_anchors_and_reported_target_evidence(self):
        self.assertEqual(tuple(story.sequence(n,2) for n in range(1,5)),NATIVE_IDS)
        self.assertEqual(start.TARGETS[2],tuple(range(3,13)))
        self.assertEqual(start.TESTED_BY_ROUTE[2],frozenset(range(3,13)))
        self.assertIn('Chapters 1 and 2 are unavailable',story_page.warning_points(2)[0])
        self.assertIn('native Chapter 2 control',story_page.evidence_note(2))
        for chapter in (1,2):
            self.assertTrue(story_page.chapter_evidence(2,chapter).startswith('Unavailable'))
        for chapter in (5,6):
            self.assertEqual(story_page.chapter_evidence(2,chapter),'Game-tested direct entry and progression')
        self.assertEqual(story.chapter_filename(2,12),'Chapter_Dit_1_12')
        for chapter in (0,1,2,13,True,'4'):
            with self.assertRaises(core.SaveError): start.edited(StoryHarness(2).core_of(),chapter)

    def test_unavailable_targets_refuse_ui_and_stale_writes_but_early_sources_load(self):
        for chapter in (1,2):
            app=StoryHarness(2);before=bytes(app.sv.payload)
            app.apply_story_chapter(chapter,True)
            self.assertEqual(bytes(app.sv.payload),before)
            self.assertFalse(getattr(app,'_undo_stack',[]))
            self.assertIsNone(getattr(app.sv,'_pending_story_chapter',None))
            self.assertIn('unavailable',app.messages[-1][0])
            # Historical/native checkpoints remain readable and can be sources
            # for Chapter 3. Only their use as new chapter-entry targets is denied.
            f=core.SaveFile(start._edited_at_entry(app.core_of(),chapter,1449,start.DIETRICH_DATES[chapter]))
            self.assertEqual(start.validate(f).chapter,chapter)
            original=bytes(f.payload)
            self.assertEqual(start.validate(core.SaveFile(start.edited(f,3))).chapter,3)
            self.assertEqual(bytes(f.payload),original)
            box=box_for(f);box._pending_story_chapter=story.ChapterFileRequest(2,chapter)
            with self.assertRaisesRegex(core.SaveError,'unavailable'):
                story_files.prepare({'synthetic':box},{'synthetic'})
            self.assertEqual(bytes(box.payload),original)

    def test_all_entries_preserve_flags_other_roots_and_serialized_summaries(self):
        f=StoryHarness(2).core_of();before=bytes(f.payload);original=start.normalized_blocks(f)
        with tempfile.TemporaryDirectory() as tmp:
            for chapter in start.DIETRICH_CHAPTERS:
                month,day,hour=DATES[chapter-1]
                g=core.SaveFile(start.edited(f,chapter));i=start.validate(g)
                self.assertEqual((i.route,i.part,i.chapter,i.sequence),(2,1,chapter,story.sequence(chapter,2)))
                self.assertEqual(struct.unpack_from('<H5B',g.payload,i.header+22),(1449,month,day,hour,0,0))
                self.assertEqual(flags(g),flags(core.SaveFile(prerequisites.edited(f,chapter))))
                after=start.normalized_blocks(g)
                for key in original.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
                    self.assertEqual(original[key],after[key])
                self.assertEqual(start.edited(g,chapter),g.payload)
                box=box_for(f);box.payload=g.payload;path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes())
                reopened=container.SaveFile(str(path));self.assertEqual(reopened.verify(),[])
                self.assertEqual(reopened.payload,g.payload)
                self.assertEqual(reopened.raw[40:43],bytes((2,1,chapter)))
                self.assertEqual(int.from_bytes(reopened.raw[73:81],'little'),i.sequence)
                self.assertEqual(reopened.raw[48:57],g.payload[i.header+20:i.header+29])
        self.assertEqual(bytes(f.payload),before)
        with self.assertRaises(core.SaveError):story.edited(f,4,route=1)
        with self.assertRaises(core.SaveError):story.edited(f,4,route=4)
        with self.assertRaises(core.SaveError):story.edited(StoryHarness(1).core_of(),4,route=2)
        for mode in (b'\x12\x06',b'\x12\x02'):
            g=core.SaveFile(f.payload);g.payload[story.read(g).header+20:story.read(g).header+22]=mode
            with self.assertRaises(core.SaveError):start.edited(g,4)

    def test_dietrich_history_save_names_and_stale_route_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=SaveHarness(tmp);path=Path(a.sv.path);box=box_for(StoryHarness(2).core_of())
            path.write_bytes(box.to_bytes());a.sv=container.SaveFile(str(path));a.files[str(path)]=a.sv
            before=bytes(a.sv.payload);target=Path(tmp)/'Chapter_Dit_1_4';target.write_bytes(path.read_bytes());old=target.read_bytes()
            other=Path(tmp)/'Chapter_Kai_1_4';other.write_bytes(b'untouched')
            a.apply_story_chapter(4,True);changed=bytes(a.sv.payload)
            self.assertEqual(target.read_bytes(),old)
            a.undo();self.assertEqual(bytes(a.sv.payload),before);self.assertIsNone(a.sv._pending_story_chapter)
            a.redo();self.assertEqual(bytes(a.sv.payload),changed)
            self.assertEqual(a.sv._pending_story_chapter,story.ChapterFileRequest(2,4))
            with patch.object(editor.messagebox,'askyesno',return_value=False):self.assertFalse(a.save_all())
            self.assertEqual(target.read_bytes(),old)
            with patch.object(editor.messagebox,'askyesno',return_value=True):self.assertTrue(a.save_all())
            self.assertEqual(target.read_bytes(),path.read_bytes());self.assertEqual(Path(str(target)+'.bak').read_bytes(),old)
            self.assertEqual(other.read_bytes(),b'untouched')
            a.apply_story_chapter(4,True)
            a.sv.payload=StoryHarness(1).sv.payload
            with self.assertRaises(core.SaveError):story_files.prepare(a.files,a.dirty)

    def test_route_switch_during_dialog_needs_new_warning(self):
        for phase in ('warning','picker'):
            a=StoryHarness(2);other=StoryHarness(1).sv;before=bytes(other.payload)
            def swap():
                a.sv.payload=bytearray(other.payload);a.sv.raw=other.raw;a.sv._core_cache=None
                return True if phase=='warning' else (4,True)
            if phase=='warning':a._confirm_story_warning=swap
            else:a._choose_story_chapter=swap
            a.open_story_progression()
            self.assertEqual(bytes(a.sv.payload),before);self.assertFalse(hasattr(a,'_undo_stack'))
            self.assertIn('route changed',a.messages[-1][0])


@unittest.skipUnless(os.environ.get('FEFW_DIETRICH_SOURCE_DIR'),'No native Dietrich captures supplied')
class DietrichPrivateTest(unittest.TestCase):
    def test_native_sources_supported_targets_and_historical_exports(self):
        root=Path(os.environ['FEFW_DIETRICH_SOURCE_DIR'])
        # Early native saves remain valid sources for supported Chapter 3–12 targets.
        for name in SOURCES:
            box=container.SaveFile(str(root/name));self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);i=start.validate(f)
            for chapter in start.DIETRICH_CHAPTERS:
                g=core.SaveFile(start.edited(f,chapter));self.assertEqual(flags(g),flags(core.SaveFile(prerequisites.edited(f,chapter))))
                self.assertEqual([core.gear(g,u).unit_number for u in g.units()],
                                 [core.gear(f,u).unit_number for u in f.units()])
            if name!='Auto':self.assertEqual(i.sequence,NATIVE_IDS[i.chapter-1])
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'cases';result=build(root,out)
            self.assertEqual([r['chapter'] for r in result['cases']],list(range(1,13)))
            for row in result['cases']:
                self.assertEqual(row['tutorial_records'],113)
                self.assertEqual(row['units'],[] if row['chapter']==1 else [4,13,5])
            for name in SOURCES:self.assertEqual((out/'00-Native-Control'/name).read_bytes(),(root/name).read_bytes())
            with self.assertRaises(ValueError):build(root,out)
        if os.environ.get('FEFW_GAMEDATA'):
            from research.story_timeline_report import report
            for row in report(os.environ['FEFW_GAMEDATA'],'dietrich')['chapters'][1:]:
                self.assertEqual(start.DIETRICH_DATES[row['chapter']],(row['month'],row['day'],row['time']//100,row['time']%100))
