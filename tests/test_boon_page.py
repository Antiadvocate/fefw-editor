"""Exercise real Boon commit/undo logic and selection gating without a display."""
from types import SimpleNamespace
import unittest

import boons
import test_boons
from test_weapon_boon import weapon_save
from test_tutorial_page import PageHarness


class BoonHarness(PageHarness):
    def __init__(self):
        super().__init__()
        self.sv.payload = test_boons.BoonEditingTest.save().payload
        self._boon_rows = {iid: (g, t) for iid, g, t in boons.matching_rows()}
        self.selected = (boons.matching_rows('経験値')[0][0],)
        self.boon_tree = SimpleNamespace(selection=lambda: self.selected)
        self.buttons = {}
        self.actions = {}
        for key in ('set', 'remove', 'max'):
            setattr(self, 'boon_' + key, SimpleNamespace(configure=lambda key=key, **kw: self.actions.update({key: kw['state']})))
        self.detail = ''
        self.boon_on = SimpleNamespace(configure=lambda **kw: self.buttons.update(on=kw['state']))
        self.boon_off = SimpleNamespace(configure=lambda **kw: self.buttons.update(off=kw['state']))
        self.boon_detail = SimpleNamespace(configure=lambda **kw: setattr(self, 'detail', kw['text']))
        self._boon_error = 'Open a save first.'
        self.refresh_boons()

    def refresh_boons(self):
        self._boon_state = boons.read_state(self.core_of()) if self.sv else None
        self._select_boon()

    def refresh_after_core(self):
        self.refreshes += 1
        self.refresh_boons()


class BoonPageTest(unittest.TestCase):
    def test_weapon_control_undo_redo_revalidation_and_independent_exp(self):
        app = BoonHarness(); app.sv.payload = weapon_save(exp_disabled=1).payload
        app.selected = (boons.matching_rows('武器割引')[0][0],); app.refresh_boons()
        before = bytes(app.sv.payload)
        self.assertEqual(app.buttons, dict(on='disabled', off='normal'))
        app.set_boon_active(False); after = bytes(app.sv.payload)
        self.assertEqual(boons.read_observation(app.core_of())['weapons_disabled'], 1)
        self.assertEqual(boons.read_observation(app.core_of())['exp_disabled'], 1)
        self.assertEqual(app.buttons, dict(on='normal', off='disabled'))
        self.assertEqual(len(app._undo_stack), 1)
        app.undo(); self.assertEqual(bytes(app.sv.payload), before)
        app.redo(); self.assertEqual(bytes(app.sv.payload), after)
        app.sv.payload = weapon_save(owner=None).payload
        before = bytes(app.sv.payload); undo_count = len(app._undo_stack)
        app.set_boon_active(True)
        self.assertEqual(bytes(app.sv.payload), before)
        self.assertEqual(len(app._undo_stack), undo_count)
        self.assertEqual(app.messages[-1][1], 'error')
        self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))

    def test_weapon_noop_mirroring_and_unknown_states_have_no_history(self):
        app = BoonHarness(); app.selected = (boons.matching_rows('武器割引')[0][0],)
        app.refresh_boons(); original = bytes(app.sv.payload)
        app.set_boon_active(True)
        app.mirrored = True; app.set_boon_active(False)
        self.assertEqual(app.messages[-1][1], 'warn')
        self.assertEqual(bytes(app.sv.payload), original)
        app.mirrored = False
        for f in (weapon_save(owner=99), weapon_save(disabled=0)):
            app.sv.payload = f.payload; app.refresh_boons()
            self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))
            app.set_boon_active(False)
            self.assertEqual(app.sv.payload, f.payload)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertFalse(app.dirty_slots)

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
        app.sv.payload = test_boons.BoonEditingTest.save(owner=99).payload
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
                         (boons.matching_rows('武器割引')[1][0],),
                         (boons.matching_rows('道具割引')[0][0],)):
            app.selected = selected; app._select_boon()
            self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))
            app.set_boon_active(False)
        self.assertEqual(bytes(app.sv.payload), original)
        self.assertFalse(hasattr(app, '_undo_stack'))
        self.assertFalse(app.dirty_slots)
        app.sv = None; app.set_boon_active(False)
        self.assertEqual(app.buttons, dict(on='disabled', off='disabled'))
