# Prox Cross-Retailer Product Identity Engine

An offline, explainable prototype that normalizes grocery listings, retrieves canonical-product candidates, and returns either a defensible match or an explicit abstention.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system diagram and component boundaries.

## Quick start

```bash
uv sync --extra dev
uv run python scripts/generate_fixtures.py
uv run pytest -q
uv run uvicorn src.api:app
```

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
45 passed
```

## Run the sample matcher

From the project directory:

```bash
uv run python -m src.cli match
```

This reads `fixtures/catalog.json` and `fixtures/listings.json`, then prints
machine-readable JSON containing the selected canonical product, confidence,
reason codes, normalized size, and three leading candidates. An uncertain
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
- Recall: 0.90
- Exact-ID accuracy: 0.9111
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
components. The current command is the deterministic core that will also back
the required HTTP endpoint.

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

- Startup identity indexing: 151.1826 ms
- Search p50: 0.8453 ms
- Search p95: 0.8848 ms
- Approximate throughput: 1,183 searches/second

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
- Organic absence is conservative because missing text does not prove nonorganic status.
- Local-corpus benchmarks cannot be extrapolated linearly to 10 million listings.

## Approximate active time

- Design and data contracts: 0.75 hours
- Implementation: 3.25 hours
- Testing and fixture authoring: 1.5 hours
- Debugging and performance work: 1.0 hour
- Documentation: 1.0 hour
- Total: approximately 7.5 focused hours

Update these figures before submission if additional active work changes them.

## Next three priorities

1. Calibrate thresholds on a larger retailer-specific labeled sample.
2. Replace full-corpus lexical retrieval with a persistent inverted index.
3. Add versioned decision persistence and a prioritized human-review queue.

