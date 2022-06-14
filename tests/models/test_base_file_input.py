import unittest
import os
import shutil
from hed import Sidecar
from hed import TabularInput
from hed.models import DefinitionDict
# TODO: Add tests for base_file_input and include correct handling of 'n/a'


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # todo: clean up these unit tests/add more
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.json_def_filename = os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        cls.json_def_sidecar = Sidecar(cls.json_def_filename)

        events_path = os.path.join(cls.base_data_dir, '../data/validator_tests/bids_events_with_index.tsv')
        cls.tabular_file = TabularInput(events_path, sidecar=cls.json_def_sidecar)

        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_gathered_defs(self):
        # todo: add unit tests for definitions in tsv file
        defs = DefinitionDict.get_as_strings(self.tabular_file.def_dict)
        expected_defs =     {'jsonfiledef': '(Item/JsonDef1/#,Item/JsonDef1)',
                             'jsonfiledef2': '(Item/JsonDef2/#,Item/JsonDef2)',
                             'jsonfiledef3': '(Item/JsonDef3/#,InvalidTag)',
                             'takesvaluedef': '(Age/#)',
                             'valueclassdef': '(Acceleration/#)'}
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
    #     validation_issues = input_file.validate_file_sidecars(validator)
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
    #     validation_issues = input_file.validate_file_sidecars(validator)
    #     self.assertEqual(len(validation_issues), 0)
    #     validation_issues = input_file.validate_file(validator, check_for_warnings=True)
    #     self.assertEqual(len(validation_issues), 1)


if __name__ == '__main__':
    unittest.main()
