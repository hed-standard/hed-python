import unittest
import os

from hed.util.column_def_group import ColumnDefGroup
from hed.util.column_definition import ColumnDef
from hed.util.exceptions import HedFileError
from hed import schema

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "HED8.0.0-alpha.1.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.json_filename = os.path.join(cls.base_data_dir, "both_types_events.json")
        cls.json_def_filename = os.path.join(cls.base_data_dir, "both_types_events_with_defs.json")
        cls.default_sidecar = ColumnDefGroup(cls.json_filename)
        cls.json_def_sidecar = ColumnDefGroup(cls.json_def_filename)

    def test_invalid_filenames(self):
        # Handle missing or invalid files.
        invalid_json = "invalidxmlfile.json"
        json_dict = None
        try:
            json_dict = ColumnDefGroup(invalid_json)
        except HedFileError as e:
            pass

        self.assertFalse(json_dict)

        json_dict = None
        try:
            json_dict = ColumnDefGroup(None)
        except HedFileError as e:
            pass
        self.assertTrue(len(json_dict._column_settings) == 0)

        json_dict = None
        try:
            json_dict = ColumnDefGroup("")
        except HedFileError as e:
            pass
        self.assertTrue(len(json_dict._column_settings) == 0)

    def test_display_filename(self):
        invalid_json = "invalidxmlfile.json"
        display_filename = "PrettyDisplayName.json"
        try:
            json_dict = ColumnDefGroup(invalid_json)
            self.assertTrue(False)
        except HedFileError as e:
            self.assertTrue(display_filename in e.format_error_message(return_string_only=True,
                                                                       display_filename=display_filename))

    def test_add_json_string(self):
        with open(self.json_filename, "r") as fp:
            input_string = fp.read()
            json_file = ColumnDefGroup(json_string=input_string)
            self.assertTrue(json_file)


    def test__iter__(self):
        columns_target = 3
        columns_count = 0
        for column_def in self.default_sidecar:
            self.assertIsInstance(column_def, ColumnDef)
            columns_count += 1

        self.assertEqual(columns_target, columns_count)

    # def save_as_json(self, save_filename):
    #
    # def add_json_file_defs(self, json_filename):
    #
    # @staticmethod
    # def load_multiple_json_files(json_file_input_list):
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
    # def validate_entries(self, hed_schema=None, display_filename=None):
    #

    def test_validate_column_group(self):
        validation_issues = self.json_def_sidecar.validate_entries(hed_schema=self.hed_schema)
        self.assertEqual(len(validation_issues), 0)

        validation_issues = self.default_sidecar.validate_entries(hed_schema=self.hed_schema)
        self.assertEqual(len(validation_issues), 0)

if __name__ == '__main__':
    unittest.main()
