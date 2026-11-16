"""Optional Leda Test 5 evidence; Chapter 1 remains a reported game failure."""
from pathlib import Path
import os
import struct
import unittest

import fefw_core as core
import fefw_save as container
import story
import story_start as start


@unittest.skipUnless(os.environ.get('FEFW_STORY5_RETURN_DIR') and os.environ.get('FEFW_OBELISK5_DIR'), 'No private Test 5 and Obelisk returns supplied')
class Story5ReturnsTest(unittest.TestCase):
    def test_eight_captures_checksums_chapters_progression_and_unknown_state_guard(self):
        root = Path(os.environ['FEFW_STORY5_RETURN_DIR'])
        obelisk = Path(os.environ['FEFW_OBELISK5_DIR'])
        paths = sorted(root.rglob('Auto*'))
        self.assertEqual(len(paths),5)
        paths += [obelisk/name for name in ('Chapter_Led_1_9(1)','OB5-01_Auto','OB5-01_Auto-after-advancement')]
        sequences = {}
        for path in paths:
            with self.subTest(path=path.name,folder=path.parent.name):
                raw=path.read_bytes();box=container.SaveFile(str(path));self.assertEqual(box.verify(),[])
                f=core.SaveFile(box.payload);h=f.block('Header').start;u=core.user_data(f)
                chapter=int(path.parent.name.split('-')[1]) if path in paths[:5] else 9
                self.assertEqual(tuple(f.payload[h+12:h+15]),(4,1,chapter))
                self.assertEqual(tuple(f.payload[u+3:u+6]),(4,1,chapter))
                sequence=struct.unpack_from('<Q',f.payload,h+45)[0]
                self.assertEqual(sequence,struct.unpack_from('<Q',f.payload,u+81)[0])
                sequences.setdefault(chapter,set()).add(sequence)
                mode=bytes(f.payload[h+20:h+22])
                if mode not in (b'\x12\x05',b'\x10\x0b'):
                    with self.assertRaises(core.SaveError):start.validate(f)
                else:
                    self.assertEqual(start.validate(f).chapter,chapter)
                self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(len(sequences[2]),2)
        self.assertEqual(len(sequences[3]),2)
        self.assertEqual(len(sequences[9]),3)

    def test_editor_created_checkpoint_has_full_entry_state_and_obelisk_returns_advance(self):
        root=Path(os.environ['FEFW_OBELISK5_DIR'])
        box=container.SaveFile(str(root/'Chapter_Led_1_9(1)'));f=core.SaveFile(box.payload)
        info=start.validate(f)
        self.assertEqual((info.chapter,info.sequence),(9,story.sequence(9)))
        self.assertEqual(struct.unpack_from('<Q',f.payload,info.user+58)[0],start.CHECKPOINT_ID)
        self.assertEqual(struct.unpack_from('<H5B',f.payload,info.header+22),(1449,7,10,18,0,0))
        self.assertEqual(start.edited(f,9),f.payload)
        self.assertEqual(box.raw[48:57],f.payload[info.header+20:info.header+29])
        for name,seq in [('OB5-01_Auto',0xd1a25c2f18128a5b),('OB5-01_Auto-after-advancement',0xa27302ce5e5e5a75)]:
            g=core.SaveFile(container.SaveFile(str(root/name)).payload)
            self.assertEqual(story.read(g).sequence,seq)
