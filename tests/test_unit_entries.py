"""Synthetic identities/owners and optional private defaults checks."""
from pathlib import Path
import os
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import unit_entries as entries
import facilities
import story_start
from test_story import fixture as story_fixture, box_for

CAI=core.id_hash('PID_カイ')
CATANIA=core.id_hash('PID_カターニャ')
OLYMPIA=core.id_hash('PID_オリンピア')


def fixture(people=((CAI,12),), equipped=False):
    f=story_fixture(chapter=9);table=f.ptr(0);p=bytearray(f.payload[:table])
    roots=[(b.hash,b.start) for b in f.blocks]
    h=f.block('Header').start;p[h+20:h+22]=b'\x12\x05'
    def leaf(body):
        at=len(p);p.extend(bytes(4)+body);p.extend(bytes(-len(p)%4))
        struct.pack_into('<I',p,at,len(p)+32);return at
    pool=len(p);p.extend(bytes(4)+b'\0\4'+struct.pack('<H',len(people)))
    for person,number in people:
        at=len(p);p.extend(bytes(72));p[at+4]=36
        struct.pack_into('<II',p,at+10,person,0xf55f5af3)
        p[at+18:at+26]=bytes(range(1,9));p[at+26:at+35]=bytes(range(9))
        struct.pack_into('<h',p,at+37,number)  # same numeric value, NOT a reference
        p[at+59]=8;struct.pack_into('<H',p,at+60,725);struct.pack_into('<H',p,at+64,31)
        leaf(b'\1\0\x50\0\1'+struct.pack('<IBB',0xf55f5af3,15,0))
        p.extend(b'\xff\xff\xff\xff\0\0\0\0')
        leaf(b'\0\0\0')
        for i in range(6):leaf(b'\0\1\0\x43'+struct.pack('<I',0xbeef0000+i))
        p.append(35);p.extend(core.Ride(0x1234,number,3,0,0,'',b'',0).bytes() if equipped else b'\0')
        p.extend(core.Legion(0,number,0x5678).bytes() if equipped else b'\0')
        p.extend(bytes([0,number,0,3,0,0,0,0,0,0,33,0,0,4,0,5,1]))
        p.extend(struct.pack('<II',0x12345678,99));p.extend(b'\0\0\0\0\0\xff\xff\0')
        p.extend(bytes(-len(p)%4));struct.pack_into('<I',p,at,len(p)+32)
    p.extend(b'\xff\0\0\0');struct.pack_into('<I',p,pool,len(p)+32)
    roots.append((core.fnv1_32(b'UnitPool'),pool))
    for name,member,body in [('RidePool',core._RIDE_M,b'\0\1\0'+core.Ride(0x1234,people[0][1],3,0,0,'',b'',0).bytes()),
                             ('LegionPool',core._LEGION_M,b'\0\1\0'+core.Legion(0,people[0][1],0x5678).bytes())]:
        start=len(p);p.extend(bytes(4));child=leaf(body if equipped else b'\0\0\0')
        t=len(p);p.extend(struct.pack('<II',member,child+32));struct.pack_into('<I',p,start,(1<<24)|(t+32))
        roots.append((core.fnv1_32(name.encode()),start))
    t=len(p)
    for key,at in roots:p.extend(struct.pack('<II',key,at+32))
    struct.pack_into('<I',p,0,(len(roots)<<24)|(t+32))
    return core.SaveFile(p)


