"""Test 3: compare a checkpoint resume identifier and optional HubSeq removal.

Research only. The exact enum/type meaning is inferred from private captures;
these diagnostics are not enabled in the editor and do not import checkpoints.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story
from research import story_entry_probe as entry

RESUME_OFFSET = 58  # Relative to the GameUserData v23 body, before its first child.
FREE_TIME_ID = 0xd8588d186b3f9502
CHECKPOINT_ID = 0xa2f3e9a7ff461708
CASES = (('ST3-09D-Resume-id', 9, False), ('ST3-09E-No-HubSeq', 9, True),
         ('ST3-04D-Resume-id', 4, False), ('ST3-04E-No-HubSeq', 4, True))


def resume_id(f):
    info = story.require_leda(f)
    return struct.unpack_from('<Q', f.payload, info.user + RESUME_OFFSET)[0]


def without_hub_seq(f):
    """Rebuild only the root membership; preserve every retained object."""
    tree = core.SaveTree(f.payload)
    root = tree.nodes[0]
    table = f.ptr(0)
    count = f.u32(0) >> 24
    if not root.struct or table + count * 8 != len(f.payload):
        raise core.SaveError('Unknown root table layout')
    rows = [(f.u32(table + 8*i), f.ptr(table + 8*i + 4)) for i in range(count)]
    hub_key = core.fnv1_32(b'HubSeq')
    hits = [at for key, at in rows if key == hub_key]
    if (len(hits) != 1 or len({k for k, _ in rows}) != count
            or len({at for _, at in rows}) != count
            or {at for _, at in rows} != {n.start for n in tree.nodes if n.parent == 0}):
        raise core.SaveError('Unknown or duplicate root members')
    hub = hits[0]
    hn = tree.node_at(hub)
    if tree.copy_object(hn, 0) != struct.pack('<I', 40) + bytes(4):
        raise core.SaveError('Only the observed empty HubSeq object may be removed')
    # The known root is a table of contiguous child objects without scalar data.
    cursor = 4
    for at in sorted(at for _, at in rows):
        n = tree.nodes[tree.node_at(at)]
        if at != cursor:
            raise core.SaveError('Unexpected root padding or unowned content')
        cursor = n.end
    if cursor != table:
        raise core.SaveError('Unexpected root tail content')
    result = bytearray(4)
    relocated = {}
    for at in sorted(at for key, at in rows if key != hub_key):
        relocated[at] = len(result)
        result.extend(tree.copy_object(tree.node_at(at), len(result)))
    new_table = len(result)
    for key, at in rows:
        if key != hub_key:
            result.extend(struct.pack('<II', key, relocated[at] + 32))
    struct.pack_into('<I', result, 0, ((count - 1) << 24) | (new_table + 32))
    check = core.SaveFile(result)
    before = entry.normalized_blocks(f)
    del before['HubSeq']
    if before != entry.normalized_blocks(check):
        raise core.SaveError('A retained object changed when removing HubSeq')
    return result


def edited_profile(f, chapter, remove_hub=False):
    if type(remove_hub) is not bool or chapter not in (4, 9) or type(chapter) is not int:
        raise core.SaveError('Only the Chapter 4/9 resume diagnostics are supported')
    if resume_id(f) != FREE_TIME_ID:
        raise core.SaveError('Expected the observed free-time resume identifier')
    # Anchor to Test 2 C, so D introduces exactly one new scalar edit.
    prior = core.SaveFile(entry.edited_profile(f, chapter, 'C'))
    p = bytearray(prior.payload)
    info = story.require_leda(prior)
    struct.pack_into('<Q', p, info.user + RESUME_OFFSET, CHECKPOINT_ID)
    wanted = entry.normalized_blocks(core.SaveFile(p))
    if remove_hub:
        p = without_hub_seq(core.SaveFile(p))
        del wanted['HubSeq']
    check = core.SaveFile(p)
    if resume_id(check) != CHECKPOINT_ID or entry.normalized_blocks(check) != wanted:
        raise core.SaveError('Resume diagnostic did not preserve its intended boundary')
    # D/E retain every flag map and every other user-data member from C.
    a = entry.normalized_blocks(prior)
    b = entry.normalized_blocks(check)
    user = bytearray(a['GameUserData'])
    struct.pack_into('<Q', user, 4 + RESUME_OFFSET, CHECKPOINT_ID)
    if bytes(user) != b['GameUserData']:
        raise core.SaveError('Unexpected changes to player data or flags')
    return p


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Use a fresh output directory')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry.BASELINE_SHA256:
        raise ValueError('These diagnostics require the unchanged accepted B0-01 baseline')
    box = container.SaveFile(str(source))
    if box.verify():
        raise ValueError('Invalid source checksums')
    original = core.SaveFile(box.payload)
    info = story.require_leda(original)
    story.check_outer(box.raw, info)
    if box.raw[48:57] != bytes(original.payload[info.header+20:info.header+29]):
        raise ValueError('Source outer/live mode or clock disagree')
    ready = []
    for name, chapter, remove in CASES:
        candidate = container.SaveFile(str(source))
        candidate.payload = edited_profile(original, chapter, remove)
        i = story.read(core.SaveFile(candidate.payload))
        summary = bytearray(candidate.raw)
        summary[48:57] = candidate.payload[i.header+20:i.header+29]
        candidate.raw = bytes(summary)
        ready.append((name, chapter, remove, candidate.to_bytes(), bytes(candidate.payload)))
    output.mkdir(parents=True)
    (output/'00-Control').mkdir()
    (output/'00-Control/Auto').write_bytes(raw)
    records = []
    for name, chapter, remove, data, payload in ready:
        folder = output/name
        folder.mkdir()
        path = folder/'Auto'
        path.write_bytes(data)
        reopened = container.SaveFile(str(path))
        assert reopened.verify() == [] and bytes(reopened.payload) == payload
        f = core.SaveFile(reopened.payload)
        assert story.read(f).chapter == chapter and resume_id(f) == CHECKPOINT_ID
        records.append({'case': name, 'chapter': chapter, 'removed_hub_seq': remove,
                        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                        'game_test': 'pending'})
    assert source.read_bytes() == raw
    report = {'source_sha256': entry.BASELINE_SHA256, 'cases': records,
              'scope': 'Research diagnostics; no in-game success claimed'}
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
