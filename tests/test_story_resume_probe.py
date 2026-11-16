"""Bounded resume-state diagnostics; game compatibility remains unverified."""
import os
import struct
import tempfile
import unittest
from pathlib import Path

import fefw_core as core
import fefw_save as container
import story
from research import story_entry_probe as entry, story_resume_probe as resume
from test_story_entry_probe import fixture as entry_fixture


def fixture():
    f = entry_fixture()
    tree = core.SaveTree(f.payload)
    p = bytearray(4)
    rows = []
    for b in f.blocks:
        at = len(p)
        p.extend(tree.copy_object(tree.node_at(b.start), at))
        rows.append((b.hash, at))
    at = len(p)
    p.extend(struct.pack('<II', at+40, 0))
    rows.append((core.fnv1_32(b'HubSeq'), at))
    table = len(p)
    for key, at in rows:
        p.extend(struct.pack('<II', key, at+32))
    struct.pack_into('<I', p, 0, (len(rows)<<24)|(table+32))
    f = core.SaveFile(p)
    struct.pack_into('<Q', f.payload, story.read(f).user+58, resume.FREE_TIME_ID)
    return f


class ResumeProbeTest(unittest.TestCase):
    def test_profiles_only_change_resume_id_and_optional_root_membership_beyond_C(self):
        f = fixture()
        before = bytes(f.payload)
        for chapter in (4, 9):
            prior = core.SaveFile(entry.edited_profile(f, chapter, 'C'))
            expected = entry.normalized_blocks(prior)
            user = bytearray(expected['GameUserData'])
            struct.pack_into('<Q', user, 62, resume.CHECKPOINT_ID)
            expected['GameUserData'] = bytes(user)
            for remove in (False, True):
                g = core.SaveFile(resume.edited_profile(f, chapter, remove))
                wanted = dict(expected)
                if remove:
                    del wanted['HubSeq']
                self.assertEqual(entry.normalized_blocks(g), wanted)
                self.assertEqual(resume.resume_id(g), resume.CHECKPOINT_ID)
                self.assertEqual(story.read(g).chapter, chapter)
        self.assertEqual(bytes(f.payload), before)

    def test_unknown_identifier_route_or_nonempty_hub_refused_without_changes(self):
        f = fixture()
        for offset, value in ((story.read(f).user+58, 99),
                              (story.read(f).user+3, 1),
                              (f.block('HubSeq').start+4, 1)):
            g = core.SaveFile(f.payload)
            g.payload[offset] = value
            before = bytes(g.payload)
            with self.assertRaises(core.SaveError):
                resume.edited_profile(g, 9, True)
            self.assertEqual(bytes(g.payload), before)
        no_hub = core.SaveFile(resume.without_hub_seq(f))
        with self.assertRaises(core.SaveError):
            resume.without_hub_seq(no_hub)
        for chapter, remove in ((1, False), (True, False), (9, 'yes')):
            with self.assertRaises(core.SaveError):
                resume.edited_profile(f, chapter, remove)

    @unittest.skipUnless(os.environ.get('FEFW_STORY_TEST_SAVE'), 'No accepted private baseline supplied')
    def test_private_four_cases_preserve_source_and_roundtrip(self):
        path = Path(os.environ['FEFW_STORY_TEST_SAVE'])
        before = path.read_bytes()
        f = core.SaveFile(container.SaveFile(str(path)).payload)
        original = entry.normalized_blocks(f)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'probes'
            report = resume.build(path, out)
            self.assertEqual(len(report['cases']), 4)
            for row in report['cases']:
                box = container.SaveFile(str(out/row['case']/'Auto'))
                self.assertEqual(box.verify(), [])
                g = core.SaveFile(box.payload)
                blocks = entry.normalized_blocks(g)
                allowed = {'Header','GameUserData','GameSchedule','Calendar','GameRestartData','HubSeq'}
                for name in original.keys()-allowed:
                    self.assertEqual(original[name], blocks[name])
                self.assertEqual([(m.index, [(fl.hash, fl.value) for fl in m.flags]) for m in core.flag_maps(f)],
                                 [(m.index, [(fl.hash, fl.value) for fl in m.flags]) for m in core.flag_maps(g)])
            with self.assertRaises(ValueError):
                resume.build(path, out)
            wrong = Path(tmp)/'wrong'
            wrong.write_bytes(before+b'wrong')
            with self.assertRaises(ValueError):
                resume.build(wrong, Path(tmp)/'wrong-output')
        self.assertEqual(path.read_bytes(), before)


