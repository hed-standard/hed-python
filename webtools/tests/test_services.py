import os
import io
import json
import shutil
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
import sys
sys.path.append('hedtools')
from hed import schema as hedschema
from hed import models
from hedweb.constants import common

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

    def test_get_input_from_service_request_empty(self):
        from hedweb.services import get_input_from_service_request
        self.assertRaises(TypeError, get_input_from_service_request, {},
                          "An exception should be raised if an empty request is passed")
        self.assertTrue(1, "Testing get_input_from_service_request")

    def test_get_input_from_service_request(self):
        from hed.models.sidecar import Sidecar
        from hed.schema import HedSchema
        from hedweb.services import get_input_from_service_request
        with self.app.test:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events_alpha.json')
            events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events.tsv')
            with open(json_path, 'rb') as fp:
                json_string = fp.read().decode('ascii')
            json_data = {common.JSON_STRING: json_string, common.CHECK_FOR_WARNINGS: 'on',
                         common.SCHEMA_VERSION: '8.0.0-alpha.1', common.SERVICE: 'sidecar_validate'}
            environ = create_environ(json=json_data)
            request = Request(environ)
            arguments = get_input_from_service_request(request)
            self.assertIsInstance(arguments[common.JSON_SIDECAR], Sidecar,
                                  "get_input_from_service_request should have a sidecar object")
            self.assertIsInstance(arguments[common.SCHEMA], HedSchema,
                                  "get_input_from_service_request should have a HED schema")
            self.assertEqual('sidecar_validate', arguments[common.SERVICE],
                             "get_input_from_service_request should have a service request")
            self.assertTrue(arguments[common.CHECK_FOR_WARNINGS],
                            "get_input_from_service_request should have check_for_warnings true when on")

    def test_services_process_empty(self):
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

    def test_process_services_sidecar(self):
        from hedweb.services import services_process
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        with open(json_path) as f:
            data = json.load(f)
        json_text = json.dumps(data)
        fb = io.StringIO(json_text)
        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml-test/HED8.0.0-beta.4.xml'
        hed_schema = hedschema.load_schema(hed_url_path=schema_url)
        json_sidecar = models.Sidecar(file=fb, name='JSON_Sidecar')
        arguments = {common.SERVICE: 'sidecar_validate', common.SCHEMA: hed_schema,
                     common.JSON_SIDECAR: json_sidecar}
        with self.app.app_context():
            response = services_process(arguments)
            self.assertFalse(response['error_type'],
                             'sidecar_validation services should not have a fatal error when file is invalid')
            results = response['results']
            self.assertEqual('success', results['msg_category'],
                             "sidecar_validation services has success on bids_events.json")
            self.assertEqual('8.0.0-beta.4', results[common.SCHEMA_VERSION], 'Version 8.0.0.-beta.4 was used')

        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml/HED7.2.0.xml'
        arguments[common.SCHEMA] = hedschema.load_schema(hed_url_path=schema_url)
        with self.app.app_context():
            response = services_process(arguments)
            self.assertFalse(response['error_type'],
                             'sidecar_validation services should not have a error when file is valid')
            results = response['results']
            self.assertTrue(results['data'], 'sidecar_validation produces errors when file not valid')
            self.assertEqual('warning', results['msg_category'], "sidecar_validation did not valid with 7.2.0")
            self.assertEqual('7.2.0', results['schema_version'], 'Version 7.2.0 was used')


if __name__ == '__main__':
    unittest.main()
