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

    def test_get_columns_info_results(self):
        response = self.app.test.post('/get-columns-info')
        self.assertEqual(400, response.status_code, 'Columns info requires data')

    def test_get_dictionary_results(self):
        response = self.app.test.post('/dictionary-submit')
        self.assertEqual(400, response.status_code, 'Dictionaryrequires data')

    def test_get_events_validation_results(self):
        response = self.app.test.post('/events-validation-submit')
        self.assertEqual(400, response.status_code, 'Event validation requires data')

    def test_get_hed_services_results(self):
        response = self.app.test.get('/hed-services-submit')
        self.assertEqual(405, response.status_code, 'HED services require data')

    def test_get_hedstring_results(self):
        response = self.app.test.get('/hed-services-submit')
        self.assertEqual(405, response.status_code, 'HED services require data')

    def test_get_hed_version(self):
        response = self.app.test.post('/get-hed-version')
        self.assertEqual(400, response.status_code, 'Returning HED version requires data')

    def test_get_major_hed_versions(self):
        response = self.app.test.post('/get-hed-major-versions')
        self.assertEqual(405, response.status_code, 'Returning HED version list requires data')
        # import hed.web.constants.common_constants as constants
        # from hed.web.web_utils import find_major_hed_versions
        # hed_info = find_major_hed_versions()
        # self.assertTrue(constants.HED_MAJOR_VERSIONS in hed_info, "The information has key hed-major-versions")
        # self.assertTrue('7.1.2' in hed_info[constants.HED_MAJOR_VERSIONS], "7.1.2 is a major versions")

    def test_get_schema_compliance_check_results(self):
        response = self.app.test.post('/schema-compliance-check-submit')
        self.assertEqual(400, response.status_code, 'Checking schema compliance requires data')

    def test_get_schema_conversion_results(self):
        response = self.app.test.post('/schema-conversion-submit')
        self.assertEqual(400, response.status_code, 'Converting schema requires data')

    def test_get_spreadsheet_validation_results(self):
        response = self.app.test.post('/spreadsheet-validation-submit')
        self.assertEqual(400, response.status_code, 'Validating spreadsheet requires data')

    def test_render_additional_examples_page(self):
        response = self.app.test.get('/additional-examples')
        self.assertEqual(response.status_code, 200, "The additional-examples content page should exist")

    def test_render_common_error_page(self):
        response = self.app.test.get('/common-errors')
        self.assertEqual(response.status_code, 200, "The common-errors content page should exist")

    def test_render_dictionary_form(self):
        response = self.app.test.get('/dictionary')
        self.assertEqual(response.status_code, 200, "The dictionary content page should exist")

    def test_render_events_form(self):
        response = self.app.test.get('/events')
        self.assertEqual(response.status_code, 200, "The events content page should exist")

    def test_render_hed_services_form(self):
        response = self.app.test.get('/hed-services')
        self.assertEqual(response.status_code, 200, "The hed-services content page should exist")

    def test_render_hedstring_form(self):
        response = self.app.test.get('/hedstring')
        self.assertEqual(response.status_code, 200, "The hedstring content page should exist")

    def test_render_help_page(self):
        response = self.app.test.get('/hed-tools-help')
        self.assertEqual(response.status_code, 200, "The hed-tools-help content page should exist" )

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
