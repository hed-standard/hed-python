import unittest
import os
import shutil
from hed import Sidecar
from hed import BaseInput, TabularInput
from hed.models.def_mapper import DefMapper
from hed.models.column_mapper import ColumnMapper
from hed.models import DefinitionDict
from hed import schema

# TODO: Add tests for base_file_input and include correct handling of 'n/a'


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # todo: clean up these unit tests/add more
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../data/'))
        cls.base_data_dir = base_data_dir
        json_def_filename = os.path.join(base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        # cls.json_def_filename = json_def_filename
        json_def_sidecar = Sidecar(json_def_filename)
        events_path = os.path.join(base_data_dir, '../data/validator_tests/bids_events_no_index.tsv')
        cls.tabular_file = TabularInput(events_path, sidecar=json_def_sidecar)

        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../data/bids_tests/eeg_ds003654s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../data/schema_tests/HED8.0.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

        cls.hed_schema = schema.load_schema(schema_path)
        sidecar1 = Sidecar(json_path, name='face_sub1_json')
        mapper1 = ColumnMapper(sidecar=sidecar1, optional_tag_columns=['HED'], warn_on_missing_column=False)
        cls.input_data1 = BaseInput(events_path, file_type='.tsv', has_column_names=True,
                                    name="face_sub1_events", mapper=mapper1,
                                    definition_columns=['HED'], allow_blank_names=False)
        cls.input_data2 = BaseInput(events_path, file_type='.tsv', has_column_names=True, name="face_sub2_events")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_get_definitions(self):
        defs1 = self.input_data1.get_definitions(as_strings=True)
        self.assertIsInstance(defs1, dict, "get_definitions returns dictionary when as strings")
        self.assertEqual(len(defs1), 17, "get_definitions should have the right number of definitions")

        defs2 = self.input_data1.get_definitions()
        self.assertIsInstance(defs2, DefMapper, "get_definitions returns a DefMapper by default")

        defs3 = self.input_data2.get_definitions(as_strings=False)
        self.assertIsInstance(defs3, DefMapper, "get_definitions returns a DefMapper when not as strings")

    def test_gathered_defs(self):
        # todo: add unit tests for definitions in tsv file
        defs = DefinitionDict.get_as_strings(self.tabular_file.def_dict)
        expected_defs = {
            'jsonfiledef': '(Item/JsonDef1/#,Item/JsonDef1)',
            'jsonfiledef2': '(Item/JsonDef2/#,Item/JsonDef2)',
            'jsonfiledef3': '(Item/JsonDef3/#,InvalidTag)',
            'takesvaluedef': '(Age/#)',
            'valueclassdef': '(Acceleration/#)'
        }
        self.assertEqual(defs, expected_defs)

    # def test_missing_column_name_issue(self):
    #     schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                '../data/validator_tests/bids_schema.mediawiki')
    #     events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                '../data/validator_tests/bids_events_bad_column_name.tsv')
    #
    #     hed_schema = schema.load_schema(schema_path)
    #     json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                              "../data/validator_tests/bids_events.json")
    #     validator = HedValidator(hed_schema=hed_schema)
    #     sidecar = Sidecar(json_path)
    #     issues = sidecar.validate_entries(validator)
    #     self.assertEqual(len(issues), 0)
    #     input_file = TabularInput(events_path, sidecars=sidecar)
    #
    #     validation_issues = input_file.validate_sidecar(validator)
    #     self.assertEqual(len(validation_issues), 0)
    #     validation_issues = input_file.validate_file(validator, check_for_warnings=True)
    #     self.assertEqual(len(validation_issues), 1)
    #
    # def test_expand_column_issues(self):
    #     schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                '../data/validator_tests/bids_schema.mediawiki')
    #     events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                '../data/validator_tests/bids_events_bad_category_key.tsv')
    #
    #     hed_schema = schema.load_schema(schema_path)
    #     json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                              "../data/validator_tests/bids_events.json")
    #     validator = HedValidator(hed_schema=hed_schema)
    #     sidecar = Sidecar(json_path)
    #     issues = sidecar.validate_entries(validator)
    #     self.assertEqual(len(issues), 0)
    #     input_file = TabularInput(events_path, sidecars=sidecar)
    #
    #     validation_issues = input_file.validate_sidecar(validator)
    #     self.assertEqual(len(validation_issues), 0)
    #     validation_issues = input_file.validate_file(validator, check_for_warnings=True)
    #     self.assertEqual(len(validation_issues), 1)


if __name__ == '__main__':
    unittest.main()
