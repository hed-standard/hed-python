import unittest
import os
import io
import shutil

from hed.errors import HedFileError, ValidationErrors
from hed.models import ColumnMetadata, HedString, Sidecar
from hed.validator import HedValidator
from hed import schema
from hed.models import DefinitionDict


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "schema_test_data/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.json_filename = os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events.json")
        cls.json_def_filename = os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        cls.json_without_definitions_filename = \
            os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events_without_definitions.json")
        cls.json_errors_filename = os.path.join(cls.base_data_dir, "sidecar_tests/json_errors.json")
        cls.default_sidecar = Sidecar(cls.json_filename)
        cls.json_def_sidecar = Sidecar(cls.json_def_filename)
        cls.errors_sidecar = Sidecar(cls.json_errors_filename)
        cls.json_without_definitions_sidecar = Sidecar(cls.json_without_definitions_filename)

        cls.base_output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        os.makedirs(cls.base_output_folder, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

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

    def test_validate_column_group(self):
        validator = HedValidator(hed_schema=None)
        validation_issues = self.json_def_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 0)

        validation_issues = self.default_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 0)

        validation_issues = self.errors_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 15)

        validation_issues = self.json_without_definitions_sidecar.validate_entries(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 1)

        hed_string = HedString("(Definition/JsonFileDef/#, (Item/JsonDef1/#,Item/JsonDef1))")
        extra_def_dict = DefinitionDict()
        hed_string.validate(extra_def_dict)

        validation_issues = self.json_without_definitions_sidecar.validate_entries(validator, check_for_warnings=True,
                                                                                   extra_def_dicts=extra_def_dict)
        self.assertEqual(len(validation_issues), 0)

    def test_duplicate_def(self):
        sidecar = self.json_def_sidecar
        def_dicts = sidecar.get_def_dicts()

        issues = sidecar.validate_entries(extra_def_dicts=def_dicts)
        self.assertEqual(len(issues), 5)
        self.assertTrue(issues[0]['code'], ValidationErrors.HED_DEFINITION_INVALID)

    def test_save_load(self):
        sidecar = Sidecar(self.json_def_filename)
        save_filename = self.base_output_folder + "test_sidecar_save.json"
        sidecar.save_as_json(save_filename)

        reloaded_sidecar = Sidecar(save_filename)

        for str1, str2 in zip(sidecar.hed_string_iter(), reloaded_sidecar.hed_string_iter()):
            self.assertEqual(str1, str2)

    def test_save_load2(self):
        sidecar = Sidecar(self.json_def_filename)
        json_string = sidecar.get_as_json_string()

        reloaded_sidecar = Sidecar(io.StringIO(json_string))

        for str1, str2 in zip(sidecar.hed_string_iter(), reloaded_sidecar.hed_string_iter()):
            self.assertEqual(str1, str2)

if __name__ == '__main__':
    unittest.main()
