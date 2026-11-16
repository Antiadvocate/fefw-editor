"""Cai-specific selectors, route isolation and Save-only checkpoint names."""
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
from research.story_cai_probes import build


def fixture():
    return core.SaveFile(StoryHarness(1).sv.payload)


class CaiStoryTest(unittest.TestCase):
    def test_independent_captured_checkpoint_ids_and_route_specific_targets(self):
        self.assertEqual(story.sequence(1,1),0x1c39b1f1e90b1ef6)
        self.assertEqual(story.sequence(2,1),0x1c36b1f1e908e8c1)
        self.assertEqual(start.TARGETS[1],(2,3,4,9))
        self.assertEqual(start.TESTED_BY_ROUTE[1],frozenset((2,3,9)))
        for chapter in (1,5,6,7,8,10,11,12,True,'2'):
            with self.assertRaises(core.SaveError): start.edited(fixture(),chapter)
        for route in (0,2,3,9,True):
            with self.assertRaises(core.SaveError): story.sequence(2,route)
        self.assertEqual(story.chapter_filename(1,9),'Chapter_Kai_1_9')
        self.assertEqual(story.chapter_filename(4,9),'Chapter_Led_1_9')

    def test_all_cai_targets_preserve_other_roots_and_use_cai_dates_and_ids(self):
        f=fixture();before=bytes(f.payload);original=start.normalized_blocks(f)
        for chapter,clock in ((2,(1449,1,25,11,0,0)),(3,(1449,2,4,8,0,0)),(4,(1449,3,1,12,0,0)),(9,(1449,9,3,12,0,0))):
            g=core.SaveFile(start.edited(f,chapter));i=start.validate(g)
            self.assertEqual((i.route,i.part,i.chapter,i.sequence),(1,1,chapter,story.sequence(chapter,1)))
            self.assertEqual(struct.unpack_from('<H5B',g.payload,i.header+22),clock)
            after=start.normalized_blocks(g)
            for key in original.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
                self.assertEqual(original[key],after[key])
            self.assertEqual(start.edited(g,chapter),g.payload)
        self.assertEqual(bytes(f.payload),before)
        with self.assertRaises(core.SaveError): story.edited(f,9)  # Leda-default low-level call.
        with self.assertRaises(core.SaveError): story.edited(StoryHarness().core_of(),9,route=1)

    def test_cai_summary_roundtrips_undo_after_save_and_does_not_change_route(self):
        box=box_for(fixture());original=bytes(box.payload)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes());box=container.SaveFile(str(path))
            changed=start.edited(core.SaveFile(box.payload),9)
            for payload in (changed,original,changed):
                box.payload=bytearray(payload);box.save()
                reopened=container.SaveFile(str(path));self.assertEqual(reopened.verify(),[])
                info=story.read(core.SaveFile(payload))
                self.assertEqual(reopened.raw[40:43],bytes((1,1,info.chapter)))
                self.assertEqual(int.from_bytes(reopened.raw[73:81],'little'),info.sequence)
                self.assertEqual(reopened.raw[48:57],payload[info.header+20:info.header+29])

    def test_route_change_during_warning_and_picker_requires_fresh_warning(self):
        for phase in ('warning','picker'):
            a=StoryHarness();cai=StoryHarness(1).sv;before=bytes(cai.payload)
            def swap():
                a.sv.payload=bytearray(cai.payload);a.sv.raw=cai.raw;a.sv._core_cache=None
                return True if phase=='warning' else (9,True)
            if phase=='warning':a._confirm_story_warning=swap
            else:a._choose_story_chapter=swap
            a.open_story_progression()
            self.assertEqual(bytes(a.sv.payload),before)
            self.assertFalse(hasattr(a,'_undo_stack'))
            self.assertIn('route changed',a.messages[-1][0])

    def test_ui_stages_cai_and_preserves_request_through_history(self):
        a=StoryHarness(1);before=bytes(a.sv.payload)
        a.apply_story_chapter(9,True)
        self.assertEqual(a.sv._pending_story_chapter,story.ChapterFileRequest(1,9))
        self.assertEqual(story.read(a.core_of()).sequence,story.sequence(9,1))
        a.undo();self.assertEqual(bytes(a.sv.payload),before);self.assertIsNone(a.sv._pending_story_chapter)
        a.redo();self.assertEqual(a.sv._pending_story_chapter,story.ChapterFileRequest(1,9))
        self.assertIn('Cai',a.messages[-3][0])
        self.assertIn('Sewers entry and progression passed',story_page.warning_points(1)[2])
        self.assertIn('direct entry remains untested',story_page.evidence_note(1))
        self.assertIn('Chapter 1 cannot be selected',story_page.warning_points(4)[0])

    def test_save_uses_only_kai_filename_and_route_bound_request_rejects_stale_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=SaveHarness(tmp);box=box_for(fixture());path=Path(a.sv.path)
            path.write_bytes(box.to_bytes());a.sv=container.SaveFile(str(path));a.files[str(path)]=a.sv
            leda=Path(tmp)/'Chapter_Led_1_9';leda.write_bytes(b'untouched Leda checkpoint')
            target=Path(tmp)/'Chapter_Kai_1_9';target.write_bytes(path.read_bytes());old=target.read_bytes()
            a.apply_story_chapter(9,True)
            self.assertEqual(target.read_bytes(),old)
            with patch.object(editor.messagebox,'askyesno',return_value=True) as prompt:
                self.assertTrue(a.save_all());self.assertIn('Chapter_Kai_1_9',prompt.call_args.args[1])
            self.assertEqual(target.read_bytes(),path.read_bytes())
            self.assertEqual(Path(str(target)+'.bak').read_bytes(),old)
            self.assertEqual(leda.read_bytes(),b'untouched Leda checkpoint')
            a.apply_story_chapter(9,True)
            # A pending Cai write must not become a Leda write after a snapshot swap.
            other=StoryHarness();other.apply_story_chapter(9)
            a.sv.payload=other.sv.payload;a.sv.raw=other.sv.raw
            with self.assertRaises(core.SaveError):story_files.prepare(a.files,a.dirty)
            self.assertEqual(leda.read_bytes(),b'untouched Leda checkpoint')


