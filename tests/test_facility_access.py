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
                self.assertTrue(all(r['stored']=='Recorded (1)' for r in result.values() if r['hash'] is not None))
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
            self.assertTrue(all(r['route_check']=='Unknown route' for r in result.values() if r['hash'] is not None))
            broken=access.report(fixture([[]]))
            self.assertTrue(all(r['stored']=='Unavailable' and r['error'] for r in broken if r['hash'] is not None))

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

    def test_yu_phas_gate_reports_both_independent_switches_without_writing(self):
        for registered in (False, True):
            for recorded in (False, True):
                general = facility_rows() + ([(0x7d2c41eb, 1, False)] if registered else [])
                travel = rows() + ([(0x65411bed, 1, False)] if recorded else [])
                f = fixture([general, travel]); before = bytes(f.payload)
                status = access.yu_phas_gate_status(f)
                expected = ('not enabled' if not registered else
                            'both flags recorded' if recorded else 'also enable Yu Phas Temple')
                self.assertIn(expected, status)
                self.assertEqual(next(r for r in access.report(f) if r['hash']==access.YU_PHAS)['gate_status'], status)
                self.assertIn(status, access.diagnostics(f))
                self.assertEqual(bytes(f.payload), before)
        for gate, travel, expected in ((2, 1, 'unknown registration'),
                                      (1, 0, 'unknown ordinary travel'),
                                      (1, 2, 'unknown ordinary travel')):
            f = fixture([facility_rows() + [(0x7d2c41eb, gate, False)],
                         rows() + [(0x65411bed, travel, False)]])
            self.assertIn(expected, access.yu_phas_gate_status(f))
        self.assertIn('cannot identify', access.yu_phas_gate_status(fixture([rows()])))
        self.assertIn('cannot check', access.yu_phas_gate_status(
            fixture([facility_rows() + [(0x7d2c41eb, 1, False)]])))
