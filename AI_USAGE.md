# AI Usage

This file will be updated throughout implementation rather than reconstructed after completion.

## Tools

- OpenAI Codex: architecture discussion, implementation assistance, test generation, and code review.

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

The expanded 90-listing evaluation revealed that `Baby Spinach` with an explicit `0 oz` size matched a nonorganic spinach product at exactly the minimum confidence threshold. A zero size is malformed evidence, not merely missing evidence, so I added a fail-safe rule that sends non-positive or invalid sizes to review with `INVALID_SIZE`. Missing size remains a separate case that can be considered alongside other evidence.

### Correction 4: search recomputed every identity match

The first 100-search benchmark measured roughly 152 ms p50 because every query reran matching for all 90 listings against all 40 canonical products. I introduced a startup `SearchIndex` containing only approved identity matches. Queries now rank this immutable index without repeating normalization and identity scoring. I retained the original measured result as the motivation for the change and reran the benchmark after implementation.

### Correction 5: a meaningful texture modifier was over-abstained

The named adversarial suite showed that `Creamy Peanut Butter` beat the crunchy candidate by 0.0462 but was rejected by the original 0.05 ambiguity margin. I reduced the margin to 0.04, which accepts the explicit creamy variant while the modifier-free `Peanut Butter` case remains tied and abstains. This was a targeted calibration based on labeled examples, not a blanket reduction of the minimum confidence threshold.