class UnitEntryTest(unittest.TestCase):
    def test_anna_uses_accepted_dismounted_profile(self):
        f=fixture();person=core.id_hash('PID_アンナ')
        g=core.SaveFile(entries.add(f,person));u=g.units()[-1]
        mounted=core.id_hash('JID_戦象兵');dismounted=core.id_hash('JID_戦象兵下馬')
        self.assertEqual(u.klass,dismounted)
        self.assertEqual(u.classes,[(mounted,0,4),(dismounted,0,4)])
        self.assertEqual(u.items,[core.id_hash('IID_青銅の槍')])
        self.assertIn('Mounted Elephant Rider also passed Part 3',entries.catalog()[person]['evidence'])
        self.assertEqual(entries.status(g,person),'Already in party')
        with self.assertRaises(core.SaveError):entries.add(g,person)

    def test_creation_uses_own_defaults_and_preserves_existing_records(self):
        f=fixture(equipped=True);before=bytes(f.payload);old=story_start.normalized_blocks(f)
        original=f.tree().copy_object(f.tree().node_at(f.units()[0].start),0)
        g=core.SaveFile(entries.add(f,CATANIA));rows=entries.roster(g);u,gear=rows[-1]
        self.assertEqual((u.person,gear.unit_number),(CATANIA,13))
        self.assertEqual(g.payload[u.level_off],1);self.assertEqual(u.stats,[0]*9)
        self.assertEqual(u.counters,[]);self.assertIsNone(gear.ride);self.assertIsNone(gear.legion)
        self.assertTrue(all(0<x<2**31 for x in struct.unpack_from('<II',g.payload,u.start+18)))
        self.assertNotEqual(g.payload[u.start+18:u.start+26],f.payload[f.units()[0].start+18:f.units()[0].start+26])
        self.assertFalse(any(0xbeef0000<=x<=0xbeef0005 for group in u.skill_lists for x in group))
        self.assertEqual(u.klass,core.id_hash('JID_兵士'))
        self.assertEqual(g.tree().copy_object(g.tree().node_at(g.units()[0].start),0),original)
        new=story_start.normalized_blocks(g)
        for name in old.keys()-{'UnitPool','GameUserData'}:self.assertEqual(old[name],new[name])
        flags=entries.flag_values(g)
        self.assertEqual(flags[core.id_hash('加入_カターニャ')],1)
        self.assertEqual(flags[core.id_hash('面識_カターニャ')],1)
        self.assertEqual(bytes(f.payload),before)
        third=core.SaveFile(entries.add(g,OLYMPIA));self.assertEqual(entries.roster(third)[-1][1].unit_number,14)
        with self.assertRaises(core.SaveError):entries.add(third,CATANIA)

    def test_same_character_alias_and_identity_collisions_refused(self):
        alias=int(entries.catalog()[CAI]['aliases'][0],16)
        with self.assertRaises(core.SaveError):entries.add(fixture(((alias,8),)),CAI)
        for f in [fixture(((CATANIA,8),)),fixture(((CAI,8),(OLYMPIA,8)))]:
            before=bytes(f.payload)
            with self.assertRaises(core.SaveError):entries.add(f,CATANIA)
            self.assertEqual(f.payload,before)
        with self.assertRaises(core.SaveError):entries.add(fixture(((CAI,254),)),CATANIA)
        with self.assertRaises(core.SaveError):entries.renumber(fixture(((CAI,12),(alias,13))),CAI,14)

    def test_unmapped_affinity_and_orphan_equipment_number_are_not_reused(self):
        f=fixture(equipped=True);pool=core.party_store(f)[1]
        rides=core.rides(f,pool);r=rides[0]
        r.owner=20
        changed=core.SaveFile(core.with_rides(f,pool,rides))
        self.assertEqual(entries.next_number(changed),21)
        r.allies=b'\x40\x01\x00'
        changed=core.SaveFile(core.with_rides(f,pool,rides))
        for action in (lambda:entries.add(changed,CATANIA),lambda:entries.renumber(changed,CAI,23)):
            with self.assertRaises(core.SaveError):action()

    def test_renumber_changes_typed_ownership_but_not_stats_or_other_units(self):
        f=fixture(((CAI,12),(OLYMPIA,14)),equipped=True)
        before=bytes(f.payload);rows=entries.roster(f)
        allowed={core.tail_at(f.payload,rows[0][0].start,rows[0][0].end)-9}
        allowed.update(at for at,owner,_ in entries._references(f,rows) if owner==12)
        g=core.SaveFile(entries.renumber(f,CAI,42))
        changed={i for i,(a,b) in enumerate(zip(before,g.payload)) if a!=b}
        self.assertEqual(changed,allowed)
        self.assertEqual([g.unit_number for _,g in entries.roster(g)],[42,14])
        self.assertEqual(g.units()[0].stats[0],12)
        self.assertEqual(entries.renumber(g,CAI,12),f.payload)
        for number in (0,255,256,-1,14,True,1.5):
            with self.assertRaises(core.SaveError):entries.renumber(f,CAI,number)
        self.assertEqual(entries.renumber(f,CAI,12),f.payload)

    def test_duplicate_number_repair_refuses_ambiguous_ownership(self):
        f=fixture(((CAI,12),(OLYMPIA,12)))
        g=core.SaveFile(entries.renumber(f,CAI,13))
        self.assertEqual([x.unit_number for _,x in entries.roster(g)],[13,12])
        with self.assertRaises(core.SaveError):entries.renumber(fixture(((CAI,12),(OLYMPIA,12)),True),CAI,13)

    def test_inactive_restore_preserves_the_unit_and_blocks_unknown_states(self):
        f=fixture()
        f=core.SaveFile(core.flag_add(f,facilities.locate(f),core.id_hash('加入_カイ'),0))
        f=core.SaveFile(core.flag_add(f,facilities.locate(f),core.id_hash('面識_カイ'),1))
        self.assertTrue(entries.status(f,CAI).startswith('Existing inactive'))
        old=story_start.normalized_blocks(f)
        g=core.SaveFile(entries.restore(f,CAI))
        self.assertEqual(entries.status(g,CAI),'Already in party')
        self.assertEqual(old['UnitPool'],story_start.normalized_blocks(g)['UnitPool'])
        with self.assertRaises(core.SaveError):entries.restore(g,CAI)
        bad=core.SaveFile(core.flag_add(f,facilities.locate(f),core.id_hash('加入_カターニャ'),9))
        with self.assertRaises(core.SaveError):entries.add(bad,CATANIA)
        for value in (0,1):
            met=core.SaveFile(core.flag_add(f,facilities.locate(f),core.id_hash('面識_カターニャ'),value))
            added=core.SaveFile(entries.add(met,CATANIA))
            self.assertEqual(entries.flag_values(added)[core.id_hash('面識_カターニャ')],1)

    def test_context_corrupt_pool_and_exhaustion_refused(self):
        for mode in (b'\x10\x08',b'\x12\x06'):
            f=fixture();h=f.block('Header').start;f.payload[h+20:h+22]=mode
            with self.assertRaises(core.SaveError):entries.add(f,CATANIA)
        f=fixture();f.payload[f.block('UnitPool').end-1]=3
        with self.assertRaises(core.SaveError):entries.add(f,CATANIA)
        f=fixture(equipped=True);pool=core.party_store(f)[1];f.payload[pool+4]=9
        with self.assertRaises(core.SaveError):entries.add(f,CATANIA)

    def test_copy_guard_reallocates_and_refuses_same_character_or_shared_gear(self):
        src=fixture(((CATANIA,12),));dst=fixture()
        g=core.SaveFile(entries.copy_in(src,src.units()[0],dst))
        self.assertEqual([x.unit_number for _,x in entries.roster(g)],[12,13])
        with self.assertRaises(core.SaveError):entries.copy_in(src,src.units()[0],g)
        src=fixture(((CATANIA,12),),True)
        with self.assertRaises(core.SaveError):entries.copy_in(src,src.units()[0],dst)

    def test_save_reload_and_numbered_backups(self):
        f=fixture();box=box_for(f)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes());original=path.read_bytes()
            box=container.SaveFile(str(path));box.payload=entries.add(core.SaveFile(box.payload),CATANIA);box.save()
            reload=container.SaveFile(str(path));self.assertEqual(reload.verify(),[])
            self.assertEqual(entries.status(core.SaveFile(reload.payload),CATANIA),'Already in party')
            box.payload=entries.renumber(core.SaveFile(box.payload),CATANIA,30);box.save()
            self.assertEqual(Path(str(path)+'.bak').read_bytes(),original)
            self.assertTrue(Path(str(path)+'.bak1').exists())


