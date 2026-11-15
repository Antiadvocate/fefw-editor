"""Synthetic payloads only: no game dump or personal save is required."""
import struct
import unittest

import fefw_core as core
import tutorials


def fixture(maps, extra=b'\xaa' * 24):
    p = bytearray(4)

    def obj(body):
        at = len(p)
        p.extend(bytes(4) + body)
        p.extend(bytes((-len(p)) % 4))
        struct.pack_into('<I', p, at, len(p) + 32)
        return at

    user = len(p)
    p.extend(bytes(4) + b'\xee' * 4)
    for entries in maps:
        body = bytearray(b'\0' + struct.pack('<H', len(entries)))
        for h, v, wide in entries:
            body += struct.pack('<I', h)
            body += b'\xff' + struct.pack('<i', v) if wide else bytes([v])
        obj(body)
    struct.pack_into('<I', p, user, len(p) + 32)
    other = obj(extra)
    table = len(p)
    p += struct.pack('<IIII', core.fnv1_32(b'GameUserData'), user + 32,
                     core.fnv1_32(b'GmapSpotMgr'), other + 32)
    struct.pack_into('<I', p, 0, (2 << 24) | (table + 32))
    return core.SaveFile(p)


AUTO = core.id_hash('TUTO_オートセーブ')
FORESIGHT = core.id_hash('TUTO_戦いの助言')
RELIQUARY = core.id_hash('TUTO_方尖塔倉庫')
THIRD_EYE = core.id_hash('TUTO_透視')
OBELISK = core.id_hash('TUTO_塔のアクセス')
UNKNOWN = 0xdeadbeef


def rows():
    return [(AUTO, 2, False), (FORESIGHT, 2, False), (OBELISK, 1, False),
            (UNKNOWN, -12345, True), (0xfedccdef, 77, False), (0xfedcba98, 999, True)]


def raw_map(f, fm):
    return {fl.hash: bytes(f.payload[fl.offset-(5 if fl.wide else 4):
                                    fl.offset+(4 if fl.wide else 1)]) for fl in fm.flags}


class TutorialsTest(unittest.TestCase):
    def test_corrected_names_and_hashes(self):
        cat = tutorials.catalog()
        self.assertEqual(len(cat), 115)
        for h, name in ((0x08373a0e, 'Foresight'), (0x2b0739cc, 'Drifting Reliquary'),
                        (0xf501dfbc, 'Third Eye (Cai)'), (0xc2a2c517, 'Obelisk Chamber')):
            self.assertEqual(cat[h]['label'], name)
        labels = {}
        tutorials.apply_labels(labels)
        self.assertEqual(labels[FORESIGHT]['name'], 'TUTO_戦いの助言')
        self.assertEqual(labels[FORESIGHT]['label'], 'Tutorial: Foresight')

    def test_label_overlay_rejects_conflicting_identity(self):
        with self.assertRaises(tutorials.TutorialError):
            tutorials.apply_labels({FORESIGHT: {'name': 'some_other_name'}})

    def test_locates_shifted_list_without_fixed_index(self):
        other = [(0xee000001+i, i, False) for i in range(7)]
        for maps, index in (([rows()], 0), ([other, rows()], 1), ([[], other, rows()], 1)):
            with self.subTest(index=index, maps=len(maps)):
                f = fixture(maps)
                self.assertEqual(tutorials.locate(f).index, index)
                self.assertEqual(tutorials.read(f)[FORESIGHT], 2)

    def test_add_remove_preserve_unknowns_other_block_and_input(self):
        f = fixture([rows()]); before = bytes(f.payload)
        old = raw_map(f, tutorials.locate(f))
        b = f.block('GmapSpotMgr'); other = bytes(f.payload[b.start+4:b.end])
        g = core.SaveFile(tutorials.edited(f, {FORESIGHT: None, RELIQUARY: 2, THIRD_EYE: 2}))
        self.assertEqual(bytes(f.payload), before)
        actual = raw_map(g, tutorials.locate(g))
        self.assertNotIn(FORESIGHT, actual)
        self.assertEqual(tutorials.read(g)[RELIQUARY], 2)
        for h in old.keys() - {FORESIGHT}:
            self.assertEqual(old[h], actual[h])
        b = g.block('GmapSpotMgr')
        self.assertEqual(other, bytes(g.payload[b.start+4:b.end]))
        core.SaveTree(g.payload)
        restored = core.SaveFile(tutorials.edited(g, {FORESIGHT: 2, RELIQUARY: None, THIRD_EYE: None}))
        self.assertEqual(raw_map(restored, tutorials.locate(restored)), old)
        core.SaveTree(restored.payload)

    def test_noop_is_byte_identical(self):
        f = fixture([rows()])
        self.assertEqual(tutorials.edited(f, {}), f.payload)
        self.assertEqual(tutorials.edited(f, {FORESIGHT: 2, RELIQUARY: None}), f.payload)

    def test_existing_wide_value_remains_wide(self):
        rr = [(h, v, True if h == OBELISK else wide) for h, v, wide in rows()]
        g = core.SaveFile(tutorials.edited(fixture([rr]), {OBELISK: 2}))
        fl = next(fl for fl in tutorials.locate(g).flags if fl.hash == OBELISK)
        self.assertTrue(fl.wide)
        self.assertEqual(fl.value, 2)

    def test_unknown_value_rejects_entire_batch(self):
        rr = [(h, 7 if h == OBELISK else v, wide) for h, v, wide in rows()]
        f = fixture([rr]); before = bytes(f.payload)
        with self.assertRaises(tutorials.TutorialError):
            tutorials.edited(f, {RELIQUARY: 2, OBELISK: None})
        self.assertEqual(bytes(f.payload), before)

    def test_unsupported_writes_rejected(self):
        f = fixture([rows()])
        for changes in ({FORESIGHT: 1}, {FORESIGHT: 0}, {FORESIGHT: 3}, {UNKNOWN: 2},
                        {FORESIGHT: 2.0}, {FORESIGHT: True}):
            with self.subTest(changes=changes), self.assertRaises(tutorials.TutorialError):
                tutorials.edited(f, changes)

    def test_ambiguous_or_missing_lists_rejected(self):
        for maps in ([], [[]], [[(UNKNOWN, 2, False)]], [rows(), rows()],
                     [[(FORESIGHT, 2, False)]]):
            with self.subTest(maps=maps), self.assertRaises(tutorials.TutorialError):
                tutorials.edited(fixture(maps), {RELIQUARY: 2})

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(tutorials.TutorialError):
            tutorials.read(fixture([rows()+[(FORESIGHT, 2, False)]]))

    def test_cannot_remove_last_identifying_entries(self):
        with self.assertRaises(tutorials.TutorialError):
            tutorials.edited(fixture([rows()]), {AUTO: None, FORESIGHT: None, OBELISK: None})

    def test_absent_is_distinct_from_zero(self):
        self.assertEqual(tutorials.state_label(None), 'Absent')
        self.assertIn('Unknown', tutorials.state_label(0))
        self.assertIn('preserved', tutorials.state_label(19))


if __name__ == '__main__':
    unittest.main()
