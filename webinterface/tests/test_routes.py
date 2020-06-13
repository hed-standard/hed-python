import unittest
import os
from web.app_factory import AppFactory
import shutil


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from web import utils
            from web.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            utils.create_upload_directory(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_render_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_delete_file_in_upload_directory(self):
        response = self.app.get('/delete/file_that_does_not_exist')
        self.assertEqual(response.status_code, 404)

    def test_get_hed_version_in_file(self):
        response = self.app.post('/get-hed-version')
        self.assertEqual(response.status_code, 400)

    def test_get_major_hed_versions(self):
        response = self.app.post('/get-major-hed-versions')
        self.assertEqual(response.status_code, 405)

    def test_get_spreadsheet_columns_info(self):
        response = self.app.post('/get-spreadsheet-columns-info')
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
