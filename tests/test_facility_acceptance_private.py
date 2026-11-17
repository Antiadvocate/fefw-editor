"""Opt-in game-return checks for FAC-01–06 and the Yu Phas follow-up.

FEFW_FACILITY_CAPTURE_DIR contains the twelve numbered folders from the return
ZIP plus FAC-05_Yu_Pha. No supplied file is ever written by these checks.
"""
import hashlib
import os
from pathlib import Path
import unittest

import facilities as fac
import facility_access as access
import fast_travel as ft
import fefw_core as core
import fefw_save as container

# Literal expected saved values, independent of the editor's polarity helper.
CASES = {
    '01-Shops-Disabled': {0xb9a0e16b: 1, 0x5e9748e0: 1},
    '02-Shops-Restored': {0xb9a0e16b: None, 0x5e9748e0: None},
    '03-Exams-Drinks-Perform-Disabled': {0x0be47d8b: None, 0x2e270aa7: None, 0xe3d04d6c: None, 0x970ba7f8: None},
    '04-Exams-Drinks-Perform-Restored': {0x0be47d8b: 1, 0x2e270aa7: 1, 0xe3d04d6c: 1, 0x970ba7f8: 1},
    '05-Market-Inn-Smith-Training-Disabled': {0x8244b3ea: None, 0x9399b963: None, 0x0f4e5aa1: None, 0xd70afcb2: None},
    '06-Market-Inn-Smith-Training-Restored': {0x8244b3ea: 1, 0x9399b963: 1, 0x0f4e5aa1: 1, 0xd70afcb2: 1},
    '07-Kalla-Gate-Removed': {0x3fdd2f30: None},
    '08-Kalla-Gate-Restored': {0x3fdd2f30: 1},
    '09-Other-Gates-Registered': {0xc125a07e: 1, 0xf2d863f0: 1, 0x515e9031: 1, 0x2574b004: 1, 0xd2f2cb2f: 1, 0x7d2c41eb: 1},
    '10-Other-Gates-Removed': {0xc125a07e: None, 0xf2d863f0: None, 0x515e9031: None, 0x2574b004: None, 0xd2f2cb2f: None, 0x7d2c41eb: None},
    '11-Access-Travel-Recorded': {0x38574e83: 1, 0x1e4d4a23: 1, 0xefb57d93: 1, 0x65411bed: 1},
    '12-Access-Travel-Removed': {0x38574e83: None, 0x1e4d4a23: None, 0xefb57d93: None, 0x65411bed: None},
}


@unittest.skipUnless(os.environ.get('FEFW_FACILITY_CAPTURE_DIR'), 'No private facility returns supplied')
class FacilityAcceptancePrivateTest(unittest.TestCase):
    def read_capture(self, relative):
        path = Path(os.environ['FEFW_FACILITY_CAPTURE_DIR']) / relative
        original = path.read_bytes(); box = container.SaveFile(str(path))
        self.assertEqual(box.verify(), [])
        f = core.SaveFile(box.payload); core.SaveTree(f.payload)
        self.assertEqual(access.route_info(f), ('Leda', 1, 9))
        ud = core.user_data(f)
        self.assertEqual(tuple(f.u32(ud + off) for off in (core.GOLD_AT, core.RENOWN_AT, core.KARMA_AT)), (1523, 6640, 410))
        self.assertNotIn(0x63fc6b22, fac.read(f))
        self.assertEqual([core.gear(f,u).unit_number for u in f.units()], [47,48,1,2,3,4,5,6,7])
        self.assertEqual(path.read_bytes(), original)
        return f, hashlib.sha256(original).hexdigest()

    def test_all_twelve_returns_retain_requested_switches(self):
        for case, expected in CASES.items():
            with self.subTest(case=case):
                f, _ = self.read_capture(case + '/Auto')
                values = ft.read(f) if case.startswith(('11-', '12-')) else fac.read(f)
                self.assertEqual({h: values.get(h) for h in expected}, expected)

    def test_yu_phas_extra_retains_both_flags_and_only_four_observed_flag_differences(self):
        before, _ = self.read_capture('09-Other-Gates-Registered/Auto')
        after, digest = self.read_capture('FAC-05_Yu_Pha')
        self.assertEqual(digest, '73bb2ac6707db02a0e161990b4ef448b072de13bf792d02b1bffabddee6f6e7a')
        self.assertEqual(fac.read(before)[0x7d2c41eb], 1)
        self.assertNotIn(0x65411bed, ft.read(before))
        self.assertEqual(fac.read(after)[0x7d2c41eb], 1)
        self.assertEqual(ft.read(after)[0x65411bed], 1)
        def flags(f):
            return {(m.index,v.hash):v.value for m in core.flag_maps(f) for v in m.flags}
        a,b=flags(before),flags(after)
        changed={(i,h):(a.get((i,h)),b.get((i,h))) for i,h in a.keys()|b.keys() if a.get((i,h))!=b.get((i,h))}
        self.assertEqual(changed, {(0,0x3c6b4ee1):(1,None), (0,0xbcd41adb):(1,None),
                                   (0,0x4cceb98e):(None,1), (3,0x65411bed):(None,1)})
        self.assertIn('both flags recorded', access.yu_phas_gate_status(after))
