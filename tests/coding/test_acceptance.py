import unittest

from normalize_names import normalize_names


class IndependentAcceptanceTests(unittest.TestCase):
    def test_non_string_entries_raise_type_error(self):
        with self.assertRaises(TypeError):
            normalize_names(["Alice", 7])

    def test_none_is_skipped_before_type_validation(self):
        self.assertEqual(normalize_names([None, " Alice "]), ["Alice"])


if __name__ == "__main__":
    unittest.main()
