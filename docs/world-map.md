# World map data (`GmapSpotMgr`)

How the save stores the world map, as far as it has been established. The
layout and the meaning of the first two bytes come from
[@Destorino5's notes in #27](https://github.com/Antiadvocate/fefw-editor/issues/27);
the editor's own saves were used to re-check them. Offsets below are into the
**decoded** payload (`fefw_core.unpack`), never the file on disk.

## The block

`GmapSpotMgr` is a dictionary: for every map point a `u32` key followed by a
small object. Find the block with `SaveFile.block("GmapSpotMgr")`, read the
payload with `SaveTree`, and take the block node's **direct children**, in order.

| Position | Meaning |
|---|---|
| `node.start - 4` | the point's key (`node.start - 5` for the first child, which is followed by one pad byte) |
| `node.start + 0` | end pointer — leave alone |
| `node.start + 4` | state: `1` hidden, `3` shown, `2` seen on some road points (not understood) |
| `node.start + 5` | secondary byte: `0` or `3` in every save looked at; meaning unknown, preserved |
| `node.start + 6` | visited: `0` dark icon, `1` white icon (a single `3` exists on one fort) |
| rest | type-specific tail, preserved |

Records are 12 bytes, except 23 of kind 6 (40 bytes) and 27 of kind 10 (32
bytes) which carry a nested tail. A record cannot be recognised by its size.
The editor writes only `+4` and `+6`, in place, so nothing is resized.

## Keys

`key = low32(fnv1_64(name))` over the internal Japanese name in UTF-8 —
`fefw_core.id_hash(name)`. It is FNV-1 (multiply, then xor), 64-bit, truncated;
not FNV-1a and not 32-bit. `帝都ダグシオン` → `621a6fd3`.

## Where the names come from

`GameData/Gmap/Data.bin` (83,680 bytes in the tested build):

* 864 point records at byte 7, 17 bytes each: `u32` name offset, `u8` kind,
  `f32` x, `f32` y, `u32` (unknown). They are in the same order as the save's
  children, and their hashes are exactly the save's 864 keys.
* 717 road chains from byte 14693: `u16 n`, `n × u32` name offsets,
  `u16 n-1` + midpoint floats, `u16 2(n-1)` + curve floats. Each chain is the
  ordered list of points a road is drawn through (`n >= 2`, ends included). The
  table ends exactly where the string pool begins.
* Strings: `u16` byte length + UTF-8, addressed by file offset.

Kinds seen: 0 major city, 1 town, 2 temple, 3 station, 4 gate/fortress,
5 landmark, 6 and 10 field/pass, 7 shrine/monument, 9 cave/mine (labels read
off the names), 11 waypoint (`中スポットNNN`), 12 junction (`分岐点NNN` and the
regional variants), 13 road point (`<from>_<to>_<n>`).

`build_map_spots.py` checks each of these invariants and stops on a build that
breaks one; it writes `map_spots.json`, which is all the editor needs at run
time. English names are the game's own (`Msg/EUen/Spot.msbt.zst`), matched to
the map spelling by label; junctions and road points are named from the parts
of their internal name.

## What a visible point does and doesn't mean

* A road is drawn through its own points, so restoring one needs the places and
  junctions at its ends as well as the intermediate points (the six-byte
  experiment in #27: `アクシオン渓谷`, `アクシオン渓谷_分岐点620_1`,
  `アクシオン渓谷_分岐点620_2` to shown restores the route to Faun's Forest).
  Hiding a junction hides every road through it, so the editor's *Hide road*
  touches only the points named after that road.
* Visible is not unlocked: gates, battle completion, rewards, quests and base
  fast travel are separate conditions elsewhere in the save.
* Unresolved: state `2` (62 road points in a mid-game save), the secondary
  byte, and the tails of the longer records. A global "unlock everything" was
  not enough to rebuild a faithful map in #27, which is why the page also
  works per point and per road.
