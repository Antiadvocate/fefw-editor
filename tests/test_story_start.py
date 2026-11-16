"""Chapter-start editing, guards, UI history and complete outer-header mirrors."""
from pathlib import Path
import os
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
import story_start as start
from research import story_resume_probe as legacy
from research.story_remaining_probes import build
from test_story import StoryHarness, box_for
from test_story_resume_probe import fixture


class StoryStartTest(unittest.TestCase):
    def test_all_nine_targets_use_entry_dates_preserve_unrelated_data_and_are_idempotent(self):
        f = fixture()
        before = bytes(f.payload)
        original = start.normalized_blocks(f)
        for chapter in start.CHAPTERS:
            g = core.SaveFile(start.edited(f,chapter))
            i = start.validate(g)
            self.assertEqual((i.chapter,i.sequence),(chapter,story.sequence(chapter)))
            month,day,hour,minute = start.ENTRY_DATES[chapter]
            self.assertEqual(struct.unpack_from('<H5B',g.payload,i.header+22),(1449,month,day,hour,minute,0))
            result = start.normalized_blocks(g)
            for name in ('GameSound','HubSeq'):
                self.assertEqual(original[name],result[name])
            self.assertEqual(len(result['GameRestartData']),360)
            self.assertEqual(start.edited(g,chapter),g.payload)
        self.assertEqual(f.payload,before)
        for chapter in (4,9):
            self.assertEqual(start.edited(f,chapter),legacy.edited_profile(f,chapter,False))

    def test_invalid_targets_states_clocks_and_restart_layout_refused_atomically(self):
        f = fixture()
        i = story.read(f)
        changes = ((i.header+21,2),(i.user+58,0),(i.user+3,1),
                   (i.header+24,13),(start.one_block(f,'GameSchedule').start+4,2),
                   (start.one_block(f,'GameRestartData').start+4,4))
        for at,value in changes:
            g = core.SaveFile(f.payload)
            g.payload[at] = value
            before = bytes(g.payload)
            with self.assertRaises(core.SaveError):
                start.edited(g,9)
            self.assertEqual(g.payload,before)
        for chapter in (1,2,3,13,True,'9',None):
            with self.assertRaises(core.SaveError):
                start.edited(f,chapter)

    def test_ui_apply_undo_redo_noop_and_slot_isolation(self):
        a = StoryHarness()
        before = bytes(a.sv.payload)
        a.choice = 4
        a.open_story_progression()
        after = bytes(a.sv.payload)
        self.assertEqual(after,start.edited(core.SaveFile(before),4))
        self.assertEqual(len(a._undo_stack),1)
        a.apply_story_chapter(4)
        self.assertEqual(len(a._undo_stack),1)
        a.undo(); self.assertEqual(a.sv.payload,before)
        a.redo(); self.assertEqual(a.sv.payload,after)
        other = StoryHarness(1).sv
        other_before = bytes(other.payload)
        a.sv = other
        a.undo(); a.redo(); a.apply_story_chapter(9)
        self.assertEqual(other.payload,other_before)

    def test_mode_clock_summary_undo_after_save_roundtrip_and_backups(self):
        f = fixture()
        box = box_for(f)
        original = bytes(box.payload)
        changed = bytes(start.edited(f,10))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'Auto'
            path.write_bytes(box.to_bytes())
            box = container.SaveFile(str(path))
            for payload in (changed,original,changed):
                box.payload = bytearray(payload)
                box.save()
                reopen = container.SaveFile(str(path))
                self.assertEqual(reopen.verify(),[])
                i = story.read(core.SaveFile(payload))
                self.assertEqual(reopen.raw[48:57],payload[i.header+20:i.header+29])
                self.assertEqual(reopen.raw[42],i.chapter)
                self.assertEqual(struct.unpack_from('<Q',reopen.raw,73)[0],i.sequence)
            self.assertTrue(Path(str(path)+'.bak2').exists())


