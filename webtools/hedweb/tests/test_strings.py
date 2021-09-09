import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from hedweb.tests.test_web_base import TestWebBase
import hed.schema as hedschema
from hedweb.constants import common


class Test(TestWebBase):
    def test_get_input_from_string_form_empty(self):
        from hedweb.strings import get_input_from_string_form
        self.assertRaises(TypeError, get_input_from_string_form, {},
                          "An exception is raised if an empty request is passed to get_input_from_string_form")

    def test_get_input_from_string_form(self):
        from hed.schema import HedSchema
        from hedweb.strings import get_input_from_string_form
        with self.app.test:
            environ = create_environ(data={common.STRING_INPUT: 'Red,Blue', common.SCHEMA_VERSION: '8.0.0',
                                           common.CHECK_FOR_WARNINGS_VALIDATE: 'on',
                                           common.COMMAND_OPTION: common.COMMAND_VALIDATE})
            request = Request(environ)
            arguments = get_input_from_string_form(request)
            self.assertIsInstance(arguments[common.STRING_LIST], list,
                                  "get_input_from_string_form should have a string list")
            self.assertIsInstance(arguments[common.SCHEMA], HedSchema,
                                  "get_input_from_string_form should have a HED schema")
            self.assertEqual(common.COMMAND_VALIDATE, arguments[common.COMMAND],
                             "get_input_from_string_form should have a command")
            self.assertTrue(arguments[common.CHECK_FOR_WARNINGS_VALIDATE],
                            "get_input_from_string_form should have check_for_warnings true when on")

    def test_string_process(self):
        from hedweb.strings import string_process
        from hed.errors.exceptions import HedFileError
        arguments = {}
        try:
            string_process(arguments)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'string_process threw wrong exception when unexpected error')
        else:
            self.fail('string_process should have thrown a HedFileError exception string_list is empty')

    def test_string_convert_to_short_invalid(self):
        from hedweb.strings import string_convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = ['Red, Blue']

        with self.app.app_context():
            results = string_convert(hed_schema, string_list)
            self.assertEqual('warning', results['msg_category'], "hedstring_convert issue warning if unsuccessful")

    def test_string_convert_to_short_valid(self):
        from hedweb.strings import string_convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = ['Property/Informational-property/Description/Blech, Blue']
        with self.app.app_context():
            results = string_convert(hed_schema, string_list, common.COMMAND_TO_SHORT)
            data = results['data']
            self.assertTrue(data, 'convert string to short returns data')
            self.assertIsInstance(data, list, "convert string to short returns data in a list")
            self.assertEqual("Description/Blech,Blue", data[0], "convert string to short returns the correct short form.")
            self.assertEqual('success', results['msg_category'],
                             "hedstring_convert should return success if converted")

    def test_string_convert_to_long(self):
        from hedweb.strings import string_convert
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = ['Red, Blue']

        with self.app.app_context():
            results = string_convert(hed_schema, string_list, command=common.COMMAND_TO_LONG)
            self.assertEqual('warning', results['msg_category'], "hedstring_convert issue warning if unsuccessful")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)

        with self.app.app_context():
            results = string_convert(hed_schema, string_list, command=common.COMMAND_TO_LONG)
            self.assertEqual('success', results['msg_category'],
                             "hedstring_convert should return success if converted")

    def test_string_validate(self):
        from hedweb.strings import string_validate
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.2.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        string_list = ['Red, Blue']

        with self.app.app_context():
            results = string_validate(hed_schema, string_list)
            self.assertEqual('warning', results['msg_category'], "string_validate has warning if validation errors")

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
        hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        with self.app.app_context():
            results = string_validate(hed_schema, string_list)
            self.assertEqual('success', results['msg_category'], "string_validate should return success if converted")


if __name__ == '__main__':
    unittest.main()
