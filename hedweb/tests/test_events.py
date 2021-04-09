import os
import shutil
import unittest
from flask import Response
from hed.web.app_factory import AppFactory
from hed.web.constants import common


def event_input():
    base_path = os.path.dirname(os.path.abspath(__file__))
    test_events = {common.HED_XML_FILE: os.path.join(base_path, 'data/HED8.0.0-alpha.1.xml'),
                   common.HED_DISPLAY_NAME: 'HED8.0.0-alpha.1.xml',
                   common.JSON_PATH: os.path.join(base_path, 'data/short_form_valid.json'),
                   common.JSON_FILE: 'short_form_valid.json',
                   common.SPREADSHEET_PATH: os.path.join(base_path, 'data/ExcelMultipleSheets.xlsx'),
                   common.SPREADSHEET_FILE: 'ExcelMultipleSheets.xlsx',
                   common.WORKSHEET_NAME: 'LKT Events',
                   common.HAS_COLUMN_NAMES: True,
                   common.CHECK_FOR_WARNINGS: True
    }
    return test_events


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

    def test_generate_input_from_events_form(self):
        self.assertTrue(1, "Testing generate_input_from_events_form")

    def test_events_validate(self):
        from hed.web.events import events_validate
        from hed.schema import hed_schema_file
        inputs = event_input()
        response = events_validate(inputs)
        print(type(response) is Response)
        self.assertTrue(type(response) is Response, "events_validate should return a response")


if __name__ == '__main__':
    unittest.main()
