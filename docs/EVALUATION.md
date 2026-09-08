# Prompt evaluation protocol

**Status: protocol provided; no systematic model-effectiveness study has been run.** Site tests and translation completeness are separate from behavioral effectiveness. Do not present generated demo output as measured before/after evidence.

## Direct First / 先说重点

Use matched tasks in independent conversations on the same displayed model and date. Remove the preference from the control conversation's account, project and other instruction sources. Record all other active settings, sample more than once, and keep task wording unchanged. Do not cherry-pick only favorable responses.

Suggested tasks: explain the purpose of a validation set to a beginner; advise a new literature-review author; evaluate remote work; correct a genuinely mistaken statistical claim. The last task tests whether necessary negation and logical contrasts survive.

Assess unnecessary reject-and-replace constructions, accuracy, preserved logical distinctions, completeness, readability and unwanted shortening. A reduced phrase count alone is insufficient evidence of improvement. Report counts with examples and acknowledge judgment-dependent categories. Do not claim a general percentage improvement without an appropriate sampling design.

## Paper Mentor / 论文研读导师

Use papers you have permission to share, spanning a theoretical, quantitative empirical, qualitative and review study. Include a narrow follow-up question and a case where one figure is deliberately unavailable. Keep the source files and accessibility conditions explicit. Protect patient, participant and confidential research data.

Assess traceable equation and table explanations, separation of source claims from inference, treatment of uncertainty, methodological fit, useful limitations, avoidance of fabricated novelty or proofs, and focus on follow-up questions. Check outputs against the actual paper. Include both strengths and failures.

## Minimal run record

| Field | Meaning |
|---|---|
| prompt_id / prompt_version / language | Exact content version and locale |
| service / displayed_model / tested_at | Model identity as shown, date |
| task / source_material / access_limits | Reproducible input and available evidence |
| active_instructions | Other user/project instructions |
| condition / repeat | Control or preference, repeat number |
| output / reviewer_notes | Unedited output or clearly marked excerpt |
| rubric / result / limitations | Assessment with qualifications |

Begin with explicit, labeled examples; graduate to a systematic comparison only when the protocol and sampling justify it. Publish independent native-speaker review separately from model-use tests. No completed run records are included in this release.
