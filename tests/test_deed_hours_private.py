"""Reproduce the isolated Hours test from the private accepted baseline."""
import os
from pathlib import Path
import tempfile
import unittest

from research.deed_hours_probe import build_probe, BASELINE_SHA256


@unittest.skipUnless(os.environ.get('FEFW_WEAPONS_TEST_SAVE'), 'No accepted baseline supplied')
class DeedHoursPrivateTest(unittest.TestCase):
    def test_probe_is_one_counter_byte_and_existing_inputs_outputs_are_not_overwritten(self):
        source = Path(os.environ['FEFW_WEAPONS_TEST_SAVE'])
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'probe'
            report = build_probe(source, output)
            self.assertEqual(report['source_sha256'], BASELINE_SHA256)
            self.assertEqual(report['counter']['before'], 17)
            self.assertEqual(report['counter']['after'], 20)
            self.assertEqual(report['claims'], {'10_hours': 4, '20_hours': None})
            self.assertEqual(len(report['payload_byte_changes_before_checksum_refresh']), 1)
            saved = (output / 'Auto').read_bytes()
            with self.assertRaises(ValueError): build_probe(source, output)
            self.assertEqual((output / 'Auto').read_bytes(), saved)
            bad = Path(tmp) / 'wrong'; bad.write_bytes(original + b'bad')
            with self.assertRaises(ValueError): build_probe(bad, Path(tmp) / 'refused')
            self.assertFalse((Path(tmp) / 'refused').exists())
        self.assertEqual(source.read_bytes(), original)
