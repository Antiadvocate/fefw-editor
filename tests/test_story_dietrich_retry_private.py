"""Private Test 2 probes stay separate from automatic story editing."""
import os
from pathlib import Path
import tempfile
import unittest
from research.dietrich_retry_kit import build


@unittest.skipUnless(os.environ.get('FEFW_DIETRICH_RETURN_DIR') and os.environ.get('FEFW_DIETRICH_TEST1_DIR'),
                     'No Dietrich Test 1 returns and delivered kit supplied')
class DietrichRetryPrivateTest(unittest.TestCase):
    def test_exact_probe_deltas_and_nonoverwriting_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'retry'
            r=build(os.environ['FEFW_DIETRICH_RETURN_DIR'],os.environ['FEFW_DIETRICH_TEST1_DIR'],out)
            cases={x['case']:x for x in r['cases']}
            self.assertEqual(len(cases),8)
            expected={
                'D2-02A-Rescue-history': {'b631f2c1:81e4a23a':None},
                'D2-02B-Hub-cache-fallback': {'b631f2c1:81e4a23a':None},
                'D2-05A-Upper-restriction': {'4ad575a2:89dc5a51':None},
                'D2-05B-Exam-switch-fallback': {'4ad575a2:89dc5a51':None,'972fa7ee:0be47d8b':[1,False],'972fa7ee:948de8dd':[1,False]},
                'D2-06A-Port-restriction': {'4ad575a2:8386d712':None},
                'D2-06B-Restriction-only-control': {'4ad575a2:8386d712':None},
                'D2-07A-One-secret-permission': {'4ad575a2:d2cbe499':[1,False]},
                'D2-07B-Soldier-fallback': {'4ad575a2:d2cbe499':[1,False]},
            }
            for name,changes in expected.items():
                self.assertEqual({x['member:hash']:x['after'] for x in cases[name]['flag_changes']},changes)
                self.assertEqual(cases[name]['game_result'],'pending')
            self.assertEqual(cases['D2-02B-Hub-cache-fallback']['changed_roots'],['GameUserData','HubData'])
            self.assertEqual(cases['D2-07B-Soldier-fallback']['changed_roots'],['GameUserData','UnitPool'])
            self.assertEqual(len(list(out.glob('*/Auto'))),9)
            before={str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):
                build(os.environ['FEFW_DIETRICH_RETURN_DIR'],os.environ['FEFW_DIETRICH_TEST1_DIR'],out)
            self.assertEqual(before,{str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()})
