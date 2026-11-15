"""Opt-in tests on private captures and the accepted B0 baseline; never edit inputs.

FEFW_WEAPONS_TEST_SAVE points to Auto from the accepted unit-selection package.
FEFW_BEDIT_CAPTURE_DIR contains W06-before, W06-off and W06-on.
"""
import hashlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import audiences
import boons
import editor_advanced as advanced
import fefw_core as core
import fefw_save as container
from test_audiences import outside_map
from test_boon_page import BoonHarness
from test_tutorials import raw_map


@unittest.skipUnless(os.environ.get('FEFW_WEAPONS_TEST_SAVE') and os.environ.get('FEFW_BEDIT_CAPTURE_DIR'),
                     'No private weapon captures and accepted baseline supplied')
class WeaponBoonPrivateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['FEFW_BEDIT_CAPTURE_DIR'])
        cls.paths = {n: root/n for n in ('W06-before','W06-off','W06-on')}
        cls.paths['baseline'] = Path(os.environ['FEFW_WEAPONS_TEST_SAVE'])
        cls.raw = {n:p.read_bytes() for n,p in cls.paths.items()}
        if hashlib.sha256(cls.raw['baseline']).hexdigest() != '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663':
            raise AssertionError('Expected the accepted supplied B0-01 Auto, not a later gameplay save')
        cls.boxes = {n:container.SaveFile(str(p)) for n,p in cls.paths.items()}
        cls.saves = {n:core.SaveFile(b.payload) for n,b in cls.boxes.items()}

    @classmethod
    def tearDownClass(cls):
        for n,p in cls.paths.items():
            if p.read_bytes() != cls.raw[n]: raise AssertionError('Input changed: '+n)

    def test_matches_captured_game_toggle_and_refuses_unpurchased_capture(self):
        for name,active,other in (('W06-on',False,'W06-off'),('W06-off',True,'W06-on')):
            edited = core.SaveFile(boons.edited_weapons_active(self.saves[name],active))
            self.assertEqual(audiences.read(edited), audiences.read(self.saves[other]))
        for active in (True,False):
            with self.assertRaises(boons.BoonError):
                boons.edited_weapons_active(self.saves['W06-before'],active)

    def test_save_reload_preserves_baseline_repairs_and_real_numbered_backups(self):
        for name in ('W06-on','W06-off','baseline'):
            source = self.saves[name]; old = raw_map(source,audiences.locate(source))
            self.assertEqual(self.boxes[name].verify(),[])
            with self.subTest(capture=name), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp)/'Auto'; output.write_bytes(self.raw[name])
                box = container.SaveFile(str(output))
                for active in (False,True):
                    before_disk = output.read_bytes()
                    payload = boons.edited_weapons_active(source,active)
                    edited = core.SaveFile(payload)
                    self.assertEqual(outside_map(edited),outside_map(source))
                    actual = raw_map(edited,audiences.locate(edited))
                    self.assertEqual(actual.keys()-{boons.WEAPONS_DISABLED},old.keys()-{boons.WEAPONS_DISABLED})
                    for h in old.keys()-{boons.WEAPONS_DISABLED}: self.assertEqual(actual[h],old[h])
                    expected = bytearray(payload); core.fix_embedded_hashes(expected)
                    box.payload = payload; box.save()
                    reread_box = container.SaveFile(str(output)); self.assertEqual(reread_box.verify(),[])
                    self.assertEqual(reread_box.payload,expected)
                    reread = core.SaveFile(reread_box.payload); core.SaveTree(reread.payload)
                    state = boons.read_observation(reread)
                    self.assertEqual(state['weapons_disabled'],None if active else 1)
                    self.assertEqual(state['weapons_purchase'],1)
                    self.assertEqual(state['karma_shards'],410)
                    self.assertEqual(state['exp_disabled'],boons.read_observation(source)['exp_disabled'])
                    self.assertEqual([(u.person,core.gear(reread,u).unit_number) for u in reread.units()],
                                     [(u.person,core.gear(source,u).unit_number) for u in source.units()])
                    expected_flags = [[(r.hash,r.wide,r.value) for r in m.flags
                                       if r.hash != boons.WEAPONS_DISABLED] for m in core.flag_maps(source)]
                    self.assertEqual([[(r.hash,r.wide,r.value) for r in m.flags
                                       if r.hash != boons.WEAPONS_DISABLED] for m in core.flag_maps(reread)],expected_flags)
                    backups = [Path(str(output)+'.bak')] + [Path(p) for _,p in container.numbered_backups(str(output))]
                    self.assertIn(before_disk,[p.read_bytes() for p in backups])
                    self.assertEqual(backups[0].read_bytes(),self.raw[name])

    def test_upstream_mastery_actions_change_all_selected_entries_only(self):
        # Exercise upstream's real page handlers and structural writer on a
        # disposable in-memory copy. These edits are never part of a test save.
        for action in ('rank','exp','remove'):
            with self.subTest(action=action):
                app = BoonHarness(); app.sv.payload = bytearray(self.saves['baseline'].payload)
                app.mas_tree = SimpleNamespace(selection=lambda: ('2','0'))
                app._cls_unit = lambda: app.core_of().units()[0]
                app._picker = lambda *args: 3
                old = list(app._cls_unit().masteries)
                if action == 'rank': app.set_mastery_rank()
                elif action == 'exp':
                    with patch.object(advanced,'_ask_number',return_value=555): app.set_mastery_exp()
                else:
                    with patch.object(advanced.messagebox,'askyesno',return_value=True): app.remove_mastery()
                expected = [v for i,v in enumerate(old) if i not in (0,2)] if action == 'remove' else [
                    (v[0],advanced.RANK_EXP[3] if action == 'rank' else 555) if i in (0,2) else v
                    for i,v in enumerate(old)]
                self.assertEqual(app._cls_unit().masteries,expected)
