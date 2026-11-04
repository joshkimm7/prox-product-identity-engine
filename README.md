# Prox Cross-Retailer Product Identity Engine

An offline, explainable prototype that normalizes grocery listings, retrieves canonical-product candidates, and returns either a defensible match or an explicit abstention.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system diagram and component boundaries.

## Quick start

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/), and Make.
Dependency installation needs internet access once; matching, search, tests,
and fixture generation then run locally without API keys or network calls.

```bash
make start
```

One-command fixture generation and test run:

```bash
make test
```

## Submission status

The implementation and regression checks are complete for this prototype.
**The candidate must still record a 2–4 minute demo and add its link here and
in DEMO.md before submitting.** A walkthrough script is not a recording.
Confirm the active-time breakdown and AI model details from your own records.

## Current checkpoint

- Typed canonical and retailer-listing contracts
- Text and brand normalization
- Weight, volume, count, and multipack normalization
- Exact/similarity scoring with reason codes
- Confidence and ambiguity abstention
- Deterministic generator for 40 canonical products and 90 listings
- 28 authored difficult matches plus 10 explicit abstention cases
- Initial automated regression tests

The dataset, matching, search, evaluation, HTTP API, category safeguards, and
performance measurement foundations are now present.

## Regenerate deterministic fixtures

```bash
uv run python scripts/generate_fixtures.py
```

The expected canonical IDs and abstentions are explicitly authored in the
generator and are never derived from matcher predictions.

## Run tests

```bash
UV_CACHE_DIR=work/uv-cache uv run --extra dev pytest -q
```

Expected result:

```text
62 passed
```

## Run the sample matcher

From the project directory:

```bash
uv run python -m src.cli match
```

This reads `fixtures/catalog.json` and `fixtures/listings.json`, then prints
machine-readable JSON containing the selected canonical product, confidence,
reason codes, normalized size, and normalized price in cents per oz/fl oz/count.
Exact signature matches return their selected candidate; similarity and abstain
results include up to three alternatives (fewer only for smaller catalogs). An uncertain
listing returns `canonical_id: null` and `match_stage: abstain`.

To test your own JSON files:

```bash
uv run python -m src.cli match \
  --catalog path/to/catalog.json \
  --listings path/to/listings.json
```

## Evaluate matching quality

The ground-truth file is manually authored and is never derived from the
matcher predictions. Run:

```bash
uv run python -m src.cli evaluate
```

The JSON report includes precision, recall, exact-ID accuracy, abstention rate,
high-confidence false-positive rate, category-error rate, and every incorrect
case. Current deterministic results across 90 labeled listings are:

- Precision: 1.00
- Recall: 0.95
- Exact-ID accuracy: 0.9556
- High-confidence false-positive rate: 0.00
- Category-error rate: 0.00

The remaining errors are conservative abstentions rather than incorrect product
assignments. This matches the product-safety goal of favoring precision while
surfacing uncertain cases for review.

## Search matched listings

```bash
uv run python -m src.cli search "chicken breast"
uv run python -m src.cli search "salmon" --retailer MarketSquare
```

Search excludes abstained identity matches, deduplicates canonical products per
retailer, filters incompatible products, and returns inspectable score
components. The CLI and HTTP endpoint use the same deterministic search core.

## Run the HTTP API

```bash
uv run uvicorn src.api:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive documentation. Routes include
`POST /match`, `GET /search`, `GET /listings/{listing_id}/match`, and `GET /health`.

## Measure performance

```bash
uv run python -m src.cli benchmark --repetitions 100
```

The report contains measured initialization time, search p50/p95 latency,
throughput, corpus sizes, and the prototype cache policy.

Latest local result on the development machine:

- Startup identity indexing: 13.1743 ms
- Search p50: 0.5441 ms
- Search p95: 0.6282 ms
- Approximate throughput: 1,794 searches/second

Machine and background activity affect timings, so regenerate the report on the
reviewer's machine rather than treating these numbers as universal.

## Feature checklist

- [x] 40 canonical products and 90 listings across three retailers
- [x] Independent labeled truth and confusion report
- [x] Text, brand alias, unit, and multipack normalization
- [x] Exact/similarity stages with top-three candidates and reason codes
- [x] Category, form, pet/human, size-dimension, confidence, and ambiguity safeguards
- [x] Explicit abstention and reviewer flag
- [x] Canonical-category protection from uncertain or timed-out upstream output
- [x] Ranked, deduplicated search with retailer filtering
- [x] HTTP API and CLI
- [x] Required adversarial regression cases
- [x] Measured indexing and repeated-search latency

## Known limitations

- Candidate retrieval is lexical and tuned to a small synthetic corpus.
- Brand aliases are a small trusted map rather than a governed alias service.
- Confidence values are heuristic scores, not calibrated probabilities.
- The local API has no production authentication, rate limiting, or persistent database.
- Explicit organic/regular conflicts block approval; absent organic text remains unknown.
- Modifier rules cover the fixture vocabulary, not arbitrary grocery language.
- Missing sizes abstain. Size comparisons allow 1% conversion tolerance; other mismatches block approval.
- Search uses lexical overlap, not semantic or typo correction.
- Local-corpus benchmarks cannot be extrapolated linearly to 10 million listings.

## Approximate active time

Approximately **5 total active hours**, as corrected by the candidate. This
supersedes the earlier 7.5-hour estimate; it is not five additional hours.
Work included design, implementation, testing, debugging, documentation, and
demo preparation. Separate per-category times were not tracked.
See [HOURS.md](HOURS.md) for the time-reporting note.

## Next three priorities

1. Calibrate thresholds on a larger retailer-specific labeled sample.
2. Replace full-corpus lexical retrieval with a persistent inverted index.
3. Add versioned decision persistence and a prioritized human-review queue.


## Evaluation definitions

Precision is correct IDs divided by accepted matches; recall is correct IDs
among truth rows expecting an ID. Exact-ID accuracy includes correct abstentions.
High-confidence false-positive rate divides wrong high-confidence approvals by
all approvals with confidence >= 0.85. Category errors compare accepted output
against the expected canonical category; approving an ABSTAIN truth row also
counts as a category error because it has no justified expected category.
Scores, including exact-signature confidence, are heuristic rather than calibrated probabilities.

## Safety regression coverage

The additional suite checks cross-dimension and wrong-size matches, signed sizes,
missing sizes, explicit organic/form/flavor conflicts, oat-milk search, duplicate
signatures, empty catalogs, unit pricing, category review propagation, and metric
denominators. These checks supplement the original independently labeled corpus.
