import io
import os
import shutil
import unittest
from flask import Response
from werkzeug.datastructures import FileStorage
from hedweb.app_factory import AppFactory
from hedweb.constants import common


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hedweb.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            app.config['WTF_CSRF_ENABLED'] = False
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_dictionary_results_empty_data(self):
        response = self.app.test.post('/dictionary_submit')
        self.assertEqual(200, response.status_code, 'HED dictionary request succeeds even when no data')
        self.assertTrue(isinstance(response, Response),
                        'dictionary_submit to short should return a Response when no data')
        header_dict = dict(response.headers)
        self.assertEqual("error", header_dict["Category"], "The header category when no dictionary is error ")
        self.assertFalse(response.data, "The response data for empty dictionary request is empty")

    def test_dictionary_results_to_long_valid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            input_data = {common.SCHEMA_VERSION: '8.0.0-alpha.2',
                          common.COMMAND_OPTION: common.COMMAND_TO_LONG,
                          common.JSON_FILE: (json_buffer, 'bids_events_alpha.json'),
                          common.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit should return a Response when valid to long dictionary')
            self.assertEqual(200, response.status_code, 'To long of a valid dictionary has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should convert to long successfully")
            self.assertTrue(response.data, "The converted to long dictionary should not be empty")
            json_buffer.close()

    def test_dictionary_results_to_long_invalid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')
        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {common.SCHEMA_VERSION: '7.2.0',
                          common.COMMAND_OPTION: common.COMMAND_TO_LONG,
                          common.JSON_FILE: (json_buffer, 'HED7.2.0.xml'),
                          common.CHECK_FOR_WARNINGS: 'on'}

            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit should return a Response when invalid to long dictionary')
            self.assertEqual(200, response.status_code, 'Conversion of an invalid dictionary to long has valid status')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Conversion of an invalid dictionary to long generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid conversion to long should have error messages")
            json_buffer.close()

    def test_dictionary_results_to_short_valid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            json_file = FileStorage(stream=json_buffer, filename='bids_events.json')
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-beta.1.xml')
            with open(schema_path, 'r') as sc:
                y = sc.read()
            schema_buffer = io.BytesIO(bytes(y, 'utf-8'))
            input_data = {common.SCHEMA_VERSION: 'Other',
                          common.SCHEMA_PATH: (schema_buffer, 'HED8.0.0-beta.1.xml'),
                          common.COMMAND_OPTION: common.COMMAND_TO_SHORT,
                          common.JSON_FILE: (json_buffer, 'bids_events.json'),
                          common.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit should return a Response when valid to short dictionary')
            self.assertEqual(200, response.status_code, 'To short of a valid dictionary has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should convert to short successfully")
            self.assertTrue(response.data, "The converted to short dictionary should not be empty")
            json_buffer.close()

    def test_dictionary_results_validate_valid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            input_data = {common.SCHEMA_VERSION: '8.0.0-alpha.2',
                          common.COMMAND_OPTION: common.COMMAND_VALIDATE,
                          common.JSON_FILE: (json_buffer, 'bids_events_alpha.json'),
                          common.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit should return a Response when valid dictionary')
            self.assertEqual(200, response.status_code, 'Validation of a valid dictionary has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should validate successfully")
            self.assertFalse(response.data, "The response for validated dictionary should be empty")
            json_buffer.close()

    def test_dictionary_results_validate_valid_other(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-beta.1.xml')
            with open(schema_path, 'r') as sc:
                y = sc.read()
            schema_buffer = io.BytesIO(bytes(y, 'utf-8'))

            input_data = {common.SCHEMA_VERSION: 'Other',
                          common.SCHEMA_PATH: (schema_buffer, 'HED8.0.0-beta.1.xml'),
                          common.COMMAND_OPTION: common.COMMAND_VALIDATE,
                          common.JSON_FILE: (json_buffer, 'bids_events.json'),
                          common.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit should return a Response when valid dictionary')
            self.assertEqual(200, response.status_code, 'Validation of a valid dictionary has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should validate successfully")
            self.assertFalse(response.data, "The response for validated dictionary should be empty")
            json_buffer.close()

    def test_dictionary_results_to_short_invalid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            input_data = {common.SCHEMA_VERSION: '7.2.0',
                          common.COMMAND_OPTION: common.COMMAND_TO_SHORT,
                          common.JSON_FILE: (json_buffer, 'bids_events_alpha.json'),
                          common.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit should return a response object when invalid to short dictionary')
            self.assertEqual(200, response.status_code, 'Conversion of invalid dictionary to short has valid status')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Conversion of an invalid dictionary to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid conversion to short should have error messages")
            json_buffer.close()

    def test_dictionary_results_validate_invalid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            input_data = {common.SCHEMA_VERSION: '7.2.0',
                          common.COMMAND_OPTION: common.COMMAND_VALIDATE,
                          common.JSON_FILE: (json_buffer, 'bids_events_alpha.json'),
                          common.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data',
                                          data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_submit validate should return a response object when invalid dictionary')
            self.assertEqual(200, response.status_code,
                             'Validation of an invalid dictionary to short has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Validation of an invalid dictionary to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid validation should have error messages")
            json_buffer.close()


if __name__ == '__main__':
    unittest.main()
