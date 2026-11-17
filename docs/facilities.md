# Functions, facilities and access conditions

This feature branch adds two related parts of the roadmap: facility
locking/unlocking and an explanation of the unresolved travel/entry conditions.
FAC-UI01–05 and FAC-01–06 passed on Leda P1 Ch9, with the Yu Phas condition
below. The feature remains on its branch pending a main merge.

## Controls

The **Functions** tab (formerly Facilities) has **Saved switches** and **Access conditions**
views. Flags remains the rightmost tab; slightly tighter tab spacing keeps it
visible at the existing minimum window width.

Saved switches contains **37 switches**: 21 service switches, seven
Gate of the Gods registrations, six Journal switches and three area-access switches. Select individual rows or a range, then
Enable selected or Disable selected. Search accepts English, Japanese or a
hash; the category filter separates services, gates, journal sections and area access.
The selected row explains its evidence. Ctrl+Z/Ctrl+Y and normal saving/backups
apply. Route mirroring must be off.

| Group | Included controls |
|---|---|
| Shops | Armorer, Item shop, Marketplace, Blacksmith, Vandahl Trading Company, Tavern gift vendor |
| Services | Inn, Pale Raven perch, Bulletin boards, Temple service, Training, Certification exams, Feasts, Stables |
| Performances and other activities | Theatre, Theatre performances, Thermae (baths), Local performances (Leda), Tavern performances (Leda), Drink vendor (Leda) |
| Gate registrations | Kalla, Mars, Jurah, Smyrnos, Credna, Aurora, Yu Phas |

**Enabled describes the saved switch, not guaranteed usability.** NPC
placement, route, story, schedule and other conditions can still apply.
Ten tested services and six gates are Game-tested; Yu Phas has a Conditional
pass. The ten original untested services and nine new controls remain Inferred.
Original Japanese keys remain in Reads As and established English names
appear in Flags. See the [acceptance report](test-results-facilities-test1.md).

No automatic all-facilities preset is applied. Stables stays unchanged unless
the player explicitly selects it; none of the supplied game-test saves change
it. Its destination and service switch are separate. These controls do not
change mounts, inventories, shop stock/prices, Renown, quests, Deeds, Boons,
units or story progression. The test baseline retains Weapons Discount 10%.

## Flag semantics and structural boundary

`facility_names.json` holds exact names, hashes, polarity and evidence.
`facilities.py` locates a unique general flag map inside a struct group directly
under GameUserData. At least two unchanged free-time/map-permission
anchors must be present; their hashes are not writable through this page.
Neither map 0 nor any enumerated child index is assumed.

- Armorer and Item shop use inverse `禁止_…` restrictions: Enable removes the
  restriction; Disable stores 1.
- Feature unlocks (`機能開放_…`) and temple-transfer registrations
  (`神殿_転移_…`) use positive switches: Enable stores 1; Disable removes it.
- Variable definitions give default 0. Existing explicit zero is recognized
  as inactive and preserved on a no-op. Absence is not silently rewritten to 0.
- Other values are shown as unknown. A selection containing an unknown value
  is refused atomically; no subset is applied. Duplicate or ambiguous maps,
  sparse maps and unexpected structure are also refused.
- Untargeted raw record encodings, including wide integers, are preserved.
  The structural writer relocates pointers; serialization refreshes embedded
  checksums. No-op edits preserve bytes and create no Undo entry.

Sewers access (Cai) uses the exact dialogue-read identity
`MID_LGV_1KAI_c02_LG11_003_m06` (`7d18367a`), in the separate dialogue-history
member `b631f2c1` of the same anchored flag group. It stores 1 when enabled
and removes only that record when disabled. The map is found structurally,
including when empty; a missing, duplicated or malformed member is read-only.
Mixed general/history selections are validated before either map is changed.
The entrance still requires Cai and an allowed story phase. Unlock and
progression passed on the natural Chapter 4 return; disabling is not game-tested.
Selecting a supported Cai Chapter 3+ automatically enables this one prerequisite.
Chapter 2 and Leda selections preserve its current state. Other switches are
not enabled automatically. See [results](test-results-sewers-functions.md).

