"""Synthetic blessing objects: no game dump or personal save fixture."""
import struct
import unittest

import blessings
import fefw_core as core

# Independent full-width identifiers observed in the reference save.
HASHES = (0xd2fdff3fa4a597ed, 0xa1e2e07e81a0a45b, 0x976774b9a9818925,
          0xf4fe5a5c9aab9f81, 0xb980ecffb61b6541, 0xbdafb8af054f07e0,
          0x72fc44e0a9217c6a)


def body(order=HASHES, version=2, count=7):
    return (bytes([version]) + struct.pack('<I', 123456) + bytes([count])
            + b''.join(struct.pack('<QBH', h, (i % 2), i * 25)
                       for i, h in enumerate(order)) + b'\xa5')


def fixture(bodies=None, prefix=b'\xee' * 4, block_name='GameUserData'):
    if bodies is None:
        bodies = [body()]
    p = bytearray(4)
    user = len(p)
    p.extend(bytes(4) + prefix)
    for data in bodies:
        at = len(p)
        p.extend(bytes(4) + data)
        p.extend(bytes(-len(p) % 4))
        struct.pack_into('<I', p, at, len(p) + 32)
    struct.pack_into('<I', p, user, len(p) + 32)
    other = len(p)
    p.extend(bytes(4) + b'\xbb' * 20)
    struct.pack_into('<I', p, other, len(p) + 32)
    table = len(p)
    p.extend(struct.pack('<IIII', core.fnv1_32(block_name.encode()), user + 32,
                         core.fnv1_32(b'GmapSpotMgr'), other + 32))
    struct.pack_into('<I', p, 0, (2 << 24) | (table + 32))
    return core.SaveFile(p)


class BlessingsTest(unittest.TestCase):
    def test_full_hashes_and_data_thresholds(self):
        self.assertEqual(tuple(g.hash for g in blessings.GODS), HASHES)
        self.assertEqual(tuple(g.thresholds for g in blessings.GODS),
                         (None, (25, 60, 120), (15, 40, 80), (20, 50, 100),
                          (25, 60, 120), (25, 60, 120), (20, 50, 100)))
        for god in blessings.GODS:
            if god.thresholds:
                for level, threshold in enumerate(god.thresholds, 1):
                    self.assertEqual(blessings.level_preview(god.hash, threshold - 1), level - 1)
                    self.assertEqual(blessings.level_preview(god.hash, threshold), level)
            else:
                for exp in (0, 1, 100, 65535):
                    self.assertIsNone(blessings.level_preview(god.hash, exp))

    def test_read_shifted_and_reordered_records(self):
        for order, prefix in ((HASHES, b'\xee' * 4), (HASHES[::-1], b'\xee' * 64)):
            with self.subTest(order=order):
                f = fixture([body(order)], prefix)
                table = blessings.read(f)
                self.assertEqual(table.divine_sand, 123456)
                self.assertEqual(tuple(r.hash for r in table.records), order)
                self.assertEqual(tuple(r.exp for r in table.records), tuple(i * 25 for i in range(7)))

    def test_each_god_changes_only_its_exp_bytes_and_input_is_immutable(self):
        f = fixture(); original = bytes(f.payload)
        for record in blessings.read(f).records:
            for value in (0, 1, 120, 65535):
                with self.subTest(god=record.hash, value=value):
                    after = blessings.edited(f, {record.hash: value})
                    expected = bytearray(original)
                    struct.pack_into('<H', expected, record.exp_offset, value)
                    self.assertEqual(after, expected)
                    self.assertEqual(bytes(f.payload), original)
                    reread = blessings.read(core.SaveFile(after))
                    actual = next(r for r in reread.records if r.hash == record.hash)
                    self.assertEqual(actual.exp, value)
                    self.assertEqual(actual.selected, record.selected)

    def test_reordered_edit_targets_identity_not_position(self):
        f = fixture([body(HASHES[::-1])])
        after = core.SaveFile(blessings.edited(f, {HASHES[1]: 61}))
        old, new = blessings.read(f), blessings.read(after)
        for a, b in zip(old.records, new.records):
            self.assertEqual(b.exp, 61 if a.hash == HASHES[1] else a.exp)

    def test_batch_is_atomic_and_rejects_invalid_values_and_unknown_ids(self):
        f = fixture(); original = bytes(f.payload)
        for value in (-1, 65536, True, False, 1.5, '25', None):
            with self.subTest(value=value), self.assertRaises(blessings.BlessingError):
                blessings.edited(f, {HASHES[0]: 1, HASHES[1]: value})
            self.assertEqual(bytes(f.payload), original)
        for key in (0xdeadbeef, HASHES[1] & 0xffffffff, True):
            with self.assertRaises(blessings.BlessingError):
                blessings.edited(f, {HASHES[0]: 1, key: 5})
            self.assertEqual(bytes(f.payload), original)

    def test_noop_returns_identical_copy(self):
        f = fixture()
        for edits in ({}, {r.hash: r.exp for r in blessings.read(f).records}):
            output = blessings.edited(f, edits)
            self.assertEqual(output, f.payload)
            self.assertIsNot(output, f.payload)

    def test_unknown_selection_and_padding_are_preserved(self):
        raw = bytearray(body()); raw[14] = 255  # first record's selection byte
        f = fixture([raw])
        table = blessings.read(f)
        self.assertEqual(table.records[0].selected, 255)
        new = core.SaveFile(blessings.edited(f, {HASHES[0]: 13}))
        self.assertEqual(blessings.read(new).records[0].selected, 255)
        self.assertEqual(new.payload[table.end - 1], 0xa5)

    def test_malformed_or_ambiguous_tables_refuse_edits(self):
        cases = [[], [body(version=3)], [body(count=6)], [body()[:-5]],
                 [body(HASHES[:-1] + (HASHES[0],))],
                 [body(HASHES[:-1] + (0x1122334455667788,))],
                 [body(), body()], [body(), body(version=3)]]
        for bodies in cases:
            with self.subTest(bodies=len(bodies)):
                f = fixture(bodies); original = bytes(f.payload)
                with self.assertRaises(core.SaveError):
                    blessings.edited(f, {HASHES[0]: 1})
                self.assertEqual(bytes(f.payload), original)

    def test_other_blocks_are_not_used_as_live_blessing_data(self):
        f = fixture(block_name='GameRestartData')
        with self.assertRaises(blessings.BlessingError):
            blessings.read(f)

    def test_hashes_inside_unrelated_content_do_not_identify_a_table(self):
        f = fixture([b'\xee' * 12 + body(), body()])
        self.assertEqual(len(blessings.read(f).records), 7)
