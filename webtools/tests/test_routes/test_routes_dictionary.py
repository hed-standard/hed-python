import io
import os
import shutil
import unittest
from hedweb.app_factory import AppFactory


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
        header_dict = dict(response.headers)
        self.assertEqual("error", header_dict["Category"], "The header category when no dictionary is error ")
        self.assertFalse(response.data, "The response data for empty dictionary request is empty")

    def test_dictionary_results_to_long_valid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_version': '8.0.0-alpha.1',
                          'command_option': 'command_to_long',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'To long of a valid dictionary has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should convert to long successfully")
            self.assertTrue(response.data, "The converted to long dictionary should not be empty")
            json_buffer.close()

    def test_dictionary_results_to_long_invalid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_version': '7.2.0',
                          'command_option': 'command_to_long',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Conversion of an invalid dictionary to long has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Conversion of an invalid dictionary to long generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid conversion to long should have error messages")
            json_buffer.close()

    def test_dictionary_results_to_short_valid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_version': '8.0.0-alpha.1',
                          'command_option': 'command_to_short',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'To short of a valid dictionary has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should convert to short successfully")
            self.assertTrue(response.data, "The converted to short dictionary should not be empty")
            json_buffer.close()

    def test_dictionary_results_to_short_valid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_version': '7.2.0',
                          'command_option': 'command_to_short',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Conversion of an invalid dictionary to short has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Conversion of an invalid dictionary to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid conversion to short should have error messages")
            json_buffer.close()

    def test_dictionary_results_validate_valid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_version': '8.0.0-alpha.1',
                          'command_option': 'command_validate',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid dictionary has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid dictionary should validate successfully")
            self.assertFalse(response.data, "The response for validated dictionary should be empty")
            json_buffer.close()

    def test_dictionary_results_validate_invalid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_version': '7.2.0',
                          'command_option': 'command_validate',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of an invalid dictionary to short has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Validation of an invalid dictionary to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid validation should have error messages")
            json_buffer.close()


if __name__ == '__main__':
    unittest.main()
