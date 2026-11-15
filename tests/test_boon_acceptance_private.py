"""Opt-in read-only checks of the BEDIT return captures, not a game simulator.

Set FEFW_BEDIT_CAPTURE_DIR to the private capture folder. The files and game
assets are deliberately not included. These assertions reproduce the evidence
in docs/test-results-boon-editing-2026-11-15.md; they do not prove other battles,
rounding rules, shop prices or a causal interpretation of unnamed flags.
"""
import os
from pathlib import Path
import unittest

import audiences
import blessings
import boons
import deeds
import fast_travel
import fefw_core as core
import fefw_save as container
import tutorials


@unittest.skipUnless(os.environ.get('FEFW_BEDIT_CAPTURE_DIR'), 'No private BEDIT captures supplied')
class BoonAcceptanceCapturesTest(unittest.TestCase):
    names = ('B0', 'E02-off-edited', 'B02-off-game', 'B03-on-edited', 'B03-on-game',
             'B05-off-before-XP', 'B05-off-after-xp', 'B05-on-before-xp', 'B05-on-after-xp',
             'W06-before', 'W06-off', 'W06-on')

    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['FEFW_BEDIT_CAPTURE_DIR'])
        cls.paths = {n: root / n for n in cls.names}
        cls.originals = {n: p.read_bytes() for n, p in cls.paths.items()}
        cls.boxes = {n: container.SaveFile(str(p)) for n, p in cls.paths.items()}
        cls.saves = {n: core.SaveFile(b.payload) for n, b in cls.boxes.items()}

    @classmethod
    def tearDownClass(cls):
        for name, path in cls.paths.items():
            if path.read_bytes() != cls.originals[name]:
                raise AssertionError('Private input changed: ' + name)

    @staticmethod
    def blessing_values(f):
        b = blessings.read(f)
        return b.divine_sand, [(r.hash, r.exp, r.selected) for r in b.records]

    @staticmethod
    def flag_values(f, h):
        # Search every map; observed map indices are not a locator contract.
        return [fl.value for m in core.flag_maps(f) for fl in m.flags if fl.hash == h]

    def test_checksums_persistence_and_menu_regression_captures(self):
        baseline = self.saves['B0']
        for name, box in self.boxes.items():
            with self.subTest(capture=name):
                self.assertEqual(box.verify(), [])
        for name, disabled in [('E02-off-edited', 1), ('B02-off-game', 1),
                               ('B03-on-edited', None), ('B03-on-game', None)]:
            with self.subTest(capture=name):
                f = self.saves[name]
                self.assertEqual(boons.read_observation(f), {
                    'karma_shards': 710, 'exp_candidate': 1,
                    'exp_disabled': disabled, 'weapons_purchase': None,
                    'weapons_disabled': None})
                expected = audiences.read(baseline)
                if disabled: expected[boons.EXP_DISABLED] = disabled
                self.assertEqual(audiences.read(f), expected)
                for module in (deeds, tutorials, fast_travel):
                    self.assertEqual(module.read(f), module.read(baseline))
                self.assertEqual(self.blessing_values(f), self.blessing_values(baseline))
                ud = core.user_data(f)
                self.assertEqual((f.u32(ud + core.GOLD_AT), f.u32(ud + core.RENOWN_AT)), (1523, 6640))

    def test_reported_single_kill_exp_gains_and_unchanged_boon_state(self):
        # Establish that both starting captures differ only by the editor's
        # toggle and the embedded checksum refresh used when saving it.
        expected = boons.edited_exp_active(self.saves['B05-off-before-XP'], True)
        core.fix_embedded_hashes(expected)
        self.assertEqual(expected, self.saves['B05-on-before-xp'].payload)
        for state, before, after, gain, disabled in [
            ('Off', 'B05-off-before-XP', 'B05-off-after-xp', 16, 1),
            ('On', 'B05-on-before-xp', 'B05-on-after-xp', 17, None),
        ]:
            with self.subTest(state=state):
                values = []
                for name in (before, after):
                    f = self.saves[name]
                    leda = [u for u in f.units() if u.person == 0x45e9244b]
                    self.assertEqual(len(leda), 1)
                    self.assertEqual(f.payload[leda[0].level_off], 20)
                    values.append(f.u16(leda[0].exp_off))
                    self.assertEqual(boons.read_observation(f)['exp_disabled'], disabled)
                    self.assertEqual(self.flag_values(f, 0x50126cb8), [281 if name == before else 282])
                    self.assertEqual(self.blessing_values(f), self.blessing_values(self.saves['B0']))
                self.assertEqual(values, [1970, 1970 + gain])

    def test_weapons_purchase_and_separate_disable_capture(self):
        before, on, off = (self.saves[n] for n in ('W06-before', 'W06-on', 'W06-off'))
        self.assertIsNone(boons.read_observation(before)['weapons_purchase'])
        self.assertEqual(boons.read_observation(before)['karma_shards'], 710)
        expected = audiences.read(before); expected[boons.WEAPONS_PURCHASE] = 1
        self.assertEqual(audiences.read(on), expected)
        expected[0xddb8d06b] = 1  # Captured weapon-disable candidate; no writer enabled.
        self.assertEqual(audiences.read(off), expected)
        for f in (on, off):
            self.assertEqual(boons.read_observation(f)['karma_shards'], 410)
            for module in (deeds, tutorials, fast_travel):
                self.assertEqual(module.read(f), module.read(before))

    def test_feast_unlock_tutorial_and_counter_already_present(self):
        for name in ('B0', 'B05-off-before-XP', 'B05-on-before-xp',
                     'B05-off-after-xp', 'B05-on-after-xp'):
            with self.subTest(capture=name):
                f = self.saves[name]
                for h, value in ((0xf0c779ce, 1), (0x3bb4016e, 2), (0x730acddc, 5)):
                    self.assertEqual(self.flag_values(f, h), [value])
