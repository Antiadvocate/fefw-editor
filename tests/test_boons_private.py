"""Optional player captures are read only; all outputs use a temporary folder."""
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
from test_tutorials import raw_map


@unittest.skipUnless(os.environ.get('FEFW_BOON_CAPTURE_DIR'), 'No private Boon captures supplied')
class BoonCapturesTest(unittest.TestCase):
    def test_both_directions_roundtrip_all_six_captures_and_preserve_other_features(self):
        root = Path(os.environ['FEFW_BOON_CAPTURE_DIR'])
        for name in ('B02-EXP-before', 'B02-EXP-off', 'B02-EXP-on',
                     'B03-purchase-before', 'B03-purchase-after', 'B04-reloaded'):
            source = root / name; raw = source.read_bytes()
            initial_box = container.SaveFile(str(source)); self.assertEqual(initial_box.verify(), [])
            initial = core.SaveFile(initial_box.payload)
            old_records = raw_map(initial, audiences.locate(initial))
            old_observation = boons.read_observation(initial)
            old_blessings = blessings.read(initial)
            for active in (False, True):
                with self.subTest(capture=name, active=active), tempfile.TemporaryDirectory() as tmp:
                    payload = boons.edited_exp_active(initial, active)
                    changed = core.SaveFile(payload)
                    self.assertEqual(outside_map(changed), outside_map(initial))
                    box = container.SaveFile(str(source)); box.payload = payload
                    output = Path(tmp) / 'Auto'; output.write_bytes(box.to_bytes())
                    loaded = container.SaveFile(str(output)); self.assertEqual(loaded.verify(), [])
                    reread = core.SaveFile(loaded.payload)
                    state = boons.read_observation(reread)
                    self.assertEqual(state['exp_disabled'], None if active else 1)
                    self.assertEqual(state['exp_candidate'], 1)
                    self.assertEqual(state['karma_shards'], old_observation['karma_shards'])
                    records = raw_map(reread, audiences.locate(reread))
                    for h in old_records.keys() - {boons.EXP_DISABLED}:
                        self.assertEqual(records[h], old_records[h])
                    for module in (deeds, tutorials, fast_travel):
                        self.assertEqual(module.read(reread), module.read(initial))
                    new_blessings = blessings.read(reread)
                    self.assertEqual(new_blessings.divine_sand, old_blessings.divine_sand)
                    self.assertEqual([(r.hash, r.exp, r.selected) for r in new_blessings.records],
                                     [(r.hash, r.exp, r.selected) for r in old_blessings.records])
                    # Compare the entire shared-map values with the desired captured shape.
                    expected = audiences.read(initial)
                    if active: expected.pop(boons.EXP_DISABLED, None)
                    else: expected[boons.EXP_DISABLED] = 1
                    self.assertEqual(audiences.read(reread), expected)
            self.assertEqual(source.read_bytes(), raw)
