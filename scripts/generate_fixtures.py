"""Generate deterministic, synthetic Track C fixtures.

Ground-truth answers are explicitly authored in this file and are never
calculated from matcher predictions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CATALOG = [
    ("C101", "Ocean Catch Solid White Tuna", "Ocean Catch", "PANTRY", "tuna", "canned", False, 5, "oz"),
    ("C102", "Atlantic Fresh Tuna Steak", "Atlantic Fresh", "SEAFOOD", "tuna", "fresh", False, 16, "oz"),
    ("C103", "Farmhouse Chicken Breast", "Farmhouse", "MEAT", "chicken", "fresh", False, 16, "oz"),
    ("C104", "Heritage Chicken Broth", "Heritage", "PANTRY", "chicken", "broth", False, 32, "fl oz"),
    ("C105", "Fresh Salmon Fillet", "Harbor Table", "SEAFOOD", "salmon", "fresh", False, 16, "oz"),
    ("C106", "Tinned Pink Salmon", "Harbor Table", "PANTRY", "salmon", "canned", False, 14.75, "oz"),
    ("C107", "Whole Milk", "Meadow Vale", "DAIRY", "milk", "liquid", False, 128, "fl oz"),
    ("C108", "Whole Milk", "Dairy Best", "DAIRY", "milk", "liquid", False, 128, "fl oz"),
    ("C109", "Organic Baby Spinach", "Green Field", "PRODUCE", "spinach", "fresh", True, 5, "oz"),
    ("C110", "Baby Spinach", "Green Field", "PRODUCE", "spinach", "fresh", False, 5, "oz"),
    ("C111", "Chicken Flavored Dog Food", "Happy Hound", "PET", "dog food", "dry pet food", False, 192, "oz"),
    ("C112", "Honey Nut Oat Cereal", "Morning Mill", "BREAKFAST", "cereal", "dry", False, 18.8, "oz"),
    ("C113", "Original Oat Milk", "Oat Valley", "DAIRY_ALT", "oat milk", "liquid", False, 64, "fl oz"),
    ("C114", "Organic Whole Milk", "Meadow Vale", "DAIRY", "milk", "liquid", True, 64, "fl oz"),
    ("C115", "Large Brown Eggs", "Sunny Farm", "DAIRY", "eggs", "fresh", False, 12, "ct"),
    ("C116", "Organic Large Brown Eggs", "Sunny Farm", "DAIRY", "eggs", "fresh", True, 12, "ct"),
    ("C117", "Creamy Peanut Butter", "Nut House", "PANTRY", "peanut butter", "spread", False, 16, "oz"),
    ("C118", "Crunchy Peanut Butter", "Nut House", "PANTRY", "peanut butter", "spread", False, 16, "oz"),
    ("C119", "Strawberry Yogurt", "Cultured Farms", "DAIRY", "yogurt", "cultured", False, 6, "oz"),
    ("C120", "Plain Greek Yogurt", "Cultured Farms", "DAIRY", "yogurt", "cultured", False, 32, "oz"),
    ("C121", "Cheddar Cheese Block", "Dairy Best", "DAIRY", "cheese", "block", False, 8, "oz"),
    ("C122", "Shredded Cheddar Cheese", "Dairy Best", "DAIRY", "cheese", "shredded", False, 8, "oz"),
    ("C123", "Ground Beef 80 Percent Lean", "Farmhouse", "MEAT", "beef", "ground fresh", False, 16, "oz"),
    ("C124", "Beef Broth", "Heritage", "PANTRY", "beef", "broth", False, 32, "fl oz"),
    ("C125", "Organic Gala Apples", "Green Field", "PRODUCE", "apple", "fresh", True, 48, "oz"),
    ("C126", "Gala Apples", "Green Field", "PRODUCE", "apple", "fresh", False, 48, "oz"),
    ("C127", "Frozen Blueberries", "North Orchard", "FROZEN", "blueberry", "frozen", False, 16, "oz"),
    ("C128", "Fresh Blueberries", "North Orchard", "PRODUCE", "blueberry", "fresh", False, 6, "oz"),
    ("C129", "Tomato Basil Pasta Sauce", "Old Kitchen", "PANTRY", "pasta sauce", "jarred", False, 24, "oz"),
    ("C130", "Diced Tomatoes", "Old Kitchen", "PANTRY", "tomato", "canned", False, 14.5, "oz"),
    ("C131", "Spaghetti Pasta", "Old Kitchen", "PANTRY", "pasta", "dry", False, 16, "oz"),
    ("C132", "Gluten Free Spaghetti", "Free Table", "PANTRY", "pasta", "dry", False, 12, "oz"),
    ("C133", "White Sandwich Bread", "Daily Loaf", "BAKERY", "bread", "baked", False, 20, "oz"),
    ("C134", "Whole Wheat Sandwich Bread", "Daily Loaf", "BAKERY", "bread", "baked", False, 20, "oz"),
    ("C135", "Extra Virgin Olive Oil", "Golden Grove", "PANTRY", "olive oil", "liquid", False, 16.9, "fl oz"),
    ("C136", "Canola Cooking Oil", "Golden Grove", "PANTRY", "canola oil", "liquid", False, 48, "fl oz"),
    ("C137", "Sparkling Lemon Water", "Clear Spring", "BEVERAGE", "sparkling water", "liquid", False, 96, "fl oz"),
    ("C138", "Still Spring Water", "Clear Spring", "BEVERAGE", "water", "liquid", False, 128, "fl oz"),
    ("C139", "Vanilla Ice Cream", "Cold Meadow", "FROZEN", "ice cream", "frozen", False, 48, "fl oz"),
    ("C140", "Vanilla Frozen Yogurt", "Cold Meadow", "FROZEN", "frozen yogurt", "frozen", False, 48, "fl oz"),
]

RETAILERS = ("FreshTown", "ValueMart", "MarketSquare")

# Explicit difficult variants. Each expected ID is authored independently.
TRICKY = [
    ("Ocean Catch White Tuna Can", "Ocean Catch Co.", "5 oz", "PANTRY", "C101", "canned tuna, packaging alias"),
    ("Atlantic Fresh Raw Tuna Steak", "Atl Fresh", "1 lb", "SEAFOOD", "C102", "raw tuna versus canned tuna"),
    ("Farmhouse Boneless Chicken Breast", "Farmhouse", "1 lb", "MEAT", "C103", "chicken meat versus broth"),
    ("Heritage Shelf Stable Chicken Broth", "Heritage", "32 fl oz", "PANTRY", "C104", "broth versus meat"),
    ("Harbor Table Fresh Salmon Fillet", "Harbor Table", "1 lb", "SEAFOOD", "C105", "fresh salmon versus tinned"),
    ("Harbor Table Canned Pink Salmon", "Harbor Table", "14.75 oz", "PANTRY", "C106", "tinned synonym"),
    ("Meadow Vale Whole Milk Gallon", "Meadow Vale", "1 gal", "DAIRY", "C107", "gallon equals 128 fluid ounces"),
    ("Dairy Best Whole Milk 128 Fluid Ounces", "Dairy Best", "128 fl oz", "DAIRY", "C108", "same title, distinct brand"),
    ("Green Field Organic Baby Spinach", "Green Field", "5 oz", "PRODUCE", "C109", "organic preference preserved"),
    ("Green Field Baby Spinach Regular", "Green Field", "5 oz", "PRODUCE", "C110", "nonorganic versus organic"),
    ("Happy Hound Chicken Dry Dog Food", "Happy Hound", "12 lb", "PET", "C111", "pet food versus human food"),
    ("Morning Mill Honey Nut Oat Cereal Family Size", "Morning Mill", "18.8 oz", "BREAKFAST", "C112", "meaningful flavor modifiers"),
    ("Oat Valley Original Oatmilk", "Oat Valley", "64 fl oz", "DAIRY_ALT", "C113", "oat milk versus dairy milk"),
    ("Meadow Vale Organic Whole Milk", "Meadow Vale", "64 fl oz", "DAIRY", "C114", "organic dairy identity"),
    ("Sunny Farm Large Brown Eggs Dozen", "Sunny Farm", "12 count", "DAIRY", "C115", "count normalization"),
    ("Sunny Farm Organic Brown Eggs", "Sunny Farm", "12 ct", "DAIRY", "C116", "organic eggs"),
    ("Nut House Creamy PB", "Nut House", "2 x 8 oz", "PANTRY", "C117", "multipack equals sixteen ounces"),
    ("Nut House Crunchy Peanut Butter", "Nut House", "16 oz", "PANTRY", "C118", "texture changes identity"),
    ("Cultured Farms Strawberry Yogurt Cup", "Cultured Farms", "6 oz", "DAIRY", "C119", "flavor modifier"),
    ("Cultured Farms Greek Yogurt Plain", "Cultured Farms", "2 lb", "DAIRY", "C120", "pounds to ounces"),
    ("Dairy Best Cheddar Block", "Dairy Best", "8 oz", "DAIRY", "C121", "block versus shredded"),
    ("Dairy Best Shredded Cheddar", "Dairy Best", "8 oz", "DAIRY", "C122", "shredded versus block"),
    ("Farmhouse 80 Lean Ground Beef", "Farmhouse", "1 lb", "MEAT", "C123", "ground beef versus broth"),
    ("Heritage Beef Broth", "Heritage", "32 fl oz", "PANTRY", "C124", "fluid broth versus meat"),
    ("Green Field Organic Gala Apples", "Green Field", "3 lb", "PRODUCE", "C125", "organic produce"),
    ("North Orchard Frozen Blueberries", "North Orchard", "1 lb", "FROZEN", "C127", "frozen versus fresh"),
    ("Golden Grove Extra Virgin Olive Oil", "Golden Grove", "16.9 fl oz", "PANTRY", "C135", "fluid volume not weight"),
    ("Cold Meadow Vanilla Frozen Yogurt", "Cold Meadow", "48 fl oz", "FROZEN", "C140", "frozen yogurt versus ice cream"),
]

ABSTAINS = [
    ("Tuna", "", "", "SEAFOOD", "missing brand, size, and form"),
    ("Whole Milk", "", "128 fl oz", "DAIRY", "identical title across brands"),
    ("Baby Spinach", "Green Field", "0 oz", "PRODUCE", "zero size and organic ambiguity"),
    ("Chicken Dinner", "Mystery Brand", "12 oz", "PET", "unrelated pet product token overlap"),
    ("Salmon", "Harbor Table", "", "SEAFOOD", "fresh versus canned ambiguity"),
    ("Cooking Oil", "Golden Grove", "", "PANTRY", "olive versus canola ambiguity"),
    ("Vanilla Frozen Dessert", "Cold Meadow", "48 fl oz", "FROZEN", "ice cream versus frozen yogurt ambiguity"),
    ("Peanut Butter", "Nut House", "16 oz", "PANTRY", "creamy versus crunchy ambiguity"),
    ("Blueberries", "North Orchard", "", "PRODUCE", "fresh versus frozen ambiguity"),
    ("Sandwich Bread", "Daily Loaf", "20 oz", "BAKERY", "white versus wheat ambiguity"),
]


def product_dict(row):
    keys = ("canonical_id", "name", "brand", "category", "type", "form", "organic", "size_value", "size_unit")
    return dict(zip(keys, row))


def build_fixtures():
    catalog = [product_dict(row) for row in CATALOG]
    products = {item[0]: product_dict(item) for item in CATALOG}
    listings = []
    truth = []
    listing_number = 1

    # One deliberately straightforward listing per canonical product.
    for index, product in enumerate(catalog):
        listing_id = f"L{listing_number:03d}"
        listings.append({
            "listing_id": listing_id,
            "retailer": RETAILERS[index % len(RETAILERS)],
            "raw_name": product["name"],
            "brand_raw": product["brand"],
            "size_raw": f'{product["size_value"]} {product["size_unit"]}',
            "retailer_category": product["category"],
            "price_cents": 199 + index * 37,
        })
        truth.append({"listing_id": listing_id, "expected": product["canonical_id"], "note": "straightforward control"})
        listing_number += 1

    # Authored difficult cases with independently specified expected IDs.
    for index, (name, brand, size, category, expected, note) in enumerate(TRICKY):
        listing_id = f"L{listing_number:03d}"
        listings.append({
            "listing_id": listing_id,
            "retailer": RETAILERS[(index + 1) % len(RETAILERS)],
            "raw_name": name,
            "brand_raw": brand,
            "size_raw": size,
            "retailer_category": category,
            "price_cents": 249 + index * 41,
        })
        truth.append({"listing_id": listing_id, "expected": expected, "note": note})
        listing_number += 1

    # Add additional deterministic retailer variants until there are 80 matches.
    variant_index = 0
    while len(listings) < 80:
        product = catalog[variant_index % len(catalog)]
        listing_id = f"L{listing_number:03d}"
        listings.append({
            "listing_id": listing_id,
            "retailer": RETAILERS[(variant_index + 2) % len(RETAILERS)],
            "raw_name": f'{product["brand"]} {product["name"]}',
            "brand_raw": product["brand"],
            "size_raw": f'{product["size_value"]} {product["size_unit"]}',
            "retailer_category": product["category"],
            "price_cents": 299 + variant_index * 29,
        })
        truth.append({"listing_id": listing_id, "expected": product["canonical_id"], "note": "cross-retailer duplicate identity"})
        listing_number += 1
        variant_index += 1

    for index, (name, brand, size, category, note) in enumerate(ABSTAINS):
        listing_id = f"L{listing_number:03d}"
        listings.append({
            "listing_id": listing_id,
            "retailer": RETAILERS[index % len(RETAILERS)],
            "raw_name": name,
            "brand_raw": brand,
            "size_raw": size,
            "retailer_category": category,
            "price_cents": 499 + index * 31,
        })
        truth.append({"listing_id": listing_id, "expected": "ABSTAIN", "note": note})
        listing_number += 1

    return catalog, listings, truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("fixtures"))
    args = parser.parse_args()
    catalog, listings, truth = build_fixtures()
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, records in (
        ("catalog.json", catalog),
        ("listings.json", listings),
        ("ground_truth.json", truth),
    ):
        (args.output / filename).write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"generated catalog={len(catalog)} listings={len(listings)} truth={len(truth)}")


if __name__ == "__main__":
    main()

