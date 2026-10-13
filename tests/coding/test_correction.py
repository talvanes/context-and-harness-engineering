import unittest

from normalize_names import normalize_names


class CorrectionTests(unittest.TestCase):
    def test_skips_none_and_preserves_unaffected_behavior(self):
        values = [" Alice ", None, "ALICE", None, " Bob ", ""]
        before = values.copy()
        self.assertEqual(normalize_names(values), ["Alice", "ALICE", "Bob"])
        self.assertEqual(values, before)


if __name__ == "__main__":
    unittest.main()
