import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request, Response


from tests.test_web_base import TestWebBase


class Test(TestWebBase):

    def test_form_has_file(self):
        from hedweb.web_utils import form_has_file
        from hedweb.constants import file_constants
        with self.app.test as _:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.json')
            with open(json_path, 'rb') as fp:
                environ = create_environ(data={'json_file': fp})

            request = Request(environ)
            self.assertTrue(form_has_file(request, 'json_file'), "Form has file when no extension requirements")
            self.assertFalse(form_has_file(request, 'temp'), "Form does not have file when form name is wrong")
            self.assertFalse(form_has_file(request, 'json_file', file_constants.SPREADSHEET_EXTENSIONS),
                             "Form does not have file when extension is wrong")
            self.assertTrue(form_has_file(request, 'json_file', [".json"]),
                            "Form has file when extensions and form field match")

    def test_form_has_option(self):
        from hedweb.web_utils import form_has_option
        from hedweb.constants import base_constants
        with self.app.test as _:
            environ = create_environ(data={base_constants.CHECK_FOR_WARNINGS: 'on'})
            request = Request(environ)
            self.assertTrue(form_has_option(request, base_constants.CHECK_FOR_WARNINGS, 'on'),
                            "Form has the required option when set")
            self.assertFalse(form_has_option(request, base_constants.CHECK_FOR_WARNINGS, 'off'),
                             "Form does not have required option when target value is wrong one")
            self.assertFalse(form_has_option(request, 'blank', 'on'),
                             "Form does not have required option when option is not in the form")

    def test_form_has_url(self):
        from hedweb.web_utils import form_has_url
        from hedweb.constants import base_constants, file_constants
        with self.app.test as _:
            environ = create_environ(data={base_constants.SCHEMA_URL: 'https://www.google.com/my.json'})
            request = Request(environ)
            self.assertTrue(form_has_url(request, base_constants.SCHEMA_URL), "Form has a URL that is specified")
            self.assertFalse(form_has_url(request, 'temp'), "Form does not have a field that is not specified")
            self.assertFalse(form_has_url(request, base_constants.SCHEMA_URL, file_constants.SPREADSHEET_EXTENSIONS),
                             "Form does not URL with the wrong extension")

    def test_generate_download_file_from_text(self):
        from hedweb.web_utils import generate_download_file_from_text
        with self.app.test_request_context():
            the_text = 'The quick brown fox\nIs too slow'
            response = generate_download_file_from_text(the_text, 'temp',
                                                        msg_category='success', msg='Successful')
            self.assertIsInstance(response, Response,
                                  'Generate_response_download_file_from_text returns a response for string')
            self.assertEqual(200, response.status_code,
                             "Generate_response_download_file_from_text has status code 200 for string")
            header_content = dict(response.headers)
            self.assertEqual('success', header_content['Category'], "The msg_category is success")
            self.assertEqual('attachment filename=temp', header_content['Content-Disposition'],
                             "generate_download_file has the correct attachment file name")

    def test_generate_download_spreadsheet_excel(self):
        with self.app.test_request_context():
            from hed.models import HedInput
            from hedweb.constants import base_constants
            from hedweb.web_utils import generate_download_spreadsheet
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelOneSheet.xlsx')

            spreadsheet = HedInput(file=spreadsheet_path, file_type='.xlsx',
                                   tag_columns=[5], has_column_names=True,
                                   column_prefix_dictionary={2: 'Attribute/Informational/Label/',
                                                             4: 'Attribute/Informational/Description/'},
                                   name='ExcelOneSheet.xlsx')
            results = {base_constants.SPREADSHEET: spreadsheet,
                       base_constants.OUTPUT_DISPLAY_NAME: 'ExcelOneSheetA.xlsx'}
            response = generate_download_spreadsheet(results, msg_category='success', msg='Successful download')
            self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response for xlsx files')
            headers_dict = dict(response.headers)
            self.assertEqual(200, response.status_code, 'generate_download_spreadsheet should return status code 200')
            self.assertEqual('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response.mimetype,
                             "generate_download_spreadsheet should return spreadsheetml for excel files")
            self.assertTrue(headers_dict['Content-Disposition'].startswith('attachment; filename='),
                            "generate_download_spreadsheet excel should be downloaded as an attachment")

    def test_generate_download_spreadsheet_excel_code(self):
        with self.app.test_request_context():
            from hed.models import HedInput
            from hedweb.constants import base_constants
            from hedweb.web_utils import generate_download_spreadsheet
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelOneSheet.xlsx')

            spreadsheet = HedInput(file=spreadsheet_path, file_type='.xlsx',
                                   tag_columns=[5], has_column_names=True,
                                   column_prefix_dictionary={2: 'Attribute/Informational/Label/',
                                                             4: 'Attribute/Informational/Description/'},
                                   name='ExcelOneSheet.xlsx')
            results = {base_constants.SPREADSHEET: spreadsheet,
                       base_constants.OUTPUT_DISPLAY_NAME: 'ExcelOneSheetA.xlsx'}
            response = generate_download_spreadsheet(results, msg_category='success', msg='Successful download')
            self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response for tsv files')
            headers_dict = dict(response.headers)
            self.assertEqual(200, response.status_code, 'generate_download_spreadsheet should return status code 200')
            self.assertEqual('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response.mimetype,
                             "generate_download_spreadsheet should return spreadsheetml for excel files")
            self.assertTrue(headers_dict['Content-Disposition'].startswith('attachment; filename='),
                            "generate_download_spreadsheet excel should be downloaded as an attachment")

    def test_generate_download_spreadsheet_tsv(self):
        with self.app.test_request_context():
            from hed.models import HedInput
            from hedweb.constants import base_constants
            from hedweb.web_utils import generate_download_spreadsheet
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            'data/LKTEventCodesHED3.tsv')

            spreadsheet = HedInput(file=spreadsheet_path, file_type='.tsv',
                                   tag_columns=[5], has_column_names=True,
                                   column_prefix_dictionary={2: 'Attribute/Informational/Label/',
                                                             4: 'Attribute/Informational/Description/'},
                                   name='LKTEventCodesHED3.tsv')
            results = {base_constants.SPREADSHEET: spreadsheet,
                       base_constants.OUTPUT_DISPLAY_NAME: 'LKTEventCodesHED3.tsv'}
            response = generate_download_spreadsheet(results, msg_category='success', msg='Successful download')
            self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response for tsv files')
            headers_dict = dict(response.headers)
            self.assertEqual(200, response.status_code, 'generate_download_spreadsheet should return status code 200')
            self.assertEqual('text/plain charset=utf-8', response.mimetype,
                             "generate_download_spreadsheet should return text for tsv files")
            self.assertTrue(headers_dict['Content-Disposition'].startswith('attachment filename='),
                            "generate_download_spreadsheet tsv should be downloaded as an attachment")

    def test_generate_filename(self):
        from hedweb.web_utils import generate_filename
        filename = generate_filename(None, prefix=None, suffix=None, extension=None)
        self.assertEqual('', filename, "Return empty when all arguments are none")
        filename = generate_filename(None, prefix=None, suffix=None, extension='.txt')
        self.assertEqual('', filename, "Return empty when base_name, prefix, and suffix are None, but extension is not")
        filename = generate_filename('c:/temp.json', prefix=None, suffix=None, extension='.txt')
        self.assertEqual('c_temp.txt', filename,
                         "Returns stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename('temp.json', prefix='prefix', suffix='suffix', extension='.txt')
        self.assertEqual('prefix_temp_suffix.txt', filename,
                         "Return stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename(None, prefix='prefix', suffix='suffix', extension='.txt')
        self.assertEqual('prefix_suffix.txt', filename,
                         "Returns correct string when no base_name")
        filename = generate_filename('event-strategy-v3_task-matchingpennies_events.json',
                                     suffix='blech', extension='.txt')
        self.assertEqual('event-strategy-v3_task-matchingpennies_events_blech.txt', filename,
                         "Returns correct string when base_name with hyphens")
        filename = generate_filename('HED7.2.0.xml', suffix='blech', extension='.txt')
        self.assertEqual('HED7.2.0_blech.txt', filename, "Returns correct string when base_name has periods")

    def test_generate_text_response(self):
        with self.app.test_request_context():
            from hedweb.web_utils import generate_text_response
            download_text = 'testme'
            test_msg = 'testing'
            response = generate_text_response(download_text, msg_category='success', msg=test_msg)
            self.assertIsInstance(response, Response, 'generate_download_text_response returns a response')
            headers_dict = dict(response.headers)
            self.assertEqual(200, response.status_code, 'generate_download_text_response should return status code 200')
            self.assertEqual('text/plain charset=utf-8', response.mimetype,
                             "generate_download_download_text_response should return text")
            self.assertEqual(test_msg, headers_dict['Message'],
                             "generate_download_text_response have the correct message in the response")
            self.assertEqual(download_text, response.data.decode('ascii'),
                             "generate_download_text_response have the download text as response data")

    def test_get_hed_schema_from_pull_down_empty(self):
        from hed.errors.exceptions import HedFileError

        from hedweb.web_utils import get_hed_schema_from_pull_down
        with self.app.test:
            environ = create_environ(data={})
            request = Request(environ)
            try:
                get_hed_schema_from_pull_down(request)
            except HedFileError:
                pass
            except Exception:
                self.fail('get_hed_schema_from_pull_down threw the wrong exception when data was empty')
            else:
                self.fail('get_hed_schema_from_pull_down should throw a HedFileError exception when data was empty')

    def test_get_hed_schema_from_pull_down_version(self):
        from hed.schema import HedSchema
        from hedweb.constants import base_constants
        from hedweb.web_utils import get_hed_schema_from_pull_down
        with self.app.test:
            environ = create_environ(data={base_constants.SCHEMA_VERSION: '8.0.0-alpha.1'})
            request = Request(environ)
            hed_schema = get_hed_schema_from_pull_down(request)
            self.assertIsInstance(hed_schema, HedSchema,
                                  "get_hed_schema_from_pull_down should return a HedSchema object")

    def test_get_hed_schema_from_pull_down_other(self):
        from hed.schema import HedSchema
        from hedweb.constants import base_constants
        from hedweb.web_utils import get_hed_schema_from_pull_down
        with self.app.test:
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
            with open(schema_path, 'rb') as fp:
                environ = create_environ(data={base_constants.SCHEMA_VERSION: base_constants.OTHER_VERSION_OPTION,
                                               base_constants.SCHEMA_PATH: fp})
            request = Request(environ)
            hed_schema = get_hed_schema_from_pull_down(request)
            self.assertIsInstance(hed_schema, HedSchema,
                                  "get_hed_schema_from_pull_down should return a HedSchema object")

    def test_handle_error(self):
        from hed.errors.exceptions import HedFileError, HedExceptions
        from hedweb.web_utils import handle_error
        ex = HedFileError(HedExceptions.BAD_PARAMETERS, "This had bad parameters", 'my.file')
        output = handle_error(ex)
        self.assertIsInstance(output, str, "handle_error should return a string if return_as_str")
        output1 = handle_error(ex, return_as_str=False)
        self.assertIsInstance(output1, dict, "handle_error should return a dict if not return_as_str")
        self.assertTrue('message' in output1, "handle_error dict should have a message")
        output2 = handle_error(ex, {'mykey': 'blech'}, return_as_str=False)
        self.assertTrue('mykey' in output2, "handle_error dict should include passed dictionary")

    def test_handle_http_error(self):
        from hed.errors.exceptions import HedFileError, HedExceptions
        from hedweb.web_utils import handle_http_error
        with self.app.test_request_context():
            ex = HedFileError(HedExceptions.BAD_PARAMETERS, "This had bad parameters", 'my.file')
            response = handle_http_error(ex)
            headers = dict(response.headers)
            self.assertEqual('error', headers["Category"], "handle_http_error should have category error")
            self.assertTrue(headers['Message'].startswith(HedExceptions.BAD_PARAMETERS),
                            "handle_http_error error message starts with the error_type")
            self.assertFalse(response.data, "handle_http_error should have empty data")
            ex = Exception()
            response = handle_http_error(ex)
            headers = dict(response.headers)
            self.assertEqual('error', headers["Category"], "handle_http_error should have category error")
            self.assertTrue(headers['Message'].startswith('Exception'),
                            "handle_http_error error message starts with the error_type")
            self.assertFalse(response.data, "handle_http_error should have empty data")


if __name__ == '__main__':
    unittest.main()