@unittest.skipUnless(os.environ.get('FEFW_GAMEDATA'),'No private game tables supplied')
class UnitDefaultsTest(unittest.TestCase):
    def test_recovered_defaults_are_reproducible(self):
        import json
        from research.unit_catalog_report import report
        self.assertEqual(report(os.environ['FEFW_GAMEDATA']),json.loads((entries.HERE/'unit_catalog.json').read_text()))


@unittest.skipUnless(os.environ.get('FEFW_UNIT_SOURCES'),'No private route saves supplied')
class PrivateUnitEntryTest(unittest.TestCase):
    def sources(self):
        import json
        return json.loads(Path(os.environ['FEFW_UNIT_SOURCES']).read_text()).items()

    def test_all_supported_candidates_preserve_each_route_save(self):
        for route,path in self.sources():
            box=container.SaveFile(path);self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);before=bytes(f.payload)
            blocks=story_start.normalized_blocks(f);flags=entries.flag_values(f)
            original=[f.tree().copy_object(f.tree().node_at(u.start),0) for u in f.units()]
            present={entries.canonical(u.person) for u in f.units()}
            number=entries.next_number(f)
            for person,row in entries.catalog().items():
                if person in present or row['restriction']:continue
                with self.subTest(route=route,name=row['name']):
                    g=core.SaveFile(entries.add(f,person));self.assertEqual(f.payload,before)
                    got=[g.tree().copy_object(g.tree().node_at(u.start),0) for u in g.units()]
                    self.assertEqual(original,got[:-1])
                    after=story_start.normalized_blocks(g)
                    for name in blocks.keys()-{'UnitPool','GameUserData'}:
                        self.assertEqual(blocks[name],after[name],name)
                    updated=entries.flag_values(g)
                    wanted=dict(flags)
                    for name in (row['recruit_flag'],row['met_flag']):
                        if name:wanted[core.id_hash(name)]=1
                    self.assertEqual(updated,wanted)
                    u,gear=entries.roster(g)[-1]
                    self.assertEqual((u.person,gear.unit_number),(person,number))
                    self.assertEqual(u.skill_lists,[[int(h,16) for h in xs] for xs in row['skills']])
                    self.assertEqual(u.progress,bytes(9));self.assertEqual(u.counters,[])
                    self.assertEqual(entries.status(g,person),'Already in party')

    def test_repeated_additions_renumber_and_container_roundtrip(self):
        for route,path in self.sources():
            with self.subTest(route=route):
                box=container.SaveFile(path);f=core.SaveFile(box.payload)
                old=[(u.person,g.unit_number) for u,g in entries.roster(f)]
                people={entries.canonical(u.person) for u in f.units()}
                for person,row in entries.catalog().items():
                    if person not in people and not row['restriction']:
                        f=core.SaveFile(entries.add(f,person))
                rows=entries.roster(f);numbers=[g.unit_number for _,g in rows]
                self.assertEqual(len(numbers),len(set(numbers)))
                self.assertEqual([(u.person,g.unit_number) for u,g in rows[:len(old)]],old)
                g=core.SaveFile(entries.renumber(f,old[0][0],max(numbers)+1))
                self.assertEqual(entries.renumber(g,old[0][0],old[0][1]),f.payload)
                box.payload=g.payload
                with tempfile.TemporaryDirectory() as tmp:
                    target=Path(tmp)/'Auto';target.write_bytes(box.to_bytes())
                    reread=container.SaveFile(str(target));self.assertEqual(reread.verify(),[])
                    self.assertEqual([(u.person,x.unit_number) for u,x in entries.roster(core.SaveFile(reread.payload))],
                                     [(u.person,x.unit_number) for u,x in entries.roster(g)])
