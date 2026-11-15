"""Verify the player's Hours return without publishing or mutating saves.

FEFW_HOURS_CAPTURE_DIR supplies Hours-before-claim and Hours-after-claim;
FEFW_WEAPONS_TEST_SAVE supplies the accepted B0-01 Auto.
"""
from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import unittest

import audiences
import blessings
import deeds
import fast_travel
import fefw_core as core
import fefw_save as container
import tutorials


@unittest.skipUnless(os.environ.get('FEFW_HOURS_CAPTURE_DIR')
                     and os.environ.get('FEFW_WEAPONS_TEST_SAVE'),
                     'No private Hours captures and accepted baseline supplied')
class DeedHoursAcceptanceTest(unittest.TestCase):
    def test_completion_claim_reward_and_preserved_progress(self):
        root = Path(os.environ['FEFW_HOURS_CAPTURE_DIR'])
        paths = {'baseline': Path(os.environ['FEFW_WEAPONS_TEST_SAVE']),
                 'before': root / 'Hours-before-claim',
                 'after': root / 'Hours-after-claim'}
        originals = {n: p.read_bytes() for n, p in paths.items()}
        hashes = {
            'baseline': '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663',
            'before': 'f9e46675094eae692e9d14dedf9e0ed77bf40638e6ae27cc90a4d9824eac51ef',
            'after': '6e5d791a0fd8fcdb98fe8dd5912fb9d14263a6ce7832c918df91cc8f4f634bf2',
        }
        saves = {}
        for name, path in paths.items():
            self.assertEqual(hashlib.sha256(originals[name]).hexdigest(), hashes[name])
            box = container.SaveFile(str(path))
            self.assertEqual(box.verify(), [])
            f = core.SaveFile(box.payload)
            core.SaveTree(f.payload)
            saves[name] = f

        hours, claim10, claim20 = 0xeb92a0f6, 0xe0de8be2, 0x71725a0a
        baseline = saves['baseline']

        def other_flags(f):
            return [{r.hash: (r.wide, r.value) for r in m.flags
                     if r.hash not in (hours, claim20)} for m in core.flag_maps(f)]

        def unit_values(f):
            # Adding a claim record moves later objects, without changing units.
            return [{k: v for k, v in asdict(u).items()
                     if k not in ('start', 'end', 'counters_off')} for u in f.units()]

        def blessing_values(f):
            b = blessings.read(f)
            return b.divine_sand, [(r.hash, r.exp, r.selected) for r in b.records]

        numbers = [(u.person, core.gear(baseline, u).unit_number) for u in baseline.units()]
        self.assertEqual(len({n for _, n in numbers}), 9)
        for name, total, state, karma in [('baseline', 17, None, 410),
                                          ('before', 20, 2, 410), ('after', 20, 4, 430)]:
            with self.subTest(capture=name):
                f = saves[name]
                self.assertEqual(deeds.read(f), deeds.read(baseline) | {hours: total}
                                 | ({claim20: state} if state is not None else {}))
                self.assertEqual(deeds.read(f)[claim10], 4)
                ud = core.user_data(f)
                self.assertEqual([f.u32(ud + x) for x in
                                  (core.GOLD_AT, core.RENOWN_AT, core.KARMA_AT)],
                                 [1523, 6640, karma])
                self.assertEqual(other_flags(f), other_flags(baseline))
                self.assertEqual(unit_values(f), unit_values(baseline))
                self.assertEqual([(u.person, core.gear(f, u).unit_number) for u in f.units()],
                                 numbers)
                for module in (tutorials, fast_travel, audiences):
                    self.assertEqual(module.read(f), module.read(baseline))
                self.assertEqual(blessing_values(f), blessing_values(baseline))

        for name, path in paths.items():
            self.assertEqual(path.read_bytes(), originals[name])
