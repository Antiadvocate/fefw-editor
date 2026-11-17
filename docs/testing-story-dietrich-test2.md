# Dietrich Story Test 2 — four focused retries

Chapters **1, 3, 4 and 8–12** and the Test 1 UI checks are recorded as passed.
No repeat of those checks is needed. These saves investigate the four reported
blocks; none is an accepted fix yet.

Back up the complete game save directory, close the game, and test in a
disposable copy. Each case is independent: copy its `Auto` into that directory
and use Continue. Never continue one case into another case. Original return
saves are unchanged.

## Run these four first

| Case | Starting point and change | Check |
| --- | --- | --- |
| **D2-06A-Port-restriction** | Your edited Chapter 6 return, with only the lower-area movement restriction removed. Your function unlocks are retained; Chapter 6's upper restriction remains. | Walk through the doors to the port, reach Vandahl Trading Co., and complete the objective. |
| **D2-05A-Upper-restriction** | Your save after arena training, with only the upper-area movement restriction removed. | Find/reach the certification proctor and complete the required exam step. No need to repeat training. |
| **D2-02A-Rescue-history** | Your blocked Chapter 2 arrival, with only the rescue scene's seen record removed. Party unchanged. | Walk away from bound Esmerelda, then approach her again. Check whether the rescue triggers and the next objective advances. |
| **D2-07A-One-secret-permission** | Original Chapter 7 entry with permission for one teachable spear secret (catalogue: Hidden Windpierce). No units/classes/skills changed. | Replay the opening, choose **Esmerelda** in Teach Secrets, complete one teaching action, then reach normal control/the next objective. |

For each, return **Auto-after-progress** if it works, or **Auto-still-blocked**
if saving is possible. State the last objective reached. For Chapter 7, if
saving is still impossible, a screenshot of the selection or disabled reason
is enough. Do not replay the chapter just to obtain a return save.

## Only if needed

| Case | When to use | Difference |
| --- | --- | --- |
| D2-05B-Exam-switch-fallback | 05A still fails | Also enables Certification exams and the upper-area function. This combination includes the restriction removal that was absent from your earlier manual test. |
| D2-02B-Hub-cache-fallback | 02A still fails | Also clears two HubData state lists (2 and 37 entries). Their exact purposes are unrecovered; this is a broader disposable-save diagnostic. |
| D2-02C-Native-control | Both Chapter 2 retries fail | Untouched native Chapter 2 checkpoint, copied as Auto. It has its original party/progress. Test the rescue to separate the replayed state from the native checkpoint. |
| D2-07B-Soldier-fallback | 07A still fails | Also changes Esmerelda to Soldier, adding that class at zero EXP. Her level, mastery EXP, items and learned skills are unchanged. Try teaching her again. |
| D2-06B-Restriction-only-control | Optional, after 06A passes | Removes the lower restriction from the original arrival, without your later function unlocks. This checks whether those unlocks are actually necessary. |

The Chapter 7 menu showed 50 Magic Echo Shards; the selected secret costs 50
in the supplied game table. This tests a missing permission and then class
eligibility. It does not establish that the original roster was too small.

The included editor updates the chapter evidence labels and names the two
movement restrictions in Flags/diagnostics. **Applying a chapter in the editor
does not apply these experimental repairs.** Use the packaged test Autos.

The manifest records every flag change, changed root, source/output checksum
and validation result. The broader 02B and class-change 07B are labelled
separately so their results cannot be mistaken for a one-flag fix.
