import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
from tests.test_web_base import TestWebBase


class Test(TestWebBase):
    def test_generate_input_from_schema_form_empty(self):
        from hedweb.schema import get_input_from_form
        self.assertRaises(TypeError, get_input_from_form, {},
                          "An exception is raised if an empty request is passed to generate_input_from_schema")

    def test_get_input_from_schema_form_valid(self):
        from hed.schema import HedSchema
        from hedweb.constants import base_constants
        from hedweb.schema import get_input_from_form
        with self.app.test:
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/HED8.0.0.xml')
            with open(schema_path, 'rb') as fp:
                environ = create_environ(data={base_constants.SCHEMA_FILE: fp,
                                               base_constants.SCHEMA_UPLOAD_OPTIONS: base_constants.SCHEMA_FILE_OPTION,
                                               base_constants.COMMAND_OPTION:  base_constants.COMMAND_CONVERT})
            request = Request(environ)
            arguments = get_input_from_form(request)
            self.assertIsInstance(arguments[base_constants.SCHEMA], HedSchema,
                                  "get_input_from_form should have a HED schema")
            self.assertEqual(base_constants.COMMAND_CONVERT, arguments[base_constants.COMMAND],
                             "get_input_from_form should have a command")
            self.assertFalse(arguments[base_constants.CHECK_FOR_WARNINGS],
                             "get_input_from_form should have check_warnings false when not given")

    def test_schema_process(self):
        from hedweb.schema import process
        from hed.errors.exceptions import HedFileError
        arguments = {'schema_path': ''}
        try:
            process(arguments)
        except HedFileError:
            pass
        except Exception:
            self.fail('process threw the wrong exception when schema_path was empty')
        else:
            self.fail('process should have thrown a HedFileError exception when schema_path was empty')

    def test_schema_check(self):
        from hedweb.schema import schema_validate
        from hed import schema as hedschema
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED7.2.0.xml'
        with self.app.app_context():
            results = schema_validate(hed_schema, display_name)
            self.assertTrue(results['data'], "HED 7.2.0 is not HED-3G compliant")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED8.0.0.xml'
        with self.app.app_context():
            results = schema_validate(hed_schema, display_name)
            self.assertFalse(results['data'], "HED8.0.0 is HED-3G compliant")

    def test_schema_convert(self):
        from hedweb.schema import schema_convert
        from hed import schema as hedschema
        from hed.errors.exceptions import HedFileError

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED7.2.0.xml'
        with self.app.app_context():
            results = schema_convert(hed_schema, display_name)
            self.assertTrue(results['data'], "HED 7.2.0.xml can be converted to mediawiki")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        display_name = 'HED8.0.0.4.xml'
        with self.app.app_context():
            results = schema_convert(hed_schema, display_name)
            self.assertTrue(results['data'], "HED 8.0.0.xml can be converted to mediawiki")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HEDbad.xml')
        display_name = 'HEDbad.xml'
        with self.app.app_context():
            try:
                hed_schema = hedschema.load_schema(hed_file_path=schema_path)
                schema_convert(hed_schema, display_name)
            except HedFileError:
                pass
            except Exception as ex:
                self.fail(f"schema_convert threw {type(ex).__name__} for invalid schema file header")
            else:
                self.fail('process should throw HedFileError when the schema file header was invalid')


if __name__ == '__main__':
    unittest.main()
