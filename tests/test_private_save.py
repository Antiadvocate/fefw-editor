"""Opt-in regression check. The supplied save is only ever read."""
import os
from pathlib import Path
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import tutorials
import blessings
from test_tutorials import FORESIGHT, RELIQUARY, THIRD_EYE, raw_map


def outside_tutorials(f):
    tree = core.SaveTree(f.payload)
    fm = tutorials.locate(f)
    node = tree.nodes[tree.node_at(fm.start)]
    p = bytearray(f.payload)
    # The low 24 bits are relocatable pointers; keep their type bits.
    for ref in tree.refs:
        value = struct.unpack_from('<I', p, ref.at)[0]
        struct.pack_into('<I', p, ref.at, value & 0xff000000)
    return bytes(p[:node.start] + p[node.end:])


@unittest.skipUnless(os.environ.get('FEFW_TEST_SAVE'), 'No private fixture supplied')
class PrivateSaveTest(unittest.TestCase):
    def test_all_seven_blessing_exp_fields_roundtrip(self):
        source = Path(os.environ['FEFW_TEST_SAVE'])
        original = source.read_bytes()
        save = container.SaveFile(str(source))
        self.assertEqual(save.verify(), [])
        initial = core.SaveFile(save.payload)
        initial_table = blessings.read(initial)
        initial_tutorials = tutorials.read(initial)
        with tempfile.TemporaryDirectory() as tmp:
            for god in blessings.GODS:
                before = core.SaveFile(save.payload)
                record = next(r for r in blessings.read(before).records if r.hash == god.hash)
                value = god.thresholds[1] if god.thresholds else 1
                expected = bytearray(before.payload)
                struct.pack_into('<H', expected, record.exp_offset, value)
                save.payload = blessings.edited(before, {god.hash: value})
                self.assertEqual(save.payload, expected)
                path = Path(tmp) / 'Auto'
                path.write_bytes(save.to_bytes())
                reread = container.SaveFile(str(path))
                self.assertEqual(reread.verify(), [])
                self.assertEqual(reread.payload, save.payload)
                after = core.SaveFile(reread.payload)
                actual = next(r for r in blessings.read(after).records if r.hash == god.hash)
                self.assertEqual(actual.exp, value)
                self.assertEqual(actual.selected, record.selected)
                self.assertEqual(tutorials.read(after), initial_tutorials)
                save = reread
            restored = core.SaveFile(blessings.edited(core.SaveFile(save.payload),
                                    {r.hash: r.exp for r in initial_table.records}))
            self.assertEqual(blessings.read(restored), initial_table)
        self.assertEqual(source.read_bytes(), original)

    def test_edits_roundtrip_and_preserve_other_content(self):
        source = Path(os.environ['FEFW_TEST_SAVE'])
        original = source.read_bytes()
        save = container.SaveFile(str(source))
        self.assertEqual(save.verify(), [])
        initial = core.SaveFile(save.payload)
        initial_values = tutorials.read(initial)
        operations = [
            {FORESIGHT: None}, {FORESIGHT: 2},
            {RELIQUARY: 2, THIRD_EYE: 2},
            {h: initial_values.get(h) for h in (FORESIGHT, RELIQUARY, THIRD_EYE)},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for index, changes in enumerate(operations):
                before = core.SaveFile(save.payload)
                outside = outside_tutorials(before)
                before_records = raw_map(before, tutorials.locate(before))
                save.payload = tutorials.edited(before, changes)
                after = core.SaveFile(save.payload)
                self.assertEqual(outside_tutorials(after), outside)
                actual = raw_map(after, tutorials.locate(after))
                for h in before_records.keys() - changes.keys():
                    self.assertEqual(actual[h], before_records[h])
                path = Path(tmp) / f'roundtrip-{index}'
                path.write_bytes(save.to_bytes())
                reread = container.SaveFile(str(path))
                self.assertEqual(reread.verify(), [])
                self.assertEqual(reread.payload, save.payload)
                values = tutorials.read(core.SaveFile(reread.payload))
                for h, value in changes.items():
                    self.assertEqual(values.get(h), value)
                save = reread
        self.assertEqual(tutorials.read(core.SaveFile(save.payload)), initial_values)
        self.assertEqual(source.read_bytes(), original)
