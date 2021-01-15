import os
import pathlib
import shutil
from shutil import copyfile
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

    def test_delete_file_in_upload_directory(self):
        response = self.app.test.post('/delete/file_that_does_not_exist')
        self.assertEqual(response.status_code, 404, "Non-existent file should cause a non-found error")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        dummy_file = os.path.join(self.app.config['UPLOAD_FOLDER'], 'HED.xml')
        dummy_path = pathlib.Path(dummy_file)
        self.assertFalse(dummy_path.is_file(), "Dummy file does not exist yet")
        copyfile(hed_file, dummy_file)
        self.assertTrue(dummy_path.is_file(), "Dummy file now exists")
        response = self.app.test.get('/delete/HED.xml')
        self.assertEqual(response.status_code, 204, "Dummy file should be deleted")

    def test_download_file_in_upload_directory(self):
        response = self.app.test.get('/download-file/file_that_does_not_exist')

        # self.assertEqual(response.status_code, 404, "Non-existent file should cause a non-found error")
        upload_dir = self.app.config['UPLOAD_FOLDER']
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        dummy_file = os.path.join(self.app.config['UPLOAD_FOLDER'], 'HED.xml')
        dummy_path = pathlib.Path(dummy_file)
        self.assertFalse(dummy_path.is_file(), "Dummy file does not exist yet")
        copyfile(hed_file, dummy_file)
        self.assertTrue(dummy_path.is_file(), "Dummy file now exists")
        response = self.app.test.get('/download-file/HED.xml')
        print(response.status_code)
        # self.assertEqual(response.status_code, 204, "Dummy file should be deleted")

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
    # import hed.web.constants.common_constants as constants
    # from hed.web.web_utils import find_major_hed_versions
    # hed_info = find_major_hed_versions()
    # self.assertTrue(constants.HED_MAJOR_VERSIONS in hed_info, "The information has key hed-major-versions")
    # self.assertTrue('7.1.2' in hed_info[constants.HED_MAJOR_VERSIONS], "7.1.2 is a major versions")
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

    def test_render_additional_examples_page(self):
        response = self.app.test.get('/additional-examples')
        self.assertEqual(response.status_code, 200, "The additional-examples content page exists")

    def test_render_common_error_page(self):
        response = self.app.test.get('/common-errors')
        self.assertEqual(response.status_code, 200, "The common-errors content page exists")

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
