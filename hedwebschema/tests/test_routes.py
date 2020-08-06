import unittest
import os
from hed.webconverter.app_factory import AppFactory
import shutil


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed.webconverter import utils
            from hed.webconverter.routes import route_blueprint
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




if __name__ == '__main__':
    unittest.main()
