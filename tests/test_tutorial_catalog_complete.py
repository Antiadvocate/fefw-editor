"""Full catalogue coverage, empty-list roundtrips and private case exports."""
from pathlib import Path
import json
import os
import struct
import tempfile
import unittest

import facilities
import fefw_core as core
import fefw_save as container
import story
import story_start as start
import tutorials as tut
from research.tutorial_catalog_report import report
from research.cai_tutorial_test_kit import build, CHAPTERS
from test_fast_travel import fixture
from test_facilities import rows as general_rows
from test_tutorials import rows, raw_map, AUTO


def structured(entries):
    f=fixture([general_rows(),entries]);tree=core.SaveTree(f.payload)
    general=facilities.locate(f);parent=tree.nodes[tree.nodes[tree.node_at(general.start)].parent]
    table=f.ptr(parent.start)
    # The synthetic fixture emits a spacer followed by general/tutorial leaves.
    struct.pack_into('<I',f.payload,table+16,tut.MAP_MEMBER)
    return core.SaveFile(f.payload)


class CompleteTutorialTest(unittest.TestCase):
    def test_catalogue_identities_evidence_and_known_names_are_separate(self):
        cat=tut.catalog();self.assertEqual(len(cat),218)
        self.assertEqual(sum(r['evidence']=='provisional-translation' for r in cat.values()),38)
        labels={};tut.apply_labels(labels)
        practice=core.id_hash('TUTO_稽古')
        self.assertEqual(cat[practice]['label'],'Mentoring (Cai)')
        self.assertNotIn('(provisional)',labels[practice]['label'])
        self.assertEqual(tut.evidence_label(cat[practice]), 'Game title checked')
        self.assertEqual(labels[practice]['name'],'TUTO_稽古')
        self.assertNotIn('provisional',labels[AUTO]['label'])
        self.assertEqual({r['category'] for r in cat.values()},set(tut.CATEGORIES))

    def test_all_entries_add_clear_and_restore_empty_member(self):
        f=structured([]);original=bytes(f.payload)
        self.assertEqual(tut.read(f),{})
        full=core.SaveFile(tut.edited(f,{h:2 for h in tut.catalog()}))
        self.assertEqual(tut.read(full),dict.fromkeys(tut.catalog(),2))
        self.assertEqual(tut.edited(full,{h:2 for h in tut.catalog()}),full.payload)
        empty=core.SaveFile(tut.edited(full,{h:None for h in tut.catalog()}))
        self.assertEqual(tut.read(empty),{})
        self.assertEqual(start.normalized_blocks(empty),start.normalized_blocks(f))
        self.assertEqual(f.payload,original)

    def test_bulk_edits_preserve_unknown_records_and_wide_encoding(self):
        f=structured(rows());before=raw_map(f,tut.locate(f))
        full=core.SaveFile(tut.edited(f,{h:2 for h in tut.catalog()}))
        empty=core.SaveFile(tut.edited(full,{h:None for h in tut.catalog()}))
        self.assertEqual(raw_map(empty,tut.locate(empty)),{h:v for h,v in before.items() if h not in tut.catalog()})
        self.assertEqual(raw_map(f,facilities.locate(f)),raw_map(empty,facilities.locate(empty)))

    def test_wrong_member_duplicates_and_ambiguous_lists_are_refused(self):
        f=structured(rows());fm=tut.locate(f);tree=core.SaveTree(f.payload)
        parent=tree.nodes[tree.nodes[tree.node_at(fm.start)].parent];table=f.ptr(parent.start)
        p=bytearray(f.payload);struct.pack_into('<I',p,table+16,0xdeadbeef)
        with self.assertRaises(core.SaveError):tut.edited(core.SaveFile(p),{AUTO:None})
        with self.assertRaises(core.SaveError):tut.read(structured(rows()+[rows()[0]]))
        bad=core.SaveFile(core.flag_add(f,facilities.locate(f),AUTO,2))
        with self.assertRaises(core.SaveError):tut.read(bad)


