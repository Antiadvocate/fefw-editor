"""Private returned saves: exact repair deltas, map tails and unchanged inputs."""
from pathlib import Path
import os
import tempfile
import unittest
import fefw_core as core
import fefw_save as container
import story
import story_start as start
import worldmap
from research.theodora_retry_kit import build,SOURCES


@unittest.skipUnless(os.environ.get('FEFW_THEODORA_RETURN_DIR'),'No private Theodora Test 1 returns supplied')
class TheodoraRetryPrivateTest(unittest.TestCase):
    def test_all_returns_validate_and_repair_exports_keep_story_party_and_scope(self):
        root=Path(os.environ['FEFW_THEODORA_RETURN_DIR']);count=0
        for path in root.glob('*/*'):
            if not path.is_file():continue
            count+=1;box=container.SaveFile(str(path));self.assertEqual(box.verify(),[])
            f=core.SaveFile(box.payload);h=f.block('Header').start;u=core.user_data(f)
            self.assertEqual(box.raw[40:43],f.payload[h+12:h+15]);self.assertEqual(box.raw[40:43],f.payload[u+3:u+6])
            self.assertEqual(box.raw[73:81],f.payload[h+45:h+53]);self.assertEqual(box.raw[73:81],f.payload[u+81:u+89])
            self.assertEqual(box.raw[48:57],f.payload[h+20:h+29])
        self.assertEqual(count,19)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'cases';result=build(root,out);self.assertEqual(len(result['cases']),6)
            expected=[{'4ad575a2:16b679c4'},
                      {'4ad575a2:16b679c4','4ad575a2:8386d712','4ad575a2:a9d310ac'},
                      {'4ad575a2:16b679c4','4ad575a2:8386d712','4ad575a2:a9d310ac','972fa7ee:948de8dd','972fa7ee:9402533e','972fa7ee:a78e9de8'},
                      {'4ad575a2:16b679c4','4ad575a2:8386d712','4ad575a2:a9d310ac'},set(),set()]
            for row,keys in zip(result['cases'],expected):
                self.assertEqual({v['member:hash'] for v in row['flag_changes']},keys)
                ch=row['chapter'];path=root/f'T1-{ch:02d}-Chapter-{ch:02d}'/'Auto'
                f=core.SaveFile(container.SaveFile(str(path)).payload)
                g=core.SaveFile(container.SaveFile(str(out/row['case']/'Auto')).payload)
                a,b=story.read(f),story.read(g)
                self.assertEqual((a.route,a.part,a.chapter,a.sequence),(b.route,b.part,b.chapter,b.sequence))
                self.assertEqual(start.normalized_blocks(f)['UnitPool'],start.normalized_blocks(g)['UnitPool'])
                for v in row['flag_changes']:
                    self.assertEqual(v['before'],[1,False] if v['member:hash'].startswith('4ad') else None)
                    self.assertEqual(v['after'],None if v['member:hash'].startswith('4ad') else [1,False])
                if ch==9:
                    self.assertEqual(len(row['map_changes']),3 if '09A' in row['case'] else 35)
                    ma,mb=worldmap.read(f),worldmap.read(g)
                    allowed={ma[int(v['key'],16)].at+4 for v in row['map_changes']}
                    self.assertEqual({i for i,(x,y) in enumerate(zip(f.payload,g.payload)) if x!=y},allowed)
                    for v in row['map_changes']:self.assertEqual(v['before'][1:],v['after'][1:]);self.assertEqual(v['after'][0],3)
                    with self.assertRaises(core.SaveError):start.edited(g,9)
            with self.assertRaises(ValueError):build(root,out)
