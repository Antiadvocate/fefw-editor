"""Regression checks for upstream 1.3.9's on-disk backup preservation."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import fefw_save as save


class NumberedBackupsTest(unittest.TestCase):
    def test_original_and_intervening_game_save_survive_repeated_editor_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp)/'Auto'; slot.write_bytes(b'original')
            box = SimpleNamespace(path=str(slot), to_bytes=lambda: b'editor one')
            save.SaveFile.save(box)
            self.assertEqual(Path(str(slot)+'.bak').read_bytes(), b'original')
            slot.write_bytes(b'game autosave between edits')
            box.to_bytes = lambda: b'editor two'; save.SaveFile.save(box)
            self.assertEqual(Path(str(slot)+'.bak1').read_bytes(), b'game autosave between edits')
            box.to_bytes = lambda: b'editor three'; save.SaveFile.save(box)
            self.assertEqual(Path(str(slot)+'.bak2').read_bytes(), b'editor two')
            self.assertEqual(Path(str(slot)+'.bak').read_bytes(), b'original')
            self.assertEqual(slot.read_bytes(), b'editor three')
            self.assertFalse(any(p.name.endswith('.tmp') for p in Path(tmp).iterdir()))

    def test_numeric_order_gaps_and_unrelated_names_do_not_overwrite_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp)/'Auto'; slot.write_bytes(b'current')
            fixtures = {'Auto.bak': b'original', 'Auto.bak2': b'two', 'Auto.bak10': b'ten',
                        'Auto.bak10.tmp': b'partial', 'Auto.bakold': b'other',
                        'AutoOther.bak99': b'unrelated'}
            for name,data in fixtures.items(): (Path(tmp)/name).write_bytes(data)
            self.assertEqual([n for n,_ in save.numbered_backups(str(slot))], [2,10])
            self.assertEqual(save.write_backup(str(slot)), str(slot)+'.bak11')
            self.assertEqual(Path(str(slot)+'.bak11').read_bytes(), b'current')
            for name,data in fixtures.items(): self.assertEqual((Path(tmp)/name).read_bytes(),data)
            self.assertIsNone(save.write_backup(str(slot)))
            self.assertFalse(Path(str(slot)+'.bak12').exists())

    def test_legacy_original_is_kept_and_duplicate_newest_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp)/'Auto'; slot.write_bytes(b'old original')
            Path(str(slot)+'.bak').write_bytes(b'old original')
            self.assertIsNone(save.write_backup(str(slot)))
            slot.write_bytes(b'new state'); save.write_backup(str(slot))
            self.assertEqual(Path(str(slot)+'.bak').read_bytes(), b'old original')
            self.assertEqual(Path(str(slot)+'.bak1').read_bytes(), b'new state')
            for name in ('Auto.bak','Auto.bak1','Chapter_Led_1_9.bak2','Route_Led.bak10'):
                self.assertFalse(save.is_slot_name(name))

    def test_backup_failure_prevents_slot_overwrite_and_disabled_backup_is_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp)/'Auto'; slot.write_bytes(b'original')
            box = SimpleNamespace(path=str(slot), to_bytes=lambda: b'edited')
            with patch.object(save,'write_backup',side_effect=OSError('backup failed')):
                with self.assertRaises(OSError): save.SaveFile.save(box)
            self.assertEqual(slot.read_bytes(), b'original')
            save.SaveFile.save(box, backup=False)
            self.assertEqual(slot.read_bytes(), b'edited')
            self.assertFalse(Path(str(slot)+'.bak').exists())
