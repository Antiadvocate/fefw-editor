"""Read-only regression evidence from the 12 returned Test 1 Auto files."""
import os,struct,unittest
from pathlib import Path
import fefw_core as core
import fefw_save as container
import story
from research import story_entry_probe as probe


@unittest.skipUnless(os.environ.get('FEFW_STORY_RETURN_DIR'),'No private story returns supplied')
class StoryReturnsTest(unittest.TestCase):
    def test_all_twelve_keep_requested_selector_but_old_clock_deadline_and_restart(self):
        root=Path(os.environ['FEFW_STORY_RETURN_DIR'])
        for chapter in range(1,13):
            with self.subTest(chapter=chapter):
                path=root/f'STORY-{chapter:02d}-Leda-P1-Chapter-{chapter:02d}'/'Auto';before=path.read_bytes()
                box=container.SaveFile(str(path));self.assertEqual(box.verify(),[])
                f=core.SaveFile(box.payload);i=story.read(f);tree=core.SaveTree(f.payload)
                self.assertEqual((i.route,i.part,i.chapter,i.sequence),(4,1,chapter,story.sequence(chapter)))
                self.assertEqual(f.payload[i.header+20:i.header+22],bytes((18,4 if chapter==1 else 5)))
                schedule=probe.one_block(f,'GameSchedule')
                self.assertEqual(f.payload[schedule.start+5:schedule.start+9],struct.pack('<HBB',1449,7,12))
                self.assertEqual(f.payload[schedule.start+12:schedule.start+19],struct.pack('<H5B',1449,9,1,12,0,0))
                slots=probe.members(f,tree,probe.one_block(f,'GameRestartData').start,probe.RESTART_KEYS)
                fields=probe.members(f,tree,slots[0x8c8807e8],{probe.HEADER_KEY,probe.DATA_KEY})
                data=fields[probe.DATA_KEY];size=f.u32(data+12)
                inner=bytes(f.payload[data+40:data+40+size]);snap=story.read(core.SaveFile(inner))
                self.assertEqual((snap.chapter,snap.sequence),(9,story.sequence(9)))
                self.assertEqual(f.u32(data+16),core.fnv1_32(inner))
                self.assertEqual(path.read_bytes(),before)
