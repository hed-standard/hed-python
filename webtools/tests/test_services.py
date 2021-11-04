import os
import io
import json
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
from tests.test_web_base import TestWebBase
from hed import schema as hedschema
from hed import models
from hedweb.constants import base_constants


class Test(TestWebBase):
    def test_get_input_from_service_request_empty(self):
        from hedweb.services import get_input_from_request
        self.assertRaises(TypeError, get_input_from_request, {},
                          "An exception should be raised if an empty request is passed")
        self.assertTrue(1, "Testing get_input_from_request")

    def test_get_input_from_service_request(self):
        from hed.models.sidecar import Sidecar
        from hed.schema import HedSchema
        from hedweb.services import get_input_from_request
        with self.app.test:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events.json')
            with open(json_path, 'rb') as fp:
                json_string = fp.read().decode('ascii')
            json_data = {base_constants.JSON_STRING: json_string, base_constants.CHECK_FOR_WARNINGS: 'on',
                         base_constants.SCHEMA_VERSION: '8.0.0-alpha.1', base_constants.SERVICE: 'sidecar_validate'}
            environ = create_environ(json=json_data)
            request = Request(environ)
            arguments = get_input_from_request(request)
            self.assertIsInstance(arguments[base_constants.JSON_SIDECAR], Sidecar,
                                  "get_input_from_request should have a sidecar object")
            self.assertIsInstance(arguments[base_constants.SCHEMA], HedSchema,
                                  "get_input_from_request should have a HED schema")
            self.assertEqual('sidecar_validate', arguments[base_constants.SERVICE],
                             "get_input_from_request should have a service request")
            self.assertTrue(arguments[base_constants.CHECK_FOR_WARNINGS],
                            "get_input_from_request should have check_warnings true when on")

    def test_services_process_empty(self):
        from hedweb.services import process
        arguments = {'service': ''}
        response = process(arguments)
        self.assertEqual(response["error_type"], "HEDServiceMissing", "process must have a service key")

    def test_services_list(self):
        from hedweb.services import services_list
        with self.app.app_context():
            results = services_list()
            self.assertIsInstance(results, dict, "services_list returns a dictionary")
            self.assertTrue(results["data"], "services_list return dictionary has a data key with non empty value")

    def test_process_services_sidecar(self):
        from hedweb.services import process
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        with open(json_path) as f:
            data = json.load(f)
        json_text = json.dumps(data)
        fb = io.StringIO(json_text)
        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml/HED8.0.0.xml'
        hed_schema = hedschema.load_schema(hed_url_path=schema_url)
        json_sidecar = models.Sidecar(file=fb, name='JSON_Sidecar')
        arguments = {base_constants.SERVICE: 'sidecar_validate', base_constants.SCHEMA: hed_schema,
                     base_constants.COMMAND: 'validate', base_constants.COMMAND_TARGET: 'sidecar',
                     base_constants.JSON_SIDECAR: json_sidecar}
        with self.app.app_context():
            response = process(arguments)
            self.assertFalse(response['error_type'],
                             'sidecar_validation services should not have a fatal error when file is invalid')
            results = response['results']
            self.assertEqual('success', results['msg_category'],
                             "sidecar_validation services has success on bids_events.json")
            self.assertEqual('8.0.0', results[base_constants.SCHEMA_VERSION], 'Version 8.0.0 was used')

        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml/HED7.2.0.xml'
        arguments[base_constants.SCHEMA] = hedschema.load_schema(hed_url_path=schema_url)
        with self.app.app_context():
            response = process(arguments)
            self.assertFalse(response['error_type'],
                             'sidecar_validation services should not have a error when file is valid')
            results = response['results']
            self.assertTrue(results['data'], 'sidecar_validation produces errors when file not valid')
            self.assertEqual('warning', results['msg_category'], "sidecar_validation did not valid with 7.2.0")
            self.assertEqual('7.2.0', results['schema_version'], 'Version 7.2.0 was used')


if __name__ == '__main__':
    unittest.main()
