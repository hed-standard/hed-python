import os
import unittest

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")


if __name__ == '__main__':
    unittest.main()
