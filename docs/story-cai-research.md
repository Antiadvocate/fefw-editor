# Cai Part 1 — native evidence and progression tests

**Update, 2026-11-17:** Cai Chapters 1–12 passed the player's opening/progression
checks, including direct Chapter 4 with the Sewers fix. See [Test 5 results](test-results-cai-tutorials-test5.md).
The dated investigations below retain their original scope and findings.

The user supplied native `Auto`, `Chapter_Kai_1_1` and `Chapter_Kai_1_2` on
2026-11-16. The uploaded Auto is named `Auto(3)`; the suffix is an upload name,
not the game filename. All three container and payload checksums validate.
They establish sufficient structural evidence to offer **Chapters 2, 4 and 9**
as **Inferred** initial targets. The initial implementation was followed by
[Test 1 results](test-results-story-cai-test1.md): Chapters 2/9 passed, Chapter 4
opened but progression was blocked. Those initial results are retained below;
[Test 2](test-results-functions-cai-test2.md) restored Journal access but all
four combinations still failed to advance Chapter 4.
[Test 3](test-results-story-cai-test3.md) passed Chapter 3 and reached Chapter 4
naturally, but its objective remained blocked. The screenshot then identified
a Sewers entrance requiring a missing Chapter 2 dialogue-read record; a
[one-record test](testing-cai-sewers.md) subsequently passed. The
[production integration](test-results-sewers-functions.md) exposes the prerequisite
in Functions and applies it to Cai Chapter 3+ selections. The initial evidence below
is retained for provenance.

## Native save evidence

| Capture | Route / part / chapter | Clock | Sequence | Resume context |
|---|---|---|---|---|
| Auto | Cai / 1 / 2 | 1449-02-03 12:00 | `d642b68c21a0fab0` | Free time: `12 05`, `d8588d186b3f9502` |
| Chapter_Kai_1_1 | Cai / 1 / 1 | 1449-01-24 02:00 | `1c39b1f1e90b1ef6` | Chapter entry: `10 0b`, `a2f3e9a7ff461708` |
| Chapter_Kai_1_2 | Cai / 1 / 2 | 1449-01-25 11:00 | `1c36b1f1e908e8c1` | Chapter entry: `10 0b`, `a2f3e9a7ff461708` |

Both natural checkpoint sequences independently reverse the FNV-1 suffix
`<chapter>_1` to the same prefix state **`eab884585a706f5d`**. Leda's prefix is
`fde8dadc5dfc1118`; these are distinct. The full symbolic key is still unrecovered.
The free-time Auto sequence is a live story beat, not a checkpoint suffix anchor.

The live Header and GameUserData agree with the outer route/part summary.
GameUserData v23, the direct sequence child, schedule/calendar and all eight
restart members validate using the shared structure. The native Chapter 2 clock
agrees with its title row. The supplied Auto and Chapter 2 checkpoint contain
three units with distinct numbers 4, 6 and 7. Chapter 1's natural checkpoint has
no populated units yet; using it as an edit source would not grant a later party.

Test generation uses the supplied **Auto**, with Gold 1,500, Renown 350 and
Karma 430. Each output preserves its three units, all flag maps, funds and every
unrelated normalized root. The source and natural checkpoints remain unchanged.

## Runtime scope

The editor reads the route from the save; there is no route-conversion control.
Cai offers 1–12. Chapters 1, 5–8 and 10–12 are Inferred targets for
[the next test kit](testing-cai-tutorials-test5.md). Chapters 2/3/9 are Game-tested; Chapter 4 has a conditional
pass after fixing Sewers on a natural Chapter 3 return. Direct entry with this
fix remains untested. Leda retains its accepted 2–12 targets and
Chapter 1 exclusion. Other routes/parts and unsupported contexts stay read-only. Cai Chapter 1
uses its captured 1449-01-24 02:00 clock; the later dates below are shared with
the production selector.

The shared entry engine selects the route-specific ID/date, sets the known
chapter-start context, clears old schedule/calendar/restart state, and retains
current progression. The game is expected to establish the scene from that
entry. Cai Chapter 3+ selections now enable the one tested Sewers dialogue
prerequisite. Other prior units, facilities, quests and unlocks remain unchanged.

An optional chapter-file request is bound to **both route and chapter**. Cai
writes `Chapter_Kai_1_N`, never `Chapter_Led_1_N`. All writes wait for Save;
existing targets require confirmation and a preserved `.bak` or numbered backup.
Undo/Redo includes the request; completed external writes are not replayed by
history. Route changes during a warning/picker require reopening the dialog.
Cai chapter-file serialization is checked, but Obelisk use remains untested.

## Primary timeline data

`Timeline_Part1_Kai.bin` contains exactly twelve chapter-title rows. The title
rows inherit year (0); the native checkpoints establish 1449. Chapter 1 inherits
its whole title date, now observed in the native checkpoint above.

| Chapter | Title-row month/day/time | Offered in first build |
|---|---|---|
| 1 | Inherited | No; separate testing deferred |
| 2 | 01-25 11:00 | Yes; accepted in Test 1 |
| 3 | 02-04 08:00 | No |
| 4 | 03-01 12:00 | Yes; blocked / Inferred |
| 5 | 03-14 12:00 | No |
| 6 | 04-19 10:00 | No |
| 7 | 06-09 12:00 | No |
| 8 | 07-10 12:00 | No |
| 9 | 09-03 12:00 | Yes; accepted in Test 1 |
| 10 | 09-15 12:00 | No |
| 11 | 10-16 08:00 | No |
| 12 | 11-03 12:00 | No |

Source SHA-256: `9d355336bff4a1d21a0a154f2d3fe3daeadf682dcc8c497f89a0f27c6fbeb819`.
Reproduce with `python research/story_timeline_report.py /path/to/GameData --route cai`.
The unrecovered type-84 action precedes Chapters 2–12, but does not prove a file
creation trigger. No GameData is committed or required at runtime.

## Route_Kai and the Obelisk Chamber

The earlier working Cai folder did not contain Route_Kai. The player has now
observed that entering the Obelisk Chamber creates the route's Route_* file
by copying the most recent Auto **before** a new Auto is written. On leaving
the chamber, Route_Ism is created for the main character. This is a player
observation, replacing the earlier speculative route-switch trigger.

The supplied Dietrich/Theodora archives contain no Route-file before/after
pairs, so the copy has not been byte-compared in this update. See the
[reference report](route-reference-saves.md#player-observed-route-file-lifecycle).
Auto and native Chapter files remain sufficient for the current editor;
Route files are not synthesized. This finding is separate from the still
unconfirmed natural Chapter-file creation trigger.

## Reproduction and limits

`research/story_cai_probes.py` requires the exact native Auto fingerprint and a
fresh output directory. It generates three independent Auto files plus an
unchanged control, using the actual editor engine and serializer. It never writes
over the input or copies the Leda baseline into Cai. Tests use synthetic public
fixtures plus optional native captures via `FEFW_CAI_SOURCE_DIR`; private saves
are not committed to Git. Initial tests do not establish the remaining Cai
chapters or long-term progression.
