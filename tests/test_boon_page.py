"""Exercise real Boon commit/undo logic and selection gating without a display."""
from types import SimpleNamespace
import unittest

import boons
import test_boons
from test_tutorial_page import PageHarness


class BoonHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = test_boons.BoonEditingTest.save().payload
        self._boon_rows = {iid: (g, t) for iid, g, t in boons.matching_rows()}
        self.selected = (boons.matching_rows('経験値')[0][0],)
        self.boon_tree = SimpleNamespace(selection=lambda: self.selected)
        self.buttons = {}
        self.detail = ''
        self.boon_on = SimpleNamespace(configure=lambda **kw: self.buttons.update(on=kw['state']))
        self.boon_off = SimpleNamespace(configure=lambda **kw: self.buttons.update(off=kw['state']))
        self.boon_detail = SimpleNamespace(configure=lambda **kw: setattr(self, 'detail', kw['text']))
        self._boon_error = 'Open a save first.'
        self.refresh_boons()

    def refresh_boons(self):
        self._boon_observed = boons.read_observation(self.core_of()) if self.sv else None
        self._select_boon()

    def refresh_after_core(self):
        self.refreshes += 1
        self.refresh_boons()


class BoonPageTest(unittest.TestCase):
    def test_toggle_undo_redo_refresh_and_replaced_payload_are_current(self):
        app = BoonHarness(); before = bytes(app.sv.payload)
        self.assertEqual(app.buttons, dict(on='disabled', off='normal'))
        app.core_of(); app.set_boon_active(False)
        after = bytes(app.sv.payload)
        self.assertEqual(boons.read_observation(app.core_of())['exp_disabled'], 1)
        self.assertEqual(app.buttons, dict(on='normal', off='disabled'))
        self.assertEqual(len(app._undo_stack), 1)
        self.assertEqual(app.dirty_slots, [app.sv])
        app.undo(); self.assertEqual(bytes(app.sv.payload), before)
        self.assertEqual(app.buttons, dict(on='disabled', off='normal'))
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        self.assertEqual(app.buttons, dict(on='normal', off='disabled'))
        # An out-of-band slot refresh must not use the earlier valid cached state.
        app.sv.payload = test_boons.BoonEditingTest.save(owner=2).payload
        before = bytes(app.sv.payload); undo_count = len(app._undo_stack)
        app.set_boon_active(True)
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertEqual(len(app._undo_stack), undo_count)
        self.assertEqual(app.messages[-1][1], 'error')
        self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))

    def test_noop_mirroring_and_wrong_rows_do_not_modify_or_create_undo(self):
        app = BoonHarness(); original = bytes(app.sv.payload)
        app.set_boon_active(True)
        app.mirrored = True; app.set_boon_active(False)
        self.assertEqual(app.messages[-1][1], 'warn')
        app.mirrored = False
        for selected in ((), (boons.matching_rows('経験値')[1][0],),
                         (boons.matching_rows('武器割引')[0][0],)):
            app.selected = selected; app._select_boon()
            self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))
            app.set_boon_active(False)
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertFalse(app.dirty_slots)
        app.sv = None; app.set_boon_active(False)
        self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))
