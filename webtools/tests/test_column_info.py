import os
import shutil
import unittest

import hed.schema as hedschema
from hed import models
from hedweb.constants import common

from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    def test_generate_input_from_dictionary_form(self):
        from hedweb.dictionary import get_input_from_dictionary_form
        self.assertRaises(TypeError, get_input_from_dictionary_form, {},
                          "An exception should be raised if an empty request is passed")

    def test_dictionary_process_empty_file(self):
        from hedweb.dictionary import dictionary_process
        from hed.errors.exceptions import HedFileError
        with self.app.app_context():
            arguments = {'json_path': ''}
            try:
                dictionary_process(arguments)
            except HedFileError:
                pass
            except Exception:
                self.fail('dictionary_process threw the wrong exception when dictionary-path was empty')
            else:
                self.fail('dictionary_process should have thrown a HedFileError exception when json_path was empty')

    def test_dictionary_process(self):
        from hedweb.dictionary import dictionary_process
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        json_dictionary = models.ColumnDefGroup(json_filename=json_path, display_name='bids_json')
        arguments = {common.SCHEMA: hed_schema, common.JSON_DICTIONARY: json_dictionary,
                     common.JSON_DISPLAY_NAME: 'bids_json', common.COMMAND: common.COMMAND_TO_SHORT}
        with self.app.app_context():
            results = dictionary_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'dictionary_process to short should return a dictionary when errors')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_process to short should give warning when JSON with errors')
            self.assertTrue(results['data'],
                            'dictionary_process to short should not convert using HED 7.1.2.xml')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        arguments = {common.SCHEMA: hed_schema, common.JSON_DICTIONARY: json_dictionary,
                     common.JSON_DISPLAY_NAME: 'bids_json', common.COMMAND: common.COMMAND_TO_SHORT}

        with self.app.app_context():
            results = dictionary_process(arguments)
            self.assertTrue(isinstance(results, dict),
                            'dictionary_process to short should return a dict when no errors')
            self.assertEqual('success', results['msg_category'],
                             'dictionary_process to short should return success if converted')

    def test_dictionary_convert_to_long(self):
        from hed import models
        from hedweb.dictionary import dictionary_convert
        from hedweb.constants import common
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        json_dictionary = models.ColumnDefGroup(json_filename=json_path, display_name='bids_events')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        arguments = {common.SCHEMA: hed_schema,
                     'json_dictionary': json_dictionary, common.COMMAND: common.COMMAND_TO_LONG}
        with self.app.app_context():
            results = dictionary_convert(hed_schema, json_dictionary, command=common.COMMAND_TO_LONG)
            self.assertTrue(results['data'],
                            'dictionary_convert to long results should have data key')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_convert to long msg_category should be warning for errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = dictionary_convert(hed_schema, json_dictionary, command=common.COMMAND_TO_LONG)
            self.assertTrue(results['data'],
                            'dictionary_convert to long results should have data key')
            self.assertEqual('success', results["msg_category"],
                             'dictionary_convert to long msg_category should be success when no errors')

    def test_dictionary_convert_to_short(self):
        from hed import models
        from hedweb.dictionary import dictionary_convert
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        json_dictionary = models.ColumnDefGroup(json_filename=json_path, display_name='bids_events')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = dictionary_convert(hed_schema, json_dictionary)
            self.assertTrue(results['data'], 'dictionary_convert results should have data key')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_convert msg_category should be warning for errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = dictionary_convert(hed_schema, json_dictionary)
            self.assertTrue(results['data'], 'dictionary_convert results should have data key')
            self.assertEqual('success', results['msg_category'],
                             'dictionary_convert msg_category should be success when no errors')

    def test_dictionary_validate(self):
        from hed import models
        from hedweb.dictionary import dictionary_validate
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
        json_dictionary = models.ColumnDefGroup(json_filename=json_path, display_name='bids_events')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = dictionary_validate(hed_schema, json_dictionary)
            self.assertTrue(results['data'],
                            'dictionary_validate results should have a data key when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-beta.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = dictionary_validate(hed_schema, json_dictionary)
            self.assertFalse(results['data'],
                             'dictionary_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results["msg_category"],
                             'dictionary_validate msg_category should be success when no errors')


if __name__ == '__main__':
    unittest.main()
