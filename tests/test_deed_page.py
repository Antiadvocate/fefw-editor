from types import SimpleNamespace
import unittest
from unittest.mock import patch

import deeds
import fefw_core as core
from test_deeds import TRAIN, rows
from test_fast_travel import fixture
from test_tutorial_page import PageHarness


class DeedHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = fixture([rows()]).payload
        self.selected = ('milestone',)
        self._deed_rows = {'milestone': (TRAIN, deeds.catalog()[TRAIN]['milestones'][5])}
        self.deed_tree = SimpleNamespace(selection=lambda: self.selected)
        self.input = '75'
        self.deed_value = SimpleNamespace(get=lambda: self.input)


class DeedPageTest(unittest.TestCase):
    def claimed_training(self):
        app = DeedHarness()
        claim = core.id_hash('実績状態_訓練を実行_4')  # 50 training sessions
        app.sv.payload = fixture([rows() + [(claim, 4, False)]]).payload
        return app, claim

    @patch('deed_page.messagebox.askokcancel', return_value=False)
    def test_cancel_preserves_payload_history_dirty_state_and_claims(self, confirm):
        app, _claim = self.claimed_training(); original = bytes(app.sv.payload)
        app.input = '40'; app.set_deed()
        confirm.assert_called_once()
        self.assertEqual(confirm.call_args.args[1],
                         'You are about to unclaim some previously claimed rewards. Continue anyway?')
        self.assertEqual(confirm.call_args.kwargs['default'], 'cancel')
        self.assertEqual(confirm.call_args.kwargs['icon'], 'warning')
        self.assertIn('Affected claimed targets: 50.', confirm.call_args.kwargs['detail'])
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertEqual(app.dirty_slots, [])
        self.assertEqual(app.refreshes, 0)
        self.assertFalse(hasattr(app, '_undo_stack'))

    @patch('deed_page.messagebox.askokcancel', return_value=True)
    def test_ok_changes_only_progress_then_undo_and_redo_work(self, confirm):
        app, claim = self.claimed_training(); original = bytes(app.sv.payload)
        app.input = '40'; app.set_deed()
        self.assertEqual(deeds.read(app.core_of())[TRAIN], 40)
        self.assertEqual(deeds.read(app.core_of())[claim], 4)
        self.assertEqual(len(app._undo_stack), 1)
        self.assertEqual(app.dirty_slots, [app.sv])
        changed = bytes(app.sv.payload)
        app.undo(); self.assertEqual(bytes(app.sv.payload), original)
        app.redo(); self.assertEqual(bytes(app.sv.payload), changed)
        confirm.assert_called_once()

    @patch('deed_page.messagebox.askokcancel', return_value=False)
    def test_safe_decreases_equal_targets_increases_noops_and_invalid_do_not_prompt(self, confirm):
        for value in ('60', '50', '75', '65', '-1', '101', 'bad'):
            app, _ = self.claimed_training(); app.input = value; app.set_deed()
        app = DeedHarness(); app.input = '15'; app.set_deed()  # 20 is unclaimed, 10 still met.
        app, _ = self.claimed_training(); app.input = '40'; app.mirrored = True; app.set_deed()
        app.mirrored = False; app.selected = (); app.set_deed()
        confirm.assert_not_called()

    def test_edit_undo_redo_refresh_and_save_target(self):
        app = DeedHarness(); before = bytes(app.sv.payload)
        app.core_of(); app.set_deed(); after = bytes(app.sv.payload)
        self.assertEqual(deeds.read(app.core_of())[TRAIN], 75)
        self.assertEqual(app.dirty_slots, [app.sv])
        self.assertEqual(len(app._undo_stack), 1)
        app.undo(); self.assertEqual(bytes(app.sv.payload), before)
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        self.assertEqual(app.refreshes, 3)

    def test_mirroring_invalid_noop_readonly_and_missing_selection_make_no_history(self):
        app = DeedHarness(); original = bytes(app.sv.payload)
        app.mirrored = True; app.set_deed()
        self.assertEqual(app.messages[-1][1], 'warn')
        app.mirrored = False
        for value in ('bad', '1.5', '-1', '101', '65'):
            app.input = value; app.set_deed()
        # Known counters remain read-only when a claim has an unknown state.
        claim = int(deeds.catalog()[TRAIN]['milestones'][0]['hash'], 16)
        app.sv.payload = fixture([[(h, 1 if h == claim else v, w) for h, v, w in rows()]]).payload
        original = bytes(app.sv.payload)
        app.input = '75'; app.set_deed()
        self.assertEqual(app.messages[-1][1], 'error')
        app.selected = (); app.set_deed()
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertFalse(hasattr(app, '_undo_stack'))
