import json

from src.cli import match_command


def test_match_command_outputs_machine_readable_json(tmp_path, capsys):
    catalog = tmp_path / "catalog.json"
    listings = tmp_path / "listings.json"
    catalog.write_text(
        json.dumps(
            [
                {
                    "canonical_id": "C1",
                    "name": "Example Whole Milk",
                    "brand": "Example",
                    "category": "DAIRY",
                    "type": "milk",
                    "form": "liquid",
                    "organic": False,
                    "size_value": 128,
                    "size_unit": "fl oz",
                }
            ]
        )
    )
    listings.write_text(
        json.dumps(
            [
                {
                    "listing_id": "L1",
                    "retailer": "FreshTown",
                    "raw_name": "Example Whole Milk",
                    "brand_raw": "Example",
                    "size_raw": "1 gal",
                    "retailer_category": "DAIRY",
                    "price_cents": 499,
                }
            ]
        )
    )

    assert match_command(catalog, listings) == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["listing_id"] == "L1"
    assert output[0]["canonical_id"] == "C1"
    assert output[0]["normalized_size"]["value"] == 128

