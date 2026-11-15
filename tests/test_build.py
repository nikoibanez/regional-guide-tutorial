import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import identity, merge_records, normalize, normalized_url, SOURCES


class DirectoryTests(unittest.TestCase):
    def test_state_and_field_aliases(self):
        rec = normalize({"business": "Sage", "town": "Raton", "region": "New Mexico", "type": "Coffee"}, "sample.csv")
        self.assertEqual((rec["name"], rec["state"], rec["category"]), ("Sage", "NM", "Coffee"))

    def test_duplicates_are_combined(self):
        entries = merge_records(SOURCES)
        self.assertEqual(len(entries), 5)
        sage = next(r for r in entries if r["name"] == "Sage Coffee")
        self.assertEqual(sage["sources"], ["new_mexico.csv", "regional_feed.csv"])
        # First nonempty category wins; we don't pretend Cafe/Coffee were reconciled.
        self.assertEqual(sage["category"], "Cafe")

    def test_missing_required_fields_are_skipped(self):
        self.assertIsNone(normalize({"name": "Missing city", "state": "NM"}, "sample.csv"))

    def test_url_cleanup_keeps_functional_queries(self):
        self.assertEqual(
            normalized_url("https://Example.org/a/?page=2&utm_source=feed"),
            "https://example.org/a?page=2"
        )

    def test_identity_normalizes_whitespace_and_case(self):
        first = {"name": "  SAGE   COFFEE", "city": "Raton", "state": "NM"}
        second = {"name": "sage coffee", "city": "raton", "state": "NM"}
        self.assertEqual(identity(first), identity(second))

    def test_non_string_csv_fields_are_safe(self):
        self.assertIsNone(normalize({"name": None, "city": "Raton", "state": "NM"}, "sample.csv"))


if __name__ == "__main__":
    unittest.main()
