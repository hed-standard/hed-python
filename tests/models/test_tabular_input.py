import unittest
import os
import shutil

from hed.models import DefinitionEntry, Sidecar, TabularInput
from hed import schema
from hed.errors import HedFileError
from hed.errors import ErrorHandler


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        os.makedirs(base_output_folder, exist_ok=True)

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../data/bids_tests/eeg_ds003645s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../data/schema_tests/HED8.0.0.xml'))
        sidecar1_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.events_path = os.path.realpath(
            os.path.join(bids_root_path, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar2_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                      '../data/remodel_tests/task-FacePerceptionSmall_events.json'))
        cls.hed_schema = schema.load_schema(schema_path)
        cls.sidecar1 = Sidecar(sidecar1_path, name='face_sub1_json')
        cls.sidecar2 = Sidecar(sidecar2_path, name='face_small_json')
        cls.base_output_folder = base_output_folder

        cls.invalid_inputs = [123, {'key': 'value'}, 'nonexistent_file.tsv']

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_missing_column_name_issue(self):
        events_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../data/validator_tests/bids_events_bad_column_name.tsv'))
        json_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  "../data/validator_tests/bids_events.json"))
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(hed_schema=self.hed_schema)
        self.assertEqual(len(validation_issues), 1)

    def test_expand_column_issues(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_bad_category_key.tsv')
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(hed_schema=self.hed_schema)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(hed_schema=self.hed_schema)
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

    def test_validate_file_warnings(self):
        issues1 = self.sidecar1.validate(hed_schema=self.hed_schema)
        input_file1 = TabularInput(self.events_path, sidecar=self.sidecar1)
        issues1a = input_file1.validate(hed_schema=self.hed_schema)

        issues2 = self.sidecar1.validate(hed_schema=self.hed_schema, error_handler=ErrorHandler(False))
        input_file2 = TabularInput(self.events_path, sidecar=self.sidecar2)
        issues2a = input_file2.validate(hed_schema=self.hed_schema, error_handler=ErrorHandler(False))

    def test_invalid_file(self):
        for invalid_input in self.invalid_inputs:
            with self.subTest(input=invalid_input):
                with self.assertRaises(HedFileError):
                    TabularInput(file=invalid_input)

    def test_invalid_sidecar(self):
        for invalid_input in self.invalid_inputs:
            with self.subTest(input=invalid_input):
                with self.assertRaises(HedFileError):
                    # Replace 'valid_path.tsv' with a path to an existing .tsv file
                    TabularInput(file=self.events_path, sidecar=invalid_input)


if __name__ == '__main__':
    unittest.main()
