# AI Usage

## Tools and how I used them

I used OpenAI Codex desktop for architecture planning, implementation assistance,
fixture and test generation, debugging, code review, documentation, and demo
preparation. I did not record the exact model identifier.

Codex helped implement the normalization, matching, search, evaluation, and API
components. I also used it to review the project against the Track C requirements,
identify gaps, add regression tests, and update the repository. For demo
preparation, I used it to outline the walkthrough and troubleshoot local startup.

The application itself does not call an LLM or paid API. After installing
dependencies, matching, search, fixture generation, and tests run offline.

## Representative agent instructions

These are summaries of the instructions I used, rather than verbatim chat logs.

1. Build an offline Python product identity engine with typed records, deterministic
   fixtures, normalization, explainable matching, explicit abstention, and tests.
2. Evaluate predictions against independently authored ground truth. Report
   precision, recall, exact-ID accuracy, abstention, high-confidence false positives,
   and category errors, with validation for malformed truth data.
3. Review the implementation against Track C, probe adversarial cases beyond the
   supplied fixtures, and fix confirmed issues with regression coverage. Preserve
   the ground-truth labels and verify the CLI, HTTP API, and local setup commands.

## Errors and corrections

I used Codex to identify and implement the following corrections:

- **Size validation:** Text normalization removed negative signs, allowing `-5 oz`
  to become a valid positive size. Validation now rejects negative values before
  punctuation cleanup. Missing sizes, incompatible dimensions, and materially
  different quantities cannot be compensated for by a high name or brand score.
- **Product identity safeguards:** Similar names could override explicit organic,
  form, or flavor conflicts. These conflicts now block approval and route the
  listing to abstention rather than forcing a canonical ID.
- **Search filtering:** The initial milk filter excluded oat milk even when it was
  requested. After that was corrected, verification exposed oat cereal appearing
  through token overlap. Milk queries now require milk products, and regression
  tests check the expected canonical ID.
- **Evaluation:** Category errors were compared with the predicted product's
  category instead of the expected product's category. The high-confidence
  false-positive denominator also included lower-confidence approvals. Both
  calculations were corrected and covered by regression tests.
- **Performance:** Search originally repeated identity matching for every query.
  Approved matches are now indexed at startup. Matching also uses an exact
  signature lookup before lexical candidate retrieval and scoring.

## Independent design decisions

- Keep the default path deterministic and offline, without requiring an API key.
- Keep weight and fluid volume separate instead of assuming a conversion.
- Prefer abstention over an unsupported product assignment.
- Keep expected fixture answers independent of matcher predictions.

The implementation and later corrections were AI-assisted; these decisions do
not imply that I wrote every component without assistance.

## Verification

Codex ran the automated suite and helped verify the local HTTP endpoints. The
updated suite has **62 passing tests**. On the unchanged 90-listing labeled corpus,
precision is **1.00**, recall is **0.95**, and exact-ID accuracy is **0.9556**.
Ground-truth labels were not changed to improve those results.

These measurements apply to the synthetic fixtures. The matching scores are
heuristics, not calibrated probabilities, and the modifier rules cover a limited
vocabulary. Broader validation would require additional independently labeled
products and retailer-specific examples.
