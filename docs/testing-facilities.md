# Facilities Test 1 — player test sequence

The private test kit contains the editor, this guide and **13 ready-made Auto
files** in numbered folders. `00-Control` is an untouched copy of the accepted
B0-01 baseline. Each pair starts from that baseline and changes only the named
switches. These are disposable tests, not replacement baseline saves. Stables
is locked in every supplied case. Route/part/chapter, units, currency, Boons
and Deeds are preserved. The earlier Weapons Discount 10% remains purchased/On.

## Start

Extract the kit into a fresh folder and run `editor/editor.py` with the normal
Python setup. No new dependencies. Keep the accepted baseline separately.
Install **one** numbered folder's `Auto` at a time using the usual save workflow,
with the game closed. Do not put all Auto files into the live folder together.
The paired Restored/Removed files are already prepared; editing them is not
necessary to run the game tests. Do not carry unrelated game progress from one
case into the next.

Work through the core tests first. The extra gate and access tests can follow
if time permits. A blocked service is a useful result even if its saved switch
says Enabled: report what the NPC/menu actually does.

## Editor checks

| ID | Action | Expected |
|---|---|---|
| FAC-UI01 | Open 00-Control; inspect Facilities | 27 switches. Stables disabled. Armorer/Item shop enabled. Kalla gate registered; six other gate switches disabled. Flags remains last. |
| FAC-UI02 | Search Certification, `機能開放_資格試験`, then `0be47d8b`; try the category filter | Each search finds Certification exams; Gate registration shows seven entries. |
| FAC-UI03 | On a disposable copy select Armorer and Certification exams together, Disable, Undo, Redo, Enable | Both logical states follow the buttons despite opposite underlying polarity. Other rows stay unchanged. Save/reopen preserves the result; normal numbered backups work. |
| FAC-UI04 | Enable route mirroring and try a facility edit | Edit is refused without changing the save. Turn mirroring off afterward. |
| FAC-UI05 | Open Access conditions; inspect all four rows and Copy diagnostics | Leda P1 Ch9; room/garden require Cai, Salamis requires Theodora; Yu Phas has no locator route filter but separate entrance conditions. No dirty state from inspection/copy. |

## Core game tests

For every pair: load the first file, inspect the named services/listings,
save and reload once, then repeat with its paired restored file. The game can
reapply progression flags; report any state that reverts. Screenshots are most
useful where behavior differs; filenames do not matter if labelled.

| ID | Files | What to check |
|---|---|---|
| FAC-01 | 01-Shops-Disabled → 02-Shops-Restored | Armorer and Item shop unavailable, then usable again. Check both. Stock is not intentionally changed; existing 10% weapon discount should remain. |
| FAC-02 | 03-Exams-Drinks-Perform-Disabled → 04-Exams-Drinks-Perform-Restored | Check the exam proctor, drink vendor, local performances/Perform availability and tavern performances separately. Record menus versus actual interactions; quest status is not edited. |
| FAC-03 | 05-Market-Inn-Smith-Training-Disabled → 06-Market-Inn-Smith-Training-Restored | Check Marketplace, Inn, Blacksmith and Training separately. Record which NPC/menu/action becomes unavailable and comes back. |
| FAC-04 | 07-Kalla-Gate-Removed → 08-Kalla-Gate-Restored | Gate of the Gods Kalla's Temple disappears/reappears in its travel list. Ordinary Kalla's Temple remains. Try restored arrival and a safe exit, then save/reload. |

Return a game-resaved Auto for **both sides of each pair**, labelled with the
folder number. One save per case is enough after the named checks and reload.
If a case fails, stop that case and keep its game-resaved file; the next pair
can still be tested from its independent supplied file.

## Additional gate and access tests

| ID | Files | What to check |
|---|---|---|
| FAC-05 | 09-Other-Gates-Registered → 10-Other-Gates-Removed | Six additional Gate of the Gods registrations are enabled together: Mars, Jurah, Smyrnos, Credna, Aurora, Yu Phas. Record each listing and any arrival/exit attempted. Kalla should stay registered in both. Ordinary temple travel and Stables should stay unchanged. After the Removed file, check the six extra listings again. |
| FAC-06 | 11-Access-Travel-Recorded → 12-Access-Travel-Removed | These change only the four ordinary travel flags from the earlier experiment. On Leda, expect Yu Phas to list/travel as before while room/garden/Salamis stay hidden. Yu Phas walking entry may remain blocked. The Access conditions view explains the route filters. Check removal after loading 12. |

For FAC-05, report each gate separately as listed/not listed, arrival tested/not
tested, exit tested/not tested. A listed gate is not automatically an arrival
pass. For FAC-06, the hidden route-filtered destinations are the expected
comparison, not a failed attempt to unlock them through broad story edits.
Return both game-resaved files for each additional pair you test, plus copied
Access diagnostics if the results differ from the expected route behavior.

Stables, Theatre performances and Thermae are not included in these prebuilt
changes. Other newly exposed switches remain Inferred until separately tested.
No new-route save or all-facilities unlock is needed for this run.

## Result shorthand

`FAC-UI01–05: Pass / detail`

`FAC-01: Armorer ..., Item shop ..., reload ...`

`FAC-02: Exams ..., Drinks ..., Local Perform ..., Tavern Perform ..., reload ...`

`FAC-03: Market ..., Inn ..., Blacksmith ..., Training ..., reload ...`

`FAC-04: Kalla gate remove/restore ..., ordinary temple ..., arrival/exit ..., reload ...`

`FAC-05: Mars ..., Jurah ..., Smyrnos ..., Credna ..., Aurora ..., Yu Phas ...`

`FAC-06: Room ..., Garden ..., Salamis ..., Yu Phas ..., removal ..., reload ...`
