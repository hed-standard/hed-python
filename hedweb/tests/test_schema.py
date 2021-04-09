import os
import shutil
import unittest
from flask import Response
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

    def test_generate_input_from_schema_form(self):
        self.assertTrue(1, "Testing generate_input_from_schema_form")

    def test_schema_check(self):
        self.assertTrue(1, "Testing run_schema_compliance_check")

    def test_schema_convert(self):
        self.assertTrue(1, "Testing convert_schema")


if __name__ == '__main__':
    unittest.main()
