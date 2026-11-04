# AI Usage

This document records implementation assistance and subsequent submission-readiness corrections.

Model identifier: not available in this chat context. The candidate should add the
verified model(s) from their own session records; no model name is inferred.

## Tools

- OpenAI Codex desktop: architecture discussion, implementation assistance, test generation, repository review, debugging, documentation, and demo preparation.
- The application itself uses no hosted model or paid AI API. Matching and evaluation run deterministically offline after dependencies are installed.

## Meaningful agent instruction 1

Create the smallest end-to-end Track C foundation using Python, typed models, deterministic offline matching, structured reason codes, explicit abstention, and tests. Keep the system simple enough to explain and modify during a live interview.

## Meaningful agent instruction 2

Add an evaluation system that compares matcher output with independently authored ground truth and reports precision, recall, exact-ID accuracy, abstention rate, high-confidence false-positive rate, and category-error rate. Validate the truth data rather than silently ignoring missing or duplicate IDs.

## Meaningful agent instruction 3

Implement deterministic search over approved identity matches. Exclude abstained listings and explicitly incompatible results such as chicken broth for `chicken breast`, support a retailer filter and deduplication, and expose ranking components for inspection.

## Independent decisions

- Use deterministic matching as the default path; no network or LLM is required.
- Keep weight and fluid-volume units in separate dimensions.
- Prefer abstention when confidence is low or the two leading candidates are too close.
- Keep fixture generation deterministic and store expected answers independently from matcher output.

## Corrections and debugging

### Correction 1: packaging and size tokens lowered a valid match

The first smoke test incorrectly abstained on `Ocean Catch Solid White Tuna Can, 5 Ounce` even though its brand, category, and normalized size matched C101. The initial name comparison treated `can`, `5`, `ounce`, and `canned` as unrelated tokens. I corrected this by removing size-only tokens from product-name comparison, normalizing `can`/`tinned` to `canned`, and including the canonical product's structured form in its comparison text. I did not simply lower the confidence threshold because that would also admit weaker unrelated matches.

### Correction 2: punctuation broke a trusted brand alias

The first automated test run found that the general text normalizer preserved the final period in `Ocean Catch Co.`, preventing its alias from matching. Decimal points are meaningful for sizes such as `14.75 oz`, so I changed normalization to remove periods only when they are not between digits. This preserves decimal sizes while making punctuation-insensitive brand aliases reliable.

### Correction 3: zero size was accepted at the confidence boundary

The expanded 90-listing evaluation revealed that `Baby Spinach` with an explicit `0 oz` size matched a nonorganic spinach product at exactly the minimum confidence threshold. A zero size is malformed evidence, not merely missing evidence, so I added a fail-safe rule that sends non-positive or invalid sizes to review with `INVALID_SIZE`. The later readiness pass also made missing sizes abstain rather than allowing other evidence to compensate.

### Correction 4: search recomputed every identity match

The first 100-search benchmark measured roughly 152 ms p50 because every query reran matching for all 90 listings against all 40 canonical products. I introduced a startup `SearchIndex` containing only approved identity matches. Queries now rank this immutable index without repeating normalization and identity scoring. I retained the original measured result as the motivation for the change and reran the benchmark after implementation.

### Correction 5: a meaningful texture modifier was over-abstained

The named adversarial suite showed that `Creamy Peanut Butter` beat the crunchy candidate by 0.0462 but was rejected by the original 0.05 ambiguity margin. I reduced the margin to 0.04, which accepts the explicit creamy variant while the modifier-free `Peanut Butter` case remains tied and abstains. This was a targeted calibration based on labeled examples, not a blanket reduction of the minimum confidence threshold.


## Submission-readiness correction pass

Instruction: “Fix these and update the repository,” referring to a review that
reproduced unsafe size, organic, flavor, and form matches, oat-milk search
exclusion, missing unit pricing, absent signature lookup, and metric issues.
Codex implemented the fixes and added executable regressions, ran the full suite,
and regenerated evaluation and benchmark results. Ground-truth labels were not
changed to accommodate predictions.

Corrections included preserving negative signs during size validation and treating
explicit identity conflicts as approval blockers rather than merely losing score.
The evaluation now uses expected categories and the high-confidence population
as its respective denominators. The candidate should review these changes and
be prepared to explain them; AI assistance does not establish personal ownership.

## Additional prompts and instructions from the readiness review

- “Can you check if this repository is submission ready for track C” — compare the repository with the supplied assessment, execute it locally, and probe cases beyond its fixtures.
- “Can you fix these and update the repository” — implement the identified corrections, add regressions, verify the result, and push the changes.
- “I don't get how to run it and what I need to show” — explain local startup, the API documentation page, tests, and a short demo sequence.

## What Codex changed and verified in the readiness pass

Codex added signature-first matching and token-index candidate retrieval; blocked
incompatible sizes and explicit organic, form, flavor, and pet/human conflicts;
rejected signed negative sizes before text normalization; added normalized unit
pricing; fixed oat-milk search; and propagated category-conflict review flags.
It corrected evaluation denominators and comparison with the expected category,
added Makefile start/test commands, and updated documentation and sample output.

The test suite increased from 45 to 62 passing tests. On the unchanged 90-row
labeled corpus, precision remained 1.00, recall increased from 0.90 to 0.95, and
exact-ID accuracy increased from 0.9111 to 0.9556. These figures describe the
synthetic corpus, not a guarantee on unseen products. Codex also ran the local
HTTP server and checked health and search responses.

### Additional error caught during verification

The first oat-milk search correction excluded dairy milk but still returned oat
cereal through token overlap. A live HTTP check exposed this. The filter was
updated to require milk for milk queries, and the regression assertion was
strengthened to check the canonical oat-milk ID rather than merely the word “Oat.”

## Demo and documentation assistance

Codex suggested a 2–4 minute walkthrough, explained how to start the server and
run tests in separate terminal tabs, helped reload the local API documentation
page, and reviewed a terminal screenshot for visible credentials. It did not
record or upload a demo video. The candidate runs and narrates the demonstration.

## Attribution and limitations

The initial independent-decision notes above are retained from the original
project record. The readiness fixes described here were proposed and implemented
with Codex assistance; they should not be represented as unaided work. The
candidate requested the review and authorized the fixes and repository update.
Active hours are recorded separately in HOURS.md; elapsed chat time and automated
execution time are not treated as measured candidate effort.
