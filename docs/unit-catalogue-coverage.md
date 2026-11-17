# Catalogue coverage audit

**Update:** Anna's dismounted-only profile is now enabled after the A1 pass.
The picker has 55 enabled and 12 restricted identities. She cannot remount.
The original Test 2 audit snapshot below retains its earlier counts/lists.

Audited 2923 Person rows from the supplied game tables.
The current catalogue has 54 enabled and 13 restricted identities.
All 55 rows with source flag byte 39 are accounted for:
54 enabled plus Eshmel, the restricted custom protagonist. This is exhaustive
for that data pattern, NOT a verified list of everyone naturally recruitable.

The earlier generator checks serials 1–99 and the presence of a generated
Recruited label. build_flag_names.py synthesizes recruitment/met keys from
unit_ids.json, so such a label is not independent recruitment evidence.
Six positive serials 100–105 are omitted: Jurah, Mars, Smyrnos, Credna, Kalla,
Aurora. They have different flags and missing single starting classes; this
does not establish that they are missing normal recruits. Castor and Long
have usable class/HP data but serial zero. Many other named rows have no
combat defaults at all. No NPC was deleted from the game or broad identity
dictionary: these rows were excluded from the Add unit picker.

To establish complete normal-recruit coverage, trace actual recruitment
events/conditions across routes and parts, canonicalize scenario variants,
compare naturally recruited saves, and validate each missing identity's
creation/deployment/persistence and later recruitment behavior. Do not expand
the normal list simply because a character has a name or recruitment label.
Custom Eshmel also needs appearance/avatar initialization research.

## Enabled ordinary-pattern candidates

Cai, Tialla, Peter, Ultand, Bertrand, Gaitz, Maxim, Goliath, Dante, Dietrich, Fabio, Esmeralda, Mikaela, Orchel, Diego, Loretta, Seteth, Ninae, Theodora, Bonaventure, Tobias, Lilian, Lysander, Talimun, Ursula, Ludia, Simon, Fianna, Leda, Buccar, Sirocco, Olympia, Mu, Anatolia, Nezha, Sha Lan, Dadao, Halvin, Guzran, Yang Jie, Io, Peppe, Noctula, Sofia, Catania, Nydine, Zarcone, Majide, Benditz, Inyoni, Jasmine, Alexandra, Nuzzuo, Kiroc.

## Restricted identities already in the picker

Eshmel, Hong Hua, Troy, Centurio, Aswan, Cleobulus, Myson, Nathan, Creek, Anna, Gladius, Klapka, Tahonia.

## Other base identities to browse

This list includes named NPCs, placeholders and creatures; names from partial
matches retain that evidence label. It is not a recruit list. Every one of the
2,923 source rows, including generic/scenario variants, is in the CSV/JSON.
Blank class or zero HP means further defaults are needed, not proof the actor
can never be playable. Names with a source flag other than 39 are unclassified
for natural recruitment until stronger evidence is available.

