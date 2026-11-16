"""Research-only chapter entry and the blocked Functions Test 2 evidence."""
from pathlib import Path
import os
import struct
import tempfile
import unittest

import facilities
import fefw_core as core
import fefw_save as container
import story
import story_start as start
from research.story_cai_chapter3_probe import build, candidate, CASE, ENTRY_CLOCK
from test_story import StoryHarness


class CaiChapter3Test(unittest.TestCase):
    def test_candidate_preserves_player_roots_and_is_not_a_production_target(self):
        f = core.SaveFile(start.edited(StoryHarness(1).core_of(),2))
        original = bytes(f.payload)
        before = start.normalized_blocks(f)
        g = core.SaveFile(candidate(f)); info = start.validate(g)
        self.assertEqual((info.route, info.part, info.chapter), (1, 1, 3))
        self.assertEqual(info.sequence, story.sequence(3, 1))
        self.assertEqual(struct.unpack_from('<H5B',g.payload,info.header+22), ENTRY_CLOCK)
        after = start.normalized_blocks(g)
        for name in before.keys()-{'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}:
            self.assertEqual(before[name], after[name])
        self.assertEqual(start.TARGETS[1], (2,4,9))
        with self.assertRaises(core.SaveError): start.edited(f,3)
        self.assertEqual(bytes(f.payload), original)

    def test_wrong_route_chapter_and_battle_source_are_refused_without_mutation(self):
        leda = StoryHarness().core_of()
        later = core.SaveFile(start.edited(StoryHarness(1).core_of(),4))
        battle = StoryHarness(1).core_of(); h = battle.block('Header').start
        battle.payload[h+20:h+22] = b'\x12\x02'
        for f in (leda,later,battle):
            original = bytes(f.payload)
            with self.assertRaises(core.SaveError): candidate(f)
            self.assertEqual(bytes(f.payload), original)


class CaiChapter3PrivateTest(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('FEFW_CAI_CH3_SOURCE'), 'No Chapter 2 advancement supplied')
    def test_real_candidate_roundtrip_flags_party_and_source_preserved(self):
        path=Path(os.environ['FEFW_CAI_CH3_SOURCE']);raw=path.read_bytes()
        f=core.SaveFile(container.SaveFile(str(path)).payload);i=story.read(f)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'cases';result=build(path,output)
            self.assertEqual(result['chapter'],3)
            self.assertEqual((output/'00-Control-Chapter-02'/'Auto').read_bytes(),raw)
            box=container.SaveFile(str(output/CASE/'Auto'));self.assertEqual(box.verify(),[])
            g=core.SaveFile(box.payload);j=story.read(g)
            self.assertEqual([(u.person,core.gear(g,u).unit_number) for u in g.units()],
                             [(u.person,core.gear(f,u).unit_number) for u in f.units()])
            self.assertEqual(g.payload[j.user+6:j.user+19],f.payload[i.user+6:i.user+19])
            with self.assertRaises(ValueError):build(path,output)
            wrong=Path(tmp)/'wrong';wrong.write_bytes(b'wrong source')
            with self.assertRaises(ValueError):build(wrong,Path(tmp)/'not-created')
            self.assertFalse((Path(tmp)/'not-created').exists())
        self.assertEqual(path.read_bytes(),raw)

    @unittest.skipUnless(os.environ.get('FEFW_CAI2_RETURN_DIR') and os.environ.get('FEFW_CAI2_SENT_DIR'), 'No Functions Test 2 returns supplied')
    def test_all_four_returns_retain_flags_and_the_same_blocked_story_beat(self):
        returned=Path(os.environ['FEFW_CAI2_RETURN_DIR']);sent=Path(os.environ['FEFW_CAI2_SENT_DIR'])
        paths=sorted(returned.rglob('Auto'));self.assertEqual(len(paths),4)
        for path in paths:
            raw=path.read_bytes();box=container.SaveFile(str(path));self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);i=start.validate(f)
            before=core.SaveFile(container.SaveFile(str(sent/path.parent.name/'Auto')).payload)
            self.assertEqual((i.route,i.part,i.chapter,i.sequence),(1,1,4,0xd63bb68c219adbe2))
            self.assertEqual(struct.unpack_from('<H5B',f.payload,i.header+22),(1449,3,1,15,0,0))
            old,new=facilities.read(before),facilities.read(f)
            for key in facilities.catalog():self.assertEqual(old.get(key),new.get(key))
            first=core.id_hash('拠点_進行_初回自由行動')
            self.assertEqual(old.get(first),new.get(first))
            self.assertTrue(all(facilities.enabled(h,new.get(h)) for h,r in facilities.catalog().items() if r['kind']=='Journal'))
            self.assertEqual([core.gear(f,u).unit_number for u in f.units()],[4,6,7])
            self.assertEqual(path.read_bytes(),raw)
