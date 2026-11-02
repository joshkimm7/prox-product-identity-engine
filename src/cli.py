from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.matcher import ProductMatcher
from src.evaluation import GroundTruth, evaluate
from src.models import CanonicalProduct, RetailerListing
from src.search import search
from src.benchmark import run_benchmark


def load_records(path: Path, record_type):
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [record_type(**row) for row in rows]


def match_command(catalog_path: Path, listings_path: Path) -> int:
    catalog = load_records(catalog_path, CanonicalProduct)
    listings = load_records(listings_path, RetailerListing)
    matcher = ProductMatcher(catalog)
    results = [matcher.match(listing).to_dict() for listing in listings]
    print(json.dumps(results, indent=2))
    return 0


def evaluate_command(
    catalog_path: Path, listings_path: Path, truth_path: Path
) -> int:
    catalog = load_records(catalog_path, CanonicalProduct)
    listings = load_records(listings_path, RetailerListing)
    truth = load_records(truth_path, GroundTruth)
    report = evaluate(ProductMatcher(catalog), listings, truth)
    print(json.dumps(report.to_dict(), indent=2))
    return 0


def search_command(
    catalog_path: Path,
    listings_path: Path,
    query: str,
    retailer: str | None,
) -> int:
    catalog = load_records(catalog_path, CanonicalProduct)
    listings = load_records(listings_path, RetailerListing)
    results = search(query, listings, ProductMatcher(catalog), retailer=retailer)
    print(json.dumps([result.to_dict() for result in results], indent=2))
    return 0


def benchmark_command(repetitions: int) -> int:
    print(json.dumps(run_benchmark(repetitions).to_dict(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline cross-retailer grocery product identity engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    match_parser = subparsers.add_parser(
        "match", help="Match retailer listings to the canonical catalog"
    )
    match_parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("fixtures/catalog.json"),
        help="Canonical catalog JSON file",
    )
    match_parser.add_argument(
        "--listings",
        type=Path,
        default=Path("fixtures/listings.json"),
        help="Retailer listings JSON file",
    )
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Compare predictions with independently authored truth"
    )
    evaluate_parser.add_argument(
        "--catalog", type=Path, default=Path("fixtures/catalog.json")
    )
    evaluate_parser.add_argument(
        "--listings", type=Path, default=Path("fixtures/listings.json")
    )
    evaluate_parser.add_argument(
        "--truth", type=Path, default=Path("fixtures/ground_truth.json")
    )
    search_parser = subparsers.add_parser(
        "search", help="Search matched retailer listings"
    )
    search_parser.add_argument("query", help="Natural-language product query")
    search_parser.add_argument("--retailer", help="Optional retailer filter")
    search_parser.add_argument(
        "--catalog", type=Path, default=Path("fixtures/catalog.json")
    )
    search_parser.add_argument(
        "--listings", type=Path, default=Path("fixtures/listings.json")
    )
    benchmark_parser = subparsers.add_parser("benchmark", help="Measure repeated search latency")
    benchmark_parser.add_argument("--repetitions", type=int, default=100)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "match":
        return match_command(args.catalog, args.listings)
    if args.command == "evaluate":
        return evaluate_command(args.catalog, args.listings, args.truth)
    if args.command == "search":
        return search_command(args.catalog, args.listings, args.query, args.retailer)
    if args.command == "benchmark":
        if args.repetitions < 1:
            raise SystemExit("--repetitions must be positive")
        return benchmark_command(args.repetitions)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

