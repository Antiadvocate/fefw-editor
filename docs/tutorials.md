# Tutorials and English flag names

## Use

Open a copied save folder and select its **Auto** slot. Turn off **Also edit this
route's other saves**, then open **Tutorials**. Search by English name, Japanese
key or eight-digit hash. Ctrl+F focuses search; Ctrl/Shift selection and Ctrl+A
work like the existing tables.

Select one or more rows and choose **Make available** or **Remove selected**.
Use category, saved-state and name-evidence filters, then **Select shown**
for a batch. Filtering changes only which rows are selected, not save data.
The detail panel explains each label's evidence. The original key and hash
remain available by scrolling horizontally.

Changes stay in memory until Ctrl+S. Ctrl+Z and Ctrl+Y undo and redo the whole
selection. Reopen the save to check the exported result.

The catalogue covers all **218 identities** in the supplied `Tutorial.bin`
and `Tutorial_P0.bin` tables. The 115 earlier labels remain checked; 103 new
English names are **provisional translations**, not confirmed localized titles.
Their availability is awaiting the Cai test run. Absent entries can be added;
unknown records outside this catalogue are counted and preserved. A tutorial describes a feature; adding it does not unlock the
facility, ability, quest or story event it describes.

The **Flags** page also shows these English names with a `Tutorial:` prefix.
**Reads as** retains the exact Japanese internal key. Hashes and keys never
change when a display label changes. Its Tutorials filter selects `TUTO_` keys.
The raw Flags page remains an advanced editor with fewer restrictions.

## States and edit limits

| Display | Stored representation | Guided action |
|---|---|---|
| Absent | No record | Make available inserts value 2 |
| Available (2) | Record with value 2 | Keep or remove |
| Present (1) | Record with value 1 | Preserve, explicitly change to 2, or remove |
| Unknown (value); preserved | Any other stored value, including 0 | Editing that selection is refused |

Value 2 successfully restored visible help entries in the tested Leda Chapter 9
save. Value 1 exists in a working save; its complete semantics have not been
established. The editor does not label either value as “read” or “unread”.
Removal deletes the record; writing zero is not an equivalent operation.

Tutorial edits apply only to the selected slot. Mirroring is refused because
the current undo stack snapshots only that slot. If the list is missing,
ambiguous, duplicated or structurally unexpected, the page refuses to edit it.
In supported flag-group layouts it can clear all identified tutorials and
repopulate an empty list. General free-time anchors or the complete captured
13-member early-checkpoint layout establish the group; tutorial member
`e9bc5b65` identifies the list independently of its contents. A missing or
malformed list is not created. Older layouts recognized only by tutorial
names still require Autosave or at least three anchors.

## Corrected identities

These four entries were checked against the user's screenshots, the game's
tutorial identifiers and a restored save subsequently confirmed in game.

| English name | Original key | Hash | Confirmed Leda reference state |
|---|---|---|---|
| Foresight | `TUTO_戦いの助言` | `08373a0e` | 2, present |
| Drifting Reliquary | `TUTO_方尖塔倉庫` | `2b0739cc` | Absent |
| Third Eye (Cai) | `TUTO_透視` | `f501dfbc` | Absent |
| Obelisk Chamber | `TUTO_塔のアクセス` | `c2a2c517` | 1, preserved |

These reference states are not defaults applied to other players' saves. The
earlier restoration incorrectly treated `透視` as Foresight and `方尖塔倉庫` as
Obelisk Chamber; the corrected catalogue keeps those distinct.

## Storage and preservation

Keys use the low 32 bits of **FNV-1 64** over the UTF-8 internal name. This is
neither FNV-1a nor FNV-1 32. `fefw_core.id_hash()` is the shared implementation.

The tutorial list is one flag map inside the live `GameUserData` block. The
enumerated list number can shift when another map is empty. `locate()` first uses the supported structural member, allowing empty lists.
On older layouts it requires a unique candidate containing Autosave or at least
three identified tutorial keys. It rejects competing tutorial maps, duplicate
hashes, malformed member tables and objects with children. This is conservative recognition, not universal format
support or proof that arbitrary saves are valid.

Relative to the list object's start:

| Offset | Field |
|---|---|
| +0 | Existing four-byte end pointer |
| +4 | List kind byte, preserved |
| +5 | Little-endian unsigned 16-bit record count |
| +7 | Variable-length records |

A record has a little-endian u32 key followed by a one-byte value. `0xff`
introduces a signed 32-bit wide value instead. Existing unselected records,
their order, and their narrow/wide encoding are copied byte for byte. New
records append as narrow value 2. All requested edits are validated before
rebuilding the list once. `core.replace_content()` relocates the object's
pointers; the existing save writer handles compression and checksums.

Only that list's content is intentionally edited. Pointer addresses and
container checksums may also change because the list changes length. Embedded
older states, other slots and unrelated flag records are not targets.

## Catalogue evidence and maintenance

`tutorial_names.json` pairs official English text transcribed from supplied
screenshots with internal keys from the supplied Tutorial/Tutorial_P0 tables.
The full restored list and the three corrections were checked by the player.
This is restoration evidence, not 115 independent controlled unlock tests.
`title_id`, when available, is a cross-reference for future review, not a save
key. Null means no reliable title identifier was recorded.

Do not add translated guesses as confirmed English names. For each new entry,
record its exact key/hash, displayed English title, source and validation
status. `build_flag_names.py` applies this overlay after rebuilding the general
dictionary, so it survives regeneration. Synthetic tests need no game files.
Follow [testing.md](testing.md) before claiming a new build works in game.

## Complete catalogue update

The source tables contain 217 entries plus one `Tutorial_P0` entry.
`research/tutorial_catalog_report.py` checks every group/child identity and
records exact title IDs without copying localized message bodies. An
ideographic space (U+3000) inside the Eshmel tutorial key is preserved exactly.

New labels carry `provisional-translation` evidence, appear as **Provisional
name** in Tutorials, and have a **(provisional)** suffix in Flags. Category
filters group General, Free time, World map, Combat and Route-specific entries
using the source title ID. This categorization does not claim route eligibility.

Make available still writes 2; Remove still deletes the record. Value 1 remains
Present (1), and unknown values remain protected. No unsupported read/unread
semantics have been invented. Bulk actions use the same whole-batch validation,
Undo/Redo, selected-slot isolation and Save handling as individual edits.

Use the [Cai and Tutorials test guide](testing-cai-tutorials-test5.md). Complete
coverage of the supplied metadata is not confirmation that all 218 entries are
visible or useful at every story stage.
