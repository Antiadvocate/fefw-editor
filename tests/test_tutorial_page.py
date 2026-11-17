"""Exercise the page's edit/undo wiring without a display server."""
from types import SimpleNamespace
import unittest

import editor_advanced as advanced
import tutorials
from test_tutorials import fixture, rows, FORESIGHT, OBELISK
from test_tutorial_catalog_complete import structured


class ValueWidget:
    def __init__(self, value=''):
        self.value = value
        self.options = {}

    def get(self):
        return self.value

    def configure(self, **options):
        self.options.update(options)


class FilterTree:
    def __init__(self):
        self.rows = {}
        self.picked = ()

    def selection(self): return self.picked
    def selection_set(self, picked): self.picked = tuple(picked)
    def get_children(self): return tuple(self.rows)
    def exists(self, iid): return iid in self.rows
    def yview(self): return (0.0, 1.0)
    def yview_moveto(self, fraction): pass
    def delete(self, *items):
        for iid in items: self.rows.pop(iid)
        self.picked = ()
    def insert(self, parent, where, iid, **options): self.rows[iid] = options


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
    def test_filtered_removal_keeps_hidden_records_and_reports_them(self):
        # Reproduce an apparently short list backed by records in other categories.
        app = PageHarness()
        cat = tutorials.catalog()
        app.sv.payload = structured([(h, 2, False) for h in cat]).payload
        app.tutorial_tree = FilterTree()
        app.tutorial_buttons = []
        app.tutorial_category = ValueWidget('Scenario-specific')
        app.tutorial_state = ValueWidget('All states')
        app.tutorial_evidence = ValueWidget('All names')
        app.tutorial_search = ValueWidget()
        app.tutorial_count = ValueWidget()
        app.tutorial_detail = ValueWidget()
        app.refresh_tutorials()
        self.assertEqual(len(app.tutorial_tree.rows), 38)
        self.assertIn('180 outside filters', app.tutorial_count.options['text'])
        app.tutorial_tree.selection_set(app.tutorial_tree.get_children())
        app.set_tutorials(None)
        remaining = tutorials.read(app.core_of())
        self.assertEqual(set(remaining), {h for h,r in cat.items() if r['category_id']!=6})
        self.assertIn('180 records remain', app.messages[-1][0])
        app.undo()
        self.assertEqual(len(tutorials.read(app.core_of())), 218)
        app.redo()
        self.assertEqual(len(tutorials.read(app.core_of())), 180)
        app.tutorial_category.value = 'Battle'
        app.tutorial_state.value = 'Stored (2)'
        app.refresh_tutorials()
        self.assertEqual(len(app.tutorial_tree.rows), 45)
        self.assertTrue(all(cat[int(h,16)]['category_id']==1 for h in app.tutorial_tree.rows))

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
