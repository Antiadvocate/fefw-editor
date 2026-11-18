"""Repairs operate on current progress, never chapter entry or another slot."""
import struct
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import facilities as fac
import fefw_core as core
import fefw_save as container
import story
import story_start as start
import story_troubleshoot as trouble
import story_prerequisites as dietrich
import story_theodora_prerequisites as theodora
import worldmap
from test_story import StoryHarness, box_for
from test_story_part2 import fixture as part2_fixture
from test_story_theodora_prerequisites import fixture as map_fixture


def source(route, part, chapter):
    f = part2_fixture(route) if part == 2 else map_fixture() if route == 3 else StoryHarness(route).core_of()
    f = core.SaveFile(story.edited(f, chapter, route=route))
    i = story.read(f)
    # A current story beat must survive even when it is not the entry sequence.
    for at in (i.header+45, i.user+81):
        struct.pack_into('<Q', f.payload, at, 0x1122334455667788)
    return f


class TroubleshootTest(unittest.TestCase):
    def test_known_route_part_chapter_rules_and_bounded_repairs(self):
        cases = [(1, 1, 3), (1, 1, 12), (2, 1, 5), (2, 1, 6), (2, 1, 7),
                 (3, 1, 4), (3, 1, 6), (3, 1, 8), (3, 1, 9)]
        cases += [(r, 2, c) for r in story.PREFIXES for c in (5, 6)]
        for route, part, chapter in cases:
            with self.subTest(route=route, part=part, chapter=chapter):
                f = source(route, part, chapter)
                rule = trouble.rule_for(story.read(f))
                if rule.switches:
                    f = core.SaveFile(fac.edited(f, {h: False for h in rule.switches}))
                    expected = fac.edited(f, {h: True for h in rule.switches})
                elif rule.secret:
                    expected = dietrich.edited(f, chapter)
                else:
                    expected = theodora.edited(f, chapter)
                before = bytes(f.payload); info = story.read(f)
                report = trouble.diagnose(f)
                self.assertTrue(report.actionable, report)
                self.assertTrue(all(row.needed for row in report.checks))
                fixed = trouble.edited(f)
                self.assertEqual(fixed, expected)
                self.assertEqual(f.payload, before)
                g = core.SaveFile(fixed); after = trouble.diagnose(g)
                self.assertFalse(after.actionable)
                self.assertTrue(all(not row.needed for row in after.checks))
                self.assertEqual(trouble.edited(g), fixed)
                self.assertEqual(story.read(g).sequence, info.sequence)
                a, b = start.normalized_blocks(f), start.normalized_blocks(g)
                for k in a.keys()-({'GmapSpotMgr'} if rule.map_exit else {'GameUserData'}):
                    self.assertEqual(a[k], b[k])
                box = box_for(f); box.payload = fixed
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder)/'Auto'; path.write_bytes(box.to_bytes())
                    reopened = container.SaveFile(path)
                    self.assertEqual(reopened.verify(), [])
                    self.assertEqual(reopened.payload, fixed)

    def test_unknown_parts_and_chapters_do_not_inherit_repairs(self):
        for route, part, chapter in ((1, 1, 2), (2, 1, 2), (4, 1, 1), (4, 1, 6), (3, 2, 4)):
            f = source(route, part, chapter)
            report = trouble.diagnose(f)
            self.assertFalse(report.actionable)
            self.assertIn('No established', report.note)
            self.assertEqual(trouble.edited(f), f.payload)
        f = source(3, 2, 6); i = story.read(f)
        f.payload[i.header+13] = f.payload[i.user+4] = 3
        report = trouble.diagnose(f)
        self.assertEqual(report.progress.part, 3)
        self.assertIn('No established Part 3 progress repair', report.note)
        self.assertFalse(report.checks)
        self.assertEqual(trouble.edited(f), f.payload)
        self.assertEqual(trouble.ISSUES_URL, 'https://github.com/Antiadvocate/fefw-editor/issues')

    def test_battle_and_unknown_values_are_read_only(self):
        f = source(3, 2, 6)
        f = core.SaveFile(fac.edited(f, {start.PART2_MIDDLE_MOVEMENT: False}))
        i = story.read(f); f.payload[i.header+20:i.header+22] = b'\x12\x02'
        report = trouble.diagnose(f)
        self.assertTrue(report.checks[0].needed)
        self.assertFalse(report.actionable)
        before = bytes(f.payload)
        with self.assertRaises(core.SaveError): trouble.edited(f)
        self.assertEqual(f.payload, before)
        f = source(2, 1, 6)
        fm = fac.locate_member(f, fac.PROGRESSION_MEMBER)
        f = core.SaveFile(core.replace_content(f, fm.start, b'\0'+struct.pack('<H', 1)+struct.pack('<IB', dietrich.LOWER, 9)))
        self.assertFalse(trouble.diagnose(f).actionable)
        before = bytes(f.payload)
        with self.assertRaises(core.SaveError): trouble.edited(f)
        self.assertEqual(f.payload, before)
        f = source(3, 1, 9); rec = worldmap.read(f)[theodora.TROY_EXIT[0]]
        f.payload[rec.at+4] = 99
        self.assertIn('Cannot safely inspect', trouble.diagnose(f).blocked)

    def test_missing_map_is_a_diagnostic_not_an_exception(self):
        f = core.SaveFile(story.edited(StoryHarness(3).core_of(), 9, route=3))
        report = trouble.diagnose(f)
        self.assertFalse(report.actionable)
        self.assertIn('Cannot safely inspect', report.blocked)

    def test_ui_history_slot_isolation_and_stale_guard(self):
        app = StoryHarness(3)
        f = source(3, 2, 6)
        f = core.SaveFile(fac.edited(f, {start.PART2_MIDDLE_MOVEMENT: False}))
        app.sv = box_for(f); slot = app.sv; before = bytes(slot.payload)
        pending = story.ChapterFileRequest(3, 6, 2); slot._pending_story_chapter = pending
        self.assertTrue(app.apply_progress_repair(slot, before))
        after = bytes(slot.payload)
        self.assertEqual(slot._pending_story_chapter, pending)
        self.assertEqual(len(app._undo_stack), 1)
        app.undo(); self.assertEqual(slot.payload, before)
        app.redo(); self.assertEqual(slot.payload, after)
        self.assertFalse(app.apply_progress_repair(slot, after))
        self.assertEqual(len(app._undo_stack), 1)
        app.undo(); app.mirrored = True
        self.assertFalse(app.apply_progress_repair(slot, before))
        self.assertEqual(slot.payload, before)
        app.mirrored = False; app.sv = StoryHarness(1).sv
        other = bytes(app.sv.payload)
        self.assertFalse(app.apply_progress_repair(slot, before))
        self.assertEqual(app.sv.payload, other)
        app.sv = slot; slot.payload = bytearray(after)
        self.assertFalse(app.apply_progress_repair(slot, before))
        self.assertEqual(slot.payload, after)

    def test_dialog_close_is_read_only_and_no_fix_offers_upstream_issues(self):
        import story_page
        app = StoryHarness(4); app.p = {'bg': '#000000'}
        app.place_dialog = MagicMock()
        app.wait_window = MagicMock()
        before = bytes(app.sv.payload); buttons = {}
        def button(*args, **kwargs):
            widget = MagicMock(); buttons[kwargs['text']] = (widget, kwargs.get('command'))
            return widget
        with patch.object(story_page.tk, 'Toplevel', return_value=MagicMock()), \
                patch.object(story_page.ttk, 'Frame', MagicMock()), \
                patch.object(story_page.ttk, 'Label', MagicMock()), \
                patch.object(story_page.ttk, 'Treeview', MagicMock()), \
                patch.object(story_page.ttk, 'Button', side_effect=button):
            app.open_progress_troubleshooter()
        self.assertEqual(app.sv.payload, before)
        self.assertFalse(app.dirty_slots)
        buttons['Apply suggested unlocks'][0].state.assert_called_with(['disabled'])
        with patch('webbrowser.open') as opened:
            buttons['Open Antiadvocate/fefw-editor issues'][1]()
            opened.assert_called_once_with(trouble.ISSUES_URL)
        buttons['Close'][1]()
        self.assertEqual(app.sv.payload, before)


if __name__ == '__main__':
    unittest.main()
