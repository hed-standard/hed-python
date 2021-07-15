import os
import io
import shutil
from shutil import copyfile
import unittest
from unittest import mock
from openpyxl import load_workbook

from werkzeug.datastructures import Headers
from werkzeug.test import create_environ
from werkzeug.wrappers import Request, Response
from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hedweb.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            app.config['WTF_CSRF_ENABLED'] = False
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_form_has_file(self):
        from hedweb.utils.web_utils import form_has_file
        from hedweb.constants import file_constants
        with self.app.test as c:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')
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
        from hedweb.utils.web_utils import form_has_option
        from hedweb.constants import common
        with self.app.test as c:
            environ = create_environ(data={common.CHECK_FOR_WARNINGS: 'on'})
            request = Request(environ)
            self.assertTrue(form_has_option(request, common.CHECK_FOR_WARNINGS, 'on'),
                            "Form has the required option when set")
            self.assertFalse(form_has_option(request, common.CHECK_FOR_WARNINGS, 'off'),
                            "Form does not have required option when target value is wrong one")
            self.assertFalse(form_has_option(request, 'blank', 'on'),
                            "Form does not have required option when option is not in the form")

    def test_form_has_url(self):
        from hedweb.utils.web_utils import form_has_url
        from hedweb.constants import common, file_constants
        with self.app.test as _:
            environ = create_environ(data={common.SCHEMA_URL: 'https://www.google.com/my.json'})
            request = Request(environ)
            self.assertTrue(form_has_url(request, common.SCHEMA_URL), "Form has a URL that is specified")
            self.assertFalse(form_has_url(request, 'temp'), "Form does not have a field that is not specified")
            self.assertFalse(form_has_url(request, common.SCHEMA_URL, file_constants.SPREADSHEET_EXTENSIONS),
                                         "Form does not URL with the wrong extension")

    def test_generate_download_file_valid(self):
        from hedweb.utils.web_utils import generate_download_file
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-beta.1.xml')
        with self.app.test_request_context():
            response = generate_download_file(hed_file, 'HED.xml', msg_category='success', msg='Successful')
            self.assertIsInstance(response, Response, 'generate_download_file returns a response for real file')
            self.assertEqual(200, response.status_code, "Generate_download_file has status code 200 for real file")
            header_content = dict(response.headers)
            self.assertEqual('success', header_content['Category'], "The msg_category is success")
            self.assertEqual('attachment filename=HED.xml', header_content['Content-Disposition'],
                             "generate_download_file has the correct attachment file name")

    def test_generate_download_file_bad_file(self):
        from hedweb.utils.web_utils import generate_download_file
        from hed.errors.exceptions import HedFileError
        with self.app.test_request_context():
            try:
                generate_download_file('badfile.xml', 'HED.xml', msg_category='success', msg='Successful')
            except HedFileError:
                pass
            except Exception:
                self.fail('generate_download_file threw the wrong exception for non-existent file')
            else:
                self.fail('generate_download_file should have thrown a HedFileError exception when file did not exist')

    def test_generate_text_response(self):
        with self.app.test_request_context():
            from hedweb.utils.web_utils import generate_text_response
            text = "The quick brown fox."
            message = "My mess"
            response = generate_text_response(text, msg_category='success', msg=message)
            self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response')
            headers_dict = dict(response.headers)
            self.assertEqual(200, response.status_code, 'generate_download_text should return status code 200')
            self.assertEqual(message, headers_dict['Message'], 'The message should match')
            self.assertEqual('success', headers_dict['Category'], "The msg_category should be success")
            str_data = str(response.data, 'utf-8')
            self.assertEqual(text, str_data, "The data sent should be the same")

    def test_generate_response_download_file_from_text(self):
        from hedweb.utils.web_utils import generate_response_download_file_from_text
        with self.app.test_request_context():
            the_text = 'The quick brown fox\nIs too slow'
            response = generate_response_download_file_from_text(the_text, 'temp',
                                                                 msg_category='success', msg='Successful')
            self.assertIsInstance(response, Response,
                                  'Generate_response_download_file_from_text returns a response for string')
            self.assertEqual(200, response.status_code,
                             "Generate_response_download_file_from_text has status code 200 for string")
            header_content = dict(response.headers)
            self.assertEqual('success', header_content['Category'], "The msg_category is success")
            self.assertEqual('attachment filename=temp', header_content['Content-Disposition'],
                             "generate_download_file has the correct attachment file name")

    # def test_generate_download_spreadsheet_excel(self):
    #     with self.app.test_request_context():
    #
    #         from hed.models import HedInput
    #         from hedweb.utils.web_utils import generate_download_spreadsheet
    #         spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                         '../data/ExcelOneSheet.xlsx')
    #
    #         spreadsheet = HedInput(filename=spreadsheet_path, worksheet_name='LKT 8Beta3',
    #                                tag_columns=[5], has_column_names=True,
    #                                column_prefix_dictionary={2:'Attribute/Informational/Label/',
    #                                                          4:'Attribute/Informational/Description/'},
    #                                display_name='ExcelMultipleSheets.xlsx')
    #         response = generate_download_spreadsheet(spreadsheet, spreadsheet_path,
    #                                                  display_name='ExcelMultipleSheets_download.xlsx',
    #                                                  msg_category='success', msg='Successful download')
    #
    #         self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response')
    #         wb = load_workbook(filename=io.BytesIO(response.data))
    #         wb.save('D:/Research/temp1.xlsx')
    #         headers_dict = dict(response.headers)
    #         self.assertEqual(200, response.status_code, 'generate_download_spreadsheet should return status code 200')


    # def test_generate_download_spreadsheet_tsv(self):
    #     with self.app.test_request_context():
    #
    #         from hed.models import HedInput
    #         from hedweb.utils.web_utils import generate_download_spreadsheet
    #         spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                         '../data/LKTEventCodes8Beta3.tsv')
    #
    #         spreadsheet = HedInput(filename=spreadsheet_path,
    #                                tag_columns=[5], has_column_names=True,
    #                                column_prefix_dictionary={2:'Attribute/Informational/Label/',
    #                                                          4:'Attribute/Informational/Description/'},
    #                                display_name='LKTEventCodes8Beta3.tsv')
    #         response = generate_download_spreadsheet(spreadsheet, spreadsheet_path,
    #                                                  display_name='LKTEventCodes8Beta3_download.tsv',
    #                                                  msg_category='success', msg='Successful download')
    #         self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response for tsv files')
    #         headers_dict = dict(response.headers)
    #         self.assertEqual(200, response.status_code, 'generate_download_spreadsheet should return status code 200')
    #         self.assertEqual('text/tab-separated-values', response.mimetype,
    #                          "generate_download_spreadsheet should return tab-separated text for tsv files")
    #         x = int(headers_dict['Content-Length'])
    #         self.assertGreater(int(headers_dict['Content-Length']), 0,
    #                            "generate_download_spreadsheet download should be non-empty")

    def test_get_hed_path_from_pull_down(self):
        mock_form = mock.Mock()
        mock_form.values = {}

    def test_get_optional_form_field(self):
        self.assertTrue(1, "Testing get_optional_form_field")

    def test_handle_error(self):
        self.assertTrue(True, "Testing to be done")

    def test_handle_http_error(self):
        self.assertTrue(True, "Testing to be done")

    def test_save_file_to_upload_folder(self):
        self.assertTrue(1, "Testing save_file_to_upload_folder")
        filename = 'HED8.0.0-beta.1.xml'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-beta.1.xml')
        # with open(hed_file) as f:
        #    upload_file = FileStorage(f, filename='HED.xml', content_type='text/xml',  content_length=0, stream=stream)
        #    with self.app.app_context():
        #         the_path = save_file_to_upload_folder(upload_file)
        #         self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")

        # temp_name = save_file_to_upload_folder('')
        # self.assertEqual(temp_name, '', "A file with empty name cnnot be copied copied")
        # some_file = '3k32j23kj1.txt'
        # temp_name = save_file_to_upload_folder(some_file)
        # self.assertEqual(temp_name, '', "A file that does not exist cannot be copied")
        # hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        #
        # self.assertTrue(os.path.exists(hed_file), "The HED.xml file should exist in the data directory")
        # actual_path = os.path.join(self.upload_directory, filename)
        # self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        # with self.app.app_context():
        #     the_path = save_text_to_upload_folder(text, filename)
        #     self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")
        # mock_file = mock.Mock()
        # mock_file.filename = hed_file
        # TODO: Context not working this is not tested
        # with Test.app_context():
        #     temp_name = save_file_to_upload_folder(mock_file)
        # self.assertNotEqual(mock_file, '', "It should create an actual file in the upload directory")
        # self.assertTrue(os.path.isfile(temp_name), "File should exist after it is uploaded")

    def test_save_file_to_upload_folder_no_exception(self):
        self.assertTrue(True, "Test to be done")

    def test_save_text_to_upload_folder(self):
        text = 'save me now'
        filename = 'test_save.txt'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        with self.app.app_context():
            from hedweb.utils.io_utils import save_text_to_upload_folder
            the_path = save_text_to_upload_folder(text, filename)
            self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")


if __name__ == '__main__':
    unittest.main()
