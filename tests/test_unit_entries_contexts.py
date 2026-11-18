"""Synthetic pre-battle, mid-battle and chapter-start recruitment checks."""
import struct
import unittest

import fefw_core as core
import story_start
import unit_entries as entries
from test_unit_entries import fixture, CAI, CATANIA, OLYMPIA
from test_unit_entry_page import Harness
from test_mirroring import peers


def grouped_fixture(groups, mode=b'\x12\x02'):
    f=fixture();pool=f.block('UnitPool');tree=f.tree()
    body=bytearray(b'\0')
    for kind,people in groups:
        body.extend(bytes([kind])+struct.pack('<H',len(people)))
        body.extend(bytes(-(pool.start+4+len(body))%4))
        for person,number,battle in people:
            at=pool.start+4+len(body)
            record=bytearray(entries._record(entries.catalog()[person],number,at))
            if battle:
                cur=struct.unpack_from('<I',record,72)[0]-32-at+8
                for _ in range(7):cur=struct.unpack_from('<I',record,cur)[0]-32-at
                child=at+cur+4
                record=(record[:cur+3]+b'\0'+struct.pack('<I',child+12+32)
                        +b'\x09'+bytes(7)+record[cur+3:]+bytes(3))
                record[5]=1;struct.pack_into('<I',record,0,at+len(record)+32)
            body.extend(record)
    body.append(255);body.extend(bytes(-(pool.start+4+len(body))%4))
    out=tree.splice(tree.node_at(pool.start),pool.start+4,pool.end-pool.start-4,body)
    g=core.SaveFile(out);h=g.block('Header').start;g.payload[h+20:h+22]=mode
    return g


def records(f):
    tree=f.tree()
    return {(kind,i):tree.copy_object(tree.node_at(u.start),0)
            for kind,_,_,rows in entries.pool_groups(f) for i,(u,g) in enumerate(rows)}


class UnitContextsTest(unittest.TestCase):
    def test_pre_battle_and_chapter_start_creation_preserves_units_and_state(self):
        for mode,label in ((b'\x12\x04','pre-battle'),(b'\x10\x0b','chapter-start')):
            f=grouped_fixture([(4,[(CAI,12,False)])],mode)
            before=bytes(f.payload);old=records(f);blocks=story_start.normalized_blocks(f)
            self.assertEqual(entries.context(f),label)
            g=core.SaveFile(entries.add(f,CATANIA))
            self.assertEqual(records(g)[(4,0)],old[(4,0)])
            self.assertEqual(entries.status(g,CATANIA),'Already in party')
            for key,value in blocks.items():
                if key not in ('UnitPool','GameUserData'):
                    self.assertEqual(story_start.normalized_blocks(g)[key],value)
            with self.assertRaises(core.SaveError):entries.renumber(g,CATANIA,99)
            self.assertEqual(f.payload,before)

    def test_mid_battle_reserve_add_preserves_allies_opponents_and_hidden_units(self):
        for reserve in ([],[(4,[(OLYMPIA,15,False)])]):
            f=grouped_fixture([(0,[(CAI,12,True)]),
                (1,[(CATANIA,80,True),(CATANIA,81,True)]),*reserve,
                (6,[(entries.canonical(core.id_hash('PID_アンナ')),49,False)])])
            before=bytes(f.payload);old=records(f);blocks=story_start.normalized_blocks(f)
            g=core.SaveFile(entries.add(f,CATANIA))
            # Enemy copies do not prevent recruitment; their numbers are occupied.
            self.assertEqual(next(gear.unit_number for u,gear in entries.roster(g) if u.person==CATANIA),82)
            self.assertTrue(all(records(g)[key]==value for key,value in old.items()))
            self.assertEqual([(u.person) for u in g.units()],[CAI])
            for key,value in blocks.items():
                if key not in ('UnitPool','GameUserData'):
                    self.assertEqual(story_start.normalized_blocks(g)[key],value)
            with self.assertRaises(core.SaveError):entries.add(g,CATANIA)
            with self.assertRaises(core.SaveError):entries.add(g,core.id_hash('PID_アンナ'))
            with self.assertRaises(core.SaveError):entries.renumber(g,CAI,99)
            self.assertEqual(f.payload,before)

    def test_unknown_group_battle_version_duplicate_number_and_truncation_refused(self):
        f=grouped_fixture([(0,[(CAI,12,True)]),(4,[(OLYMPIA,15,False)])])
        variants=[]
        bad=f.copy();bad.payload[bad.block('UnitPool').start+5]=2;variants.append(bad)
        bad=f.copy();bad.payload[bad.block('UnitPool').start+6]=99;variants.append(bad)
        bad=f.copy();u=bad.units()[0];cur=bad.ptr(u.start+72)+8
        for _ in range(7):cur=bad.ptr(cur)
        bad.payload[cur+8]=10;variants.append(bad)
        variants.append(grouped_fixture([(0,[(CAI,12,True)]),(1,[(CATANIA,12,True)])]))
        for bad in variants:
            before=bytes(bad.payload)
            with self.assertRaises(core.SaveError):entries.add(bad,CATANIA)
            self.assertEqual(bad.payload,before)

    def test_mid_battle_mirrored_add_undo_redo_and_invalid_peer_atomicity(self):
        a=Harness();a.sv.payload=grouped_fixture([(0,[(CAI,12,True)])]).payload
        slots=peers(a);before=[bytes(s.payload) for s in slots]
        self.assertTrue(a.apply_unit_entry('add',CATANIA),a.messages)
        after=[bytes(s.payload) for s in slots]
        a.undo();self.assertEqual([bytes(s.payload) for s in slots],before)
        a.redo();self.assertEqual([bytes(s.payload) for s in slots],after)
        a.undo();f=core.SaveFile(slots[-1].payload)
        slots[-1].payload[f.block('UnitPool').start+5]=2
        before=[bytes(s.payload) for s in slots]
        self.assertFalse(a.apply_unit_entry('add',CATANIA))
        self.assertEqual([bytes(s.payload) for s in slots],before)
