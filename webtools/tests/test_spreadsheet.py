import os
import shutil
import unittest

import hed.schema as hedschema
from hed import models
from hedweb.constants import common

from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hedweb.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_generate_input_from_spreadsheet_form(self):
        from hedweb.spreadsheet import get_input_from_spreadsheet_form
        self.assertRaises(TypeError, get_input_from_spreadsheet_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_spreadsheet")

    def test_spreadsheet_process_empty_file(self):
        from hedweb.constants import common
        from hedweb.spreadsheet import spreadsheet_process
        from hed.errors.exceptions import HedFileError
        arguments = {common.SPREADSHEET: None}
        try:
            a = spreadsheet_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('spreadsheet_process threw the wrong exception when spreadsheet-path was empty')
        else:
            self.fail('spreadsheet_process should have thrown a HedFileError exception when spreadsheet-path was empty')

    def test_spreadsheet_process(self):
        from hedweb.spreadsheet import spreadsheet_process
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4: "Event/Description/"}
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT Events',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary= prefix_dict,
                                      display_name=spreadsheet_path)
        arguments = {common.SCHEMA: hed_schema, common.SPREADSHEET: spreadsheet,
                     common.COMMAND: common.COMMAND_VALIDATE, common.CHECK_FOR_WARNINGS: True}
        with self.app.app_context():
            results = spreadsheet_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'spreadsheet_process validate should return a dictionary when errors')
            self.assertEqual('warning', results['msg_category'],
                             'spreadsheet_process validate should give warning when spreadsheet has errors')
            self.assertTrue(results['data'],
                            'spreadsheet_process should validate using HED 8.0.0-beta.1')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        arguments[common.SCHEMA] = hed_schema

        with self.app.app_context():
            results = spreadsheet_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'spreadsheet_process should return a dict when no errors')
            self.assertEqual('success', results['msg_category'],
                             'spreadsheet_process should return success if converted')

    def test_spreadsheet_validate(self):
        from hedweb.spreadsheet import spreadsheet_validate
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4: "Event/Description/"}
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        spreadsheet = models.HedInput(spreadsheet_path,
                                      worksheet_name='LKT Events',
                                      tag_columns=[5],
                                      has_column_names=True,
                                      column_prefix_dictionary=prefix_dict,
                                      display_name=spreadsheet_path)
        with self.app.app_context():
            results = spreadsheet_validate(hed_schema, spreadsheet)
            self.assertFalse(results['data'],
                             'spreadsheet_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results["msg_category"],
                             'spreadsheet_validate msg_category should be success when no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = spreadsheet_validate(hed_schema, spreadsheet)
            self.assertTrue(results['data'],
                            'spreadsheet_validate results should have a data key when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'spreadsheet_validate msg_category should be warning when errors')


if __name__ == '__main__':
    unittest.main()
