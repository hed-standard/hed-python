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

    def test_events_results_empty_data(self):
        response = self.app.test.post('/events_submit')
        self.assertEqual(200, response.status_code, 'HED events request succeeds even when no data')
        header_dict = dict(response.headers)
        self.assertEqual("error", header_dict["Category"], "The header category when no events is error ")
        self.assertFalse(response.data, "The response data for empty events request is empty")

    def test_events_results_assemble_valid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))

        with open(events_path, 'r') as sc:
            y = sc.read()
        events_buffer = io.BytesIO(bytes(y, 'utf-8'))

        with self.app.app_context():
            input_data = {'schema_version': '8.0.0-alpha.1',
                          'command_option': 'command_assemble',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'events_file': (events_buffer, 'bids_events.tsv'),
                          'defs_expand': 'on',
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/events_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Assembly of a valid events file has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid events file should assemble successfully")
            self.assertTrue(response.data, "The assembled events file should not be empty")
            json_buffer.close()
            events_buffer.close()

    def test_events_results_assemble_invalid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))

        with open(events_path, 'r') as sc:
            y = sc.read()
        events_buffer = io.BytesIO(bytes(y, 'utf-8'))

        with self.app.app_context():
            input_data = {'schema_version': '7.2.0',
                          'command_option': 'command_assemble',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'events_file': (events_buffer, 'bids_events.tsv'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/events_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Assembly of invalid events files has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Assembly with invalid events files generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid event assembly should have error messages")
            json_buffer.close()

    def test_events_results_validate_valid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))

        with open(events_path, 'r') as sc:
            y = sc.read()
        events_buffer = io.BytesIO(bytes(y, 'utf-8'))

        with self.app.app_context():
            input_data = {'schema_version': '8.0.0-alpha.1',
                          'command_option': 'command_validate',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'events_file': (events_buffer, 'bids_events.tsv'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/events_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid events file has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid events file should validate successfully")
            self.assertFalse(response.data, "The validated events file should not return data")
            json_buffer.close()
            events_buffer.close()

    def test_events_results_validate_invalid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))

        with open(events_path, 'r') as sc:
            y = sc.read()
        events_buffer = io.BytesIO(bytes(y, 'utf-8'))

        with self.app.app_context():
            input_data = {'schema_version': '7.2.0',
                          'command_option': 'command_validate',
                          'json_file': (json_buffer, 'bids_events.json'),
                          'events_file': (events_buffer, 'events_file'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/events_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of invalid events files has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Validation of invalid events files generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid event validation should have error messages")
            json_buffer.close()
            events_buffer.close()


if __name__ == '__main__':
    unittest.main()
