# Dietrich Test 2 validation — 17 November 2026

- Full unittest discovery: **233 tests, 182 passed, 51 skipped**, no failures.
  Native Dietrich sources, game tables and Test 1 returns/kit were enabled.
  Skips need other historical private fixtures unavailable in this workspace.
- The new private test independently checks each probe's exact flag delta,
  expected HubData/UnitPool exceptions, nine exported Autos and refusal to
  overwrite an existing kit. It also passed alone.
- Eight modified probes and one unchanged native control are packaged. Each
  modified save passes export/reopen, payload equality, checksums, story
  summaries, unchanged sequence, unchanged tutorial list and roster identities,
  and comparison of pointer-normalized roots against its own source.
- All 20 returned Test 1 saves pass checksums and route/chapter/sequence mirrors.
  The returned Chapter 1 battle capture and reported completed transition are
  recorded separately. No Chapter 7 return was supplied or required.
- Flag-label regeneration/check passes. Exactly two labels changed: upper and
  lower Dagsion movement restrictions. All original identifiers/hashes and other
  catalogue content remain unchanged. `git diff --check` passes.
- The first test run overlapped label regeneration and read the old generated
  dictionary, causing the label-sync test to fail. After regeneration completed,
  the complete final suite above passed. No unresolved test failure remains.
- Chapter-entry payload preparation is unchanged. Tests retain party/flag/root
  preservation and the existing Cai Sewers exception. Only evidence text and
  the two read-only diagnostic labels changed in the application.
- Test 1's live UI checks are player-confirmed. New text has automated/controller
  coverage, not a new live visual layout check. Test 2 game progression and
  Dietrich Obelisk behavior remain untested.

The repair builder is under `research/` and is never imported by the application.
Inputs are fingerprinted, copied and left unchanged. Its manifest records each
source/output fingerprint, root/flag differences and pending game result.

Reproduce with `FEFW_DIETRICH_SOURCE_DIR`, `FEFW_GAMEDATA`,
`FEFW_DIETRICH_RETURN_DIR` and `FEFW_DIETRICH_TEST1_DIR` pointing to the supplied
private fixtures, then run `python -m unittest discover -s tests -v`.
Build into a new directory with
`python research/dietrich_retry_kit.py <returns> <Test-1-kit> <output>`.
