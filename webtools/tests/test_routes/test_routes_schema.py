import os
import io
import json
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

    def test_schema_version_results1(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.1.xml')
        with open(schema_path, 'r') as sc:
            x = sc.read()
        y = io.BytesIO(bytes(x, 'utf-8'))
        with self.app.app_context():
            response = self.app.test.post('/schema_version', content_type='multipart/form-data',
                                          data={'schema_path': (y, 'schema_path')})
            self.assertEqual(200, response.status_code, 'The HED version list does not require data')
            response_dict = json.loads(response.data.decode('utf-8'))
            self.assertEqual("8.0.0-alpha.1", response_dict["schema_version"], "The HED version should be returned")
        y.close()

if __name__ == '__main__':
    unittest.main()
