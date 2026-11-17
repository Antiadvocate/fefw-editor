"""Optional private story evidence; source files are never changed."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
from research.story_probes import build_probes


class StoryPrivateTest(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('FEFW_STORY_TEST_SAVE'),'No private story baseline supplied')
    def test_all_chapter_probes_preserve_every_unrelated_byte_and_refuse_overwrite(self):
        source=Path(os.environ['FEFW_STORY_TEST_SAVE']);original=source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'probes';r=build_probes(source,output)
            self.assertEqual(len(r['cases']),12)
            self.assertEqual((output/'00-Control'/'Auto').read_bytes(),original)
            for row in r['cases']:
                self.assertEqual(row['status'],'Checksum/structure/preservation passed; game test pending')
                self.assertLessEqual(len(row['changed_payload_offsets']),18)
            with self.assertRaises(ValueError):build_probes(source,output)
            self.assertEqual((output/'00-Control'/'Auto').read_bytes(),original)
        self.assertEqual(source.read_bytes(),original)

    @unittest.skipUnless(os.environ.get('FEFW_STORY_CHECKPOINT_DIR'),'No original checkpoint evidence supplied')
    def test_natural_chapter_ids_and_exact_earlier_chapter9_payload_reproduced(self):
        root=Path(os.environ['FEFW_STORY_CHECKPOINT_DIR'])
        for chapter in (1,2):
            path=root/f'Chapter_Led_1_{chapter}';old=path.read_bytes();box=container.SaveFile(str(path))
            self.assertEqual(box.verify(),[]);f=core.SaveFile(box.payload)
            self.assertEqual(story.read(f).sequence,story.sequence(chapter))
            self.assertEqual(path.read_bytes(),old)
        f=core.SaveFile(container.SaveFile(str(root/'Chapter_Led_1_2')).payload)
        p=story.edited(f,9)
        # Hash of the successful round-two restoration's decompressed payload,
        # independently recorded from the original private C experiment.
        expected=os.environ.get('FEFW_STORY_PRIOR_CH9')
        if expected:
            prior=container.SaveFile(expected);self.assertEqual(prior.verify(),[])
            self.assertEqual(bytes(p),bytes(prior.payload))
