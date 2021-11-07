import unittest
import os
import io

from hed import HedInput, Sidecar, EventsInput
import shutil
from hed import schema
from hed import HedValidator

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/tests_output/")
        os.makedirs(cls.base_output_folder, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_missing_column_name_issue(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/validator_tests/bids_events_bad_column_name.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/validator_tests/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = EventsInput(events_path, sidecars=sidecar)

        validation_issues = input_file.validate_file_sidecars(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 1)

    def test_expand_column_issues(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/validator_tests/bids_events_bad_category_key.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/validator_tests/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = EventsInput(events_path, sidecars=sidecar)

        validation_issues = input_file.validate_file_sidecars(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 1)


if __name__ == '__main__':
    unittest.main()