@unittest.skipUnless(os.environ.get('FEFW_STORY2_RETURN_DIR') and os.environ.get('FEFW_STORY2_CHAPTER'),
                     'No private Test 2 returns and external checkpoint supplied')
class Story2ReturnsTest(unittest.TestCase):
    def test_failed_cases_retain_resume_identifier_and_hub_seq(self):
        root = Path(os.environ['FEFW_STORY2_RETURN_DIR'])
        for name, chapter, date in (('ST2-09A-Entry-mode',9,(7,12)),
                                    ('ST2-09B-Empty-restart',9,(7,12)),
                                    ('ST2-09C-Entry-date',9,(7,10)),
                                    ('ST2-04C-Entry-date',4,(3,1))):
            with self.subTest(case=name):
                path = root/name/'Auto'
                before = path.read_bytes()
                box = container.SaveFile(str(path))
                self.assertEqual(box.verify(), [])
                f = core.SaveFile(box.payload)
                i = story.read(f)
                self.assertEqual((i.chapter,i.sequence),(chapter,story.sequence(chapter)))
                self.assertEqual(resume.resume_id(f),resume.FREE_TIME_ID)
                self.assertIsNotNone(f.block('HubSeq'))
                self.assertEqual(tuple(f.payload[i.header+24:i.header+26]),date)
                tree = core.SaveTree(f.payload)
                slots = entry.members(f,tree,f.block('GameRestartData').start,entry.RESTART_KEYS)
                data_lengths = []
                for at in slots.values():
                    fields = entry.members(f,tree,at,{entry.HEADER_KEY,entry.DATA_KEY})
                    data_lengths.append(f.u32(fields[entry.DATA_KEY]+4))
                self.assertEqual(sum(data_lengths)>0,name=='ST2-09A-Entry-mode')
                self.assertEqual(path.read_bytes(),before)

    def test_checkpoint_and_embedded_snapshot_share_older_world_and_roster(self):
        root = Path(os.environ['FEFW_STORY2_RETURN_DIR'])
        p = Path(os.environ['FEFW_STORY2_CHAPTER'])
        before = p.read_bytes()
        checkpoint = container.SaveFile(str(p))
        self.assertEqual(checkpoint.verify(),[])
        f = core.SaveFile(checkpoint.payload)
        self.assertEqual(resume.resume_id(f),resume.CHECKPOINT_ID)
        self.assertIsNone(f.block('HubSeq'))
        box = container.SaveFile(str(root/'ST2-09A-Entry-mode/Auto'))
        a = core.SaveFile(box.payload)
        t = core.SaveTree(a.payload)
        slots = entry.members(a,t,a.block('GameRestartData').start,entry.RESTART_KEYS)
        fields = entry.members(a,t,slots[0x8c8807e8],{entry.HEADER_KEY,entry.DATA_KEY})
        at = fields[entry.DATA_KEY]
        size = a.u32(at+12)
        inner = bytes(a.payload[at+40:at+40+size])
        self.assertEqual(core.fnv1_32(inner),a.u32(at+16))
        snapshot = core.SaveFile(inner)
        ca, cb = entry.normalized_blocks(f), entry.normalized_blocks(snapshot)
        for name in ('UnitPool','HubData','GmapSpotMgr','GmapTroopMgr','Transporter','GameSchedule'):
            self.assertEqual(ca[name],cb[name])
        # Shared data does not identify which source Restart reads.
        self.assertEqual(p.read_bytes(),before)
