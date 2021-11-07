import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from tests.test_web_base import TestWebBase
import hed.schema as hedschema
from hed.models.hed_string import HedString
from hedweb.constants import base_constants


class Test(TestWebBase):
    def test_get_input_from_string_form_empty(self):
        from hedweb.strings import get_input_from_form
        self.assertRaises(TypeError, get_input_from_form, {},
                          "An exception is raised if an empty request is passed to get_input_from_form")

    def test_get_input_from_string_form(self):
        from hed.schema import HedSchema
        from hedweb.strings import get_input_from_form
        with self.app.test:
            environ = create_environ(data={base_constants.STRING_INPUT: 'Red,Blue',
                                           base_constants.SCHEMA_VERSION: '8.0.0',
                                           base_constants.CHECK_FOR_WARNINGS: 'on',
                                           base_constants.COMMAND_OPTION: base_constants.COMMAND_VALIDATE})
            request = Request(environ)
            arguments = get_input_from_form(request)
            self.assertIsInstance(arguments[base_constants.STRING_LIST], list,
                                  "get_input_from_form should have a string list")
            self.assertIsInstance(arguments[base_constants.SCHEMA], HedSchema,
                                  "get_input_from_form should have a HED schema")
            self.assertEqual(base_constants.COMMAND_VALIDATE, arguments[base_constants.COMMAND],
                             "get_input_from_form should have a command")
            self.assertTrue(arguments[base_constants.CHECK_FOR_WARNINGS],
                            "get_input_from_form should have check_warnings true when on")

    def test_string_process(self):
        from hedweb.strings import process
        from hed.errors.exceptions import HedFileError
        arguments = {}
        try:
            process(arguments)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f"string_process threw wrong exception {type(ex).__name__} when unexpected error")
        else:
            self.fail('string_process should have thrown a HedFileError exception string_list is empty')

    def test_string_convert_to_short_invalid(self):
        from hedweb.strings import convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = [HedString('Red, Blue')]

        with self.app.app_context():
            results = convert(hed_schema, string_list)
            self.assertEqual('warning', results['msg_category'], "hedstring_convert issue warning if unsuccessful")

    def test_string_convert_to_short_valid(self):
        from hedweb.strings import convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = [HedString('Property/Informational-property/Description/Blech, Blue')]
        with self.app.app_context():
            results = convert(hed_schema, string_list, base_constants.COMMAND_TO_SHORT)
            data = results['data']
            self.assertTrue(data, 'convert string to short returns data')
            self.assertIsInstance(data, list, "convert string to short returns data in a list")
            self.assertEqual("Description/Blech,Blue", data[0],
                             "convert string to short returns the correct short form.")
            self.assertEqual('success', results['msg_category'],
                             "hedstring_convert should return success if converted")

    def test_string_convert_to_long(self):
        from hedweb.strings import convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = [HedString('Red'), HedString('Blue')]

        with self.app.app_context():
            results = convert(hed_schema, string_list, command=base_constants.COMMAND_TO_LONG)
            self.assertEqual('warning', results['msg_category'], "hedstring_convert issue warning if unsuccessful")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = convert(hed_schema, string_list, command=base_constants.COMMAND_TO_LONG)
            self.assertEqual('success', results['msg_category'],
                             "hedstring_convert should return success if converted")

    def test_string_validate(self):
        from hedweb.strings import validate
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = [HedString('Red'), HedString('Blue')]

        with self.app.app_context():
            results = validate(hed_schema, string_list)
            self.assertEqual('warning', results['msg_category'], "validate has warning if validation errors")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = validate(hed_schema, string_list)
            self.assertEqual('success', results['msg_category'], "validate should return success if converted")


if __name__ == '__main__':
    unittest.main()
