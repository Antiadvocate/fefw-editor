"""Opt-in Brawling/Black-Magic capture checks; no private save bytes in git."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import audiences
import blessings
import boons
import deeds
import fast_travel
import fefw_core as core
import fefw_save as container
import tutorials
from test_audiences import outside_map


CAPTURES = {
    'Brawling': ('技能経験格闘', 0x45409cb9, 0x79b46b58,
                '5913739433601e7d656d8c70d5d739b9f30333559a885d2aede52621b19ee37b',
                'd88769c291b438300160f6f0be61b05fd0f3305d45736922810b69907fddda65'),
    'Black_Magic': ('技能経験黒魔法', 0x45227c65, 0x79c9024c,
                   '9b60659f6ed1f98ec63f05434f9b2d72db407d1d181414a03048c7274fe36013',
                   'eb696025aad254c8bf98bc99845f7c528308bdabcd2859a5abdd0bb6f75753e9'),
}
BASELINE_SHA = '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663'


@unittest.skipUnless(os.environ.get('FEFW_SKILL_BOON_CAPTURE_DIR'), 'No private skill-Boon captures supplied')
class BoonSkillCaptureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['FEFW_SKILL_BOON_CAPTURE_DIR'])
        cls.paths = {}; cls.saves = {}; cls.originals = {}
        for stem, (_, _, _, on_sha, off_sha) in CAPTURES.items():
            for name, expected in [(f'Before_{stem}', BASELINE_SHA),
                                   (f'After_{stem}_On', on_sha), (f'After_{stem}_Off', off_sha)]:
                p = root / name; raw = p.read_bytes(); box = container.SaveFile(str(p))
                if hashlib.sha256(raw).hexdigest() != expected:
                    raise AssertionError('Unexpected private capture: ' + name)
                if box.verify(): raise AssertionError('Invalid container: ' + name)
                core.SaveTree(box.payload)
                cls.paths[name] = p; cls.originals[name] = raw; cls.saves[name] = core.SaveFile(box.payload)

    @classmethod
    def tearDownClass(cls):
        for name, p in cls.paths.items():
            if p.read_bytes() != cls.originals[name]: raise AssertionError('Input changed: ' + name)

    def test_game_changes_are_only_the_captured_map_records_and_purchase_cost(self):
        for stem, (name, level_key, off_key, _, _) in CAPTURES.items():
            before = self.saves[f'Before_{stem}']
            baseline_maps = [{r.hash: r.value for r in m.flags} for m in core.flag_maps(before)]
            shared_index = next(i for i, m in enumerate(core.flag_maps(before)) if m.start == audiences.locate(before).start)
            numbers = [(u.person, core.gear(before, u).unit_number) for u in before.units()]
            def bless(f):
                b = blessings.read(f)
                return b.divine_sand, [(r.hash, r.exp, r.selected) for r in b.records]
            for suffix, disabled in [('On', None), ('Off', 1)]:
                with self.subTest(group=stem, state=suffix):
                    f = self.saves[f'After_{stem}_{suffix}']
                    expected = [dict(m) for m in baseline_maps]
                    expected[shared_index][level_key] = 1
                    if disabled: expected[shared_index][off_key] = 1
                    self.assertEqual([{r.hash: r.value for r in m.flags} for m in core.flag_maps(f)], expected)
                    self.assertEqual(boons.read_state(f)['groups'][name], {'level': 1, 'disabled': disabled})
                    self.assertEqual([f.u32(core.user_data(f)+o) for o in (core.GOLD_AT, core.RENOWN_AT, core.KARMA_AT)], [1523, 6640, 110])
                    self.assertEqual([(u.person, core.gear(f, u).unit_number) for u in f.units()], numbers)
                    for module in (deeds, tutorials, fast_travel): self.assertEqual(module.read(f), module.read(before))
                    self.assertEqual(bless(f), bless(before))

    def test_editor_writes_match_independent_game_maps_and_preserve_unrelated_payload(self):
        for stem, (name, _, _, _, _) in CAPTURES.items():
            for source, target, edits in [
                (f'Before_{stem}', f'After_{stem}_On', {'levels': {name: 1}}),
                (f'After_{stem}_On', f'After_{stem}_Off', {'active': {name: False}}),
                (f'After_{stem}_Off', f'After_{stem}_On', {'active': {name: True}}),
            ]:
                with self.subTest(source=source, target=target), tempfile.TemporaryDirectory() as tmp:
                    f = self.saves[source]; payload = boons.edited_groups(f, **edits)
                    g = core.SaveFile(payload)
                    self.assertEqual(audiences.read(g), audiences.read(self.saves[target]))
                    self.assertEqual(outside_map(g), outside_map(f))
                    self.assertEqual(boons.read_state(g)['karma_shards'], boons.read_state(f)['karma_shards'])
                    box = container.SaveFile(str(self.paths[source])); box.payload = payload
                    p = Path(tmp) / 'Auto'; box.save(str(p)); reopened = container.SaveFile(str(p))
                    self.assertEqual(reopened.verify(), [])
                    self.assertEqual(audiences.read(core.SaveFile(reopened.payload)), audiences.read(g))
