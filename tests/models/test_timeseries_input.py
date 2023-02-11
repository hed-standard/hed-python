import unittest
import os
import shutil

from hed.models import TimeseriesInput

# TODO: Add tests about correct handling of 'n/a'


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_output_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/tests_output/"))
        cls.base_output_folder = base_output_folder
        os.makedirs(base_output_folder, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_constructor(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header.tsv')
        input_file = TimeseriesInput(events_path)
        self.assertIsInstance(input_file, TimeseriesInput, "TimeseriesInput constructor creates a timeseries object")


if __name__ == '__main__':
    unittest.main()
