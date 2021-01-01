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
            cls.app = app.test_client()

        # cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        # app = AppFactory.create_app('config.TestConfig')
        # with app.app_context():
        #
        #     from hed.web.routes import route_blueprint
        #     app.register_blueprint(route_blueprint)
        #     web_utils.create_upload_directory(cls.upload_directory)
        #     app.config['UPLOAD_FOLDER'] = cls.upload_directory
        #     cls.app = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_delete_file_in_upload_directory(self):
        print("help")
        # with unittest.TestCase.app.test_client() as c:
        #     response = c.get('/delete/file_that_does_not_exist')
        #     self.assertEquals(response.status_code, 404)

    # def test_download_file_in_upload_directory(self):
    #     response = self.app.get('/download-file/file_that_does_not_exist')
    #     self.assertEqual(response.status_code, 404)
    #
    # def test_get_duplicate_tag_results(self):
    #     response = self.app.get('/schema-duplicate-tag-results')
    #     self.assertEqual(response.status_code, 404)
    #
    # def test_get_eeg_events_validation_results(self):
    #     response = self.app.get('/eeg-validation-submit')
    #     self.assertEqual(response.status_code, 404)
    #
    # def test_get_hed_version_in_file(self):
    #     response = self.app.post('/get-hed-version')
    #     self.assertEqual(response.status_code, 400)
    #
    # def test_get_major_hed_versions(self):
    #     response = self.app.post('/get-hed-major-versions')
    #     self.assertEqual(response.status_code, 405)
    #
    # def test_get_major_hed_versions(self):
    #     response = self.app.post('/get-hed-major-versions')
    #     self.assertEqual(response.status_code, 405)
    #
    # def test_get_schema_conversion_results(self):
    #     response = self.app.post('/schema-conversion-submit')
    #     self.assertEqual(response.status_code, 400)
    #
    # def test_get_spreadsheet_columns_info(self):
    #     response = self.app.post('/get-spreadsheet-columns-info')
    #     self.assertEqual(response.status_code, 400)
    #
    # def test_get_validation_results(self):
    #     response = self.app.post('/validation-submit')
    #     self.assertEqual(response.status_code, 400)
    #
    # def test_get_worksheets_info(self):
    #     response = self.app.post('/get-worksheets-info')
    #     self.assertEqual(response.status_code, 400)
    #
    # def test_render_additional_examples_page(self):
    #     response = self.app.get('/additional-examples')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_render_common_error_page(self):
    #     response = self.app.get('/common-errors')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_render_eeg_validation_form(self):
    #     response = self.app.get('/eeg-validation')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_render_home_page(self):
    #     response = self.app.get('/')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_render_help_page(self):
    #     response = self.app.get('/hed-tools-help')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_render_schema_form(self):
    #     response = self.app.get('/schema')
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_render_validation_form(self):
    #     response = self.app.get('/validation')
    #     self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
