# Facilities and access conditions — Test 1

This feature branch adds two related parts of the roadmap: facility
locking/unlocking and an explanation of the unresolved travel/entry conditions.
It is prepared for player testing, not merged into main or game-accepted.

## Controls

The **Facilities** tab has **Services and gates** and **Access conditions**
views. Flags remains the rightmost tab; slightly tighter tab spacing keeps it
visible at the existing minimum window width.

Services and gates contains **27 switches**: 20 service switches and seven
Gate of the Gods registrations. Select individual rows or a range, then
Enable selected or Disable selected. Search accepts English, Japanese or a
hash; the category filter separates services from gate registrations.
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
The two shop restrictions have accepted removal/unlock evidence from the B0
repair; Kalla has accepted registration evidence. The new UI and reverse
operations need testing. The other 24 switches are Inferred. Original Japanese
keys remain in Reads As and newly established English names appear in Flags.

No automatic all-facilities preset is applied. Stables stays unchanged unless
the player explicitly selects it; none of the supplied game-test saves change
it. Its destination and service switch are separate. These controls do not
change mounts, inventories, shop stock/prices, Renown, quests, Deeds, Boons,
units or story progression. The test baseline retains Weapons Discount 10%.

## Flag semantics and structural boundary

`facility_names.json` holds exact names, hashes, polarity and evidence.
`facilities.py` locates a unique general flag map inside a struct group directly
under GameUserData. At least two unchanged journal/free-time/map-permission
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

The seven gate switches live in this general map. They are independent of the
ordinary temple destinations in the existing Fast travel tab. Kalla's gate is
`3fdd2f30 / 神殿_転移_カーラ神殿`; ordinary Kalla travel is `b482d5dc`.
Registering other gates does not claim that their approach, menu, arrival or
story event is available on this route.

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
[the preparation report](test-results-facilities-test1.md).
