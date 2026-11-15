# Fast travel: destination availability

The **Fast travel** tab edits 20 identified Dagsion destination flags in the
selected save: the original 16 plus four experimental early-access candidates. Milestone 3's [numbered acceptance tests](testing-fast-travel.md)
passed on the reported Leda Part I Chapter 9 / `fefw-recomp-0.1.5` setup.
Port, Kalla's Temple and Stables were tested for removal, restoration, travel
and persistence. The full destination list and all English names were confirmed
with player screenshots; the other 13 original destinations have not each had isolated
in-game add/remove tests. See the [validation report](test-results-fast-travel-2026-11-15.md).

## Using the page

1. Close the game and open a copied save using **Open…** in the top action bar.
   Select a slot file, such as `Auto`; the editor loads its folder and selects
   that slot. Ctrl+O still opens the same chooser. Unsaved edits trigger the
   existing save/discard/cancel prompt.
2. Turn off **Also edit this route's other saves**. Select **Fast travel**.
3. Search by English label, original Japanese key or eight-digit hash. Ctrl+F
   focuses search. Select one or more rows, then **Make available** or
   **Remove selected**. The controls change memory; **Save** / Ctrl+S writes it.
4. Ctrl+Z and Ctrl+Y undo/redo. **Reload** reads the saved state again.

**Available (1)** means the stored flag is present with value 1. **Absent**
means the record is missing, not value zero. Other values display as
**Unknown (value); preserved** and cannot be changed by this page. The summary
counts all known destinations, including rows hidden by search.

The original 16 English labels match the **in-game Base Map menu**, confirmed in the player's
2026-11-15 screenshots. Test 1 used provisional translations; the report records
the eight corrections, including Harbor → Port and Slums → Lowtown.
The same labels appear in **Flags**, prefixed by `Fast travel:`; experimental
ones also carry an experimental suffix.
**Reads as** retains the full original key. A hash is the stable identity.

## Catalogue

Every key below has the exact prefix `拠点_FT_Hub_000_`. Append the suffix
without spaces. `fast_travel_names.json` stores the complete keys, labels and
evidence notes; `catalog()` verifies each identity against its hash.

| In-game English label | Hash | Exact key suffix |
|---|---|---|
| Arena Plaza | `5a48ce35` | `A1_ファストトラベル_闘技場前` |
| Shopping Arcade | `bb86129f` | `A1_ファストトラベル_商店街` |
| City Streets | `ad2b97e0` | `A1_ファストトラベル_商業区画` |
| Upper Temple Row | `387f1e5a` | `A1_ファストトラベル_上参道` |
| Lower Temple Row | `9b4262d7` | `A1_ファストトラベル_下参道` |
| Entertainment District | `90d7a0f8` | `A1_ファストトラベル_富裕区画` |
| Jurah's Temple | `2c475b48` | `A110_ファストトラベル_ジュラ神殿` |
| Mars's Temple | `2d2ded41` | `A120_ファストトラベル_マーズ神殿` |
| Smyrnos's Temple | `547cf68b` | `A130_ファストトラベル_スミルノス神殿` |
| Credna's Temple | `16f93ab4` | `A161_ファストトラベル_クレール神殿` |
| Kalla's Temple | `b482d5dc` | `A150_ファストトラベル_カーラ神殿` |
| Aurora's Temple | `00fe96da` | `A102_ファストトラベル_アウロラ神殿` |
| Stables | `2478dd30` | `A1_ファストトラベル_厩舎前` |
| Port | `1b5a4006` | `A1_ファストトラベル_港` |
| Lowtown | `e86370a7` | `A1_ファストトラベル_貧民街` |
| Tavern | `c1c872f8` | `A70_ファストトラベル_酒場` |

## Four experimental additions (Polish Test 1)

These exact scoped keys occur in `GameData/Timeline_Com.bin`; corresponding
names and locators are in Hub/HubDispos data. All four are absent from the
private FT-04 save. **English names are provisional translations, and early
access is untested.** They may be subject to chapter, route or scene conditions.
The Coverage column distinguishes them from the original confirmed list.
Test them one per copied save using [FTX-01–04](testing-polish.md), without
changing first-audience or chapter flags at the same time.

Use the same `拠点_FT_Hub_000_` prefix for each suffix below.

| Provisional label | Hash | Exact suffix |
|---|---|---|
| Aurora's private room | `38574e83` | `A100_ファストトラベル_アウロラの私室` |
| Aurora's garden | `1e4d4a23` | `A101_ファストトラベル_アウロラの庭園` |
| Salamis Guesthouse | `efb57d93` | `A9_ファストトラベル_サラミス迎賓館` |
| Yu-Fas Temple | `65411bed` | `A141_ファストトラベル_ユ・ファス神殿` |

## Format and locator

These are hashed-key records in a `GameUserData` flag map. Their key is the
low 32 bits of FNV-1 64 applied to the full UTF-8 name, via `core.id_hash`.
An earlier unsuccessful attempt used unscoped names such as
`ファストトラベル_厩舎前` in another namespace. Those are different identities
and must not be substituted.

The successful reference's list happened to be enumerated as map 3. Enumeration
and absolute offsets are not stable. `fast_travel.locate()` instead requires:

* Exactly one `GameUserData` block and one candidate map containing known keys.
* At least three distinct original destination keys and no duplicate keys.
  Experimental additions do not count toward these identifying anchors.
* A non-struct map node with no child objects, inside a struct group whose
  parent is the live `GameUserData` node. Embedded or unexpected layouts fail.

The format uses an end pointer, version byte 0, u16 count, then records:
u32 hash followed by a one-byte value, or `ff` plus a signed i32. Newly added
available records use a one-byte 1. Removal deletes the record and reduces the
count. Existing records, including wider encodings, retain their exact bytes
and order. New records append to the list. Restoring a removed record therefore
restores its meaning but is not promised to restore its original byte position.

`core.replace_content()` handles alignment and pointer relocation; container
serialization updates checksums. Unknown records remain untouched. The B0
reference has the original 16 flags at 1, four experimental flags absent, and
14 other list records. Thirteen other records match support-conversation keys;
one remains unidentified. They are not a catalogue of 14 more destinations.
The edit is validated as a whole before it changes memory. No-op requests
are byte-identical and create no undo entry. Invalid or unknown-state requests
reject the entire batch. At least three original keys must remain, to preserve
reliable future identification. Sparse or ambiguous saves are read-only here;
the page does not invent identifying entries or guess a map.

## Boundaries

This page does not change world-map visibility/visited bytes, gates, story,
quests, tutorials, blessing EXP/selection/Sand, Karma Shards or facility flags.
The **Stables destination is separate from the stable facility**. In the
reference the destination exists while `機能開放_厩舎` remains absent. Neither
adding the destination nor changing its English label grants facility access.

An available flag does not override travel restrictions imposed by the current
scene or story. Visiting a location may let the game discover it again; isolate
removal tests from travel through that area. Other routes, hubs, sparse early
saves and game versions have not been established. Raw Flags remains an
advanced interface with broader abilities; this page's guarantees apply to its
own controls. There is no unlock-everything preset.

See [the validation report](test-results-fast-travel-2026-11-15.md) for the
distinction between automated preservation checks and the scope of game testing.
