import unittest
import os
import io

from hed import Sidecar, HedFileError, HedValidator, schema
from hed.models.column_metadata import ColumnMetadata


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "hed_pairs/HED8.0.0.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.json_filename = os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events.json")
        cls.json_def_filename = os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        cls.json_errors_filename = os.path.join(cls.base_data_dir, "sidecar_tests/json_errors.json")
        cls.default_sidecar = Sidecar(cls.json_filename)
        cls.json_def_sidecar = Sidecar(cls.json_def_filename)
        cls.errors_sidecar = Sidecar(cls.json_errors_filename)

    def test_invalid_filenames(self):
        # Handle missing or invalid files.
        invalid_json = "invalidxmlfile.json"
        self.assertRaises(HedFileError, Sidecar, invalid_json)

        json_dict = None
        try:
            json_dict = Sidecar(None)
        except HedFileError:
            pass
        self.assertTrue(len(json_dict._column_data) == 0)

        json_dict = None
        try:
            json_dict = Sidecar("")
        except HedFileError:
            pass
        self.assertTrue(len(json_dict._column_data) == 0)

    def test_name(self):
        invalid_json = "invalidxmlfile.json"
        name = "PrettyDisplayName.json"
        try:
            json_dict = Sidecar(invalid_json)
            self.assertTrue(False)
        except HedFileError as e:
            self.assertTrue(name in e.format_error_message(return_string_only=True, name=name))

    def test_add_json_string(self):
        with open(self.json_filename) as file:
            file_as_string = io.StringIO(file.read())
            json_file = Sidecar(file_as_string)
            self.assertTrue(json_file)

    def test__iter__(self):
        columns_target = 3
        columns_count = 0
        for column_data in self.default_sidecar:
            self.assertIsInstance(column_data, ColumnMetadata)
            columns_count += 1

        self.assertEqual(columns_target, columns_count)

    # todo: fill out these tests.
    # def save_as_json(self, save_filename):
    #
    # def add_sidecars(self, json_filename):
    #
    # @staticmethod
    # def load_multiple_sidecars(json_file_input_list):
    #
    # def hed_string_iter(self, include_position=False):
    #
    #
    # def set_hed_string(self, new_hed_string, position):
    #
    #
    # def _add_single_col_type(self, column_name, dict_for_entry, column_type=None):
    #
    # def get_validation_issues(self):
    #
    # def validate_entries(self, hed_schema=None, name=None):
    #

    def test_validate_column_group(self):
        validator = HedValidator(hed_schema=None)
        validation_issues = self.json_def_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 0)

        validation_issues = self.default_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 0)

        validation_issues = self.errors_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 15)


if __name__ == '__main__':
    unittest.main()
