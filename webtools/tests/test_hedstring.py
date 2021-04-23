import os
import shutil
import unittest

from hedweb.app_factory import AppFactory, hedstring


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
        self.assertRaises(TypeError, hedstring.generate_input_from_hedstring_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_hedstring")

    def test_hedstring_process(self):
        from hedweb.hedstring import hedstring_process
        from hed.util.exceptions import HedFileError
        arguments = {'hedstring': ''}
        try:
            a = hedstring_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('dictionary_process threw the wrong exception when dictionary-path was empty')
        else:
            self.fail('dictionary_process should have thrown a HedFileError exception when json-path was empty')

    def test_hedstring_convert(self):
        from hedweb.hedstring import hedstring_convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED 7.1.2.xml',
                     'hedstring': 'Red, Blue'}
        with self.app.app_context():
            response = hedstring_convert(arguments)
            self.assertEqual('warning', response['category'], "hedstring_convert issue warning if unsuccessful")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED8.0.0-alpha.1.xml',
                     'hedstring': 'Red, Blue'}
        with self.app.app_context():
            response = hedstring_convert(arguments)
            self.assertEqual('success', response['category'], "hedstring_convert should return success if converted")

    def test_hedstring_validate(self):
        from hedweb.hedstring import hedstring_validate
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED 7.1.2.xml',
                     'hedstring': 'Red, Blue'}
        with self.app.app_context():
            response = hedstring_validate(arguments)
            self.assertEqual('warning', response['category'], "hedstring_validate has warning if validation errors")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        arguments = {'hed-xml-file': schema_path, 'hed-display-name': 'HED8.0.0-alpha.1.xml',
                     'hedstring': 'Red, Blue'}
        with self.app.app_context():
            response = hedstring_validate(arguments)
            self.assertEqual('success', response['category'], "hedstring_validate should return success if converted")


if __name__ == '__main__':
    unittest.main()