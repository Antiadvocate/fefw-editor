"""A one-record access hypothesis must preserve the current Chapter 4 state."""
from pathlib import Path
import hashlib
import os
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
import story_start as start
from research import cai_sewers_probe as probe
from research.cai_sewers_report import report
from test_story import StoryHarness


class SewersGuardsTest(unittest.TestCase):
    def test_other_route_and_story_stage_are_refused_without_changes(self):
        for f in (StoryHarness().core_of(), StoryHarness(1).core_of()):
            original=bytes(f.payload)
            with self.assertRaises(core.SaveError):probe.candidate(f)
            self.assertEqual(bytes(f.payload),original)


@unittest.skipUnless(os.environ.get('FEFW_CAI3_RETURN_DIR'),'No Cai Chapter 3/4 returns supplied')
class SewersPrivateTest(unittest.TestCase):
    def source(self):return Path(os.environ['FEFW_CAI3_RETURN_DIR'])/'04-arrival/Auto'

    def test_returns_validate_natural_transition_and_missing_dialogue(self):
        root=Path(os.environ['FEFW_CAI3_RETURN_DIR'])
        for folder,chapter,seq,clock,count in (
                ('03-opening',3,0xd645768c21a2c3a9,(1449,2,4,10,0,0),3),
                ('04-arrival',4,0xd63bb68c219adbe2,(1449,3,1,15,0,0),4)):
            path=root/folder/'Auto';raw=path.read_bytes();box=container.SaveFile(str(path))
            self.assertEqual(box.verify(),[]);f=core.SaveFile(box.payload);i=start.validate(f)
            self.assertEqual((i.route,i.part,i.chapter,i.sequence),(1,1,chapter,seq))
            self.assertEqual(struct.unpack_from('<H5B',f.payload,i.header+22),clock)
            self.assertEqual(len(f.units()),count)
            self.assertFalse(any(v.hash==probe.READ_HASH for m in core.flag_maps(f) for v in m.flags))
            self.assertEqual(path.read_bytes(),raw)

    def test_single_history_record_preserves_all_existing_objects_and_guards(self):
        f=core.SaveFile(container.SaveFile(str(self.source())).payload);original=bytes(f.payload)
        fm=probe.locate(f);g=core.SaveFile(probe.candidate(f));gm=probe.locate(g)
        old=[(v.hash,v.value,v.wide) for v in fm.flags];new=[(v.hash,v.value,v.wide) for v in gm.flags]
        self.assertEqual(new,old+[(probe.READ_HASH,1,False)])
        for a,b in zip(core.flag_maps(f),core.flag_maps(g)):
            if a.start!=fm.start:
                self.assertEqual([(v.hash,v.value,v.wide) for v in a.flags],[(v.hash,v.value,v.wide) for v in b.flags])
        restored=core.SaveFile(core.flag_remove(g,gm,gm.flags[-1]))
        self.assertEqual(start.normalized_blocks(restored),start.normalized_blocks(f))
        self.assertEqual([core.gear(g,u).unit_number for u in g.units()],[4,6,7,37])
        before=bytes(g.payload)
        with self.assertRaises(core.SaveError):probe.candidate(g)
        self.assertEqual(bytes(g.payload),before)
        # A matching set of dialogue anchors in the wrong member is refused.
        tree=core.SaveTree(f.payload);node=tree.node_at(fm.start)
        parent=tree.nodes[tree.nodes[node].parent].start;table=f.ptr(parent)
        bad=bytearray(original)
        for n in range(f.u32(parent)>>24):
            if f.u32(table+n*8)==probe.MAP_KEY:struct.pack_into('<I',bad,table+n*8,0xdeadbeef)
        with self.assertRaises(core.SaveError):probe.candidate(core.SaveFile(bad))
        self.assertEqual(bytes(f.payload),original)

    def test_export_roundtrip_control_fingerprint_and_overwrite_refusal(self):
        source=self.source();raw=source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'cases';r=probe.build(source,output)
            self.assertEqual((output/'00-Control-Natural-Chapter-04/Auto').read_bytes(),raw)
            path=output/probe.CASE/'Auto';box=container.SaveFile(str(path))
            self.assertEqual(box.verify(),[])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),r['sha256'])
            self.assertEqual(r['sequence'],'d63bb68c219adbe2')
            self.assertEqual(r['clock'],(1449,3,1,15,0,0))
            with self.assertRaises(ValueError):probe.build(source,output)
            wrong=Path(tmp)/'wrong';wrong.write_bytes(b'wrong source')
            with self.assertRaises(ValueError):probe.build(wrong,Path(tmp)/'absent')
            self.assertFalse((Path(tmp)/'absent').exists())
        self.assertEqual(source.read_bytes(),raw)


@unittest.skipUnless(os.environ.get('FEFW_GAMEDATA'),'No private GameData supplied')
class SewersDataTest(unittest.TestCase):
    def test_city_entrance_checks_exact_chapter2_dialogue_and_accepts_chapter4_phase(self):
        r=report(os.environ['FEFW_GAMEDATA'])
        self.assertEqual(r['read_function'],'IsAlreadyRead')
        self.assertEqual(r['entrance']['dialogue'],probe.DIALOGUE)
        self.assertEqual(r['entrance']['offset'],'0x2fbc10')
        self.assertEqual(r['entrance']['route'],['KAI'])
        self.assertIn('拠点_カイ篇1部4章_行動制限1',r['entrance']['allowed_phase_flags'])
