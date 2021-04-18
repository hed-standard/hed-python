import os
import shutil
import unittest
from unittest import mock
from flask import Flask, current_app
from hedweb.app_factory import AppFactory, spreadsheet


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
        self.assertRaises(TypeError, spreadsheet.generate_input_from_spreadsheet_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_spreadsheet")

    def test_spreadsheet_process(self):
        from hedweb.spreadsheet import spreadsheet_process
        from hed.util.exceptions import HedFileError
        arguments = {'spreadsheet-path': ''}
        try:
            a = spreadsheet_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('spreadsheet_process threw the wrong exception when spreadsheet-path was empty')
        else:
            self.fail('spreadsheet_process should have thrown a HedFileError exception when spreadsheet-path was empty')

    # def test_dictionary_convert(self):
    #     from hed.hedweb.dictionary import dictionary_convert
    #     json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
    #     schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    #     arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED 7.1.2.xml',
    #                  'json-path': json_path, 'json-file': 'good_events.json'}
    #     with self.app.app_context():
    #         response = dictionary_convert(arguments)
    #         headers = dict(response.headers)
    #         self.assertEqual('warning', headers['Category'], "dictionary_convert issue warning if unsuccessful")
    #         self.assertTrue(response.data, "good_events should not convert using HED 7.1.2.xml")
    #
    #     schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
    #     arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED8.0.0-alpha.1.xml',
    #                  'json-path': json_path, 'json-file': 'good_events.json'}
    #     with self.app.app_context():
    #         response = dictionary_convert(arguments)
    #         headers = dict(response.headers)
    #         self.assertEqual('success', headers['Category'], "dictionary_convert should return success if converted")

    def test_spreadsheet_validate(self):
        from hedweb.spreadsheet import spreadsheet_validate
        spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        prefix_dict = {3: "Event/Long name/", 2: "Event/Label/", 4:"Event/Description/"}
        arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED 7.1.2.xml',
                     'spreadsheet-path': spreadsheet_path, 'spreadsheet-file': 'ExcelMultipleSheets.xlsx',
                     'worksheet-selected': 'LKT Events', 'has-column-names': True,
                     'tag_columns': [5], 'column-prefix-dictionary': prefix_dict}

        with self.app.app_context():
            response = spreadsheet_validate(arguments)
            headers = dict(response.headers)
            self.assertEqual('success', headers['Category'], "spreadsheet_validate should return success if converted")
            self.assertFalse(response.data, "ExcelMultipleSheets should validate using HED 7.1.2.xml")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments['hed-xml-file'] = schema_path
        arguments['hed-display-name'] = 'HED8.0.0-alpha.1.xml'
        with self.app.app_context():
            response = spreadsheet_validate(arguments)
            headers = dict(response.headers)
            self.assertEqual('warning', headers['Category'], "spreadsheet_validate issues warning if validation errors")
            self.assertTrue(response.data, "ExcelMultipleSheets should validate using HED 7.1.2.xml")


if __name__ == '__main__':
    unittest.main()
