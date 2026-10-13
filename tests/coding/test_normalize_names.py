import unittest

from normalize_names import normalize_names


class NormalizeNamesInitialTests(unittest.TestCase):
    def test_strips_drops_empty_deduplicates_exact_matches_and_keeps_first_order(self):
        values = [" Alice ", "", "ALICE", " Bob", "bob ", " Carol "]
        self.assertEqual(normalize_names(values), ["Alice", "ALICE", "Bob", "bob", "Carol"])

    def test_case_variants_are_both_preserved(self):
        self.assertEqual(normalize_names(["Ada", "ada"]), ["Ada", "ada"])

    def test_does_not_mutate_input(self):
        values = ["  Alice ", "Bob"]
        before = values.copy()
        normalize_names(values)
        self.assertEqual(values, before)

    def test_empty_input(self):
        self.assertEqual(normalize_names([]), [])


if __name__ == "__main__":
    unittest.main()
