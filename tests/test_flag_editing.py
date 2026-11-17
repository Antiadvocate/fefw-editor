"""Flag value edits must preserve the list and allow recruitment restoration."""
import unittest

import fefw_core as core
import facilities
import story_start
import unit_entries as entries
from test_unit_entry_page import Harness
from test_unit_entries import fixture

BENDITZ=core.id_hash('PID_ベンディッツ')
JOIN=core.id_hash('加入_ベンディッツ')
ALIASES=[core.id_hash(k) for k in ('加入_Venditz','加入_SC11_06_ベンディッツ')]


class FlagEditingTest(unittest.TestCase):
    def prepared(self):
        app=Harness();f=core.SaveFile(entries.add(fixture(),BENDITZ))
        for h in ALIASES:f=core.SaveFile(core.flag_add(f,facilities.locate(f),h,1))
        app.sv.payload=f.payload;return app

    def test_real_flags_ui_then_restore_preserves_list_unit_and_undo(self):
        app=self.prepared();original=bytes(app.sv.payload)
        for h in ALIASES:app._write_flag(facilities.locate(app.core_of()).index,h,0)
        self.assertEqual(entries.status(app.core_of(),BENDITZ),'Already in party')
        f=app.core_of();before=bytes(f.payload);flags=entries.flag_values(f)
        selected=next(x for x in facilities.locate(f).flags if x.hash==JOIN)
        app._write_flag(facilities.locate(f).index,JOIN,0)
        self.assertEqual({i for i,(a,b) in enumerate(zip(before,app.sv.payload)) if a!=b},{selected.offset})
        expected=dict(flags);expected[JOIN]=0
        self.assertEqual(entries.flag_values(app.core_of()),expected)
        self.assertTrue(entries.status(app.core_of(),BENDITZ).startswith('Existing inactive'))
        off=bytes(app.sv.payload)
        app.undo();self.assertEqual(app.sv.payload,before)
        app.redo();self.assertEqual(app.sv.payload,off)
        self.assertTrue(app.apply_unit_entry('restore',BENDITZ))
        restored=bytes(app.sv.payload)
        self.assertEqual(story_start.normalized_blocks(core.SaveFile(original))['UnitPool'],
                         story_start.normalized_blocks(app.core_of())['UnitPool'])
        self.assertEqual(entries.flag_values(app.core_of()),flags)
        app.undo();self.assertEqual(app.sv.payload,off)
        app.redo();self.assertEqual(app.sv.payload,restored)

    def test_wide_promotion_and_reduction_preserve_other_values_and_blocks(self):
        app=self.prepared();f=app.core_of();blocks=story_start.normalized_blocks(f)
        flags=entries.flag_values(f);initial_count=len(flags)
        for value in (254,255,65536,0x7fffffff,0):
            fm=facilities.locate(app.core_of());app._write_flag(fm.index,JOIN,value)
            flags[JOIN]=value
            self.assertEqual(entries.flag_values(app.core_of()),flags)
            self.assertEqual(len(facilities.locate(app.core_of()).flags),initial_count)
            after=story_start.normalized_blocks(app.core_of())
            for key in blocks.keys()-{'GameUserData'}:self.assertEqual(after[key],blocks[key])
        self.assertTrue(next(x for x in facilities.locate(app.core_of()).flags if x.hash==JOIN).wide)

    def test_invalid_stale_or_noop_edits_leave_payload_and_history_alone(self):
        app=self.prepared();before=bytes(app.sv.payload);fm=facilities.locate(app.core_of())
        for value in (-1,2**31,True,1.5):app._write_flag(fm.index,JOIN,value)
        app._write_flag(fm.index,JOIN,1)
        app._write_flag(999,JOIN,0)
        app._write_flag(fm.index,0xdeadbeef,0)
        app.mirrored=True;app._write_flag(fm.index,JOIN,0)
        self.assertEqual(app.sv.payload,before)
        self.assertFalse(hasattr(app,'_undo_stack'))
        f=core.SaveFile(before);fm=facilities.locate(f);fm.flags.append(fm.flags[-1])
        with self.assertRaises(core.SaveError):core.flag_set(f,fm,fm.flags[-1].hash,0)

    def test_zero_aliases_without_a_unit_do_not_offer_restoration(self):
        f=fixture()
        for h in ALIASES:f=core.SaveFile(core.flag_add(f,facilities.locate(f),h,0))
        self.assertEqual(entries.status(f,BENDITZ),'Not present — add level 1')
        with self.assertRaises(core.SaveError):entries.restore(f,BENDITZ)