@unittest.skipUnless(os.environ.get('FEFW_GAMEDATA'),'No private game tables supplied')
class TutorialTablesTest(unittest.TestCase):
    def test_all_source_rows_and_title_ids_match_including_ideographic_space(self):
        actual=report(os.environ['FEFW_GAMEDATA']);cat=tut.catalog()
        self.assertEqual(set(actual['entries']),{f'{h:08x}' for h in cat})
        self.assertEqual([s['entries'] for s in actual['sources']],[217,1])
        for key,row in actual['entries'].items():
            for field in ('name','title_id','source','offset'):
                self.assertEqual(cat[int(key,16)][field],row[field])
        self.assertIn('\u3000',cat[0x759e15fb]['name'])


@unittest.skipUnless(os.environ.get('FEFW_CAI_KIT_SOURCES'),'No private Cai kit inputs supplied')
class CaiKitTest(unittest.TestCase):
    def test_every_export_validates_and_preserves_originals_and_controls(self):
        source=Path(os.environ['FEFW_CAI_KIT_SOURCES'])
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'cases';result=build(source,out)
            self.assertEqual([r['chapter'] for r in result['cases'] if r['kind']=='chapter-entry'],list(CHAPTERS))
            self.assertEqual(len(result['cases']),12)
            self.assertEqual(next(r['clock'] for r in result['cases'] if r['chapter']==1),(1449,1,24,2,0,0))
            self.assertEqual(next(r['tutorial_records'] for r in result['cases'] if r['case']=='TUT5-02-All-218'),218)
            self.assertEqual(next(r['tutorial_records'] for r in result['cases'] if r['case']=='TUT5-03-Empty'),0)
            for row in result['cases']:
                box=container.SaveFile(str(out/row['case']/'Auto'));self.assertEqual(box.verify(),[])
                if row['kind']=='chapter-entry':
                    self.assertEqual(start.edited(core.SaveFile(box.payload),row['chapter']),box.payload)
            with self.assertRaises(ValueError):build(source,out)

    def test_cai_chapter_one_keeps_native_year_and_all_timeline_dates_match(self):
        from research.story_timeline_report import report as timeline
        source=Path(os.environ['FEFW_CAI_KIT_SOURCES'])/'Chapter_Kai_1_1'
        f=core.SaveFile(container.SaveFile(str(source)).payload)
        # Early Chapter 1 has no free-time anchors: the full group signature
        # identifies only its sibling stores, without relaxing general edits.
        with self.assertRaises(core.SaveError):facilities.locate(f)
        self.assertIsNotNone(facilities.locate_history(f))
        empty=core.SaveFile(tut.edited(f,{h:None for h in tut.catalog()}))
        self.assertEqual(tut.read(empty),{})
        tree,group,_=facilities.flag_group(f);at=tree.nodes[group].start;table=f.ptr(at)
        bad=bytearray(f.payload);struct.pack_into('<I',bad,table,0xdeadbeef)
        with self.assertRaises(core.SaveError):start.edited(core.SaveFile(bad),3)
        native=story.read(f)
        for chapter in range(1,13):
            g=core.SaveFile(start.edited(f,chapter));info=start.validate(g)
            self.assertEqual((info.route,info.part,info.chapter),(1,1,chapter))
            self.assertEqual(struct.unpack_from('<H',g.payload,info.header+22)[0],1449)
        g=core.SaveFile(start.edited(f,1));info=story.read(g)
        self.assertEqual(g.payload[info.header+22:info.header+29],f.payload[native.header+22:native.header+29])
        if os.environ.get('FEFW_GAMEDATA'):
            for row in timeline(os.environ['FEFW_GAMEDATA'],'cai')['chapters'][1:]:
                self.assertEqual(start.target(row['chapter'],1),(row['month'],row['day'],row['time']//100,row['time']%100))
