from __future__ import annotations

import statistics
import time
from dataclasses import asdict, dataclass

from src.runtime import load_runtime
from src.search import search


@dataclass(frozen=True)
class BenchmarkReport:
    catalog_size: int
    listing_size: int
    repeated_searches: int
    initialization_ms: float
    search_p50_ms: float
    search_p95_ms: float
    searches_per_second: float
    cache_policy: str

    def to_dict(self) -> dict:
        return asdict(self)


def run_benchmark(repetitions: int = 100) -> BenchmarkReport:
    started = time.perf_counter()
    runtime = load_runtime()
    initialization_ms = (time.perf_counter() - started) * 1000
    queries = ("chicken breast", "whole milk", "salmon", "peanut butter", "olive oil")
    durations = []
    for index in range(repetitions):
        started = time.perf_counter()
        runtime.search_index.search(queries[index % len(queries)])
        durations.append((time.perf_counter() - started) * 1000)
    ordered = sorted(durations)
    p95_index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95) - 1))
    total_seconds = sum(durations) / 1000
    return BenchmarkReport(len(runtime.catalog), len(runtime.listings), repetitions, round(initialization_ms, 4), round(statistics.median(ordered), 4), round(ordered[p95_index], 4), round(repetitions / total_seconds, 2), "Approved identity matches indexed once at startup; no query-result cache.")
