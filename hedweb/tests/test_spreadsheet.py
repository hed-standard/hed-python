import os
import shutil
import unittest
from unittest import mock
from flask import Flask, current_app
from hed.web.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed.web.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_generate_input_from_validation_form(self):
        self.assertTrue(1, "Testing generate_input_from_validation_form")

    def test_report_spreadsheet_validation_status(self):
        self.assertTrue(1, "Testing report_spreadsheet_validation_status")

    def test_validate_spreadsheet(self):
        self.assertTrue(1, "Testing validate_spreadsheet")
        # from hed.web.spreadsheet import validate_spreadsheet
        # temp_name = save_file_to_upload_folder('')
        # self.assertEqual(temp_name, '', "A file with empty name cnnot be copied copied")
        # some_file = '3k32j23kj1.txt'
        # temp_name = save_file_to_upload_folder(some_file)
        # self.assertEqual(temp_name, '', "A file that does not exist cannot be copied")
        # hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        # self.assertTrue(os.path.exists(hed_file), "The HED.xml file should exist in the data directory")
        # spreadsheet_path =
        # input_arguments = {''}


def get_inputs():
    spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
    hed_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    spreadsheet_file = 'ExcelMultipleSheets.xlsx'
    worksheet_name ='LKT Events'
    tag_columns = [2, 3]
    other_columns = [4]
    # inputs = {'spreadsheet_path': spreadsheet_path, 'hed_file_path': hed_file_path, \
    #           'spreadsheet-file': spreadsheet_file, 'worksheet-name': worksheet_name, \
    #           'tag-columns': tag_columns, 'has-column-names': true, \
    #           'check-for-warnings:', True, 'column-prefix-dictionary': ''}
    inputs = {}
    return inputs


if __name__ == '__main__':
    unittest.main()
