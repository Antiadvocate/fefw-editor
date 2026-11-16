"""Journal editing must not remove its own map identity or alter progression."""
import os
from pathlib import Path
import struct
import tempfile
import unittest

import facilities as fac
import facility_access
import fefw_core as core
import fefw_save as container
import story
import story_start
from research.function_access_probes import build, FIRST_FREE, TRAINING, PRACTICE
from test_facilities import rows, outside
from test_fast_travel import fixture
from test_tutorials import raw_map


class FunctionsTest(unittest.TestCase):
    def test_journal_can_be_removed_and_reenabled_without_losing_map_identity(self):
        journal = {h for h,r in fac.catalog().items() if r['kind']=='Journal'}
        quest = 0x31bdf33c
        self.assertEqual(len(journal),6)
        self.assertNotIn(quest,fac.ANCHORS)
        # Cai has only the map/travel anchors before first free time.
        source = [r for r in rows() if r[0]!=FIRST_FREE] + [(quest,1,True)]
        f = fixture([source]); before = outside(f)
        g = core.SaveFile(fac.edited(f,{h:False for h in journal}))
        self.assertNotIn(quest,fac.read(g))
        self.assertEqual(fac.read(g)[0x78814e6e],1)
        self.assertEqual(outside(g),before)
        g = core.SaveFile(fac.edited(g,{h:True for h in journal}))
        self.assertNotIn(0x78814e6e,fac.read(g))
        self.assertEqual(fac.read(g)[quest],1)
        self.assertEqual(outside(g),before)
        with self.assertRaises(core.SaveError): fac.edited(f,{FIRST_FREE:True})
        # Quest list alone plus one immutable anchor is insufficient evidence.
        sparse = [(next(iter(fac.ANCHORS)),1,False),(quest,1,False)]
        with self.assertRaises(core.SaveError): fac.read(fixture([sparse]))

    def test_arena_diagnostics_never_treat_training_as_an_arena_switch(self):
        f = fixture([rows()]); before=bytes(f.payload)
        row=next(r for r in facility_access.report(f) if r.get('id')=='arena')
        self.assertEqual(row['stored'],'Switch not mapped')
        self.assertIsNone(row['hash'])
        self.assertIn('not a proven substitute',row['detail'])
        self.assertEqual(bytes(f.payload),before)
        self.assertNotIn(core.id_hash('機能開放_闘技場'),fac.catalog())


@unittest.skipUnless(os.environ.get('FEFW_CAI1_RETURN_DIR'),'No private Cai Test 1 returns supplied')
class Cai1ReturnsTest(unittest.TestCase):
    def root(self): return Path(os.environ['FEFW_CAI1_RETURN_DIR'])

    def test_five_returns_validate_and_record_progression_and_missing_prerequisites(self):
        paths=sorted(self.root().rglob('Auto*'));self.assertEqual(len(paths),5)
        seqs={}
        for path in paths:
            raw=path.read_bytes();box=container.SaveFile(str(path));self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);info=story.read(f);chapter=int(path.parent.name.split('-')[1])
            self.assertEqual((info.route,info.part,info.chapter),(1,1,chapter))
            self.assertEqual(box.raw[40:43],bytes((1,1,chapter)))
            seqs.setdefault(chapter,set()).add(info.sequence)
            if chapter==2 and path.name=='Auto':
                with self.assertRaises(core.SaveError):story_start.validate(f)
            else:self.assertEqual(story_start.validate(f).chapter,chapter)
            values=fac.read(f)
            self.assertTrue(all(values.get(h) is None for h,r in fac.catalog().items() if r['kind']=='Journal'))
            self.assertEqual(path.read_bytes(),raw)
        self.assertEqual({k:len(v) for k,v in seqs.items()},{2:2,4:1,9:2})
        for name in ('Auto','Auto-after-advancement'):
            f=core.SaveFile(container.SaveFile(str(self.root()/'CAI1-09-Chapter-09'/name)).payload)
            values=fac.read(f);expected=1 if name.endswith('advancement') else None
            for h in (FIRST_FREE,TRAINING,PRACTICE,0x948de8dd,0x9402533e):self.assertEqual(values.get(h),expected)

    def test_probe_files_only_change_named_flags_and_preserve_story_party_other_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'cases';report=build(self.root(),output)
            self.assertEqual(len(report['cases']),6)
            for row in report['cases']:
                source=self.root()/('CAI1-04-Chapter-04/Auto' if row['chapter']==4 else 'CAI1-09-Chapter-09/Auto-after-advancement')
                original=source.read_bytes();before=core.SaveFile(container.SaveFile(str(source)).payload)
                box=container.SaveFile(str(output/row['case']/'Auto'));self.assertEqual(box.verify(),[])
                after=core.SaveFile(box.payload);a,b=story.read(before),story.read(after)
                self.assertEqual((a.route,a.part,a.chapter,a.sequence),(b.route,b.part,b.chapter,b.sequence))
                self.assertEqual(before.payload[a.header+20:a.header+29],after.payload[b.header+20:b.header+29])
                self.assertEqual(outside(before),outside(after))
                allowed={int(h,16) for h in row['switches']}
                if row['research_only_first_free']:allowed.add(FIRST_FREE)
                old,new=raw_map(before,fac.locate(before)),raw_map(after,fac.locate(after))
                self.assertEqual({k:v for k,v in old.items() if k not in allowed},{k:v for k,v in new.items() if k not in allowed})
                self.assertEqual(source.read_bytes(),original)
            with self.assertRaises(ValueError):build(self.root(),output)
