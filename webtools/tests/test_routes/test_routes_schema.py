import io
import os
import unittest
from tests.test_web_base import TestWebBase


class Test(TestWebBase):
    def test_schema_results_empty_data(self):
        response = self.app.test.post('/schema_submit')
        self.assertEqual(200, response.status_code, 'HED schema request succeeds even when no data')
        header_dict = dict(response.headers)
        self.assertEqual("error", header_dict["Category"],
                         "The header msg_category when no schema request data is error ")
        self.assertFalse(response.data, "The response data for empty schema request is empty")

    def test_schema_results_convert_mediawiki_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0Bad.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'convert',
                          'schema_file': (schema_buffer, 'HED8.0.0Bad.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Convert of a invalid mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "The invalid mediawiki should not convert to xml successfully")
            self.assertTrue(response.data, "The response data for invalid mediawiki conversion should not be empty")
            self.assertTrue(headers_dict['Message'],
                            "The error message for invalid mediawiki conversion should not be empty")
            self.assertNotEqual(None, headers_dict.get('Content-Disposition', None),
                             "A file should be returned for invalid mediawiki conversion")
            schema_buffer.close()

    def test_schema_results_convert_mediawiki_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'convert',
                          'schema_file': (schema_buffer, 'HED8.0.0.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Convert of a valid mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid mediawiki should convert to xml successfully")
            self.assertTrue(response.data, "The converted schema should not be empty")
            self.assertEqual('attachment filename=HED8.0.0.xml',
                             headers_dict['Content-Disposition'], "Convert of valid mediawiki should return xml")
            schema_buffer.close()

    def test_schema_results_convert_mediawiki_gen2_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED7.2.0Bad.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'convert',
                          'schema_file': (schema_buffer, 'HED7.2.0Bad.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Convert of a invalid gen2 mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "The invalid gen2 mediawiki should not convert to xml successfully")
            self.assertTrue(response.data, "The response data for invalid gen2 mediawiki convert should not be empty")
            self.assertTrue(headers_dict['Message'],
                            "The error message for invalid gen2 mediawiki conversion should not be empty")
            self.assertNotEqual(None, headers_dict.get('Content-Disposition', None),
                             "A file should be returned for invalid gen2 mediawiki conversion")
            schema_buffer.close()

    def test_schema_results_convert_mediawiki_gen2_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED7.2.0.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'convert',
                          'schema_file': (schema_buffer, 'HED-generation2-schema-7.2.0.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Convert of a valid gen2 mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid gen2 mediawiki should convert to xml successfully")
            self.assertTrue(response.data, "The converted gen2 schema should not be empty")
            self.assertEqual('attachment filename=HED-generation2-schema-7.2.0.xml',
                             headers_dict['Content-Disposition'],
                             "Conversion of valid gen2 mediawiki should return xml")
            schema_buffer.close()

    def test_schema_results_convert_xml_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0.xml')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'convert',
                          'schema_file': (schema_buffer, 'HED8.0.0.xml'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Convert of a valid xml has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid xml should validate successfully")
            self.assertTrue(response.data, "The validated schema should not be empty")
            self.assertEqual('attachment filename=HED8.0.0.mediawiki',
                             headers_dict['Content-Disposition'],
                             "Validation of valid xml should not return a file")
            schema_buffer.close()

    def test_schema_results_convert_xml_gen2_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED7.2.0.xml')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'convert',
                          'schema_file': (schema_buffer, 'HED7.2.0.xml'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Convert of a valid gen2 xml has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid gen2 xml should convert to mediawiki successfully")
            self.assertTrue(response.data, "The converted gen2 schema should not be empty")
            self.assertEqual('attachment filename=HED7.2.0.mediawiki',
                             headers_dict['Content-Disposition'],
                             "Conversion of valid gen2 xml should return mediawiki")
            schema_buffer.close()

    def test_schema_results_convert_xml_url_valid(self):
        schema_url = \
            'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_url_option',
                          'command_option': 'convert',
                          'schema_url': schema_url,
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Conversion of a valid xml url has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid xml url should convert to mediawiki successfully")
            self.assertTrue(response.data, "The converted xml url schema should not be empty")
            self.assertEqual('attachment filename=HED8.0.0.mediawiki',
                             headers_dict['Content-Disposition'], "Conversion of valid xml url should return mediawiki")

    def test_schema_results_convert_xml_url_valid2(self):
        schema_url = \
            'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_url_option',
                          'command_option': 'convert',
                          'schema_url': schema_url,
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Conversion of a valid xml url has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid xml url should convert to mediawiki successfully")
            self.assertTrue(response.data, "The converted xml url schema should not be empty")
            self.assertEqual('attachment filename=HED8.0.0.mediawiki',
                             headers_dict['Content-Disposition'], "Conversion of valid xml url should return mediawiki")

    def test_schema_results_validate_mediawiki_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0Bad.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'validate',
                          'schema_file': (schema_buffer, 'HED8.0.0Bad.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a invalid mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "The invalid mediawiki should return validation errors successfully")
            self.assertTrue(response.data, "The response data for invalid mediawiki validation should be empty")
            self.assertTrue(headers_dict['Message'],
                            "The error message for invalid mediawiki conversion should not be empty")
            self.assertNotEqual(None, headers_dict.get('Content-Disposition', None),
                             "A file should be returned for invalid mediawiki validation")
            schema_buffer.close()

    def test_schema_results_validate_mediawiki_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'validate',
                          'schema_file': (schema_buffer, 'HED8.0.0.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid mediawiki should validate successfully")
            self.assertFalse(response.data, "The response data for validated mediawiki should be empty")
            self.assertEqual(None, headers_dict.get('Content-Disposition', None),
                             "Validation of valid mediawiki should not return a file")
            schema_buffer.close()

    def test_schema_results_validate__mediawiki_gen2_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED7.2.0.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'validate',
                          'schema_file': (schema_buffer, 'HED7.2.0.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid gen2 mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "The valid gen2 mediawiki should is not compliant and should return a warning")
            self.assertTrue(response.data, "The validated gen2 schema response data has non compliance errors")
            self.assertTrue(headers_dict['Content-Disposition'],
                            "The validation of valid gen2 mediawiki still returns a file of errors")
            schema_buffer.close()

    def test_schema_results_validate_mediawiki_gen2_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED7.2.0Bad.mediawiki')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'validate',
                          'schema_file': (schema_buffer, 'HED7.2.0Bad.mediawiki'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a invalid gen2 mediawiki has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "The invalid gen2 mediawiki should validate with errors ")
            self.assertTrue(response.data, "The response data for invalid gen2 mediawiki validation should errors")
            self.assertTrue(headers_dict['Message'],
                            "The error message for invalid gen2 mediawiki validation should not be empty")
            self.assertNotEqual(None, headers_dict.get('Content-Disposition', None),
                             "A file should be returned for invalid gen2 mediawiki validation")
            schema_buffer.close()

    def test_schema_results_validate_xml_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0.xml')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'validate',
                          'schema_file': (schema_buffer, 'HED8.0.0.xml'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid xml has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid xml should validate successfully")
            self.assertFalse(response.data, "The validated schema data should be empty")
            self.assertEqual(None, headers_dict.get('Content-Disposition', None),
                             "Validation of valid xml should return any response data")
            schema_buffer.close()

    def test_schema_results_validate_xml_gen2_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED7.2.0.xml')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_buffer = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_file_option',
                          'command_option': 'validate',
                          'schema_file': (schema_buffer, 'HED7.2.0.xml'),
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid gen2 xml has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "The valid gen2 xml should still have compliance errors")
            self.assertTrue(response.data, "The validated gen2 schema should not be empty")
            self.assertTrue(headers_dict['Content-Disposition'],
                            "Validation of valid gen2 xml should return validation error file")
            schema_buffer.close()

    def test_schema_results_validate_xml_url_valid(self):
        schema_url = \
            'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        with self.app.app_context():
            input_data = {'schema_upload_options': 'schema_url_option',
                          'command_option': 'validate',
                          'schema_url': schema_url,
                          'check_for_warnings': 'on'}
            response = self.app.test.post('/schema_submit', content_type='multipart/form-data', data=input_data)
            self.assertEqual(200, response.status_code, 'Validation of a valid xml url has a response')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid xml url should be successful")
            self.assertFalse(response.data, "The validated xml url schema should return empty response data")
            self.assertEqual(None, headers_dict.get('Content-Disposition', None),
                             "Validation of valid xml url should not return an error file")


if __name__ == '__main__':
    unittest.main()
