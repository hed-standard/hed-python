import os
import shutil
import unittest
from flask import Response
from hedweb.app_factory import AppFactory


def test_dictionaries():
    base_path = os.path.dirname(os.path.abspath(__file__))
    test_dict = {'schema_xml_file': os.path.join(base_path, 'data/HED8.0.0-alpha.1.xml'),
                 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                 'json_path': os.path.join(base_path, 'data/short_form_valid.json'),
                 'json_file': 'short_form_valid.json',
                 'check-for-warnings': True}
    return test_dict


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
        from hedweb.dictionary import generate_input_from_dictionary_form
        self.assertRaises(TypeError, generate_input_from_dictionary_form, {},
                          "An exception should be raised if an empty request is passed")

    def test_dictionary_process_empty_file(self):
        from hedweb.dictionary import dictionary_process
        from hed.util.exceptions import HedFileError
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
        from hedweb.constants import common
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED 7.1.2.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', 'command': common.COMMAND_TO_SHORT}
        with self.app.app_context():
            response = dictionary_process(arguments)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_process to short should return a response object when errors')
            headers = dict(response.headers)
            self.assertEqual('warning', headers['Category'],
                             'dictionary_process to short should give warning when JSON with errors')
            self.assertTrue(response.data,
                            'dictionary_process to short should not convert using HED 7.1.2.xml')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', 'command': common.COMMAND_TO_SHORT}
        with self.app.app_context():
            response = dictionary_process(arguments)
            self.assertTrue(isinstance(response, Response),
                            'dictionary_process to short should return a response object when no errors')
            headers = dict(response.headers)
            self.assertEqual('success', headers['Category'],
                             'dictionary_process to short should return success if converted')

    def test_dictionary_convert_to_long(self):
        from hedweb.dictionary import dictionary_convert
        from hedweb.constants import common
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED 7.1.2.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', common.COMMAND: common.COMMAND_TO_LONG}
        with self.app.app_context():
            results = dictionary_convert(arguments)
            self.assertTrue(results['data'],
                            'dictionary_convert to long results should have data key')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_convert to long msg_category should be warning for errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', common.COMMAND: common.COMMAND_TO_LONG}
        with self.app.app_context():
            results = dictionary_convert(arguments)
            self.assertTrue(results['data'],
                            'dictionary_convert to long results should have data key')
            self.assertEqual('success', results["msg_category"],
                             'dictionary_convert to long msg_category should be success when no errors')

    def test_dictionary_convert_to_short(self):
        from hedweb.dictionary import dictionary_convert
        from hedweb.constants import common
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED 7.1.2.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', common.COMMAND: common.COMMAND_TO_SHORT}
        with self.app.app_context():
            results = dictionary_convert(arguments)
            self.assertTrue(results['data'], 'dictionary_convert results should have data key')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_convert msg_category should be warning for errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', common.COMMAND: common.COMMAND_VALIDATE}
        with self.app.app_context():
            results = dictionary_convert(arguments)
            self.assertTrue(results['data'], 'dictionary_convert results should have data key')
            self.assertEqual('success', results['msg_category'],
                             'dictionary_convert msg_category should be success when no errors')

    def test_dictionary_validate(self):
        from hedweb.dictionary import dictionary_validate
        from hedweb.constants import common
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/good_events.json')
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED 7.1.2.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', common.COMMAND: common.COMMAND_VALIDATE}
        with self.app.app_context():
            results = dictionary_validate(arguments)
            self.assertTrue(results['data'],
                            'dictionary_validate results should have a data key when validation errors')
            self.assertEqual('warning', results['msg_category'],
                             'dictionary_validate msg_category should be warning when errors')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                     'json_path': json_path, 'json_file': 'good_events.json', common.COMMAND: common.COMMAND_VALIDATE}
        with self.app.app_context():
            results = dictionary_validate(arguments)
            self.assertFalse(results['data'],
                             'dictionary_validate results should not have a data key when no validation errors')
            self.assertEqual('success', results["msg_category"],
                             'dictionary_validate msg_category should be success when no errors')


if __name__ == '__main__':
    unittest.main()
