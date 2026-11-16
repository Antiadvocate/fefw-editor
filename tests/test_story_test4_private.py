"""Optional Test 4 return and early-checkpoint evidence checks."""
from pathlib import Path
import os
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import facilities
import fast_travel
import story
import story_start as start
from research.story_early_probes import build


@unittest.skipUnless(os.environ.get('FEFW_STORY4_RETURN_DIR') and os.environ.get('FEFW_STORY_TEST_SAVE'), 'No private Test 4 returns and baseline supplied')
class Story4ReturnsTest(unittest.TestCase):
    def test_all_fourteen_returns_checksums_progression_flags_roster_and_checkpoints(self):
        root = Path(os.environ['FEFW_STORY4_RETURN_DIR'])
        base = core.SaveFile(container.SaveFile(os.environ['FEFW_STORY_TEST_SAVE']).payload)
        wanted = {u.person: core.gear(base,u).unit_number for u in base.units()}
        bf, bt = facilities.read(base), fast_travel.read(base)
        paths = sorted(root.rglob('Auto*'))
        self.assertEqual(len(paths), 14)
        seqs = {}
        for path in paths:
            with self.subTest(path=path.relative_to(root)):
                raw = path.read_bytes(); box = container.SaveFile(str(path))
                self.assertEqual(box.verify(), [])
                f = core.SaveFile(box.payload); i = story.read(f)
                chapter = int(path.parent.name.split('-')[1])
                self.assertEqual(i.chapter, chapter)
                seqs.setdefault(chapter, set()).add(i.sequence)
                for key in facilities.catalog(): self.assertEqual(facilities.read(f).get(key), bf.get(key))
                for key in fast_travel.catalog(): self.assertEqual(fast_travel.read(f).get(key), bt.get(key))
                if f.payload[i.header+20:i.header+22] == b'\x12\x02':
                    with self.assertRaises(core.SaveError): start.validate(f)
                else:
                    actual = {u.person: core.gear(f,u).unit_number for u in f.units() if u.person in wanted}
                    self.assertEqual(actual, wanted)
                t = core.SaveTree(f.payload)
                slots = start.members(f,t,f.block('GameRestartData').start,start.RESTART_KEYS)
                fields = start.members(f,t,slots[0x8c8807e8],{start.HEADER_KEY,start.DATA_KEY})
                at = fields[start.DATA_KEY]; size = f.u32(at+12)
                p = bytes(f.payload[at+40:at+40+size])
                self.assertEqual(core.fnv1_32(p),f.u32(at+16))
                checkpoint = core.SaveFile(p); h = checkpoint.block('Header').start
                self.assertEqual(checkpoint.payload[h+14],chapter)
                self.assertEqual(struct.unpack_from('<Q',p,h+45)[0],story.sequence(chapter))
                self.assertEqual({u.person:core.gear(checkpoint,u).unit_number for u in checkpoint.units() if u.person in wanted}, wanted)
                self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(set(seqs),{5,6,7,8,10,11,12})
        self.assertTrue(all(len(ids)==2 for ids in seqs.values()))


@unittest.skipUnless(os.environ.get('FEFW_STORY_CHECKPOINT_DIR') and os.environ.get('FEFW_STORY_TEST_SAVE'), 'No private natural checkpoints and baseline supplied')
class EarlyCheckpointTest(unittest.TestCase):
    def test_early_cases_build_and_natural_dates_modes_identifiers_match(self):
        root = Path(os.environ['FEFW_STORY_CHECKPOINT_DIR'])
        for chapter in (1,2):
            box = container.SaveFile(str(root/f'Chapter_Led_1_{chapter}'))
            self.assertEqual(box.verify(),[])
            f = core.SaveFile(box.payload); i = story.read(f)
            self.assertEqual(i.sequence,story.sequence(chapter))
            self.assertEqual(struct.unpack_from('<H5B',f.payload,i.header+22),
                             (start.ENTRY_YEARS[chapter],*start.ENTRY_DATES[chapter],0))
            self.assertEqual(f.payload[i.header+20:i.header+22],b'\x10\x0b')
            self.assertEqual(struct.unpack_from('<Q',f.payload,i.user+58)[0],start.CHECKPOINT_ID)
        with tempfile.TemporaryDirectory() as tmp:
            result = build(os.environ['FEFW_STORY_TEST_SAVE'],Path(tmp)/'cases')
            self.assertEqual([r['chapter'] for r in result['cases']],[1,2,3])
