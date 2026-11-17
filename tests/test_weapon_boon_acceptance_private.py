"""Read-only evidence checks for the accepted WEDIT player return.

FEFW_WEDIT_CAPTURE_DIR contains the four files under their returned names.
FEFW_WEAPONS_TEST_SAVE is Auto from the accepted B0-01 package. No price or
backup screenshot/content is inferred from these slot files.
"""
import hashlib
import os
from pathlib import Path
import unittest

import blessings
import boons
import deeds
import fast_travel
import fefw_core as core
import fefw_save as container
import tutorials


@unittest.skipUnless(os.environ.get('FEFW_WEDIT_CAPTURE_DIR') and os.environ.get('FEFW_WEAPONS_TEST_SAVE'),
                     'No private WEDIT captures and accepted baseline supplied')
class WeaponBoonAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['FEFW_WEDIT_CAPTURE_DIR'])
        cls.paths = {n: root/n for n in ('WE02-off-edited','WE02-off-game','WE03-on-edited','W03-on-game')}
        cls.paths['baseline'] = Path(os.environ['FEFW_WEAPONS_TEST_SAVE'])
        cls.originals = {n:p.read_bytes() for n,p in cls.paths.items()}
        if hashlib.sha256(cls.originals['baseline']).hexdigest() != '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663':
            raise AssertionError('Expected the accepted supplied B0-01 Auto')
        cls.boxes = {n:container.SaveFile(str(p)) for n,p in cls.paths.items()}
        cls.saves = {n:core.SaveFile(b.payload) for n,b in cls.boxes.items()}

    @classmethod
    def tearDownClass(cls):
        for n,p in cls.paths.items():
            if p.read_bytes() != cls.originals[n]: raise AssertionError('Input changed: '+n)

    def test_edited_payloads_equal_only_the_requested_toggle_and_checksum_refresh(self):
        for source,target,active in [('baseline','WE02-off-edited',False),
                                     ('WE02-off-game','WE03-on-edited',True)]:
            with self.subTest(capture=target):
                expected = boons.edited_weapons_active(self.saves[source],active)
                core.fix_embedded_hashes(expected)
                self.assertEqual(self.saves[target].payload,expected)

    def test_persisted_states_resources_features_and_repaired_unit_numbers(self):
        baseline = self.saves['baseline']
        def flags(f):
            return [{r.hash:(r.wide,r.value) for r in m.flags if r.hash != boons.WEAPONS_DISABLED}
                    for m in core.flag_maps(f)]
        def blessing_values(f):
            b=blessings.read(f)
            return b.divine_sand,[(r.hash,r.exp,r.selected) for r in b.records]
        numbers=[(u.person,core.gear(baseline,u).unit_number) for u in baseline.units()]
        self.assertEqual(len({n for _,n in numbers}),9)
        for name,disabled in [('WE02-off-edited',1),('WE02-off-game',1),
                              ('WE03-on-edited',None),('W03-on-game',None)]:
            with self.subTest(capture=name):
                f=self.saves[name];self.assertEqual(self.boxes[name].verify(),[])
                core.SaveTree(f.payload)
                self.assertEqual(boons.read_observation(f),{
                    'karma_shards':410,'exp_candidate':1,'exp_disabled':None,
                    'weapons_purchase':1,'weapons_disabled':disabled})
                ud=core.user_data(f)
                self.assertEqual([f.u32(ud+x) for x in (core.GOLD_AT,core.RENOWN_AT,core.KARMA_AT)],
                                 [1523,6640,410])
                self.assertEqual(flags(f),flags(baseline))
                self.assertEqual([(u.person,core.gear(f,u).unit_number) for u in f.units()],numbers)
                for module in (deeds,tutorials,fast_travel):
                    self.assertEqual(module.read(f),module.read(baseline))
                self.assertEqual(blessing_values(f),blessing_values(baseline))
