# Unit creation Test 1 — automated validation, 17 November 2026

Game acceptance is pending. No deployment, movement, natural recruitment,
level-up or visual UI pass is claimed by this report.

- Full regression: **273 tests, 218 passed, 55 skipped**, no failures. Skips
  are older private fixtures not present for this run. Private game tables,
  Cai chapter sources and four unit baselines were enabled.
- The focused unit suite also passes independently. Game level-up behavior
  remains unverified. Public CI is configured for the synthetic cases without
  private inputs; remote CI has not run for this unpublished branch.
- The catalogue reproduces exactly from the private source tables: 67 named
  candidates, 54 enabled and 13 restricted. Known aliases share one identity.
- **197 independent additions** across Cai Chapter 4, Dietrich Chapter 4,
  Theodora Chapter 3 and the old Leda Chapter 9 baseline passed structural
  readback. Each baseline was also expanded cumulatively to the 54 enabled
  identities: another 197 additions, with unique numbers and unchanged original
  unit records. Existing records are compared with internal pointers normalized.
- Each independent addition preserves every unrelated root block, all original
  unit records and every flag except the exact recruitment/met pair. Source
  payloads remain unchanged. Known/unknown catalogue keys are not substituted.
- Existing zero/one met flags are updated/preserved correctly. Unknown/wide
  recruitment states, duplicate identities, malformed pool headers/trailers,
  unsupported contexts and exhausted number allocation are refused.
- Synthetic embedded and pooled mount/battalion owners follow renumbering.
  Same-valued stats and unrelated units remain untouched. Renumbering back is
  byte-identical. Ambiguous duplicate owners, occupied equipment numbers and
  unmapped mount affinities are refused.
- Repeated additions, reverse renumbering and container save/reload pass on all
  four private baselines. Container checksums pass. Separate tests verify
  numbered backups, stale-preview rejection, selected-slot edits and Undo/Redo.
- UI import and the legacy creation API use the guarded identity path. Release
  packaging includes the new catalogue. The source compiles; English flag label
  refresh/check and whitespace checks pass. The version remains 1.3.9 and Flags
  remains last. A live Tk visual test was not available in this environment.

The private kit contains unchanged Cai/Leda controls and three independent
`Auto` cases. Their identities and checksums are verified after serialization.
No private saves or game binaries are committed to the repository.

See [scope](unit-creation.md) and [game/UI checks](testing-unit-creation-test1.md).
