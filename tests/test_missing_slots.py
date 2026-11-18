"""External renames must not interrupt refresh or silently recreate a slot."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import unittest

import editor
from test_story_files import SaveHarness


class MissingSlotsTest(unittest.TestCase):
    def test_cached_missing_slot_label_preserves_edits_and_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = SaveHarness(tmp, 'Part_Kai_2')
            original = bytes(app.sv.payload); path = Path(app.sv.path)
            app.slot_box = MagicMock(); app.dirty.add(str(path))
            path.rename(path.with_name('renamed-checkpoint'))
            editor.App._populate_slot_box(app)
            labels = app.slot_box.configure.call_args.kwargs['values']
            self.assertIn('Missing on disk — cached copy', labels[0])
            self.assertIn('● ', labels[0])
            app.slot_box.current.assert_called_with(0)
            self.assertEqual(app.sv.payload, original)
            self.assertIn(str(path), app.dirty)
            self.assertIn(str(path), app.files)

    def test_focus_refresh_updates_missing_labels_without_game_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = SaveHarness(tmp); app._populate_slot_box = MagicMock()
            Path(app.sv.path).unlink()
            editor.App._check_disk(app)
            app._populate_slot_box.assert_called_once()
            self.assertFalse(app._checking)

    def test_removal_between_directory_scan_and_stat_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            auto = Path(tmp)/'Auto'; part = Path(tmp)/'Part_Kai_2'
            auto.write_bytes(b'a'); part.write_bytes(b'b')
            real = os.path.getmtime
            def racing(path):
                if Path(path) == part:
                    part.unlink(); raise FileNotFoundError(path)
                return real(path)
            with patch.object(editor.os.path, 'getmtime', side_effect=racing):
                self.assertEqual(editor.App._slot_files(None, tmp), [str(auto)])

    def test_save_refuses_all_writes_until_removed_edited_file_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = SaveHarness(tmp, 'Part_Kai_2'); path = Path(app.sv.path)
            app.dirty.add(str(path)); app.sv._pending_story_chapter = None
            renamed = path.with_name('renamed-checkpoint'); path.rename(renamed)
            before = renamed.read_bytes()
            with patch.object(editor.messagebox, 'showerror') as error:
                self.assertFalse(app.save_all())
            self.assertIn('removed or renamed', error.call_args.args[1])
            self.assertFalse(path.exists()); self.assertEqual(renamed.read_bytes(), before)
            self.assertIn(str(path), app.dirty)
            self.assertEqual(list(Path(tmp).iterdir()), [renamed])
            renamed.rename(path)
            self.assertTrue(app.save_all())
            self.assertFalse(app.dirty)

    def test_reload_falls_back_to_existing_auto_when_selected_path_was_renamed(self):
        with tempfile.TemporaryDirectory() as tmp:
            auto = Path(tmp)/'Auto'; auto.write_bytes(b'placeholder')
            app = SimpleNamespace(folder=None, files={}, mtimes={}, dirty=set(),
                                  _slot_files=lambda _: [str(auto)], config=MagicMock(),
                                  update_idletasks=MagicMock(), _get=MagicMock(),
                                  _save_settings=MagicMock(), _populate_slot_box=MagicMock(),
                                  load=MagicMock())
            app._default_slot = lambda: editor.App._default_slot(app)
            editor.App.open_folder(app, tmp, prefer=str(Path(tmp)/'Part_Kai_2'))
            app.load.assert_called_once_with(str(auto))


if __name__ == '__main__':
    unittest.main()
