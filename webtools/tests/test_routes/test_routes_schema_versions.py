import os
import io
import json
import unittest
from werkzeug.datastructures import FileStorage
from tests.test_web_base import TestWebBase


class Test(TestWebBase):
    def test_schema_versions(self):
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
        with self.app.app_context():
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0.xml')
            with open(schema_path, 'r') as sc:
                x = sc.read()
            y = io.BytesIO(bytes(x, 'utf-8'))
            the_file = FileStorage(stream=y, filename='HED8.0.0.xml')
            data = {'schema_path': the_file}
            response = self.app.test.post('/schema_version', content_type='multipart/form-data', data=data)
            self.assertEqual(200, response.status_code, 'The HED version list does not require data')
            response_dict = json.loads(response.data.decode('utf-8'))
            self.assertEqual("8.0.0", response_dict["schema_version"], "The HED version should be returned")
            y.close()


if __name__ == '__main__':
    unittest.main()
