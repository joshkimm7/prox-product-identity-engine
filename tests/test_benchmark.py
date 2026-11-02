from src.benchmark import run_benchmark


def test_benchmark_returns_positive_measurements():
    report = run_benchmark(5)
    assert report.catalog_size == 40
    assert report.listing_size == 90
    assert report.repeated_searches == 5
    assert report.search_p50_ms > 0
    assert report.search_p95_ms >= report.search_p50_ms
    assert report.searches_per_second > 0
