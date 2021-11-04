import io
import os
import unittest
from flask import Response
from tests.test_web_base import TestWebBase
from hedweb.constants import base_constants


class Test(TestWebBase):
    def test_sidecar_results_empty_data(self):
        response = self.app.test.post('/sidecar_submit')
        self.assertEqual(200, response.status_code, 'HED sidecar request succeeds even when no data')
        self.assertTrue(isinstance(response, Response),
                        'sidecar_submit to short should return a Response when no data')
        header_dict = dict(response.headers)
        self.assertEqual("error", header_dict["Category"], "The header msg_category when no sidecar is error ")
        self.assertFalse(response.data, "The response data for empty sidecar request is empty")

    def test_sidecar_results_to_long_valid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            input_data = {base_constants.SCHEMA_VERSION: '8.0.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_TO_LONG,
                          base_constants.JSON_FILE: (json_buffer, 'bids_events.json'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit should return a Response when valid to long sidecar')
            self.assertEqual(200, response.status_code, 'To long of a valid sidecar has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid sidecar should convert to long successfully")
            self.assertTrue(response.data, "The converted to long sidecar should not be empty")
            json_buffer.close()

    def test_sidecar_results_to_long_invalid(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {base_constants.SCHEMA_VERSION: '7.2.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_TO_LONG,
                          base_constants.JSON_FILE: (json_buffer, 'HED7.2.0.xml'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}

            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit should return a Response when invalid to long sidecar')
            self.assertEqual(200, response.status_code, 'Conversion of an invalid sidecar to long has valid status')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Conversion of an invalid sidecar to long generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid conversion to long should have error messages")
            json_buffer.close()

    def test_sidecar_results_to_short_valid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0.xml')
            with open(schema_path, 'r') as sc:
                y = sc.read()
            schema_buffer = io.BytesIO(bytes(y, 'utf-8'))
            input_data = {base_constants.SCHEMA_VERSION: 'Other',
                          base_constants.SCHEMA_PATH: (schema_buffer, 'HED8.0.0.xml'),
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_TO_SHORT,
                          base_constants.JSON_FILE: (json_buffer, 'bids_events.json'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit should return a Response when valid to short sidecar')
            self.assertEqual(200, response.status_code, 'To short of a valid sidecar has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid sidecar should convert to short successfully")
            self.assertTrue(response.data, "The converted to short sidecar should not be empty")
            json_buffer.close()

    def test_sidecar_results_validate_valid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            input_data = {base_constants.SCHEMA_VERSION: '8.0.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_VALIDATE,
                          base_constants.JSON_FILE: (json_buffer, 'bids_events.json'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit should return a Response when valid sidecar')
            self.assertEqual(200, response.status_code, 'Validation of a valid sidecar has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid sidecar should validate successfully")
            self.assertFalse(response.data, "The response for validated sidecar should be empty")
            json_buffer.close()

    def test_sidecar_results_validate_valid_other(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0.xml')
            with open(schema_path, 'r') as sc:
                y = sc.read()
            schema_buffer = io.BytesIO(bytes(y, 'utf-8'))

            input_data = {base_constants.SCHEMA_VERSION: 'Other',
                          base_constants.SCHEMA_PATH: (schema_buffer, 'HED8.0.0.xml'),
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_VALIDATE,
                          base_constants.JSON_FILE: (json_buffer, 'bids_events.json'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit should return a Response when valid sidecar')
            self.assertEqual(200, response.status_code, 'Validation of a valid sidecar has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid sidecar should validate successfully")
            self.assertFalse(response.data, "The response for validated sidecar should be empty")
            json_buffer.close()

    def test_sidecar_results_to_short_invalid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))

            input_data = {base_constants.SCHEMA_VERSION: '7.2.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_TO_SHORT,
                          base_constants.JSON_FILE: (json_buffer, 'bids_events.json'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit should return a response object when invalid to short sidecar')
            self.assertEqual(200, response.status_code, 'Conversion of invalid sidecar to short has valid status')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Conversion of an invalid sidecar to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid conversion to short should have error messages")
            json_buffer.close()

    def test_sidecar_results_validate_invalid(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            input_data = {base_constants.SCHEMA_VERSION: '7.2.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_VALIDATE,
                          base_constants.JSON_FILE: (json_buffer, 'bids_events.json'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/sidecar_submit', content_type='multipart/form-data',
                                          data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'sidecar_submit validate should return a response object when invalid sidecar')
            self.assertEqual(200, response.status_code,
                             'Validation of an invalid sidecar to short has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Validation of an invalid sidecar to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid validation should have error messages")
            json_buffer.close()


if __name__ == '__main__':
    unittest.main()