| Name | Name evidence | Serial | Source flags | Starting class | HP |
|---|---|---:|---:|---|---:|
| Sothis | exact | 0 | 32 | Not set | 0 |
| Fortuna | exact | 0 | 32 | Not set | 0 |
| Yu Phas | part | 0 | 32 | Not set | 0 |
| Dagda | exact | 0 | 32 | Not set | 30 |
| Balor | exact | 0 | 32 | Not set | 0 |
| Lyrah | exact | 0 | 32 | Not set | 28 |
| Eishet | exact | 0 | 32 | Not set | 27 |
| Mahna | exact | 0 | 32 | Not set | 28 |
| Solel | exact | 0 | 32 | Not set | 0 |
| Jurah | exact | 100 | 57 | Not set | 23 |
| Mars | exact | 101 | 57 | Not set | 30 |
| Smyrnos | exact | 102 | 57 | Not set | 28 |
| Credna | exact | 103 | 57 | Not set | 25 |
| Kalla | exact | 104 | 57 | Not set | 25 |
| Aurora | exact | 105 | 57 | Not set | 23 |
| Castor | exact | 0 | 32 | Guardian | 25 |
| Nomved | exact | 0 | 32 | Not set | 24 |
| Oktar | exact | 0 | 32 | Not set | 30 |
| Long | exact | 0 | 32 | Pugilist | 24 |
| Churness | exact | 0 | 32 | Not set | 26 |
| Chiara | exact | 0 | 32 | Not set | 24 |
| Shenlo | exact | 0 | 32 | Not set | 24 |
| Baozi | exact | 0 | 32 | Not set | 26 |
| Yanjin | exact | 0 | 32 | Not set | 23 |
| Gilchris | exact | 0 | 32 | Not set | 29 |
| Randa | exact | 0 | 32 | Not set | 27 |
| Tsuze | exact | 0 | 32 | Not set | 23 |
| Zenon | exact | 0 | 32 | Not set | 27 |
| Suarez | exact | 0 | 32 | Not set | 24 |
| Zenzele | exact | 0 | 32 | Not set | 25 |
| Harrison | exact | 0 | 32 | Not set | 28 |
| Gervasio | exact | 0 | 32 | Not set | 23 |
| Karle | exact | 0 | 32 | Not set | 23 |
| Buspha | exact | 0 | 32 | Not set | 24 |
| Dyan | exact | 0 | 32 | Not set | 24 |
| Huver | exact | 0 | 32 | Not set | 29 |
| Bahr Vahn | part | 0 | 32 | Not set | 29 |
| Bjor | exact | 0 | 32 | Not set | 26 |
| Balboa | exact | 0 | 32 | Not set | 28 |
| Lechner | exact | 0 | 32 | Not set | 26 |
| Mandalan | exact | 0 | 32 | Not set | 26 |
| Aragonian Citizen | prefix | 0 | 32 | Not set | 26 |
| Hanno | exact | 0 | 32 | Not set | 26 |
| Lind | exact | 0 | 32 | Not set | 25 |
| Vandahl | exact | 0 | 32 | Not set | 26 |
| Ianuarius | exact | 0 | 32 | Not set | 0 |
| Vinicius | exact | 0 | 32 | Not set | 0 |
| Breza | exact | 0 | 32 | Not set | 0 |
| Guillermo | exact | 0 | 32 | Not set | 24 |
| Drake | exact | 0 | 32 | Not set | 0 |
| Jarcham | exact | 0 | 32 | Not set | 30 |
| Cohen | exact | 0 | 32 | Not set | 0 |
| Mahadu | exact | 0 | 32 | Not set | 0 |
| Llewellyn | exact | 0 | 32 | Not set | 0 |
| Nero | exact | 0 | 0 | Not set | 0 |
| Whill | exact | 0 | 0 | Not set | 0 |
| Tarek | exact | 0 | 0 | Not set | 0 |
| Redears | exact | 0 | 0 | Sea Beast | 0 |
| Idi | exact | 0 | 0 | Not set | 0 |
| Adebayor | exact | 0 | 0 | Not set | 0 |
| Canute | exact | 0 | 0 | Not set | 0 |
| Altrus | exact | 0 | 0 | Not set | 0 |
| Zakuani | exact | 0 | 0 | Not set | 0 |
| Morrow | exact | 0 | 32 | Not set | 0 |
| Poloni | exact | 0 | 32 | Not set | 0 |
| Gabriel | exact | 0 | 32 | Not set | 0 |
| Hasdrubal | exact | 0 | 32 | Not set | 0 |
| Kumos | part | 0 | 32 | Not set | 0 |
| Nasshim | exact | 0 | 32 | Not set | 0 |
| Orpheus | exact | 0 | 32 | Not set | 0 |
| Hedda | exact | 0 | 32 | Not set | 0 |
| Gephma | exact | 0 | 32 | Not set | 0 |
| Ozin | exact | 0 | 32 | Not set | 0 |
| Jiang | exact | 0 | 32 | Not set | 0 |
| Katarina | unclassified | 0 | 32 | Not set | 0 |
| Hannibal | exact | 0 | 32 | Not set | 0 |
| Tsiskaridze | exact | 0 | 32 | Not set | 0 |
| Sanba | exact | 0 | 32 | Not set | 0 |
| Kubaja | exact | 0 | 32 | Not set | 0 |
| Tandor | exact | 0 | 32 | Not set | 0 |
| Roxana | exact | 0 | 32 | Not set | 0 |
| Karina | exact | 0 | 32 | Not set | 0 |
| Leilidahna | exact | 0 | 0 | Not set | 0 |
| Gyatal | exact | 0 | 0 | Light Cavalry | 0 |
| Blight Louse | part | 0 | 0 | Blight Louse | 0 |
| Blight Louse | part | 0 | 0 | Blight Louse | 0 |
| Blight Louse | part | 0 | 0 | Blight Louse | 0 |
| Blight Louse | part | 0 | 0 | Blight Louse | 0 |
| Balor's Shade | exact | 0 | 0 | Not set | 0 |
| Striped Wolf | exact | 0 | 0 | Striped Wolf | 0 |
| Digamma | exact | 0 | 0 | Digamma | 0 |
| Atlas Bear | exact | 0 | 0 | Atlas Bear | 0 |
| Sea Beast | exact | 0 | 0 | Sea Beast | 0 |
| Giant | exact | 0 | 0 | Giant | 0 |
| Golem | exact | 0 | 0 | Golem | 0 |
| Underworld Pillar | exact | 0 | 0 | Underworld Pillar | 0 |
| Cetus | exact | 0 | 0 | Cetus | 0 |
