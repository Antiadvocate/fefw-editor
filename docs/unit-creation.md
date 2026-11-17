# Unit creation and identity editing — Test 1

The Units page now offers **Add unit…**, a visible **Unit #** column, and
**Change unit number…**. The initial functional test set has passed within its
[reported scope](unit-restoration-fix.md). Expanded cross-route, special and
NPC cases are [pending game tests](testing-unit-expansion-test2.md); a correctly
parsed record does not establish working deployment.

## Catalogue and creation

The picker has 67 named character identities with PID-derived recruitment keys.
54 ordinary candidates are enabled. Twelve special-character entries and the
custom protagonist remain visible but disabled pending their own validation.
An [audit of all 2,923 Person rows](unit-catalogue-coverage.md) accounts for all
55 entries with source flag byte 39: 54 enabled plus the custom protagonist.
That heuristic is not proof of an exhaustive natural-recruitment list.
An existing character, including a known alternate template, cannot be added
again. Status is calculated over the entire live UnitPool, including records
hidden by the editor's roster filter.

Each addition uses the character's own recovered level-one class, HP, mastery
ranks, starting inventory and eligible learned abilities. A new version-36
record is built independently: it does not clone another character's identity,
level-up gains, skills, inventory or history. The current class is registered;
mounts and battalions are not copied or created. Some candidates have no starting
weapon and need one from the convoy before combat. These are level-one defaults,
not the game's chapter-scaled natural recruitment loadouts.

Defaults come from Person, Job, Growth and Skill tables. Conditional learning
rows and zero-level/zero-rank scripted grants are excluded. The JSON stores
source hashes and evidence; `research/unit_catalog_report.py` reproduces it
when private game tables are supplied. No game binaries or private unit records
are distributed. Two positive 31-bit seed words are derived from the character
key and allocated number; progress accumulators and battle counters
start empty. This initialization still needs game level-up testing.

Only the exact PID-derived recruitment and met flags are set. The flag catalogue
generates those names; their existence there is not independent evidence of a
natural recruitment event. No story completion,
facility, class-unlock, support, reward or tutorial flags are granted. Route and
part eligibility for natural recruitment is **unverified**. Adding a character
early may affect its later scripted recruitment; that check remains required.

An exact existing record with clear unit flags and an absent/zero recruitment
flag offers **Restore recruitment**. It re-enables only those recruitment/met
flags and preserves the existing record, including its number and progress.
It is not a general revive or missing-character repair. Alternate templates,
ambiguous records and unknown flag values require review.

## Identity rules

The character's PID, Person-table serial and save `unit_number` are different
values. Character duplicates are checked using canonical PID/known aliases;
numeric collisions are checked across all live units and mapped equipment owners.

Automatic allocation chooses one above the highest occupied/referenced number,
within 1–254. It does not recycle gaps or allocate 0/255. Existing duplicates
and exhausted allocation are refused. Manual edits reject numbers used by any
other live unit or by equipment. Renumbering updates the unit and the typed
owner byte in embedded and pooled mounts/battalions, including the reliquary.
It does not search-and-replace matching numbers in unrelated fields.

Nonempty mount affinity records are not decoded, so allocation and renumbering
are disabled for those saves. A duplicate number can be repaired only if there
are no ambiguous equipment owners. Other historic or scripted references have
not been exhaustively proven; renumbering remains experimental.

**Copy unit in…** also refuses an existing canonical character and allocates
a fresh destination number. Attached source mounts/battalions must be detached
first. Copy retains the imported character's progress, unlike fresh creation,
and does not automatically set recruitment flags. The old `new_unit` template
API now delegates only supported catalogue defaults to the guarded creator.

## Scope and editor behavior

Creation/import/renumbering support recognized **Part 1 free-time saves** for
the four routes. Battle saves, chapter-start checkpoints, unknown layouts and
other parts are refused. The selected save is edited alone; turn off
**Also edit this route's other saves**. A changed destination invalidates an
open preview. Actions support Undo/Redo, apply in memory and write on Save;
the existing numbered backup behavior remains in use.

Automated coverage includes aliases, hidden/duplicate identities, equipment
owners, number boundaries, inactive records, unknown layouts, independent
defaults, source preservation, stale previews, Undo/Redo and serialization.
Private route checks can be enabled with `FEFW_UNIT_SOURCES`, pointing to a
JSON object whose values are private baseline save paths. No private save is
needed for public CI. See [the game test guide](testing-unit-creation-test1.md).
