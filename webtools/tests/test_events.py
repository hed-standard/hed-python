import os
import shutil
import unittest
from flask import Response
from hedweb.app_factory import AppFactory
from hedweb.constants import common


def event_input():
    base_path = os.path.dirname(os.path.abspath(__file__))
    test_events = {common.SCHEMA_PATH: os.path.join(base_path, 'data/HED8.0.0-alpha.1.xml'),
                   common.SCHEMA_DISPLAY_NAME: 'HED8.0.0-alpha.1.xml',
                   common.JSON_PATH: os.path.join(base_path, 'data/short_form_valid.json'),
                   common.JSON_DISPLAY_NAME: 'short_form_valid.json',
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

    def test_generate_input_from_events_form(self):
        self.assertTrue(1, "Testing generate_input_from_events_form")

    def test_events_process_empty_file(self):
        from hedweb.events import events_process
        from hed.util.exceptions import HedFileError
        # Test for empty events_path
        arguments = {'events_path': ''}
        try:
            events_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('events_process threw the wrong exception when events_path was empty')
        else:
            self.fail('events_process should have thrown a HedFileError exception when events_path was empty')

    def test_events_process(self):
        from hedweb.events import events_process
        from hedweb.constants import common
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {'events_path': events_path, 'command': common.COMMAND_VALIDATE, common.DEFS_EXPAND: True,
                     'json_path': json_path, 'json_file': 'good_events.json', common.CHECK_FOR_WARNINGS: True,
                     common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml'}
        with self.app.app_context():
            response = events_process(arguments)
            self.assertTrue(isinstance(response, Response),
                            'events_process validation should return a response object when validation errors')
            headers = dict(response.headers)
            self.assertEqual('success', headers['Category'],
                             'events_process validate should return success if no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {'events_path': events_path, 'command': common.COMMAND_VALIDATE, common.DEFS_EXPAND: True,
                     'json_path': json_path, 'json_file': 'good_events.json',  common.CHECK_FOR_WARNINGS: True,
                     common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED 7.1.2.xml'}
        with self.app.app_context():
            response = events_process(arguments)
            self.assertTrue(isinstance(response, Response),
                            'events_process validation should return a response object when no validation errors')
            headers = dict(response.headers)
            self.assertEqual('warning', headers['Category'],
                             'events_process validate should give warning when errors')
            self.assertTrue(response.data,
                            'events_process validate should return data when errors')

    def test_events_assemble(self):
        from hedweb.events import events_assemble
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')

        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                     'events_path': events_path, 'events': 'bids_events.tsv',
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     'json_path': json_path, 'json_file': 'bids_events.json'}
        with self.app.app_context():
            results = events_assemble(arguments)
            self.assertTrue('data' in results,
                            'events_assemble results should have a data key when no errors')
            self.assertEqual('success', results["msg_category"],
                             'events_assemble msg_category should be success when no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED7.1.2.xml',
                     'events_path': events_path, 'events': 'bids_events.tsv',
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     'json_path': json_path, 'json_file': 'bids_events.json'}
        with self.app.app_context():
            results = events_assemble(arguments)
            self.assertTrue(results['data'],
                            'events_assemble results should have a data key when errors')
            self.assertEqual('warning', results['msg_category'],
                             'events_assemble msg_category should be warning when errors')

    def test_events_validate_file(self):
        from hedweb.events import events_validate
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')

        arguments = {'command': common.COMMAND_VALIDATE,
                     common.SCHEMA_PATH: schema_path, common.SCHEMA_DISPLAY_NAME: 'HED7.1.2.xml',
                     common.EVENTS_PATH: events_path, common.EVENTS_FILE: 'bids_events.tsv',
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     common.JSON_PATH: json_path, common.JSON_FILE: 'bids_events.json'}

        with self.app.app_context():
            results = events_validate(arguments)
            self.assertTrue(results['data'],
                            'events_validate results should have a data key when validation errors')
            self.assertEqual('warning', results["msg_category"],
                             'events_validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {'command': common.COMMAND_VALIDATE,
                     common.SCHEMA_PATH: schema_path, common.SCHEMA_DISPLAY_NAME: 'HED8.0.0-alpha.1.xml',
                     common.EVENTS_PATH: events_path, common.EVENTS_FILE: 'bids_events.tsv',
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     common.JSON_PATH: json_path, common.JSON_FILE: 'bids_events.json'}

        with self.app.app_context():
            results = events_validate(arguments)
            self.assertFalse(results['data'],
                             'events_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results['msg_category'],
                             'events_validate msg_category should be success when no errors')

    def test_events_validate_string(self):
        from hedweb.events import events_validate
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        with open(events_path, "r") as myfile:
            events_string = myfile.read()

        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        with open(json_path, "r") as myfile:
            json_string = myfile.read()

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        with open(schema_path, "r") as myfile:
            schema_string = myfile.read()

        arguments = {common.SCHEMA_STRING: schema_string, common.SCHEMA_DISPLAY_NAME: 'HED7.1.2.xml',
                     common.EVENTS_STRING: events_string,
                     common.JSON_STRING: json_string}

        with self.app.app_context():
            results = events_validate(arguments)
            self.assertTrue(results['data'],
                            'events_validate results should have a data key when validation errors')
            self.assertEqual('warning', results["msg_category"],
                             'events_validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        with open(schema_path, "r") as myfile:
            schema_string = myfile.read()
        arguments = {common.SCHEMA_STRING: schema_string, common.SCHEMA_DISPLAY_NAME: 'HED7.1.2.xml',
                     common.EVENTS_STRING: events_string, common.JSON_STRING: json_string,
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True}

        with self.app.app_context():
            results = events_validate(arguments)
            self.assertFalse(results['data'],
                             'events_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results['msg_category'],
                             'events_validate msg_category should be success when no errors')


if __name__ == '__main__':
    unittest.main()
