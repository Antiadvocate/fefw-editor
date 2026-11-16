"""Exercise actual Save dispatch, overwrite refusal, backups and staged history."""
from pathlib import Path
from unittest.mock import patch
import os
import tempfile
import unittest

import editor
import fefw_core as core
import fefw_save as container
import story
import story_files
import story_start
from test_story import StoryHarness, box_for
from test_story_resume_probe import fixture


class SaveHarness(StoryHarness):
    save_all = editor.App.save_all

    def __init__(self, folder, name='Auto'):
        super().__init__()
        path = Path(folder)/name
        path.write_bytes(box_for(fixture()).to_bytes())
        self.sv = container.SaveFile(str(path))
        self.files = {str(path): self.sv}
        self.dirty = set()
        self.mtimes = {str(path): path.stat().st_mtime}
        self.slot_paths = [str(path)]
        self.folder = str(folder)

    def _touch(self, slots): self.dirty.update(s.path for s in slots)
    def _changed_on_disk(self, path): return False
    def _populate_slot_box(self): pass
    def _update_file_label(self): pass
    def _update_dirty(self): pass
    def refresh_story(self): pass
    def flash(self, message, kind='info'): self.messages.append((message, kind))
    def _get(self, path): self.files[path] = container.SaveFile(path)


class StoryFilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.app = SaveHarness(self.root)
        self.source = self.root/'Auto'
        self.original = self.source.read_bytes()
        self.target = self.root/'Chapter_Led_1_4'
        self.errors = self.enterContext(patch.object(editor.messagebox, 'showerror'))
        self.confirm = self.enterContext(patch.object(editor.messagebox, 'askyesno', return_value=True))

    def test_apply_undo_redo_wait_for_save_then_write_same_state_and_consume_request(self):
        a = self.app
        a.apply_story_chapter(4, True)
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.target.exists())
        a.undo(); self.assertIsNone(a.sv._pending_story_chapter)
        a.redo(); self.assertEqual(a.sv._pending_story_chapter, 4)
        # Subsequent ordinary edits belong in both saved files.
        i = story.read(a.core_of())
        a.sv.payload[i.user+6] = 99
        self.assertTrue(a.save_all())
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())
        self.assertEqual(container.SaveFile(str(self.target)).verify(), [])
        self.assertIsNone(a.sv._pending_story_chapter)
        self.assertIn(str(self.target), a.slot_paths)
        self.confirm.assert_not_called()
        self.assertFalse(Path(str(self.target)+'.bak').exists())
        # Undo after Save cannot remove the external file or requeue its write.
        saved = self.target.read_bytes()
        a.undo(); a.redo(); self.assertIsNone(a.sv._pending_story_chapter)
        self.assertTrue(a.save_all()); self.assertEqual(self.target.read_bytes(), saved)
        self.confirm.assert_not_called()

    def test_no_checkbox_or_unchecked_reapply_does_not_create_file(self):
        a = self.app
        a.apply_story_chapter(4, True)
        a.apply_story_chapter(4, False)
        self.assertTrue(a.save_all())
        self.assertFalse(self.target.exists())

    def test_checkbox_only_change_is_undoable_and_restaging_after_save_is_explicit(self):
        a = self.app
        a.apply_story_chapter(4)
        before = bytes(a.sv.payload)
        a.apply_story_chapter(4, True)
        self.assertEqual(a.sv.payload, before)
        self.assertEqual(len(a._undo_stack), 2)
        a.undo(); self.assertIsNone(a.sv._pending_story_chapter)
        a.redo(); self.assertEqual(a.sv._pending_story_chapter, 4)
        self.assertTrue(a.save_all())
        a.apply_story_chapter(4, True)
        self.assertEqual(a.sv._pending_story_chapter, 4)
        self.assertTrue(a.save_all()); self.confirm.assert_called_once()

    def test_existing_target_no_cancels_entire_save_yes_preserves_numbered_backups(self):
        a = self.app
        self.target.write_bytes(self.original)
        a.apply_story_chapter(4, True)
        self.confirm.return_value = False
        self.assertFalse(a.save_all())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse(list(self.root.glob('*.bak*')))
        self.assertEqual(a.sv._pending_story_chapter, 4)
        self.confirm.return_value = True
        self.assertTrue(a.save_all())
        self.assertEqual(Path(str(self.target)+'.bak').read_bytes(), self.original)
        first = self.target.read_bytes()
        a.apply_story_chapter(4, True)
        i = story.read(a.core_of()); a.sv.payload[i.user+6] ^= 1
        self.assertTrue(a.save_all())
        self.assertEqual(Path(str(self.target)+'.bak').read_bytes(), self.original)
        self.assertEqual(Path(str(self.target)+'.bak1').read_bytes(), first)

    def test_backup_failure_preserves_both_files_and_pending_request(self):
        self.target.write_bytes(self.original)
        self.app.apply_story_chapter(4, True)
        with patch.object(container, 'write_backup', side_effect=OSError('backup failed')):
            self.assertFalse(self.app.save_all())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(self.app.sv._pending_story_chapter, 4)
        self.errors.assert_called_once()

    def test_target_changes_during_confirmation_are_not_overwritten(self):
        self.target.write_bytes(self.original)
        self.app.apply_story_chapter(4, True)
        def change(*args, **kwargs): self.target.write_bytes(b'new game state'); return True
        self.confirm.side_effect = change
        self.assertFalse(self.app.save_all())
        self.assertEqual(self.target.read_bytes(), b'new game state')
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(Path(str(self.target)+'.bak').exists())

    def test_target_appearing_after_preflight_is_not_overwritten(self):
        a = self.app; a.apply_story_chapter(4, True)
        plan = story_files.prepare(a.files, a.dirty)[a.sv.path]
        self.target.write_bytes(b'new checkpoint')
        with self.assertRaises(core.SaveError): story_files.write(plan)
        self.assertEqual(self.target.read_bytes(), b'new checkpoint')

    def test_conflicting_pending_slots_and_dirty_target_refused_before_any_save(self):
        a = self.app; a.apply_story_chapter(4, True)
        other = SaveHarness(self.root, 'Route_Led')
        other.apply_story_chapter(4, True)
        a.files.update(other.files); a.dirty.update(other.dirty)
        self.assertFalse(a.save_all())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.target.exists()); self.confirm.assert_not_called()
        a.dirty = {a.sv.path, str(self.target)}
        self.assertFalse(a.save_all())
        self.assertFalse(self.target.exists())

    def test_stale_non_start_payload_refused_without_mutation(self):
        a = self.app; a.apply_story_chapter(4, True)
        a.sv.payload = fixture().payload  # Simulate restoring an unrelated snapshot.
        self.assertFalse(a.save_all())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.target.exists())

    def test_editing_target_itself_prompts_and_writes_only_once(self):
        a = SaveHarness(self.root, self.target.name)
        original = self.target.read_bytes()
        a.apply_story_chapter(4, True)
        self.assertTrue(a.save_all()); self.confirm.assert_called_once()
        self.assertEqual(Path(str(self.target)+'.bak').read_bytes(), original)
        self.assertFalse(Path(str(self.target)+'.bak1').exists())
        self.assertEqual(container.SaveFile(str(self.target)).verify(), [])

    def test_requests_stay_with_source_slot_and_reload_drops_pending(self):
        a = self.app; a.apply_story_chapter(4, True)
        other = SaveHarness(self.root, 'Route_Led')
        a.sv = other.sv; a.undo(); a.redo()
        self.assertIsNone(getattr(a.sv, '_pending_story_chapter', None))
        self.assertEqual(a.files[str(self.source)]._pending_story_chapter, 4)
        reloaded = container.SaveFile(str(self.source))
        self.assertIsNone(getattr(reloaded, '_pending_story_chapter', None))
        a.sv = reloaded; a.undo(); a.redo()
        self.assertEqual(reloaded.raw, self.original)

    def test_second_source_failure_does_not_repeat_completed_external_write_on_retry(self):
        a = self.app; a.apply_story_chapter(4, True)
        with patch.object(a.sv, 'save', side_effect=OSError('source write failed')):
            self.assertFalse(a.save_all())
        self.assertTrue(self.target.exists()); self.assertIsNone(a.sv._pending_story_chapter)
        self.assertTrue(a.save_all())
        self.confirm.assert_not_called()
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())

    def test_chapter_one_and_later_chapter_restore_their_own_year(self):
        f = core.SaveFile(story_start.edited(fixture(), 1))
        i = story.read(f)
        self.assertEqual(int.from_bytes(f.payload[i.header+22:i.header+24], 'little'), 1444)
        g = core.SaveFile(story_start.edited(f, 2)); j = story.read(g)
        self.assertEqual(int.from_bytes(g.payload[j.header+22:j.header+24], 'little'), 1449)
