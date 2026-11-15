"""Opt-in private fixture validation; never write the supplied baseline."""
import os
from pathlib import Path
import tempfile
import unittest

import facilities as fac
import fefw_core as core
import fefw_save as container
from test_facilities import outside, STABLES
from test_tutorials import raw_map


@unittest.skipUnless(os.environ.get('FEFW_FACILITY_TEST_SAVE'), 'No private facility fixture supplied')
class FacilityPrivateTest(unittest.TestCase):
    def test_every_switch_both_directions_preserves_unrelated_records(self):
        source=Path(os.environ['FEFW_FACILITY_TEST_SAVE']);original=source.read_bytes()
        box=container.SaveFile(str(source));self.assertEqual(box.verify(),[])
        f=core.SaveFile(box.payload);before=raw_map(f,fac.locate(f));preserved=outside(f)
        for h in fac.catalog():
            for state in (False,True):
                with self.subTest(h=f'{h:08x}',state=state):
                    changed=core.SaveFile(fac.edited(f,{h:state}))
                    self.assertEqual(fac.enabled(h,fac.read(changed).get(h)),state)
                    after=raw_map(changed,fac.locate(changed))
                    self.assertEqual({k:v for k,v in before.items() if k!=h},
                                     {k:v for k,v in after.items() if k!=h})
                    self.assertEqual(outside(changed),preserved)
        self.assertEqual(source.read_bytes(),original)

    def test_mixed_controls_serialize_reopen_preserving_baseline_and_other_maps(self):
        source=Path(os.environ['FEFW_FACILITY_TEST_SAVE']);original=source.read_bytes()
        box=container.SaveFile(str(source));before=core.SaveFile(box.payload)
        edits={0xb9a0e16b:False,0x0be47d8b:False,0x2e270aa7:False,0xc125a07e:True}
        box.payload=fac.edited(before,edits)
        expected=bytearray(box.payload);core.fix_embedded_hashes(expected)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'Auto';target.write_bytes(box.to_bytes())
            loaded=container.SaveFile(str(target));self.assertEqual(loaded.verify(),[])
            self.assertEqual(loaded.payload,expected)
            after=core.SaveFile(loaded.payload)
            self.assertEqual(fac.read(after).get(STABLES),fac.read(before).get(STABLES))
            for h,state in edits.items():self.assertEqual(fac.enabled(h,fac.read(after).get(h)),state)
            a,b=core.flag_maps(before),core.flag_maps(after)
            index=fac.locate(before).index
            self.assertEqual(len(a),len(b))
            for i in range(len(a)):
                if i!=index:self.assertEqual(raw_map(before,a[i]),raw_map(after,b[i]))
        self.assertEqual(source.read_bytes(),original)
