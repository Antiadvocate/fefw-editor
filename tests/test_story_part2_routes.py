"""Inferred shared Part 2 targets must preserve route, player data and history."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import fefw_core as core
import fefw_save as container
import facilities
import story
import story_start as start
import story_files
import story_page
from test_story import StoryHarness, box_for
from test_story_part2 import fixture


class Part2RoutesTest(unittest.TestCase):
    def test_each_route_conversion_and_six_targets_preserve_player_data(self):
        for route in story.PREFIXES:
            with self.subTest(route=route):
                f = fixture(route, 1)
                f = core.SaveFile(facilities.edited(f, {start.PART2_UPPER_MOVEMENT: False, start.PART2_MIDDLE_MOVEMENT: False}))
                before = bytes(f.payload)
                old = start.normalized_blocks(f)
                converted = core.SaveFile(start.enter_part2(f))
                self.assertEqual(start.chapters_for(route, 2), tuple(range(1, 7)))
                for chapter in start.chapters_for(route, 2):
                    g = core.SaveFile(start.edited(converted, chapter))
                    info = start.validate(g)
                    self.assertEqual((info.route, info.part, info.chapter), (route, 2, chapter))
                    self.assertEqual(info.sequence, story.sequence(chapter, 1, 2))
                    self.assertEqual(struct.unpack_from('<H5B', g.payload, info.header+22),
                                     (1450, *start.PART2_DATES[chapter], 0))
                    now = start.normalized_blocks(g)
                    for key in old.keys()-{'Header', 'GameUserData', 'GameSchedule', 'Calendar', 'GameRestartData'}:
                        self.assertEqual(old[key], now[key])
                    # Compare the entire user object, permitting only the existing
                    # chapter-specific movement repair plus part/chapter/sequence/resume fields.
                    repair = {5: start.PART2_UPPER_MOVEMENT, 6: start.PART2_MIDDLE_MOVEMENT}.get(chapter)
                    expected_source = core.SaveFile(facilities.edited(f, {repair: True})) if repair else f
                    expected = bytearray(start.normalized_blocks(expected_source)['GameUserData'])
                    expected[8:10] = bytes((2, chapter))
                    struct.pack_into('<Q', expected, 85, info.sequence)
                    struct.pack_into('<Q', expected, 4+start.RESUME_OFFSET, start.CHECKPOINT_ID)
                    self.assertEqual(expected, now['GameUserData'])
                    self.assertEqual(start.edited(g, chapter), g.payload)
                self.assertEqual(f.payload, before)

    def test_route_specific_files_and_undo_after_save_for_each_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            for route, code in story.FILE_CODES.items():
                a = StoryHarness(route); a.sv = box_for(fixture(route, 1))
                a.sv.path = str(Path(tmp)/f'Auto-{code}')
                original = bytes(a.sv.payload)
                a.apply_part2_entry()
                converted = bytes(a.sv.payload)
                self.assertNotEqual(original, converted)
                for part, action in ((2, None), (1, a.undo), (2, a.redo)):
                    if action: action()
                    a.sv.save(backup=False)
                    b = container.SaveFile(a.sv.path); i = story.read(core.SaveFile(b.payload))
                    self.assertEqual(b.verify(), [])
                    self.assertEqual((i.route, i.part, b.raw[40], b.raw[41]), (route, part, route, part))
                a.apply_story_chapter(5, True)
                plan = story_files.prepare({a.sv.path: a.sv}, {a.sv.path})[a.sv.path]
                self.assertEqual(Path(plan.target).name, f'Chapter_{code}_2_5')
                a.sv._pending_story_chapter = story.ChapterFileRequest(route, 5, 1)
                with self.assertRaises(core.SaveError):
                    story_files.prepare({a.sv.path: a.sv}, {a.sv.path})
                self.assertFalse(list(Path(tmp).glob('Part_*')))

    def test_opt_in_never_allows_route_swaps_or_unsupported_parts(self):
        for route in story.PREFIXES:
            box = box_for(fixture(route, 1))
            info = story.read(core.SaveFile(start.enter_part2(fixture(route, 1))))
            with self.assertRaises(core.SaveError): story.check_outer(box.raw, info)
            story.check_outer(box.raw, info, allow_part_change=True)
            for other in set(story.PREFIXES)-{route}:
                raw = bytearray(box.raw); raw[40] = other
                with self.assertRaises(core.SaveError): story.check_outer(raw, info, allow_part_change=True)
            raw = bytearray(box.raw); raw[41] = 3
            with self.assertRaises(core.SaveError): story.check_outer(raw, info, allow_part_change=True)
        for route, part in ((9, 1), (4, 2), (2, 3)):
            with self.assertRaises(core.SaveError): start.enter_part2(fixture(route, part))

    def test_route_evidence_warning_and_slot_swap(self):
        for route in (2, 3, 4):
            self.assertIn('reached the next battle', story_page.warning_points(route, 2)[0])
            self.assertIn('Game-tested', story_page.chapter_evidence(route, 5, 2))
            a = StoryHarness(route); a.sv = box_for(fixture(route, 1))
            original = a.sv; before = bytes(original.payload)
            with patch.object(story_page.messagebox, 'askyesno', return_value=False) as dialog:
                a.open_part2_entry()
            warning = dialog.call_args.args[1]
            self.assertIn(f'Part_{story.FILE_CODES[route]}_2', warning)
            self.assertEqual(original.payload, before)
            other = box_for(fixture(1, 1)); other_before = bytes(other.payload)
            def swap(*args, **kwargs):
                a.sv = other
                return True
            with patch.object(story_page.messagebox, 'askyesno', side_effect=swap):
                a.open_part2_entry()
            self.assertEqual(other.payload, other_before)
            self.assertEqual(original.payload, before)
            self.assertIn('selected save changed', a.messages[-1][0])
