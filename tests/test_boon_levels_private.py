"""Read-only WD20 acceptance and all-group serialization on private fixtures."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import blessings
import boons
import deeds
import fast_travel
import fefw_core as core
import fefw_save as container
import tutorials
from test_audiences import outside_map


@unittest.skipUnless(os.environ.get('FEFW_WD20_CAPTURE_DIR') and os.environ.get('FEFW_WEAPONS_TEST_SAVE'),
                     'No private WD20 captures and accepted baseline supplied')
class BoonLevelsPrivateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['FEFW_WD20_CAPTURE_DIR'])
        cls.paths = {n: root / n for n in ('WD20-off-game', 'WD20-on-reloaded')}
        cls.paths['baseline'] = Path(os.environ['FEFW_WEAPONS_TEST_SAVE'])
        cls.raw = {n: p.read_bytes() for n, p in cls.paths.items()}
        if hashlib.sha256(cls.raw['baseline']).hexdigest() != '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663':
            raise AssertionError('Use the accepted B0-01 package Auto')
        cls.boxes = {n: container.SaveFile(str(p)) for n, p in cls.paths.items()}
        cls.saves = {n: core.SaveFile(b.payload) for n, b in cls.boxes.items()}

    @classmethod
    def tearDownClass(cls):
        for n, p in cls.paths.items():
            if p.read_bytes() != cls.raw[n]: raise AssertionError('Input changed: ' + n)

    def test_wd20_game_returns_preserve_level_two_switch_resources_and_repairs(self):
        baseline = self.saves['baseline']
        def flags(f):
            return [{r.hash:(r.wide, r.value) for r in m.flags
                     if r.hash not in (boons.WEAPONS_PURCHASE, boons.WEAPONS_DISABLED)}
                    for m in core.flag_maps(f)]
        def bless(f):
            b = blessings.read(f)
            return b.divine_sand, [(r.hash, r.exp, r.selected) for r in b.records]
        numbers = [(u.person, core.gear(baseline, u).unit_number) for u in baseline.units()]
        for name, disabled in (('WD20-off-game', 1), ('WD20-on-reloaded', None)):
            with self.subTest(name=name):
                f = self.saves[name]
                self.assertEqual(self.boxes[name].verify(), [])
                core.SaveTree(f.payload)
                state = boons.read_state(f)
                self.assertEqual(state['groups']['武器割引'], {'level': 2, 'disabled': disabled})
                self.assertEqual(state['groups']['経験値'], {'level': 1, 'disabled': None})
                self.assertEqual(flags(f), flags(baseline))
                ud = core.user_data(f)
                self.assertEqual([f.u32(ud+x) for x in (core.GOLD_AT,core.RENOWN_AT,core.KARMA_AT)], [1523,6640,410])
                self.assertEqual([(u.person,core.gear(f,u).unit_number) for u in f.units()], numbers)
                for module in (deeds, tutorials, fast_travel):
                    self.assertEqual(module.read(f), module.read(baseline))
                self.assertEqual(bless(f), bless(baseline))

    def test_all_group_maxima_save_reload_and_removal_preserve_unrelated_payload(self):
        for name, source in self.saves.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                outside = outside_map(source)
                original_state = boons.read_state(source)
                payload = boons.edited_groups(source, levels=boons.max_levels())
                edited = core.SaveFile(payload)
                self.assertEqual(outside_map(edited), outside)
                expected = bytearray(payload); core.fix_embedded_hashes(expected)
                box = container.SaveFile(str(self.paths[name])); box.payload = payload
                path = Path(tmp) / 'Auto'; box.save(str(path))
                loaded = container.SaveFile(str(path))
                self.assertEqual(loaded.verify(), [])
                self.assertEqual(loaded.payload, expected)
                state = boons.read_state(core.SaveFile(loaded.payload))
                self.assertEqual({n:s['level'] for n,s in state['groups'].items()}, boons.max_levels())
                self.assertEqual({n:s['disabled'] for n,s in state['groups'].items()},
                                 {n:s['disabled'] for n,s in original_state['groups'].items()})
                self.assertEqual(state['karma_shards'], 410)
                removed = core.SaveFile(boons.edited_groups(edited, levels={n:0 for n in boons.max_levels()}))
                self.assertTrue(all(s['level'] is None for s in boons.read_state(removed)['groups'].values()))
                self.assertEqual(outside_map(removed), outside)
