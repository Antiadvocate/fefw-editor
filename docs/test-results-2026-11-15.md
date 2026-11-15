# Milestone 1 developer validation — 2026-11-15

Base: upstream `2ef2f482a1f5c995783da4d80e909810849e882e`.
Branch: `feature/verified-tutorials`. Source test candidate, not an upstream
release. See the delivery archive's `BUILD.txt` for the exact candidate commit.

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
| Game load and gameplay on this new GUI build | PENDING player tests TUT-01–07 |
| Windows/macOS GUI and packaged executable | NOT RUN |
| GitHub Actions matrix | Defined, not run in this local validation |

The 17-case run used the reference save privately. CI without that fixture runs
16 cases and skips the private-save case. No saves or game data are included in
the repository or source archive. The prior corrected tutorial restoration was
confirmed by the player; that does not substitute for testing this new GUI.

During test development, comparing every intermediate export to the original
payload also detected the save writer's expected embedded-checksum updates.
The regression now compares unrelated content before/after each tutorial edit,
then independently verifies the serialized container and reloaded payload.

Next gate: complete [testing.md](testing.md) with the exact game/runtime version
before requesting an upstream merge. Blessings, fast travel, deeds, Boons and
story controls are subsequent contributions, documented in
[research-status.md](research-status.md).
