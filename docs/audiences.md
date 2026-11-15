# First audiences: experimental controls

**Polish Test 1** adds a **First audience** column and a selected-god checkbox
to Blessings. The six ordinary gods have exact first-talk conditions in the
game data. Fortuna's condition is empty: she displays **Not required**, and
her checkbox is disabled. There is no invented Fortuna flag.

The player reported **AUD-01–08 passed** on Leda Part I Chapter 9 /
`fefw-recomp-0.1.5`. Supplied Mars Off/On screenshots show his portrait obscured
when Off and visible when On, while Bless Lv remains 1. His four before/after
saves independently confirm audience absence/1 persists and EXP stays 25.
The other five gods have reported passes without individual files/screenshots
in this submission; their precise visible effects are not independently verified.

A recorded audience is not a promise of temple entry, an available conversation,
or a usable blessing in every scene. The game may impose other conditions.
See [acceptance evidence](test-results-polish-2026-11-15.md#player-acceptance-and-supplied-saves)
for a stored-selection change during the Mars Off game session and the limits
of these observations.

## Use

Open a disposable save, turn route mirroring off, and select one god in
Blessings. The checkbox reflects the **stored flag**, not the selected
blessing. Clicking it changes memory immediately; Save / Ctrl+S writes the
change. Ctrl+Z and Ctrl+Y undo/redo. Changing the selected row does not edit it.

* **Recorded (1):** the exact flag is present with value 1; checkbox on.
* **Not recorded:** the flag is absent; checkbox off.
* **Unknown (value); preserved:** the flag has another value; checkbox disabled.
  Zero is not silently treated as absence.
* **Unavailable:** the shared map cannot be reliably identified. Audience
  edits are disabled; validated EXP edits can still work independently.
* **Not required:** Fortuna's condition is empty in the inspected game data.

Turning the control off removes the record. It does not undo a conversation,
cutscene, quest, or other consequence of meeting the god. Turning it on writes
only a one-byte 1. It does not add EXP, alter selection or Divine Sand, or
enable a fast-travel destination. Any changes made by the game after loading
must be recorded separately. Test one god at a time with
[AUD-01–08](testing-polish.md).

## Exact identities

These are **low 32 bits of FNV-1 64** over the full UTF-8 keys. They are not the
full-width MIR record hashes used by the EXP table. The Flags tab shows an
English `First audience:` label and keeps the exact key in Reads as; the
Blessings form shows the same key and flag hash for its selected god.

| God | Exact condition key | Flag hash | Private B0 state |
|---|---|---|---|
| Fortuna | None: empty condition | None | Not required |
| Mars | `共有_行動_初めてマーズと話した` | `db6908aa` | 1 |
| Credna | `共有_行動_初めてクレールと話した` | `19d34a8a` | Absent |
| Kalla | `共有_行動_初めてカーラと話した` | `f1a2fc34` | 1 |
| Jurah | `共有_行動_初めてジュラと話した` | `4af1cfb8` | Absent |
| Smyrnos | `共有_行動_初めてスミルノスと話した` | `067eec7d` | Absent |
| Aurora | `共有_行動_初めてアウロラと話した` | `b8ccf6c9` | Absent |

In the local `Skill.bin` dump, the seven MIR rows start at `0x28a3f8` with
stride 176, key pointer at +8, audience-condition pointer at +48. Ordinary
rows name the six conditions above; Fortuna's pointer is zero. These dump
offsets are research provenance, not save offsets or portable locators. The
source dump and private save are not distributed.

## Shared-map locator and preservation

`audiences.locate()` requires a unique `GameUserData` block and exactly one
candidate map containing audience identities or the unchanged anchors below.
It requires at least two distinct anchors, no duplicate keys, and a leaf map
in a struct group directly under the live `GameUserData` node. Map enumeration
and absolute address are never used. In B0 this happens to be enumerated map 6.

| Unedited anchor key | Hash |
|---|---|
| `方尖塔の間_カメライベント済` | `d9941983` |
| `拠点_経由_方尖塔の間` | `e268cf4c` |
| `共有_実績リスト表示_拠点興行` | `8bf67af4` |
| `共有_実績リスト表示_酒場興行` | `061d7670` |

The independent anchors allow all six audience flags to be absent while the
map stays identifiable. Saves lacking two anchors, including some earlier
chapters, remain read-only for this control. It does not manufacture anchors.
An additional candidate map or an unexpected parent layout also refuses edits.

The object is an end pointer, version byte 0, u16 record count and hashed-key
records. Records store u32 hash then a byte, or `ff` plus signed i32. All
requests are validated before mutation. Unknown states, unknown gods and
Fortuna writes fail atomically. No-ops preserve every byte and add no history.
Untouched records retain bytes/order/encoding, including the existing candidate
boon flag in the same map. New records append; removal/re-add need not preserve
original byte positions or wide encoding for the edited record.

`core.replace_content()` relocates pointers and the container writer refreshes
checksums. Tests compare the rest of the payload after normalizing relocatable
pointers and check the serialized file again. The GUI uses the normal selected
slot undo/cache/save flow and refuses edits with route mirroring enabled.

See [validation](test-results-polish-2026-11-15.md) for automated and player evidence.
Other routes, chapters and game versions remain unverified.
