# Editor refresh optimisation — 18 November 2026

Profiling the current editor identified a redundant full object-tree parse in
Convoy refresh. Other pages already share the byte-validated decoded save.
Convoy now accepts that same decoded save while retaining its bytes-based API
for existing callers. It still returns fresh rows on every read. No global
payload cache, editing rules or save output changes were introduced.

On two private samples, the median of seven warm full-page refreshes fell from
42.4 to 21.1 ms and from 94.7 to 62.5 ms (about 50% and 34% less time). These are
local Python 3.12/Tk measurements including idle layout, excluding disk loading,
decompression and game performance; they are not a claim about every machine.
The unit-list and Add Unit preview profiles did not justify further changes.
The first sample's Add Unit action is unsupported and was excluded from preview
comparisons. No private files or identifiers are included here.

Reproduce before/after with `research/benchmark_ui.py`, a display, the same
private input files, `--source /checkout`, and `--output /tmp/result.json`.
Baseline public revision: fe8b3714dbdc8d76cc977020e7c5208a3ae346ac.
The benchmark checks displayed convoy values and unchanged payload bytes.

Regression checks cover tree reuse, independent returned rows, direct quantity
edits, payload replacement, resizing item records, undo-style restoration and
missing convoy data. Existing structural edit validation is unchanged.

Before merging, keep this report, the benchmark and the test suite on the
feature branch. Main retains product source, catalogues, usage documentation
and build/source checks only.
