"""Multi-save edits are staged atomically and share one undo transaction."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest

import editor
import fefw_core as core
import facilities
import story
import story_files
import unit_entries as entries
from test_tutorial_page import PageHarness, FORESIGHT
from test_blessing_page import BlessingHarness
from test_audience_page import AudienceHarness
from test_fast_travel_page import FastTravelHarness
from test_facility_page import FacilityHarness
from test_deed_page import DeedHarness
from test_boon_page import BoonHarness
from test_unit_entry_page import Harness as UnitHarness
from test_unit_entries import CATANIA, CAI
from test_story_part2 import fixture as story_fixture
from test_story import box_for


def peers(app, payloads=None):
    payloads = payloads if payloads is not None else [app.sv.payload]
    app.mirrored = True
    app.sv.path = 'selected'
    slots = [app.sv] + [SimpleNamespace(path=f'peer{i}', payload=bytearray(p), scan=lambda: None)
                        for i, p in enumerate(payloads)]
    app._targets = lambda: slots if app.mirrored else [app.sv]
    return slots


class MirroringTest(unittest.TestCase):
    def cases(self):
        return [(PageHarness, lambda a: a.set_tutorials(None)),
                (BlessingHarness, lambda a: a.apply_blessing_exp()),
                (AudienceHarness, lambda a: a.toggle_blessing_audience()),
                (FastTravelHarness, lambda a: a.set_fast_travel(None)),
                (FacilityHarness, lambda a: a.set_facilities(True)),
                (DeedHarness, lambda a: a.set_deed()),
                (BoonHarness, lambda a: a.set_boon_active(False)),
                (BoonHarness, lambda a: a.max_boons())]

    def test_every_added_page_mirrors_and_undo_redo_restores_all_slots(self):
        for harness, edit in self.cases():
            with self.subTest(page=harness.__name__, action=edit):
                app = harness(); slots = peers(app)
                before = [bytes(s.payload) for s in slots]
                edit(app)
                after = [bytes(s.payload) for s in slots]
                self.assertTrue(all(a != b for a,b in zip(before,after)), app.messages)
                self.assertEqual(after[0], after[1]); self.assertEqual(len(app._undo_stack), 1)
                app.mirrored = False  # Undo scope belongs to the edit, not the current checkbox.
                app.undo(); self.assertEqual([bytes(s.payload) for s in slots], before)
                app.redo(); self.assertEqual([bytes(s.payload) for s in slots], after)

    def test_invalid_peer_aborts_entire_batch_without_history(self):
        for harness, edit in self.cases():
            with self.subTest(page=harness.__name__):
                app = harness(); slots = peers(app, [b'unsupported'])
                before = [bytes(s.payload) for s in slots]
                edit(app)
                self.assertEqual([bytes(s.payload) for s in slots], before)
                self.assertFalse(hasattr(app, '_undo_stack')); self.assertFalse(app.dirty_slots)
                self.assertIn('Nothing changed: peer0', app.messages[-1][0])

    def test_selected_noop_still_updates_peer_and_only_snapshots_changes(self):
        for harness, edit in self.cases():
            with self.subTest(page=harness.__name__):
                app = harness(); original = bytes(app.sv.payload); edit(app)
                app._undo_stack.clear(); app.dirty_slots.clear()
                slots = peers(app, [original]); selected = bytes(app.sv.payload)
                edit(app)
                self.assertEqual(bytes(slots[1].payload), selected, app.messages)
                self.assertEqual(len(app._undo_stack), 1)
                self.assertEqual([s.path for s,_,_ in app._undo_stack[0]], ['peer0'])
                app.undo(); self.assertEqual(bytes(slots[1].payload), original)
                self.assertEqual(bytes(slots[0].payload), selected)

    def test_reloaded_peer_blocks_undo_without_partially_restoring(self):
        app=PageHarness(); slots=peers(app); app.files={s.path:s for s in slots}
        app.set_tutorials(None); after=[bytes(s.payload) for s in slots]
        app.files['peer0']=SimpleNamespace(payload=bytearray(b'new disk copy'))
        app.undo(); self.assertEqual([bytes(s.payload) for s in slots],after)
        self.assertEqual(len(app._undo_stack),1); self.assertIn('reloaded',app.messages[-1][0])

    def test_add_restores_or_preserves_existing_and_allocates_numbers_locally(self):
        app=UnitHarness(); base=app.core_of()
        active=core.SaveFile(entries.add(base,CATANIA))
        active=core.SaveFile(entries.renumber(active,CATANIA,30))
        flag=core.id_hash(entries.catalog()[CATANIA]['recruit_flag'])
        inactive=core.flag_set(active,facilities.locate(active),flag,0)
        slots=peers(app,[active.payload,inactive])
        original=[bytes(s.payload) for s in slots]
        self.assertTrue(app.apply_unit_entry('add',CATANIA),app.messages)
        for sv in slots:
            f=core.SaveFile(sv.payload)
            self.assertEqual(entries.status(f,CATANIA),'Already in party')
            self.assertEqual(sum(u.person==CATANIA for u,g in entries.roster(f)),1)
        self.assertEqual(bytes(slots[1].payload),original[1])
        self.assertEqual(bytes(slots[2].payload),original[1])
        numbers=[next(g.unit_number for u,g in entries.roster(core.SaveFile(s.payload)) if u.person==CATANIA) for s in slots]
        self.assertNotEqual(numbers[0],30);self.assertEqual(numbers[1:],[30,30])
        app.undo();self.assertEqual([bytes(s.payload) for s in slots],original)
        app.redo();self.assertEqual(entries.status(app.core_of(),CATANIA),'Already in party')

    def test_peer_number_collision_refuses_renumber_for_every_slot(self):
        app=UnitHarness(); app.apply_unit_entry('add',CATANIA)
        peer=entries.renumber(app.core_of(),CAI,30)
        slots=peers(app,[peer]);before=[bytes(s.payload) for s in slots];count=len(app._undo_stack)
        self.assertFalse(app.apply_unit_entry('renumber',CATANIA,30))
        self.assertEqual([bytes(s.payload) for s in slots],before);self.assertEqual(len(app._undo_stack),count)

    def test_named_flag_mirroring_uses_member_identity_and_inserts_missing_flags(self):
        from test_flag_editing import FlagEditingTest, JOIN
        app=FlagEditingTest().prepared();f=app.core_of()
        fm=facilities.locate(f);fl=next(fl for fl in fm.flags if fl.hash==JOIN)
        peer=core.flag_remove(f,fm,fl)
        slots=peers(app,[peer]);before=[bytes(s.payload) for s in slots]
        app._write_flag(fm.index,JOIN,254)
        for sv in slots:
            self.assertEqual(entries.flag_values(core.SaveFile(sv.payload))[JOIN],254)
        self.assertEqual(len(app._undo_stack),1)
        app.undo();self.assertEqual([bytes(s.payload) for s in slots],before)

    @patch('deed_page.messagebox.askokcancel',return_value=False)
    def test_claim_warning_includes_peer_claims_and_cancel_keeps_all_saves(self,confirm):
        from test_deed_page import DeedPageTest
        app=DeedHarness();claimed,_=DeedPageTest().claimed_training()
        app.input='40';slots=peers(app,[claimed.sv.payload]);before=[bytes(s.payload) for s in slots]
        app.set_deed();confirm.assert_called_once()
        self.assertEqual([bytes(s.payload) for s in slots],before)
        self.assertFalse(hasattr(app,'_undo_stack'))

    def test_finished_chapter_write_does_not_erase_other_slots_pending_requests(self):
        app=PageHarness();slots=peers(app)
        for n,s in enumerate(slots):s._pending_story_chapter=story.ChapterFileRequest(4,n+2)
        app.push_undo(); story_files.completed(app,slots[0])
        snapshot=app._undo_stack[0]
        self.assertIsNone(snapshot[0][2]);self.assertEqual(snapshot[1][2],slots[1]._pending_story_chapter)


class PeerSelectionTest(unittest.TestCase):
    def test_character_part_playthrough_and_checkpoint_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=SimpleNamespace(sv=None,files={},slot_paths=[])
            app._is_checkpoint=editor.App._is_checkpoint
            app._same_route=lambda s:editor.App._same_route(app,s)
            app._get=lambda p:app.files[p]
            for name,route,part,playthrough in [('Auto',1,2,0),('Manual',1,2,0),('OtherRoute',4,2,0),
                    ('OtherPart',1,1,0),('OtherRun',1,2,1),('Chapter_Kai_2_1',1,2,0),('Missing',1,2,0)]:
                f=story_fixture(route,part);f.payload[13]=playthrough
                sv=box_for(f);sv.path=str(Path(tmp)/name)
                app.files[sv.path]=sv;app.slot_paths.append(sv.path)
                if name!='Missing':Path(sv.path).touch()
                if name=='Auto':app.sv=sv
            self.assertEqual([Path(p).name for p in editor.App._peers(app)],['Manual'])
            app.sv=app.files[str(Path(tmp)/'Chapter_Kai_2_1')]
            self.assertEqual(editor.App._peers(app),[])
