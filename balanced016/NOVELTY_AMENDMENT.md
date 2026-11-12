# Study016: novelty correction before all new validation inference

Candidate weights were already fixed and saved (stream
`e6e628ad8b82c4ebf2a008b1805163640cbdc75329b173a587d213ebd6923a35`).
Historical retention screening was underway; ZERO questions from the new
programming/control validation were queried by any model. No new validation
output informed these replacements. No weights or acceptance gates changed.

A broader repository search found that four proposed v1 control facts were
already present in older studies: Peru/Lima (lab_rsi development, observed),
silver/Ag (history/pilot1_data.json), tooth/teeth (lab_rsi heldout, observed),
and teach/taught (code_rsi/data.json, earlier test-bank entry). These cannot
all be described as new project questions. Presence in a reserved bank does
not mean it was queried in016; no previously reserved model run was opened.

Preserve validation_controls.json as the original, UNUSED v1. The amended
runner validate.py uses validation_controls_v2.json: replace those four facts
with Ghana/Accra, tungsten/W, criterion/criteria and cling/clung. All eight v2
items receive FRESH016v2 IDs. Other four controls and ALL eight code tasks,
tests, correct answers, reference audits and generation settings stay fixed.
The v1 runner is preserved as validate_initial.py for audit ONLY; do not run it.

novelty_check.py checks exact v2 questions, new rare fact terms and all eight
code entry names against existing .json/.py/.md text under rg defaults,
excluding016 itself. No matches were found. This cannot prove absence from
pretraining, compressed files or every paraphrase, and common algorithm/language
families overlap. It is a pilot with new questions, not a novel skill-family test.
General teaching examples are different from the12old controls as declared;
some ordinary teaching facts can occur in much older project data.

The initial frozen snapshots, v1 controls and earlier commits are preserved.
The new v2 source/data/addendum hashes must be committed BEFORE any validation
model sees them. The same retention gate still controls whether they are queried;
if it fails, v2 remains unqueried. No lower gate, relabeling of model outputs,
new dose search or change to the official historical judges is permitted.
