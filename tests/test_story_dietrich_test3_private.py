"""Private Test 3 exports and byte-equivalence to the accepted Chapter 7 case."""
import os
from pathlib import Path
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story_start
from research.dietrich_test3_kit import build


@unittest.skipUnless(all(os.environ.get(k) for k in (
    'FEFW_DIETRICH_RETURN_DIR','FEFW_DIETRICH_TEST2_RETURN_DIR',
    'FEFW_DIETRICH_TEST1_DIR','FEFW_DIETRICH_TEST2_DIR')), 'No Dietrich private retry captures')
class Test3PrivateTest(unittest.TestCase):
    def test_probe_deltas_and_accepted_chapter7_equivalence(self):
        test1=Path(os.environ['FEFW_DIETRICH_TEST1_DIR'])
        test2=Path(os.environ['FEFW_DIETRICH_TEST2_DIR'])
        box=container.SaveFile(str(test1/'test-saves/00-Native-Control/Auto'))
        box.payload=story_start.edited(core.SaveFile(box.payload),7)
        self.assertEqual(box.to_bytes(),(test2/'test-saves/D2-07A-One-secret-permission/Auto').read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'cases'
            args=(os.environ['FEFW_DIETRICH_RETURN_DIR'],os.environ['FEFW_DIETRICH_TEST2_RETURN_DIR'],test1,out)
            result=build(*args)
            expected=[
                {'06c136c7:be852456':None},
                {'06c136c7:be852456':None,'b631f2c1:81e4a23a':None},
                {'06c136c7:be852456':None,'b631f2c1:81e4a23a':None,'06c136c7:370344f7':None},
                {'4ad575a2:89dc5a51':None},
                {'4ad575a2:8386d712':None,'972fa7ee:948de8dd':[1,False],
                 '972fa7ee:9402533e':[1,False],'972fa7ee:a78e9de8':[1,False]},
            ]
            for row,want in zip(result['cases'],expected):
                self.assertEqual({r['member:hash']:r['after'] for r in row['flag_changes']},want)
            self.assertEqual(len(result['cases']),5)
            before={p:p.read_bytes() for p in out.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):build(*args)
            self.assertEqual(before,{p:p.read_bytes() for p in out.rglob('*') if p.is_file()})
