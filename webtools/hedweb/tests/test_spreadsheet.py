import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
from hedweb.tests.test_web_base import TestWebBase
import hed.schema as hedschema
from hed import models
from hedweb.constants import common


class Test(TestWebBase):
    def test_get_input_from_spreadsheet_form_empty(self):
        from hedweb.spreadsheet import get_input_from_spreadsheet_form
        self.assertRaises(TypeError, get_input_from_spreadsheet_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_spreadsheet")

    def test_get_input_from_spreadsheet_form(self):
        from hed.models import HedInput
        from hed.schema import HedSchema
        from hedweb.spreadsheet import get_input_from_spreadsheet_form
        with self.app.test:
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/ExcelOneSheet.xlsx')
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/HED8.0.0.xml')
            with open(spreadsheet_path, 'rb') as fp:
                with open(schema_path, 'rb') as sp:
                    environ = create_environ(data={common.SPREADSHEET_FILE: fp,
                                                   common.SCHEMA_VERSION: common.OTHER_VERSION_OPTION,
                                                   common.SCHEMA_PATH: sp,
                                                   'column_5_check': 'on', 'column_5_input': '',
                                                   common.WORKSHEET_SELECTED: 'LKT 8HED3',
                                                   common.HAS_COLUMN_NAMES: 'on',
                                                   common.COMMAND_OPTION: common.COMMAND_VALIDATE})

            request = Request(environ)
            arguments = get_input_from_spreadsheet_form(request)
            self.assertIsInstance(arguments[common.SPREADSHEET], HedInput,
                                  "generate_input_from_spreadsheet_form should have an events object")
            self.assertIsInstance(arguments[common.SCHEMA], HedSchema,
                                  "generate_input_from_spreadsheet_form should have a HED schema")
            self.assertEqual(common.COMMAND_VALIDATE, arguments[common.COMMAND],
                             "generate_input_from_spreadsheet_form should have a command")
            self.assertEqual('LKT 8HED3', arguments[common.WORKSHEET_NAME],
                             "generate_input_from_spreadsheet_form should have a sheet_name name")
            self.assertTrue(arguments[common.HAS_COLUMN_NAMES],
                            "generate_input_from_spreadsheet_form should have column names")

    def test_spreadsheet_process_empty_file(self):
        from hedweb.constants import common
        from hedweb.spreadsheet import spreadsheet_process
        from hed.errors.exceptions import HedFileError
        arguments = {common.SPREADSHEET: None}
        try:
            spreadsheet_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('spreadsheet_process threw the wrong exception when spreadsheet-path was empty')
        else:
            self.fail('spreadsheet_process should have thrown a HedFileError exception when spreadsheet-path was empty')

    def test_spreadsheet_process_validate_invalid(self):
        from hedweb.spreadsheet import spreadsheet_process
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4: "Event/Description/"}
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT Events',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary=prefix_dict,
                                      name=spreadsheet_path)
        arguments = {common.SCHEMA: hed_schema, common.SPREADSHEET: spreadsheet,
                     common.COMMAND: common.COMMAND_VALIDATE, common.CHECK_FOR_WARNINGS_VALIDATE: True}
        with self.app.app_context():
            results = spreadsheet_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'spreadsheet_process validate should return a dictionary when errors')
            self.assertEqual('warning', results['msg_category'],
                             'spreadsheet_process validate should give warning when spreadsheet has errors')
            self.assertTrue(results['data'],
                            'spreadsheet_process validate should return validation errors using HED 8.0.0-beta.1')

    def test_spreadsheet_process_validate_valid(self):
        from hedweb.spreadsheet import spreadsheet_process
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4: "Event/Description/"}
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT Events',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary=prefix_dict,
                                      name=spreadsheet_path)
        arguments = {common.SCHEMA: hed_schema, common.SPREADSHEET: spreadsheet,
                     common.COMMAND: common.COMMAND_VALIDATE, common.CHECK_FOR_WARNINGS_VALIDATE: True}
        arguments[common.SCHEMA] = hed_schema

        with self.app.app_context():
            results = spreadsheet_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'spreadsheet_process should return a dict when no errors')
            self.assertEqual('success', results['msg_category'],
                             'spreadsheet_process should return success if validated')

    def test_spreadsheet_validate_valid_excel(self):
        from hedweb.spreadsheet import spreadsheet_validate
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4: "Event/Description/"}
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT Events',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary=prefix_dict,
                                      name=spreadsheet_path)
        with self.app.app_context():
            results = spreadsheet_validate(hed_schema, spreadsheet)
            self.assertFalse(results['data'],
                             'spreadsheet_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results["msg_category"],
                             'spreadsheet_validate msg_category should be success when no errors')

    def test_spreadsheet_validate_valid_excel1(self):
        from hedweb.spreadsheet import spreadsheet_validate
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        prefix_dict = {2: "Property/Informational-property/Label/", 4: "Property/Informational-property/Description/"}
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT 8HED3',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary=prefix_dict,
                                      name=spreadsheet_path)
        with self.app.app_context():
            results = spreadsheet_validate(hed_schema, spreadsheet)
            self.assertFalse(results['data'],
                             'spreadsheet_validate results should have empty data when no errors')
            self.assertEqual('success', results['msg_category'],
                             'spreadsheet_validate msg_category should be success when no errors')

    def test_spreadsheet_validate_invalid_excel(self):
        from hedweb.spreadsheet import spreadsheet_validate
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        prefix_dict = {2: "Property/Informational-property/Label/", 4: "Property/Informational-property/Description/"}
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT 8HED3',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary=prefix_dict,
                                      name=spreadsheet_path)
        with self.app.app_context():
            results = spreadsheet_validate(hed_schema, spreadsheet)
            self.assertTrue(results['data'],
                            'spreadsheet_validate results should have empty data when errors')
            self.assertEqual('warning', results['msg_category'],
                             'spreadsheet_validate msg_category should be warning when no errors')


if __name__ == '__main__':
    unittest.main()