@unittest.skipUnless(os.environ.get('FEFW_STORY_TEST_SAVE'),'No accepted private baseline supplied')
class StoryStartPrivateTest(unittest.TestCase):
    def test_production_matches_passed_D_profiles_and_all_flags_are_preserved(self):
        path = Path(os.environ['FEFW_STORY_TEST_SAVE'])
        raw = path.read_bytes()
        f = core.SaveFile(container.SaveFile(str(path)).payload)
        for chapter in (4,9):
            p = start.edited(f,chapter)
            self.assertEqual(p,legacy.edited_profile(f,chapter,False))
            g = core.SaveFile(p)
            def flags(x):return [[(v.hash,v.value) for v in m.flags] for m in core.flag_maps(x)]
            self.assertEqual(flags(f),flags(g))
            saved = os.environ.get('FEFW_STORY3_SENT_DIR')
            if saved:
                prior = container.SaveFile(str(Path(saved)/f'ST3-{chapter:02d}D-Resume-id/Auto'))
                self.assertEqual(p,prior.payload)
                box = container.SaveFile(str(path));box.payload=p
                self.assertEqual(box.to_bytes(),prior.raw)
        self.assertEqual(path.read_bytes(),raw)

    def test_remaining_cases_build_with_real_serializer_and_refuse_overwrite(self):
        path = Path(os.environ['FEFW_STORY_TEST_SAVE'])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'cases'
            result = build(path,out)
            self.assertEqual([r['chapter'] for r in result['cases']],[5,6,7,8,10,11,12])
            with self.assertRaises(ValueError):build(path,out)


@unittest.skipUnless(os.environ.get('FEFW_STORY3_RETURN_DIR'),'No private Test 3 returns supplied')
class Story3ReturnsTest(unittest.TestCase):
    def test_returns_validate_and_free_time_preserves_party_and_target_restart(self):
        root = Path(os.environ['FEFW_STORY3_RETURN_DIR'])
        wanted = {'45e9244b':47,'4e88d94e':48,'5477ab4f':1,'076d3f72':2,'b1c36239':3,
                  'bc368eb6':4,'fd0849a1':5,'786afccd':6,'1a788ba7':7}
        paths = sorted(root.rglob('Auto*'))
        self.assertEqual(len(paths),12)
        for path in paths:
            with self.subTest(path=str(path.relative_to(root))):
                raw = path.read_bytes();box = container.SaveFile(str(path))
                self.assertEqual(box.verify(),[])
                f = core.SaveFile(box.payload);i = story.read(f)
                chapter = 4 if '04' in path.parent.name else 9
                self.assertEqual(i.chapter,chapter)
                if chapter==9 and path.name=='Auto-after-advancement':
                    self.assertEqual(i.sequence,0xa27302ce5e5e5a75)
                    with self.assertRaises(core.SaveError):start.validate(f)
                else:
                    party = {f'{u.person:08x}':core.gear(f,u).unit_number for u in f.units() if f'{u.person:08x}' in wanted}
                    self.assertEqual(party,wanted)
                    start.validate(f)
                t = core.SaveTree(f.payload)
                slots = start.members(f,t,f.block('GameRestartData').start,start.RESTART_KEYS)
                fields = start.members(f,t,slots[0x8c8807e8],{start.HEADER_KEY,start.DATA_KEY})
                at = fields[start.DATA_KEY];size = f.u32(at+12)
                payload = bytes(f.payload[at+40:at+40+size])
                self.assertEqual(core.fnv1_32(payload),f.u32(at+16))
                checkpoint = core.SaveFile(payload)
                h = checkpoint.block('Header').start
                self.assertEqual(checkpoint.payload[h+14],chapter)
                self.assertEqual(struct.unpack_from('<Q',checkpoint.payload,h+45)[0],story.sequence(chapter))
                self.assertEqual(path.read_bytes(),raw)
