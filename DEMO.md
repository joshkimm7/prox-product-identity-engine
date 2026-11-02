# Demo Plan

Target length: approximately 3 minutes.

## 0:00–0:25 — Problem and architecture

Explain that retailer titles are messy and unsafe forced matches hurt search and carts. Show `ARCHITECTURE.md`: normalization, two-stage matching, safeguards, abstention, indexed search, and evaluation against independent truth.

## 0:25–0:50 — Reproducible setup

Run:

```bash
uv sync --extra dev
uv run python scripts/generate_fixtures.py
uv run pytest -q
```

Point out 40 canonical products, 90 listings, three retailers, and passing tests.

## 0:50–1:35 — Matching and difficult cases

Open `http://127.0.0.1:8000/docs`. Use `GET /listings/L041/match` to show an explainable canned-tuna match with confidence, components, and alternatives. Then use a generic/ambiguous listing from the CLI output to show `ABSTAIN` and a reviewer flag. Explain why weight and fluid volume never compare directly.

## 1:35–2:05 — Search and category safety

Call `GET /search?q=chicken%20breast`. Show that chicken broth and dog food are excluded and that score components are visible. Call `POST /match` with `upstream_status: timeout` and show that the known canonical category remains intact.

## 2:05–2:35 — Measured quality

Run `uv run python -m src.cli evaluate` and show precision, recall, exact-ID accuracy, abstention, false-positive rate, and category-error rate. State clearly that remaining errors are conservative abstentions rather than incorrect assignments.

## 2:35–3:00 — Performance and limitations

Run `uv run python -m src.cli benchmark --repetitions 100`. Explain the startup index and measured p50/p95. Close with limitations: small synthetic corpus, hand-tuned thresholds, lexical retrieval only, no production persistence, and no calibrated retailer-specific confidence yet.
