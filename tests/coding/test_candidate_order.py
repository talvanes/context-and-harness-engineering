import unittest
from normalize_names import normalize_names

class CandidateOrderTests(unittest.TestCase):
    def test_output_preserves_input_order(self):
        self.assertEqual(normalize_names(["Zoe", "Ada"]), ["Zoe", "Ada"])

if __name__ == "__main__":
    unittest.main()
