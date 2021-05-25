import os
import shutil
import unittest
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
        from hedweb.spreadsheet import generate_input_from_spreadsheet_form
        self.assertRaises(TypeError, generate_input_from_spreadsheet_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_spreadsheet")

    def test_spreadsheet_process_empty_file(self):
        from hedweb.constants import common
        from hedweb.spreadsheet import spreadsheet_process
        from hed.util.exceptions import HedFileError
        arguments = {common.SPREADSHEET_PATH: ''}
        try:
            a = spreadsheet_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('spreadsheet_process threw the wrong exception when spreadsheet-path was empty')
        else:
            self.fail('spreadsheet_process should have thrown a HedFileError exception when spreadsheet-path was empty')

    def test_spreadsheet_validate(self):
        from hedweb.constants import common
        from hedweb.spreadsheet import spreadsheet_validate
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4: "Event/Description/"}
        arguments = {common.SCHEMA_PATH: schema_path, common.SCHEMA_DISPLAY_NAME: 'HED 7.1.2.xml',
                     common.SPREADSHEET_PATH: spreadsheet_path, common.SPREADSHEET_FILE: 'ExcelMultipleSheets.xlsx',
                     common.WORKSHEET_SELECTED: 'LKT Events', common.HAS_COLUMN_NAMES: True,
                     common.TAG_COLUMNS: [5], common.COLUMN_PREFIX_DICTIONARY: prefix_dict,
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True}

        with self.app.app_context():
            results = spreadsheet_validate(arguments)
            self.assertFalse(results['data'],
                             'spreadsheet_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results["msg_category"],
                             'spreadsheet_validate msg_category should be success when no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments[common.SCHEMA_PATH] = schema_path
        arguments[common.SCHEMA_DISPLAY_NAME] = 'HED8.0.0-alpha.1.xml'
        with self.app.app_context():
            results = spreadsheet_validate(arguments)
            self.assertTrue(results['data'],
                            'spreadsheet_validate results should have a data key when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'spreadsheet_validate msg_category should be warning when errors')


if __name__ == '__main__':
    unittest.main()
