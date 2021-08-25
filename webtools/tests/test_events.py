import os
import shutil
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

import sys
sys.path.append('hedtools')
from hed import schema as hedschema
from hed import models
from hed.errors.exceptions import HedFileError
from hedweb.constants import common
from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed import schema as hedschema
            hedschema.set_cache_directory(app.config['HED_CACHE_FOLDER'])
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

    def test_get_input_from_events_form_empty(self):
        from hedweb.events import get_input_from_events_form
        self.assertRaises(TypeError, get_input_from_events_form, {},
                          "An exception should be raised if an empty request is passed")
        self.assertTrue(1, "Testing get_input_from_events_form")

    # def test_get_input_from_events_form(self):
    #     from hed.models import EventsInput
    #     from hed.schema import HedSchema
    #     from hedweb.events import get_input_from_events_form
    #     with self.app.test:
    #         json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events_alpha.json')
    #         events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/bids_events.tsv')
    #         with open(json_path, 'rb') as fp:
    #             with open(events_path, 'rb') as fpe:
    #                 environ = create_environ(data={common.JSON_FILE: fp, common.SCHEMA_VERSION: '8.0.0-alpha.1',
    #                                          common.EVENTS_FILE: fpe, common.DEFS_EXPAND: 'on',
    #                                          common.COMMAND_OPTION: common.COMMAND_ASSEMBLE})
    #         request = Request(environ)
    #         arguments = get_input_from_events_form(request)
    #         self.assertIsInstance(arguments[common.EVENTS], EventsInput,
    #                               "get_input_from_events_form should have an events object")
    #         self.assertIsInstance(arguments[common.SCHEMA], HedSchema,
    #                               "get_input_from_events_form should have a HED schema")
    #         self.assertEqual(common.COMMAND_ASSEMBLE, arguments[common.COMMAND],
    #                          "get_input_from_events_form should have a command")
    #         self.assertTrue(arguments[common.DEFS_EXPAND],
    #                         "get_input_from_events_form should have defs_expand true when on")

    def test_events_process_empty_file(self):
        # Test for empty events_path
        from hedweb.events import events_process
        arguments = {'events_path': ''}
        try:
            events_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('events_process threw the wrong exception when events_path was empty')
        else:
            self.fail('events_process should have thrown a HedFileError exception when events_path was empty')

    def test_events_process(self):
        from hedweb.events import events_process
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.4.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        events = models.EventsInput(file=events_path, sidecars=json_sidecar, name='bids_events')
        arguments = {common.EVENTS: events, common.COMMAND: common.COMMAND_VALIDATE, common.DEFS_EXPAND: True,
                     common.CHECK_FOR_WARNINGS: True, common.SCHEMA: hed_schema}
        with self.app.app_context():
            results = events_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'events_process validation should return a result dictionary when validation errors')
            self.assertEqual('success', results['msg_category'],
                             'events_process validate should return success if no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        arguments[common.SCHEMA] = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = events_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'events_process validation should return a dictionary when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'events_process validate should give warning when errors')
            self.assertTrue(results["data"], 'events_process validate should return data when errors')

    def test_events_assemble(self):
        from hedweb.events import events_assemble
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.4.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        events = models.EventsInput(file=events_path, sidecars=json_sidecar,name='bids_events')
        with self.app.app_context():
            results = events_assemble(hed_schema, events, defs_expand=True)
            self.assertTrue('data' in results,
                            'events_assemble results should have a data key when no errors')
            self.assertEqual('success', results["msg_category"],
                             'events_assemble msg_category should be success when no errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = events_assemble(hed_schema, events, defs_expand=True)
            self.assertTrue(results['data'],
                            'events_assemble results should have a data key when errors')
            self.assertEqual('warning', results['msg_category'],
                             'events_assemble msg_category should be warning when errors')

    def test_events_validate(self):
        from hedweb.events import events_validate
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_sidecar = models.Sidecar(file=json_path, name='bids_json')
        events = models.EventsInput(file=events_path, sidecars=json_sidecar, name='bids_events')
        with self.app.app_context():
            results = events_validate(hed_schema, events)
            self.assertTrue(results['data'],
                            'events_validate results should have a data key when validation errors')
            self.assertEqual('warning', results["msg_category"],
                             'events_validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.4.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = events_validate(hed_schema, events)
            self.assertFalse(results['data'],
                             'events_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results['msg_category'],
                             'events_validate msg_category should be success when no errors')


if __name__ == '__main__':
    unittest.main()
