"""Private Test 2 returns and equality with the game-tested repair exports."""
from pathlib import Path
import os
import tempfile
import unittest
import fefw_core as core
import fefw_save as container
import story_start as start
import story_theodora_prerequisites as pre
from research.theodora_retry_kit import build
from research.dietrich_retry_kit import flag_snapshot
import tutorials


@unittest.skipUnless(all(os.environ.get(k) for k in ('FEFW_THEODORA_SOURCE_DIR',
    'FEFW_THEODORA_RETURN_DIR','FEFW_THEODORA_TEST2_RETURN_DIR')), 'No Theodora acceptance captures supplied')
class TheodoraAcceptancePrivateTest(unittest.TestCase):
    def test_returns_and_integrated_entries_match_accepted_repair_deltas(self):
        returns=Path(os.environ['FEFW_THEODORA_TEST2_RETURN_DIR']);count=0
        for path in returns.glob('*/*'):
            if not path.is_file():continue
            count+=1;box=container.SaveFile(str(path));f=core.SaveFile(box.payload)
            self.assertEqual(box.verify(),[]);h=f.block('Header').start;u=core.user_data(f)
            self.assertEqual(box.raw[40:43],f.payload[h+12:h+15]);self.assertEqual(box.raw[40:43],f.payload[u+3:u+6])
            self.assertEqual(box.raw[73:81],f.payload[h+45:h+53]);self.assertEqual(box.raw[73:81],f.payload[u+81:u+89])
            self.assertEqual(box.raw[48:57],f.payload[h+20:h+29])
        self.assertEqual(count,9)
        for name in ('T2-04-Middle-gate','T2-06A-City-passages','T2-08-City-passages','T2-09A-Troy-exit'):
            a=container.SaveFile(str(returns/name/'Auto'));b=container.SaveFile(str(returns/name/'Auto-after-progress'))
            self.assertNotEqual(a.raw[73:81],b.raw[73:81])
        source=Path(os.environ['FEFW_THEODORA_SOURCE_DIR'])/'Auto'
        box=container.SaveFile(str(source));f=core.SaveFile(box.payload);original=bytes(f.payload)
        old=Path(os.environ['FEFW_THEODORA_RETURN_DIR'])
        with tempfile.TemporaryDirectory() as tmp:
            kit=Path(tmp)/'cases';build(old,kit)
            for ch,name in ((4,'T2-04-Middle-gate'),(6,'T2-06A-City-passages'),(8,'T2-08-City-passages'),(9,'T2-09A-Troy-exit')):
                arrival=core.SaveFile(container.SaveFile(str(old/f'T1-{ch:02d}-Chapter-{ch:02d}'/'Auto')).payload)
                expected=container.SaveFile(str(kit/name/'Auto'))
                self.assertEqual(pre.edited(arrival,ch),expected.payload)
            for ch in range(1,13):
                baseline=core.SaveFile(start._edited_at_entry(f,ch,start.THEODORA_YEARS[ch],start.THEODORA_DATES[ch]))
                g=core.SaveFile(start.edited(f,ch));self.assertEqual(g.payload,pre.edited(baseline,ch))
                self.assertEqual(start.edited(g,ch),g.payload)
                self.assertEqual(tutorials.read(g),tutorials.read(f))
                a,b=start.normalized_blocks(baseline),start.normalized_blocks(g)
                allowed={'GmapSpotMgr'} if ch==9 else {'GameUserData'}
                for k in a.keys()-allowed:self.assertEqual(a[k],b[k])
                before,after=flag_snapshot(baseline),flag_snapshot(g)
                delta={k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}
                self.assertEqual(delta,{f'4ad575a2:{h:08x}' for h in pre.CITY.get(ch,())})
                out=Path(tmp)/'Auto';box.payload=g.payload;out.write_bytes(box.to_bytes())
                reopened=container.SaveFile(str(out));self.assertEqual(reopened.verify(),[]);self.assertEqual(reopened.payload,g.payload)
                self.assertEqual(reopened.raw[40:43],bytes((3,1,ch)))
        self.assertEqual(bytes(f.payload),original)
