import unittest
from unittest.mock import patch

import facility_access as access
import fefw_core as core
from test_fast_travel import fixture, rows
from test_facilities import rows as facility_rows


class FacilityAccessTest(unittest.TestCase):
    def test_route_filters_distinct_from_registered_travel_and_entry(self):
        data=rows()+[(h,1,False) for h in access.DETAILS]
        f=fixture([facility_rows(),data]);original=bytes(f.payload)
        for route in ('Cai','Dietrich','Theodora','Leda','Eshmel'):
            with patch.object(access,'route_info',return_value=(route,1,9)):
                result={r['hash']:r for r in access.report(f)}
                self.assertTrue(all(r['stored']=='Recorded (1)' for r in result.values()))
                for h,required in ((access.ROOM,'Cai'),(access.GARDEN,'Cai'),(access.SALAMIS,'Theodora')):
                    self.assertIn('Route matches' if route==required else 'Route mismatch', result[h]['route_check'])
                self.assertEqual(result[access.YU_PHAS]['route_check'],'No locator route filter')
                self.assertIn('route/chapter',result[access.YU_PHAS]['entry'])
                text=access.diagnostics(f);self.assertIn(route+' P1 Ch9',text)
                self.assertIn('absent',text);self.assertIn('not a guarantee',text)
        self.assertEqual(bytes(f.payload),original)

    def test_missing_unknown_invalid_map_and_unknown_route_are_not_available(self):
        f=fixture([rows()+[(access.ROOM,2,False)]])
        with patch.object(access,'route_info',return_value=None):
            result={r['hash']:r for r in access.report(f)}
            self.assertEqual(result[access.ROOM]['stored'],'Unknown (2)')
            self.assertEqual(result[access.SALAMIS]['stored'],'Absent')
            self.assertTrue(all(r['route_check']=='Unknown route' for r in result.values()))
            broken=access.report(fixture([[]]))
            self.assertTrue(all(r['stored']=='Unavailable' and r['error'] for r in broken))

    def test_diagnostics_preserves_duplicate_condition_records_and_label_identity(self):
        key='拠点_Hub_000_A60_アウロラ神殿側ドア開放';h=core.id_hash(key)
        f=fixture([rows(),[(h,1,False)],[(h,2,False)]])
        with patch.object(access,'route_info',return_value=('Leda',1,9)):
            text=access.diagnostics(f)
        self.assertIn('list 1: 1, list 2: 2',text)
        names={};access.apply_labels(names);self.assertEqual(names[h]['name'],key)
        names[h]['name']='wrong';before=dict(names)
        with self.assertRaises(core.SaveError):access.apply_labels(names)
        self.assertEqual(names,before)
