"""Opt-in regression check. The supplied save is only ever read."""
import os
from pathlib import Path
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import tutorials
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
