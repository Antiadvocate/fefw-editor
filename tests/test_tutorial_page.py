"""Exercise the page's edit/undo wiring without a display server."""
from types import SimpleNamespace
import unittest

import editor_advanced as advanced
import tutorials
from test_tutorials import fixture, rows, FORESIGHT, OBELISK


class PageHarness(advanced.AdvancedMixin):
    push_undo = advanced.push_undo
    undo = advanced.undo
    redo = advanced.redo

    def __init__(self):
        self.sv = SimpleNamespace(path='synthetic', payload=fixture([rows()]).payload,
                                  scan=lambda: None)
        self.mirrored = False
        self.selected = (f'{FORESIGHT:08x}',)
        self.mirror = SimpleNamespace(get=lambda: self.mirrored)
        self.tutorial_tree = SimpleNamespace(selection=lambda: self.selected)
        self.messages = []
        self.refreshes = 0
        self.dirty_slots = []

    def flash(self, message, kind):
        self.messages.append((message, kind))

    def _commit_form(self):
        pass

    def _targets(self):
        return [self.sv]

    def _touch(self, slots):
        self.dirty_slots.extend(slots)

    def refresh_after_core(self):
        self.refreshes += 1


class TutorialPageTest(unittest.TestCase):
    def test_edit_undo_redo_and_cache_invalidation(self):
        app = PageHarness()
        before = bytes(app.sv.payload)
        app.core_of()  # Populate the same cache the GUI uses.
        app.set_tutorials(None)
        after = bytes(app.sv.payload)
        self.assertNotIn(FORESIGHT, tutorials.read(app.core_of()))
        self.assertEqual(tutorials.read(app.core_of())[OBELISK], 1)
        self.assertEqual(len(app._undo_stack), 1)
        self.assertEqual(app.dirty_slots, [app.sv])
        app.undo()
        self.assertEqual(bytes(app.sv.payload), before)
        app.redo()
        self.assertEqual(bytes(app.sv.payload), after)
        self.assertEqual(app.refreshes, 3)

    def test_mirroring_refused_without_mutation_or_undo(self):
        app = PageHarness(); app.mirrored = True
        before = bytes(app.sv.payload)
        app.set_tutorials(None)
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.messages[-1][1], 'warn')

    def test_no_selection_and_noop_do_not_create_undo(self):
        app = PageHarness(); app.selected = ()
        app.set_tutorials(None)
        app.selected = (f'{FORESIGHT:08x}',)
        app.set_tutorials(2)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.refreshes, 0)

    def test_invalid_batch_is_not_partially_applied(self):
        app = PageHarness()
        app.selected = (f'{FORESIGHT:08x}', 'deadbeef')
        before = bytes(app.sv.payload)
        app.set_tutorials(None)
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertEqual(app.messages[-1][1], 'error')
