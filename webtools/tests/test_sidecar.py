import os
import unittest

from werkzeug.test import create_environ
from werkzeug.wrappers import Request
from tests.test_web_base import TestWebBase
import hed.schema as hedschema
from hed import models
from hedweb.constants import common


class Test(TestWebBase):
    def test_generate_input_from_sidecar_form_empty(self):
        from hedweb.sidecar import get_input_from_form
        self.assertRaises(TypeError, get_input_from_form, {},
                          "An exception should be raised if an empty request is passed")

    def test_generate_input_from_sidecar_form(self):
        from hed.models import Sidecar
        from hed.schema import HedSchema
        from hedweb.sidecar import get_input_from_form
        with self.app.test:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events.json')
            with open(json_path, 'rb') as fp:
                environ = create_environ(data={common.JSON_FILE: fp, common.SCHEMA_VERSION: '8.0.0',
                                         common.COMMAND_OPTION: common.COMMAND_TO_LONG})
            request = Request(environ)
            arguments = get_input_from_form(request)
            self.assertIsInstance(arguments[common.JSON_SIDECAR], Sidecar,
                                  "generate_input_from_sidecar_form should have a JSON dictionary")
            self.assertIsInstance(arguments[common.SCHEMA], HedSchema,
                                  "generate_input_from_sidecar_form should have a HED schema")
            self.assertEqual(common.COMMAND_TO_LONG, arguments[common.COMMAND],
                             "generate_input_from_sidecar_form should have a command")
            self.assertFalse(arguments[common.CHECK_WARNINGS_VALIDATE],
                             "generate_input_from_sidecar_form should have check for warnings false when not given")

    def test_sidecar_process_empty_file(self):
        from hedweb.sidecar import process
        from hed.errors.exceptions import HedFileError
        with self.app.app_context():
            arguments = {'json_path': ''}
            try:
                process(arguments)
            except HedFileError:
                pass
            except Exception:
                self.fail('process threw the wrong exception when sidecar path was empty')
            else:
                self.fail('process should have thrown a HedFileError exception when json_path was empty')

    def test_sidecar_process(self):
        from hedweb.sidecar import process
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        arguments = {common.SCHEMA: hed_schema, common.JSON_SIDECAR: json_sidecar,
                     common.JSON_DISPLAY_NAME: 'bids_json', common.COMMAND: common.COMMAND_TO_SHORT}
        with self.app.app_context():
            results = process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'process to short should return a dictionary when errors')
            self.assertEqual('warning', results['msg_category'],
                             'process to short should give warning when JSON with errors')
            self.assertTrue(results['data'],
                            'process to short should not convert using HED 7.1.2.xml')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        arguments = {common.SCHEMA: hed_schema, common.JSON_SIDECAR: json_sidecar,
                     common.JSON_DISPLAY_NAME: 'bids_json', common.COMMAND: common.COMMAND_TO_SHORT}

        with self.app.app_context():
            results = process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'process to short should return a dict when no errors')
            self.assertEqual('success', results['msg_category'],
                             'process to short should return success if converted')

    def test_sidecar_convert_to_long(self):
        from hed import models
        from hedweb.sidecar import sidecar_convert
        from hedweb.constants import common
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        json_sidecar = models.Sidecar(file=json_path, name='bids_events')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = sidecar_convert(hed_schema, json_sidecar, command=common.COMMAND_TO_LONG)
            self.assertTrue(results['data'],
                            'sidecar_convert to long results should have data key')
            self.assertEqual('warning', results['msg_category'],
                             'sidecar_convert to long msg_category should be warning for errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = sidecar_convert(hed_schema, json_sidecar, command=common.COMMAND_TO_LONG)
            self.assertTrue(results['data'],
                            'sidecar_convert to long results should have data key')
            self.assertEqual('success', results["msg_category"],
                             'sidecar_convert to long msg_category should be success when no errors')

    def test_sidecar_convert_to_short(self):
        from hed import models
        from hedweb.sidecar import sidecar_convert
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        json_sidecar = models.Sidecar(file=json_path, name='bids_events')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = sidecar_convert(hed_schema, json_sidecar)
            self.assertTrue(results['data'], 'sidecar_convert results should have data key')
            self.assertEqual('warning', results['msg_category'],
                             'sidecar_convert msg_category should be warning for errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = sidecar_convert(hed_schema, json_sidecar)
            self.assertTrue(results['data'], 'sidecar_convert results should have data key')
            self.assertEqual('success', results['msg_category'],
                             'sidecar_convert msg_category should be success when no errors')

    def test_sidecar_validate(self):
        from hed import models
        from hedweb.sidecar import sidecar_validate
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        json_sidecar = models.Sidecar(file=json_path, name='bids_events')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = sidecar_validate(hed_schema, json_sidecar)
            self.assertTrue(results['data'],
                            'sidecar_validate results should have a data key when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'sidecar_validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = sidecar_validate(hed_schema, json_sidecar)
            self.assertFalse(results['data'],
                             'sidecar_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results["msg_category"],
                             'sidecar_validate msg_category should be success when no errors')


if __name__ == '__main__':
    unittest.main()
