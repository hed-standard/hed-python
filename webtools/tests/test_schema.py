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

    def test_generate_input_from_schema_form(self):
        from hedweb.schema import get_input_from_schema_form
        self.assertRaises(TypeError, get_input_from_schema_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_schema")

    def test_schema_process(self):
        from hedweb.schema import schema_process
        from hed.errors.exceptions import HedFileError
        arguments = {'schema_path': ''}
        try:
            a = schema_process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('schema_process threw the wrong exception when schema_path was empty')
        else:
            self.fail('schema_process should have thrown a HedFileError exception when schema_path was empty')

    def test_schema_check(self):
        from hedweb.schema import schema_validate
        from hed import schema as hedschema
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED7.1.2.xml'
        with self.app.app_context():
            results = schema_validate(hed_schema, display_name)
            self.assertTrue(results['data'], "HED 7.1.2 is not HED-3G compliant")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED8.0.0-alpha.1.xml'
        with self.app.app_context():
            results = schema_validate(hed_schema, display_name)
            self.assertFalse(results['data'], "HED8.0.0-alpha.1 is HED-3G compliant")

    def test_schema_convert(self):
        from hedweb.schema import schema_convert
        from hed import schema as hedschema
        from hed.errors.exceptions import HedFileError

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED7.1.2.xml'
        with self.app.app_context():
            results = schema_convert(hed_schema, display_name)
            self.assertTrue(results['data'], "HED 7.1.2.xml can be converted to mediawiki")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED8.0.0-alpha.1.xml'
        with self.app.app_context():
            results = schema_convert(hed_schema, display_name)
            self.assertTrue(results['data'], "HED 8.0.0-alpha.1.xml can be converted to mediawiki")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HEDbad.xml')
        display_name = 'HEDbad.xml'
        with self.app.app_context():
            try:
                hed_schema = hedschema.load_schema(hed_file_path=schema_path)
                results = schema_convert(hed_schema, display_name)
            except HedFileError:
                pass
            except Exception:
                self.fail('schema_convert threw Exception instead of HedFileError for invalid schema file header')
            else:
                self.fail('schema_process should throw HedFileError when the schema file header was invalid')


if __name__ == '__main__':
    unittest.main()
