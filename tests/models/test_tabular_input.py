import unittest
import os
import shutil

from hed.models import DefinitionEntry, Sidecar, TabularInput
from hed import schema
from hed.validator import HedValidator
from hed.errors import HedFileError


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        os.makedirs(base_output_folder, exist_ok=True)

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../data/bids/eeg_ds003654s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../data/schema_test_data/HED8.0.0.xml'))
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

        cls.hed_schema = schema.load_schema(schema_path)
        sidecar1 = Sidecar(json_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.base_output_folder = base_output_folder

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_get_definitions(self):
        defs1 = self.input_data.get_definitions().gathered_defs
        self.assertIsInstance(defs1, dict, "get_definitions returns dictionary by default")
        self.assertEqual(len(defs1), 17, "get_definitions should have the right number of definitions")
        for key, value in defs1.items():
            self.assertIsInstance(key, str, "get_definitions dictionary keys should be strings")
            self.assertIsInstance(value, DefinitionEntry,
                                  "get_definitions dict values should be strings when as strings")
        defs2 = self.input_data.get_definitions(as_strings=False).gathered_defs
        self.assertIsInstance(defs2, dict, "get_definitions returns dictionary by when not as strings")
        self.assertEqual(len(defs2), 17, "get_definitions should have the right number of definitions when not strings")
        for key, value in defs2.items():
            self.assertIsInstance(key, str, "get_definitions dictionary keys should be strings")
            self.assertIsInstance(value, DefinitionEntry,
                                  "get_definitions dictionary values should be strings when as strings")
        self.assertIsInstance(defs2, dict, "get_definitions returns DefinitionDict when not as strings")

    def test_missing_column_name_issue(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_bad_column_name.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate_sidecar(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 1)

    def test_expand_column_issues(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_bad_category_key.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        # Fix whatever is wrong with onset tag here.  It's thinking Description/Onset continues is an invalid tag???'
        validation_issues = input_file.validate_sidecar(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 1)

    def test_blank_and_duplicate_columns(self):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "../data/model_tests/blank_column_name.tsv")

        with self.assertRaises(HedFileError):
            _ = TabularInput(filepath)

        # todo: add back in when we do this check
        # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
        # "../data/model_tests/duplicate_column_name.tsv")
        #
        # with self.assertRaises(HedFileError):
        #     _ = TabularInput(filepath)


if __name__ == '__main__':
    unittest.main()