The seven gate switches live in the general map. They are independent of the
ordinary temple destinations in the existing Fast travel tab. Kalla's gate is
`3fdd2f30 / 神殿_転移_カーラ神殿`; ordinary Kalla travel is `b482d5dc`.
The six non-Yu Phas gates passed listing, travel and portal checks on Leda
P1 Ch9. **Yu Phas also needs Yu Phas Temple enabled in Fast travel in the tested
setup.** The row and Access conditions report whether both switches are stored.
Neither switch edits the other automatically. Walking entrances and story
events remain separate from the tested portal behavior.

## Why the earlier travel experiments behaved differently

The old four destination flags were correct, but three locators are filtered
by protagonist. `Hub.bin` maps `主人公` to `IsHero`. Typed rows in
`HubDispos/Hub_000.bin` give these conditions:

| Destination / event | Data condition | Consequence for Leda P1 Ch9 |
|---|---|---|
| Aurora's private room travel locator | `主人公 [KAI]` | Does not match Leda |
| Aurora's garden travel locator | `主人公 [KAI]` | Does not match Leda |
| Salamis Guesthouse travel locator | `主人公 [SEO]` | Does not match Leda |
| Yu Phas travel locator | No protagonist filter in this row | Consistent with the accepted arrival/exit test |
| Salamis A1-to-A9 entrance | Theodora plus P1 Ch6/Ch11 action-restriction checks | A destination flag cannot bypass the route condition |
| Yu Phas A1 main entrance | Theodora P1 Ch12/free time or Eshmel rows; separate block rows for Cai/Dietrich/Leda | Consistent with Leda's blocked walking entrance |
| Yu Phas A140 inner entrance | Free-time condition | Separate entrance; not game-tested |

A matching route is necessary for the filtered locator; it is **not** a complete
visibility/access prediction. The current game version and other routes have
not been independently game-tested for these newly identified conditions.
Aurora's room/garden English names and Salamis Guesthouse remain provisional
translations pending a matching-route menu screenshot.

Aurora's A60 walking entrances have separate action-restriction/cauldron-room
conditions and alternate red-line/hidden-name rows. Two A60 door-open flags are
referenced by **Cai-only** door events. They are not universal access toggles.
The editor leaves these story/door conditions read-only; it does not spoof a
route or set broad action-restriction flags to bypass an entrance.

Access conditions shows the four travel flags, route filters and entrance
notes. **Copy diagnostics** includes route/part/chapter and related stored
condition flags, retaining duplicate occurrences and unknown values rather
than declaring them safe. No save is changed by inspecting or copying it.

## Reproduce the data observation

Run `python research/facility_access_report.py /path/to/GameData` against a
personal dump. It discovers typed field definitions and follows string/array
references rather than relying on fixed file offsets. It emits the source
SHA-256, row offsets, group names and condition arguments for the relevant
locators/entrances. No game binary or extracted table is distributed here.
The public regression fixtures are synthetic. The player's baseline and
prebuilt game-test saves are supplied separately from Git.

See [the test sequence](testing-facilities.md) and
[the acceptance report](test-results-facilities-test1.md).

## Journal and area controls (Cai Test 2)

The six journal controls separate its global permission from five section
unlocks. Enabling permission clears `禁止_冒険手帳`; it does not grant sections.
Enable the sections separately. Their labels preserve the Japanese identifiers
in Reads As; translated section names are pending in-game confirmation.

The quest-list flag is no longer an identity anchor. Two of the unchanged
first-free-time/map/travel permissions still identify the general map, so
disabling all journal sections does not disable the controls themselves.

Training and Mentoring (Cai), previously labelled Practice, are separate switches. Dagsion upper/lower permissions
are separately editable; none removes chapter restrictions or registers travel.
Arena has no verified saved switch. Access conditions exposes the distinction
and the relevant activity switch states without making an Arena write.
See [Test 1 evidence](test-results-story-cai-test1.md) and the
[Test 2 guide](testing-functions-cai-test2.md). No automatic grant occurs on a
chapter change. First-free-time manipulation remains confined to named research
probes, never the production switch allowlist.
