# Scale and Cost Strategy

## Assumptions and objective

Assume 10 million active retailer listings, weekly full refreshes, daily incremental updates affecting 2% of listings, 500,000 canonical products, and a high-precision objective: fewer than 0.5% false positives among automatically approved matches. False matches are more damaging than review-queue growth, so ambiguous cases abstain.

## Processing design

Normalize listings in idempotent batches keyed by retailer and listing ID. Store normalized fields and a versioned signature so unchanged records reuse prior decisions. Retrieve candidates from category-partitioned lexical indexes using brand, type/form tokens, and compatible size dimensions; do not score every canonical product. Rerank the top 20–50 candidates with the deterministic scorer. Cache canonical lookups by catalog version and invalidate only affected product families.

A queue separates ingestion, normalization, candidate generation, scoring, and review. Failed batches retry safely; a dead-letter queue preserves malformed records. Decisions record the source listing version, catalog version, scorer version, candidates, components, and reason codes so results can be reproduced.

## Human review and error budget

Prioritize review by estimated business impact, confidence margin, listing traffic, category risk, and novelty. Never auto-approve cross-dimension units, pet/human conflicts, incompatible forms, invalid sizes, or category conflicts. Sample at least 1% of high-confidence approvals for audit. Alert if sampled precision falls below 99.5%, high-confidence false positives exceed 0.5%, abstention changes by more than 20% week over week, or a retailer's category-error rate doubles.

## Performance and storage

The local 40-product/90-listing prototype indexes approved identities in about 151 ms and measured search p50/p95 near 0.85/0.88 ms on the development machine. At scale, use a persistent inverted index and precomputed approved-match table rather than rebuilding in request handlers. Partition listing state by retailer and hash of listing ID; partition audit history by event date. Keep current decisions in hot storage and compress immutable history after 30 days.

At roughly 2 KB per listing for normalized data, decision metadata, and index overhead, 10 million current listings require approximately 20 GB before replicas and database overhead. With history, indexes, backups, and two replicas, budget 100–150 GB. A weekly 10-million-record refresh averaging 50 records/second per worker is about 56 worker-hours; 20 workers finish in under three hours before queue overhead.

## Illustrative monthly cost model

These are planning assumptions, not vendor quotes: $0.10 per compute-hour, $0.12/GB-month for hot database storage, $0.025/GB-month for archived objects, and $0.10 per million queue operations. Budget approximately $150–300 for batch compute, $20 for 150 GB hot storage before managed-service premiums, under $10 for archive/queue traffic, and $200–500 for the search/database service. A reasonable initial total is $400–800/month, with managed replicas, observability, and traffic potentially raising it to $1,500/month. The deterministic core has no per-item LLM charge.

## Drift, rollback, and releases

Version fixtures, normalizers, aliases, thresholds, and scorer weights. Run every candidate release against the frozen labeled set plus retailer-specific shadow samples. Compare precision, recall, category errors, abstention, latency, and review volume. Deploy in shadow mode, then 5%, 25%, and 100% stages. Preserve the previous decision table and scorer image; rollback switches the read alias to the prior version without deleting new audit data. The first likely bottleneck is candidate retrieval/index update throughput, followed by human-review capacity—not the small deterministic reranker.

