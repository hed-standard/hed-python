import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from tests.test_web_base import TestWebBase
from hed import schema as hedschema
from hed import models
from hed.errors.exceptions import HedFileError
from hedweb.constants import base_constants


class Test(TestWebBase):
    cache_schemas = True

    def test_get_input_from_events_form_empty(self):
        from hedweb.events import get_input_from_events_form
        self.assertRaises(TypeError, get_input_from_events_form, {},
                          "An exception should be raised if an empty request is passed")
        self.assertTrue(1, "Testing get_input_from_events_form")

    def test_get_input_from_events_form(self):
        from hed.models import EventsInput
        from hed.schema import HedSchema
        from hedweb.events import get_input_from_events_form
        with self.app.test:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events.json')
            events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events.tsv')
            with open(json_path, 'rb') as fp:
                with open(events_path, 'rb') as fpe:
                    environ = create_environ(data={base_constants.JSON_FILE: fp, base_constants.SCHEMA_VERSION: '8.0.0',
                                             base_constants.EVENTS_FILE: fpe, base_constants.DEFS_EXPAND: 'on',
                                             base_constants.COMMAND_OPTION: base_constants.COMMAND_ASSEMBLE})
            request = Request(environ)
            arguments = get_input_from_events_form(request)
            self.assertIsInstance(arguments[base_constants.EVENTS], EventsInput,
                                  "get_input_from_events_form should have an events object")
            self.assertIsInstance(arguments[base_constants.SCHEMA], HedSchema,
                                  "get_input_from_events_form should have a HED schema")
            self.assertEqual(base_constants.COMMAND_ASSEMBLE, arguments[base_constants.COMMAND],
                             "get_input_from_events_form should have a command")
            self.assertTrue(arguments[base_constants.DEFS_EXPAND],
                            "get_input_from_events_form should have defs_expand true when on")

    def test_events_process_empty_file(self):
        # Test for empty events_path
        from hedweb.events import process
        arguments = {'events_path': ''}
        try:
            process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('process threw the wrong exception when events_path was empty')
        else:
            self.fail('process should have thrown a HedFileError exception when events_path was empty')

    def test_events_process(self):
        from hedweb.events import process
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        events = models.EventsInput(file=events_path, sidecars=json_sidecar, name='bids_events')
        arguments = {base_constants.EVENTS: events, base_constants.COMMAND: base_constants.COMMAND_VALIDATE,
                     base_constants.DEFS_EXPAND: True,
                     base_constants.CHECK_FOR_WARNINGS: True, base_constants.SCHEMA: hed_schema}
        with self.app.app_context():
            results = process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'process validation should return a result dictionary when validation errors')
            self.assertEqual('success', results['msg_category'],
                             'process validate should return success if no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        arguments[base_constants.SCHEMA] = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'process validation should return a dictionary when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'process validate should give warning when errors')
            self.assertTrue(results["data"], 'process validate should return data when errors')

    def test_events_assemble(self):
        from hedweb.events import assemble
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        events = models.EventsInput(file=events_path, sidecars=json_sidecar, name='bids_events')
        with self.app.app_context():
            results = assemble(hed_schema, events,  defs_expand=True)
            self.assertTrue('data' in results,
                            'assemble results should have a data key when no errors')
            self.assertEqual('success', results["msg_category"],
                             'assemble msg_category should be success when no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = assemble(hed_schema, events, defs_expand=True)
            self.assertTrue(results['data'],
                            'assemble results should have a data key when errors')
            self.assertEqual('warning', results['msg_category'],
                             'assemble msg_category should be warning when errors')

    def test_events_validate(self):
        from hedweb.events import validate
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        events = models.EventsInput(file=events_path, sidecars=json_sidecar, name='bids_events')
        with self.app.app_context():
            results = validate(hed_schema, events)
            self.assertTrue(results['data'],
                            'validate results should have a data key when validation errors')
            self.assertEqual('warning', results["msg_category"],
                             'validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = validate(hed_schema, events)
            self.assertFalse(results['data'],
                             'validate results should not have a data key when no validation errors')
            self.assertEqual('success', results['msg_category'],
                             'validate msg_category should be success when no errors')


if __name__ == '__main__':
    unittest.main()
