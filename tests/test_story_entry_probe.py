"""Synthetic checkpoint-entry diagnostics and explicit preservation limits."""
from pathlib import Path
import os,struct,tempfile,unittest
import fefw_core as core
import story
from research import story_entry_probe as probe
from test_story import fixture as old_fixture


def fixture():
    f=old_fixture(chapter=9,seq=0xd1a25c2f18128a5b);t=core.SaveTree(f.payload);p=bytearray(4);blocks=[]
    for b in f.blocks:
        at=len(p);p.extend(t.copy_object(t.node_at(b.start),at));blocks.append((b.name,at))
    clock=struct.pack('<H5B',1449,7,12,21,6,31);p[24:26]=b'\x12\x05';p[26:33]=clock
    def leaf(body):
        at=len(p);p.extend(bytes(4)+body);p.extend(bytes(-len(p)%4));struct.pack_into('<I',p,at,len(p)+32);return at
    blocks.append(('GameSchedule',leaf(b'\x01'+clock+struct.pack('<H5B',1449,9,1,12,0,0)+bytes(5))))
    blocks.append(('Calendar',leaf(b'\x06'+bytes(5)+struct.pack('<HBB',1449,7,12)+bytes(2))))
    restart=len(p);p.extend(bytes(4)+b'\x03\0\0\0');slots=[]
    def blob(body):
        header=struct.pack('<IIII',core.MAGIC,len(body),core.fnv1_32(body),1)+bytes(16)
        encoded=header+body;return struct.pack('<I',len(encoded))+encoded
    for i,key in enumerate(sorted(probe.RESTART_KEYS)):
        start=len(p);p.extend(bytes(4));slots.append((key,start))
        h=leaf(blob(b'\xaa'*224) if i==0 else bytes(4))
        d=leaf(blob(b'\xbb'*100) if i==0 else bytes(4))
        table=len(p);p.extend(struct.pack('<IIII',probe.HEADER_KEY,h+32,probe.DATA_KEY,d+32))
        struct.pack_into('<I',p,start,(2<<24)|(table+32))
    table=len(p)
    for key,at in slots:p.extend(struct.pack('<II',key,at+32))
    struct.pack_into('<I',p,restart,(8<<24)|(table+32));blocks.append(('GameRestartData',restart))
    table=len(p)
    for name,at in blocks:p.extend(struct.pack('<II',core.fnv1_32(name.encode()),at+32))
    struct.pack_into('<I',p,0,(len(blocks)<<24)|(table+32))
    return core.SaveFile(p)


class EntryProbeTest(unittest.TestCase):
    def test_three_profiles_isolate_mode_restart_and_calendar(self):
        f=fixture();before=bytes(f.payload);old=probe.normalized_blocks(f)
        for profile in 'ABC':
            g=core.SaveFile(probe.edited_profile(f,9,profile));new=probe.normalized_blocks(g);i=story.read(g)
            self.assertEqual(g.payload[i.header+20:i.header+22],b'\x10\x0b')
            self.assertEqual(i.sequence,story.sequence(9))
            self.assertEqual(new['GameSound'],old['GameSound'])
            if profile=='A':self.assertEqual(new['GameRestartData'],old['GameRestartData'])
            else:
                self.assertEqual(len(new['GameRestartData']),360)
                self.assertEqual(len(probe.restart_leaves(g)),16)
                self.assertEqual(probe.clear_restart(g),g.payload)
            if profile=='C':
                clock=struct.pack('<H5B',1449,7,10,18,0,0);s=probe.one_block(g,'GameSchedule');c=probe.one_block(g,'Calendar')
                self.assertEqual(g.payload[s.start+5:s.end],clock+bytes(12))
                self.assertEqual(g.payload[i.header+22:i.header+29],clock)
                self.assertEqual(g.payload[c.start+5:c.end],bytes(11))
            else:
                for n in ('GameSchedule','Calendar'):self.assertEqual(new[n],old[n])
        self.assertEqual(bytes(f.payload),before)
        g=core.SaveFile(probe.edited_profile(f,4,'C'));i=story.read(g)
        self.assertEqual(g.payload[i.header+22:i.header+29],struct.pack('<H5B',1449,3,1,8,0,0))

    def test_unknown_layout_and_corrupt_restart_are_refused_atomically(self):
        f=fixture();info=story.read(f)
        for at,value in ((info.header+20,99),(info.header+12,1),
                         (probe.one_block(f,'Calendar').start+4,99),
                         (probe.one_block(f,'GameSchedule').start+5,0),
                         (probe.restart_leaves(f)[0]+16,123)):
            g=core.SaveFile(f.payload);g.payload[at]=value;before=bytes(g.payload)
            with self.assertRaises(core.SaveError):probe.edited_profile(g,9,'C')
            self.assertEqual(bytes(g.payload),before)
        for chapter,profile in ((1,'A'),(12,'C'),(True,'C'),(4,'D')):
            with self.assertRaises(core.SaveError):probe.edited_profile(f,chapter,profile)

    @unittest.skipUnless(os.environ.get('FEFW_STORY_TEST_SAVE'),'No accepted private baseline supplied')
    def test_private_four_cases_source_and_output_guards(self):
        source=Path(os.environ['FEFW_STORY_TEST_SAVE']);before=source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'probes';r=probe.build(source,out);self.assertEqual(len(r['cases']),4)
            self.assertEqual((out/'00-Control/Auto').read_bytes(),before)
            with self.assertRaises(ValueError):probe.build(source,out)
            bad=Path(tmp)/'wrong';bad.write_bytes(before+b'wrong')
            with self.assertRaises(ValueError):probe.build(bad,Path(tmp)/'bad-out')
            self.assertFalse((Path(tmp)/'bad-out').exists())
        self.assertEqual(source.read_bytes(),before)
