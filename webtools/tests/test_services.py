import os
import json
import shutil
import unittest

from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hedweb.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_services_process(self):
        from hedweb.services import services_process
        arguments = {'service': ''}
        response = services_process(arguments)
        self.assertEqual(response["error_type"], "HEDServiceMissing", "services_process must have a service key")

    def test_services_list(self):
        from hedweb.services import services_list
        with self.app.app_context():
            results = services_list()
            self.assertIsInstance(results, dict, "services_list returns a dictionary")
            self.assertTrue(results["data"], "services_list return dictionary has a data key with non empty value")

    def test_process_services_dictionary(self):
        from hedweb.services import services_process
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
        with open(json_path) as f:
            data = json.load(f)
        json_text = json.dumps(data)
        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml/HED8.0.0-alpha.1.xml'
        arguments = {'service': 'dictionary_validate', 'schema_url': schema_url, 'json_string': json_text}
        with self.app.app_context():
            response = services_process(arguments)
            self.assertFalse(response['error_type'],
                             'dictionary_validation services should not have a error when file is valid')
            results = response['results']
            self.assertEqual('success', results['msg_category'], "dictionary_validation services has success on good.json")
            self.assertEqual('8.0.0-alpha.1', results['schema_version'], 'Version 8.0.0.-alpha.1 was used')

        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml/HED7.2.0.xml'
        arguments = {'service': 'dictionary_validate', 'schema_url': schema_url, 'json_string': json_text}
        with self.app.app_context():
            response = services_process(arguments)
            self.assertFalse(response['error_type'],
                             'dictionary_validation services should not have a error when file is valid')
            results = response['results']
            self.assertTrue(results['data'], 'dictionary_validation produces errors when file not valid')
            self.assertEqual('warning', results['msg_category'], "dictionary_validation did not valid with 7.2.0")
            self.assertEqual('7.2.0', results['schema_version'], 'Version 7.2.0 was used')


if __name__ == '__main__':
    unittest.main()
