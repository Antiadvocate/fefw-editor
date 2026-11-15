# Milestone 1 validation — 2026-11-15

Base: upstream `2ef2f482a1f5c995783da4d80e909810849e882e`.
Branch: `feature/verified-tutorials`. Source test candidate, not an upstream
release. See the delivery archive's `BUILD.txt` for the exact candidate commit.

## Developer checks

| Check | Result |
|---|---|
| Python compilation of changed modules | PASS |
| Synthetic format and page-controller tests | PASS, 16 cases |
| Opt-in private corrected Leda save regression | PASS, 1 case with four write/read cycles |
| Unknown records, wide encoding, unrelated data and shifted indices | PASS in automated cases |
| Input reference file left untouched | PASS |
| GUI launch and load disposable Auto | PASS, Linux desktop, Python 3.12 |
| Ctrl+F search for Foresight | PASS |
| Remove → Undo → Redo → Make available | PASS, observed states/counts update |
| Ctrl+S export, F5 reload, parsed exported file | PASS; valid checksums, all tutorial values restored |
| GUI export's non-tutorial content, accounting for pointers | PASS, no differing bytes |
| Japanese glyph rendering in this test desktop | LIMITED: keys are correct in data, but local font/Tk rendering displays garbled glyphs; check on tester's system |
| Game load and gameplay on this new GUI build | PASS reported for TUT-01–07; evidence and limits below |
| Windows/macOS GUI and packaged executable | NOT RUN |
| GitHub Actions matrix | PASS: Linux/Windows, Python 3.10/3.12; [run 43700900282](https://github.com/Destorino5/fefw-editor/actions/runs/43700900282) on code commit `1ffa9d25e7f1434353f50abd14a8d321013eaf74` |

The 17-case run used the reference save privately. CI without that fixture runs
16 cases and skips the private-save case. No saves or game data are included in
the repository or source archive. The prior corrected tutorial restoration was
confirmed by the player; that does not substitute for testing this new GUI.

During test development, comparing every intermediate export to the original
payload also detected the save writer's expected embedded-checksum updates.
The regression now compares unrelated content before/after each tutorial edit,
then independently verifies the serialized container and reloaded payload.

## Player acceptance results

The player reported all seven cases passed on 2026-11-15. TUT-06 was initially
blocked by unclear wording in the guide; it passed after identifying the
**Also edit this route's other saves** checkbox. No code change was needed.

| Environment | Reported value |
|---|---|
| Source candidate | FEFW-Tutorials-Test-1; archive BUILD.txt identifies local commit `37c68fee2ce123b996c704325813cf87aa09c101` |
| Equivalent published code | `1ffa9d25e7f1434353f50abd14a8d321013eaf74`; later setup/documentation edits do not change the tested editor code |
| OS | Bazzite 45 NVIDIA Edition, 64-bit |
| Desktop | KDE Plasma 6.8.2; KDE Frameworks 6.31.0; Qt 6.11.2; Wayland |
| Kernel | `7.2.15-ogc1.1.fc45.x86_64` |
| CPU / RAM / GPU | AMD Ryzen 7 5800X3D (8 cores, 16 threads); 32 GiB RAM; NVIDIA GeForce RTX 5080 |
| Runtime | `fefw-recomp-0.1.5` |
| Route / chapter | Leda, Chapter 9 (Part I reference) |
| Baseline | Private `Auto (B0)`, after deed claims and EXP +10% Boon activation |
| Python / installation method | Not separately reported; successful editor use is confirmed |
| Game data version | Not separately reported; coverage is tied to the runtime and reference save above |

| Case | Result | Evidence and limits |
|---|---|---|
| TUT-01 | PASS, player-reported | Four editor screenshots show Foresight 2, Obelisk 1 and both extras absent, with readable Japanese keys and matching hashes. Search and Flags behavior are covered by the player's report. |
| TUT-02 | PASS, player-reported | Undo/redo sequence reported successful. |
| TUT-03 | PASS | Player report, in-game screenshot without Foresight, and private post-game save comparison. |
| TUT-04 | PASS | Player report, in-game screenshot with Foresight, and private post-game save comparison. |
| TUT-05 | PASS, player-reported | Supplied game screenshots show the added Reliquary and Third Eye entries. They document the addition stage; final removal is reported by the player, not independently shown by those images. No separate TUT-05 save was supplied. |
| TUT-06 | PASS, player-reported | Confirmed in follow-up after the checkbox explanation. No separate screenshots or multi-slot comparison supplied. |
| TUT-07 | PASS, player-reported | No unintended changes reported to the chapter, blessings, inventory/gold, supports, fast travel, deed claims or EXP +10% Boon. |

Japanese keys render correctly in the player's screenshots. This resolves the
acceptance question for that Bazzite environment; it does not establish that
the developer desktop's font issue is fixed on every platform. The installation
method was not reported, so this is not a separate validation of the documented
Distrobox setup procedure.

## Read-only comparison of supplied saves

All three containers passed checksum validation. The comparison only read the
uploaded originals, and confirmed they remained unchanged.

| Tutorial record | B0 | Post-game TUT-03 | Post-game TUT-04 |
|---|---|---|---|
| Foresight (`08373a0e`) | 2 | Absent | 2 |
| Obelisk Chamber (`c2a2c517`) | 1 | 1 | 1 |
| Drifting Reliquary (`2b0739cc`) | Absent | Absent | Absent |
| Third Eye (Cai) (`f501dfbc`) | Absent | Absent | Absent |
| Total tutorial records | 113 | 112 | 113 |

Foresight is the only tutorial record that differs between B0 and TUT-03, and
between TUT-03 and TUT-04. The full tutorial key/value map in TUT-04 exactly
matches B0. This is a tutorial-record comparison, not a claim that the entire
post-game saves are byte-identical or that every gameplay system was
independently revalidated by the comparison. TUT-07 remains the player's
regression report.

## Milestone status

TUT-01 through TUT-07 are complete for this reported environment. The contribution
can proceed to upstream review with these limits documented. Other routes,
native console execution, Windows/macOS GUI operation and packaged executables
remain untested by this acceptance run. No private saves, screenshots or game
data are published as fixtures.

Blessings, fast travel, deeds, Boons and story controls are subsequent
contributions, documented in [research-status.md](research-status.md). Each
requires its own acceptance guide; the tutorial passes do not validate those
future controls.
