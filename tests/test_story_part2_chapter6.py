"""Chapter 6 needs middle-city movement without broad progression unlocks."""
from pathlib import Path
import os
import unittest

import fefw_core as core
import fefw_save as container
import facilities
import story
import story_start as start
import story_page
from test_story_part2 import fixture


class Chapter6RepairTest(unittest.TestCase):
    def test_only_middle_restriction_is_removed_on_all_routes(self):
        lower = core.id_hash('行動範囲制限_下層')
        for route in story.PREFIXES:
            f = core.SaveFile(start.edited(fixture(route), 6))
            f = core.SaveFile(facilities.edited(f, {
                start.PART2_MIDDLE_MOVEMENT: False,
                start.PART2_UPPER_MOVEMENT: False, lower: False}))
            before = bytes(f.payload); roots = start.normalized_blocks(f)
            fixed = core.SaveFile(start.repair_part2_chapter6(f))
            expected = facilities.edited(f, {start.PART2_MIDDLE_MOVEMENT: True})
            self.assertEqual(fixed.payload, expected)
            values = {v.hash: v.value for v in facilities.locate_member(fixed, facilities.PROGRESSION_MEMBER).flags}
            self.assertNotIn(start.PART2_MIDDLE_MOVEMENT, values)
            self.assertEqual(values[start.PART2_UPPER_MOVEMENT], 1)
            self.assertEqual(values[lower], 1)
            after = start.normalized_blocks(fixed)
            for key in roots.keys()-{'GameUserData'}:
                self.assertEqual(roots[key], after[key])
            self.assertEqual(start.repair_part2_chapter6(fixed), fixed.payload)
            self.assertEqual(start.edited(f, 6), fixed.payload)
            self.assertEqual(f.payload, before)
            with self.assertRaises(core.SaveError): start.repair_part2_chapter6(fixture(route))
        self.assertIn('manual', story_page.chapter_evidence(3, 6, 2))
        self.assertIn('awaiting retest', story_page.chapter_evidence(3, 6, 2))


@unittest.skipUnless(os.environ.get('FEFW_PART2_REMAINING_RETURN_DIR'), 'No private remaining-route returns supplied')
class RemainingReturnsTest(unittest.TestCase):
    def test_all_returns_reach_battle_and_theodora_middle_flag_is_repaired(self):
        root = Path(os.environ['FEFW_PART2_REMAINING_RETURN_DIR'])
        for route, name in ((2, 'Dietrich'), (3, 'Theodora'), (4, 'Leda')):
            for chapter in range(1, 7):
                folder = root/name/f'P2-{chapter:02d}-Chapter-{chapter:02d}'
                after_name = 'Auto-after-progress-and-edit' if (route, chapter) == (3, 6) else 'Auto-after-progress'
                for filename, mode in (('Auto', b'\x12\x05'), (after_name, b'\x12\x02')):
                    box = container.SaveFile(folder/filename); f = core.SaveFile(box.payload); i = story.read(f)
                    self.assertEqual(box.verify(), [])
                    self.assertEqual((i.route, i.part, i.chapter), (route, 2, chapter))
                    self.assertEqual(f.payload[i.header+20:i.header+22], mode)
                    if chapter == 6:
                        flags = {v.hash: v.value for v in facilities.locate_member(f, facilities.PROGRESSION_MEMBER).flags}
                        expected = int(route == 3 and filename == 'Auto')
                        self.assertEqual(flags.get(start.PART2_MIDDLE_MOVEMENT, 0), expected)
