"""Unit creation in later parts uses the existing live-roster format and guards."""
from pathlib import Path
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
import story_start
import unit_entries as entries
from test_unit_entries import fixture, CATANIA
from test_story import box_for
from test_unit_entry_page import Harness
from test_mirroring import peers


def later_fixture(route, part):
    f=fixture();info=story.read(f)
    for at in (info.header+12,info.user+3):f.payload[at:at+3]=bytes((route,part,2))
    for at in (info.header+45,info.user+81):struct.pack_into('<Q',f.payload,at,story.sequence(2,route,part))
    return f


class LaterUnitTest(unittest.TestCase):
    def test_all_later_routes_add_renumber_save_and_preserve_existing_records(self):
        for route,part in [(r,2) for r in (1,2,3,4)]+[(9,3)]:
            with self.subTest(route=route,part=part):
                f=later_fixture(route,part);before=bytes(f.payload)
                blocks=story_start.normalized_blocks(f)
                oldunit=f.tree().copy_object(f.tree().node_at(f.units()[0].start),0)
                g=core.SaveFile(entries.add(f,CATANIA))
                self.assertEqual(entries.status(g,CATANIA),'Already in party')
                self.assertEqual(g.tree().copy_object(g.tree().node_at(g.units()[0].start),0),oldunit)
                for key,value in blocks.items():
                    if key not in ('UnitPool','GameUserData'):
                        self.assertEqual(story_start.normalized_blocks(g)[key],value)
                with self.assertRaises(core.SaveError):entries.add(g,CATANIA)
                g=core.SaveFile(entries.renumber(g,CATANIA,45))
                self.assertEqual(entries.roster(g)[-1][1].unit_number,45)
                with tempfile.TemporaryDirectory() as tmp:
                    box=box_for(g);box.path=str(Path(tmp)/'Auto');box.save(backup=False)
                    reread=container.SaveFile(box.path)
                    self.assertEqual(reread.verify(),[])
                    self.assertEqual(story.read(core.SaveFile(reread.payload)).part,part)
                    self.assertEqual(reread.payload,g.payload)
                self.assertEqual(f.payload,before)

    def test_later_parts_use_multi_save_undo_and_redo(self):
        for route,part in ((1,2),(9,3)):
            app=Harness();app.sv.payload=later_fixture(route,part).payload
            slots=peers(app);before=[bytes(s.payload) for s in slots]
            self.assertTrue(app.apply_unit_entry('add',CATANIA),app.messages)
            after=[bytes(s.payload) for s in slots]
            app.undo();self.assertEqual([bytes(s.payload) for s in slots],before)
            app.redo();self.assertEqual([bytes(s.payload) for s in slots],after)

    def test_wrong_characters_parts_and_unsupported_contexts_still_refused(self):
        f=later_fixture(9,3);info=story.read(f)
        for route,part in ((1,3),(9,2),(9,1),(4,0),(9,4)):
            g=f.copy()
            for at in (info.header+12,info.user+3):g.payload[at:at+2]=bytes((route,part))
            with self.assertRaises(core.SaveError):entries.add(g,CATANIA)
        for mode in (b'\x12\x06',b'\x10\x08'):
            g=f.copy();g.payload[info.header+20:info.header+22]=mode
            with self.assertRaises(core.SaveError):entries.add(g,CATANIA)
