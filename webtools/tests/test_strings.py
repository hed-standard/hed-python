import os
import shutil
import unittest

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

    def test_generate_input_from_hedstring_form(self):
        from hedweb.strings import generate_input_from_string_form
        self.assertRaises(TypeError, generate_input_from_string_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_hedstring")

    def test_string_process(self):
        from hedweb.strings import string_process
        from hed.util.exceptions import HedFileError
        arguments = {'string_list': ''}
        try:
            string_process(arguments)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail('string_process threw the wrong exception when unexpected error')
        else:
            self.fail('string_process should have thrown a HedFileError exception string_list is empty')

    def test_string_convert_to_long(self):
        from hedweb.strings import string_convert
        from hedweb.constants import common
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.COMMAND: common.COMMAND_TO_LONG, common.SCHEMA_PATH: schema_path,
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     common.SCHEMA_DISPLAY_NAME: 'HED 7.1.2.xml', 'string_list': ['Red, Blue']}
        with self.app.app_context():
            response = string_convert(arguments)
            self.assertEqual('warning', response['msg_category'], "hedstring_convert issue warning if unsuccessful")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {common.COMMAND: common.COMMAND_TO_LONG, common.SCHEMA_PATH: schema_path,
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     common.SCHEMA_DISPLAY_NAME: 'HED8.0.0-alpha.1.xml', 'string_list': ['Red, Blue']}
        with self.app.app_context():
            response = string_convert(arguments)
            self.assertEqual('success', response['msg_category'],
                             "hedstring_convert should return success if converted")

    def test_string_validate(self):
        from hedweb.strings import string_validate
        from hedweb.constants import common
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {common.COMMAND: common.COMMAND_VALIDATE,
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     common.SCHEMA_PATH: schema_path, common.SCHEMA_DISPLAY_NAME: 'HED 7.1.2.xml',
                     'string_list': ['Red, Blue']}
        with self.app.app_context():
            response = string_validate(arguments)
            self.assertEqual('warning', response['msg_category'], "string_validate has warning if validation errors")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {common.COMMAND: common.COMMAND_VALIDATE,
                     common.CHECK_FOR_WARNINGS: True, common.DEFS_EXPAND: True,
                     common.SCHEMA_PATH: schema_path, common.SCHEMA_DISPLAY_NAME: 'HED8.0.0-alpha.1.xml',
                     'string_list': ['Red, Blue']}
        with self.app.app_context():
            response = string_validate(arguments)
            self.assertEqual('success', response['msg_category'], "string_validate should return success if converted")


if __name__ == '__main__':
    unittest.main()
