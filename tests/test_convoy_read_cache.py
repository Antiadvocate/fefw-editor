"""Convoy refresh may reuse the validated save, never stale rows or offsets."""
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import fefw_core as core
import fefw_layer as layer
from editor_advanced import AdvancedMixin
from test_story import fixture


def convoy_fixture():
    f = fixture()
    p = bytearray(f.payload[:f.ptr(0)])
    at = len(p)
    p.extend(bytes(4) + b'\x01\x03\x00' + struct.pack('<HB I HH', 7, 65, 0x12345678, 0, 0))
    p.extend(bytes(-len(p) % 4))
    struct.pack_into('<I', p, at, len(p) + 32)
    table = len(p)
    for key, start in [(b.hash, b.start) for b in f.blocks] + [(core.fnv1_32(b'Transporter'), at)]:
        p.extend(struct.pack('<II', key, start + 32))
    struct.pack_into('<I', p, 0, ((len(f.blocks) + 1) << 24) | (table + 32))
    return core.SaveFile(p)


def contents(convoy):
    return (convoy.header, convoy.end, convoy.slots,
            [tuple(getattr(row, name) for name in row.__slots__) for row in convoy.rows])


class ConvoyReadCacheTest(unittest.TestCase):
    def test_repeated_read_reuses_tree_but_returns_independent_rows(self):
        f = convoy_fixture()
        expected = layer.live_convoy(bytes(f.payload))
        f.tree()
        with patch.object(core.SaveTree, 'read', side_effect=AssertionError('reparsed')):
            first = layer.live_convoy(f)
            self.assertEqual(contents(first), contents(expected))
            first.rows[0].qty = 999
            self.assertEqual(contents(layer.live_convoy(f)), contents(expected))
        self.assertEqual(f.payload, convoy_fixture().payload)

    def test_editor_cache_tracks_quantity_edits_resize_and_undo(self):
        original = convoy_fixture()
        app = SimpleNamespace(sv=SimpleNamespace(path='synthetic', payload=bytearray(original.payload)))
        read = lambda: layer.live_convoy(AdvancedMixin.core_of(app))
        first = read()
        struct.pack_into('<H', app.sv.payload, first.rows[0].qty_off, 9)
        self.assertEqual(read().rows[0].qty, 9)
        f = AdvancedMixin.core_of(app)
        slots = core.convoy_read(f, core.convoy_at(f))
        slots[1] = core.Slot(3, core.Item(0x87654321, b''))
        app.sv.payload = core.convoy_write(f, core.convoy_at(f), slots)
        resized = read()
        self.assertEqual(resized.rows[1].iid, 0x87654321)
        self.assertEqual(contents(resized), contents(layer.live_convoy(bytes(app.sv.payload))))
        app.sv.payload = bytearray(original.payload)
        self.assertEqual(contents(read()), contents(first))

    def test_direct_decoded_edits_revalidate_and_missing_convoy_is_unchanged(self):
        f = convoy_fixture()
        first = layer.live_convoy(f)
        struct.pack_into('<H', f.payload, first.rows[0].qty_off, 15)
        self.assertEqual(layer.live_convoy(f).rows[0].qty, 15)
        self.assertIsNone(layer.live_convoy(fixture()))
        self.assertIsNone(layer.live_convoy(bytes(fixture().payload)))
