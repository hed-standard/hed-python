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

    def test_get_columns_info_results(self):
        response = self.app.test.post('/get-columns-info')
        self.assertEqual(400, response.status_code, 'Columns info requires data')

    def test_get_dictionary_results(self):
        response = self.app.test.post('/dictionary_submit')
        self.assertEqual(400, response.status_code, 'Dictionary requires data')

    def test_get_events_results(self):
        response = self.app.test.post('/events_submit')
        self.assertEqual(400, response.status_code, 'Event processing requires data')

    def test_get_services_results(self):
        response = self.app.test.get('/services_submit')
        self.assertEqual(405, response.status_code, 'HED services require data')

    def test_get_schema_version(self):
        response = self.app.test.post('/get_schema_version')
        self.assertEqual(400, response.status_code, 'Returning HED version requires data')

    def test_schema_versions(self):
        with self.app.app_context():
            response = self.app.test.post('/schema_versions')
        self.assertEqual(400, response.status_code, 'Returning HED version requires data')

    def test_schema_versions(self):
        import json
        with self.app.app_context():
            response = self.app.test.post('/schema_versions')
            self.assertEqual(200, response.status_code, 'The HED version list does not require data')
            versions = response.data
            self.assertTrue(versions, "The returned data is not empty")
            v_dict = json.loads(versions)
            self.assertIsInstance(v_dict, dict, "The versions are returned in a dictionary")
            v_list = v_dict["schema_version_list"]
            self.assertIsInstance(v_list, list, "The versions are in a list")

    def test_schema_version_results(self):
        import io
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/../data/HED8.0.0-alpha.1.xml')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        schema_string = io.StringIO()
        schema_string.write(x)
        with self.app.app_context():
            response = self.app.test.post('/schema_version', content_type='multipart/form-data',
                                          data={'schema_path': (schema_string, 'my_schema.xml')})
            self.assertEqual(200, response.status_code, 'The HED version list does not require data')
        print("here")

    def test_get_spreadsheet_results(self):
        response = self.app.test.post('/spreadsheet-submit')
        self.assertEqual(400, response.status_code, 'Spreadsheet processing requires data')

    def test_string_results_empty_data(self):
        import json
        response = self.app.test.post('/string_submit')
        self.assertEqual(200, response.status_code, 'HED string request succeeds even when no data')
        self.assertTrue(response.data, "The returned data is not empty")
        response_dict = json.loads(response.data)
        self.assertIsInstance(response_dict, dict, "The versions are returned in a dictionary")
        self.assertTrue(response_dict["message"], "The message is not empty")

    def test_string_results_validate(self):
        import json
        with self.app.app_context():
            response = self.app.test.post('/string_submit', content_type='multipart/form-data',
                                          data={'schema_version': '8.0.0-alpha.1',
                                                'command_option': 'command_validate',
                                                'check_for_warnings': 'on',
                                                'string_input': 'Red,Blue,Label/3'})

            self.assertEqual(200, response.status_code, 'Validation of a valid string has a response')
            response_dict = json.loads(response.data)
            self.assertEqual("success", response_dict["msg_category"], "The list should validate successfully")
            self.assertFalse(response_dict["data"], "No data should be returned if validation successful")

            response = self.app.test.post('/string_submit', content_type='multipart/form-data',
                                          data={'schema_version': '8.0.0-alpha.1',
                                                'command_option': 'command_validate',
                                                'check_for_warnings': 'on',
                                                'string_input': 'Blob,Blue,Label/3'})
            self.assertEqual(200, response.status_code, 'Validation of an invalid string has a response')
            response_dict = json.loads(response.data)
            self.assertEqual("warning", response_dict["msg_category"],
                             "Invalid hed string validation generates a warning")
            self.assertTrue(response_dict["data"], "The data should have error messages")

    def test_render_additional_examples_page(self):
        response = self.app.test.get('/additional-examples')
        self.assertEqual(response.status_code, 200, "The additional-examples content page should exist")

    def test_render_common_errors_page(self):
        response = self.app.test.get('/common-errors')
        self.assertEqual(response.status_code, 200, "The common-errors content page should exist")

    def test_render_dictionary_form(self):
        response = self.app.test.get('/dictionary')
        self.assertEqual(response.status_code, 200, "The dictionary content page should exist")

    def test_render_events_form(self):
        response = self.app.test.get('/events')
        self.assertEqual(response.status_code, 200, "The events content page should exist")

    def test_render_services_form(self):
        response = self.app.test.get('/services')
        self.assertEqual(response.status_code, 200, "The hed-services content page should exist")

    def test_render_hedstring_form(self):
        response = self.app.test.get('/string')
        self.assertEqual(response.status_code, 200, "The hedstring content page should exist")

    def test_render_help_page(self):
        response = self.app.test.get('/hed-tools-help')
        self.assertEqual(response.status_code, 200, "The hed-tools-help content page should exist")

    def test_render_home_page(self):
        response = self.app.test.get('/')
        self.assertEqual(response.status_code, 200, "The root hed home page should exist")

    def test_render_schema_form(self):
        response = self.app.test.get('/schema')
        self.assertEqual(response.status_code, 200, "The schema page should exist")

    def test_render_spreadsheet_form(self):
        response = self.app.test.get('/spreadsheet')
        self.assertEqual(response.status_code, 200, "The spreadsheet page should exist")


if __name__ == '__main__':
    unittest.main()
