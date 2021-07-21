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

    def test_render_additional_examples_page(self):
        response = self.app.test.get('/additional-examples')
        self.assertEqual(response.status_code, 200, "The additional-examples content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_common_errors_page(self):
        response = self.app.test.get('/common-errors')
        self.assertEqual(response.status_code, 200, "The common-errors content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_dictionary_form(self):
        response = self.app.test.get('/dictionary')
        self.assertEqual(response.status_code, 200, "The dictionary content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_events_form(self):
        response = self.app.test.get('/events')
        self.assertEqual(response.status_code, 200, "The events content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_services_form(self):
        response = self.app.test.get('/services')
        self.assertEqual(response.status_code, 200, "The hed-services content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_hedstring_form(self):
        response = self.app.test.get('/string')
        self.assertEqual(response.status_code, 200, "The hedstring content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_help_page(self):
        response = self.app.test.get('/hed-tools-help')
        self.assertEqual(response.status_code, 200, "The hed-tools-help content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_home_page(self):
        response = self.app.test.get('/')
        self.assertEqual(response.status_code, 200, "The root hed home page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_schema_form(self):
        response = self.app.test.get('/schema')
        self.assertEqual(response.status_code, 200, "The schema page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_spreadsheet_form(self):
        response = self.app.test.get('/spreadsheet')
        self.assertEqual(response.status_code, 200, "The spreadsheet page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")


if __name__ == '__main__':
    unittest.main()