@unittest.skipUnless(os.environ.get('FEFW_CAI_SOURCE_DIR'),'No native Cai captures supplied')
class CaiPrivateTest(unittest.TestCase):
    def test_natural_checkpoints_anchor_same_prefix_and_resume_layout(self):
        root=Path(os.environ['FEFW_CAI_SOURCE_DIR']);prefixes=[]
        for chapter in (1,2):
            path=root/f'Chapter_Kai_1_{chapter}';raw=path.read_bytes();box=container.SaveFile(str(path))
            self.assertEqual(box.verify(),[]);f=core.SaveFile(box.payload);info=start.validate(f)
            self.assertEqual((info.route,info.part,info.chapter),(1,1,chapter))
            self.assertEqual(info.sequence,story.sequence(chapter,1))
            value=info.sequence
            for byte in reversed(f'{chapter}_1'.encode()):value=((value^byte)*pow(0x100000001b3,-1,1<<64))&((1<<64)-1)
            prefixes.append(value)
            self.assertEqual(struct.unpack_from('<Q',f.payload,info.user+58)[0],start.CHECKPOINT_ID)
            self.assertEqual(len(start.restart_leaves(f)),16)
            self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(prefixes,[0xeab884585a706f5d]*2)

    def test_three_candidates_preserve_native_party_flags_money_and_original_files(self):
        root=Path(os.environ['FEFW_CAI_SOURCE_DIR']);source=root/'Auto(3)';raw=source.read_bytes()
        f=core.SaveFile(container.SaveFile(str(source)).payload);i=story.read(f)
        self.assertEqual(struct.unpack_from('<II',f.payload,i.user+6),(1500,350))
        self.assertEqual(struct.unpack_from('<I',f.payload,i.user+15)[0],430)
        wanted={0x3d853178:4,0x6eea5a06:6,0xdd42cdd3:7}
        def flags(x):return [[(v.hash,v.value) for v in m.flags] for m in core.flag_maps(x)]
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'cases';report=build(source,output)
            self.assertEqual([r['chapter'] for r in report['cases']],[2,4,9])
            self.assertEqual((output/'00-Control/Auto').read_bytes(),raw)
            for row in report['cases']:
                g=core.SaveFile(container.SaveFile(str(output/row['case']/'Auto')).payload);j=story.read(g)
                self.assertEqual({u.person:core.gear(g,u).unit_number for u in g.units()},wanted)
                self.assertEqual(flags(g),flags(f))
                self.assertEqual(g.payload[j.user+6:j.user+19],f.payload[i.user+6:i.user+19])
            with self.assertRaises(ValueError):build(source,output)
        self.assertEqual(source.read_bytes(),raw)
