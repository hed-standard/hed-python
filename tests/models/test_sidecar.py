import unittest
import os
import io
import shutil

from hed.errors import HedFileError, ValidationErrors, ErrorSeverity
from hed.models import ColumnMetadata, HedString, Sidecar
from hed import schema
from hed.models import DefinitionDict, DefinitionEntry
from hed.errors import ErrorHandler


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.base_data_dir = base_data_dir
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        json_filename = os.path.join(base_data_dir, "sidecar_tests/both_types_events.json")
        cls.json_filename = json_filename
        json_def_filename = os.path.join(base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        cls.json_def_filename = json_def_filename
        json_without_definitions_filename = \
            os.path.join(base_data_dir, "sidecar_tests/both_types_events_without_definitions.json")
        json_errors_filename = os.path.join(base_data_dir, "sidecar_tests/json_errors.json")
        json_errors_filename_minor = os.path.join(base_data_dir, "sidecar_tests/json_errors_minor.json")
        cls.default_sidecar = Sidecar(json_filename)
        cls.json_def_sidecar = Sidecar(json_def_filename)
        cls.errors_sidecar = Sidecar(json_errors_filename)
        cls.errors_sidecar_minor = Sidecar(json_errors_filename_minor)
        cls.json_without_definitions_sidecar = Sidecar(json_without_definitions_filename)

        base_output_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/tests_output/"))
        cls.base_output_folder = base_output_folder
        os.makedirs(base_output_folder, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_file_not_found(self):
        with self.assertRaises(HedFileError):
            Sidecar('nonexistent_file.json')

    def test_invalid_input_type_int(self):
        with self.assertRaises(HedFileError):
            Sidecar(123)

    def test_invalid_input_type_dict(self):
        with self.assertRaises(HedFileError):
            Sidecar({'key': 'value'})

    def test_invalid_filenames(self):
        # Handle missing or invalid files.
        invalid_json = "invalidxmlfile.json"
        self.assertRaises(HedFileError, Sidecar, invalid_json)

        json_dict = None
        try:
            json_dict = Sidecar(None)
        except HedFileError:
            pass
        self.assertTrue(len(json_dict.loaded_dict) == 0)

        json_dict = None
        try:
            json_dict = Sidecar("")
        except HedFileError:
            pass
        self.assertTrue(len(json_dict.loaded_dict) == 0)

    def test_name(self):
        invalid_json = "invalidxmlfile.json"
        with self.assertRaises(HedFileError) as context:
            Sidecar(invalid_json)
        self.assertEqual(context.exception.args[0], 'fileNotFound')

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
        validation_issues = self.errors_sidecar.validate(self.hed_schema)
        self.assertEqual(len(validation_issues), 4)

        validation_issues2 = self.errors_sidecar_minor.validate(self.hed_schema)
        self.assertEqual(len(validation_issues2), 1)

        validation_issues = self.json_without_definitions_sidecar.validate(self.hed_schema)
        self.assertEqual(len(validation_issues), 7)

        hed_string = HedString("(Definition/JsonFileDef/#, (Item/JsonDef1/#,Item/JsonDef1))", self.hed_schema)
        extra_def_dict = DefinitionDict()
        extra_def_dict.check_for_definitions(hed_string)

        validation_issues2 = self.json_without_definitions_sidecar.validate(self.hed_schema,
                                                                            extra_def_dicts=extra_def_dict)
        # this removes one undef matched error
        self.assertEqual(len(validation_issues2), 7)

    def test_duplicate_def(self):
        sidecar = self.json_def_sidecar
        # If external defs are the same, no error
        duplicate_dict = sidecar.extract_definitions(hed_schema=self.hed_schema)
        issues = sidecar.validate(self.hed_schema, extra_def_dicts=duplicate_dict, error_handler=ErrorHandler(False))
        self.assertEqual(len(issues), 2)
        errors = [issue for issue in issues if issue['severity'] < ErrorSeverity.WARNING]
        self.assertEqual(len(errors), 0)
        test_dict = {"jsonfiledef3": DefinitionEntry("jsonfiledef3", None, False, None)}
        issues2 = sidecar.validate(self.hed_schema, extra_def_dicts=test_dict, error_handler=ErrorHandler(False))
        self.assertEqual(len(issues2), 3)
        errors = [issue for issue in issues2 if issue['severity'] < ErrorSeverity.WARNING]
        self.assertEqual(len(errors), 1)
        self.assertTrue(issues2[0]['code'], ValidationErrors.DEFINITION_INVALID)

    def test_save_load(self):
        sidecar = Sidecar(self.json_def_filename)
        save_filename = os.path.join(self.base_output_folder, "test_sidecar_save.json")
        sidecar.save_as_json(save_filename)

        reloaded_sidecar = Sidecar(save_filename)

        for data1, data2 in zip(sidecar, reloaded_sidecar):
            self.assertEqual(data1.source_dict, data2.source_dict)

    def test_save_load2(self):
        sidecar = Sidecar(self.json_def_filename)
        json_string = sidecar.get_as_json_string()

        reloaded_sidecar = Sidecar(io.StringIO(json_string))

        for data1, data2 in zip(sidecar, reloaded_sidecar):
            self.assertEqual(data1.source_dict, data2.source_dict)

    def test_merged_sidecar(self):
        base_folder = self.base_data_dir + "sidecar_tests/"
        combined_sidecar_json = base_folder + "test_merged_merged.json"
        sidecar_json1 = base_folder + "test_merged1.json"
        sidecar_json2 = base_folder + "test_merged2.json"

        sidecar = Sidecar([sidecar_json1, sidecar_json2])
        sidecar2 = Sidecar(combined_sidecar_json)

        self.assertEqual(sidecar.loaded_dict, sidecar2.loaded_dict)

    def test_set_hed_strings(self):
        from hed.models import df_util
        sidecar = Sidecar(os.path.join(self.base_data_dir, "sidecar_tests/short_tag_test.json"))

        for column_data in sidecar:
            hed_strings = column_data.get_hed_strings()
            df_util.convert_to_form(hed_strings, self.hed_schema, "long_tag")
            column_data.set_hed_strings(hed_strings)
        sidecar_long = Sidecar(os.path.join(self.base_data_dir, "sidecar_tests/long_tag_test.json"))
        self.assertEqual(sidecar.loaded_dict, sidecar_long.loaded_dict)

        sidecar = Sidecar(os.path.join(self.base_data_dir, "sidecar_tests/long_tag_test.json"))

        for column_data in sidecar:
            hed_strings = column_data.get_hed_strings()
            df_util.convert_to_form(hed_strings, self.hed_schema, "short_tag")
            column_data.set_hed_strings(hed_strings)
        sidecar_short = Sidecar(os.path.join(self.base_data_dir, "sidecar_tests/short_tag_test.json"))
        self.assertEqual(sidecar.loaded_dict, sidecar_short.loaded_dict)


if __name__ == '__main__':
    unittest.main()
