import os
import io
import shutil
from shutil import copyfile
import unittest
from unittest import mock

from flask import Response
from werkzeug.datastructures import Headers
from hedweb.constants import common
from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/upload')
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
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids_events_alpha.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            input_data = {common.SCHEMA_VERSION: '7.2.0', common.COMMAND_OPTION: common.COMMAND_VALIDATE,
                          common.JSON_FILE: (json_buffer, 'bids_events_alpha.json')}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            headers_dict = dict(response.headers)
            self.assertTrue(1, "Testing form_has_file")

    def test_form_has_file(self):
        with self.app.app_context():
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids_events_alpha.json')
            with open(json_path, 'r') as sc:
                x = sc.read()
            json_buffer = io.BytesIO(bytes(x, 'utf-8'))
            input_data =  {common.SCHEMA_VERSION: '7.2.0', common.COMMAND_OPTION: common.COMMAND_VALIDATE,
                           common.JSON_FILE: (json_buffer, 'bids_events_alpha.json')}
            response = self.app.test.post('/dictionary_submit', content_type='multipart/form-data', data=input_data)
            headers_dict = dict(response.headers)
            self.assertTrue(1, "Testing form_has_file")

    def test_form_has_option(self):
        self.assertTrue(1, "Testing form_has_option")
        from hedweb.utils.web_utils import form_has_option
        mock_form = mock.Mock()
        mock_dict = {'upload': 'me', 'download:': 'them'}
        mock_form.values = mock_dict
        self.assertTrue(form_has_option(mock_form, 'upload', 'me'),
                        "True if option_name has target_value")
        self.assertFalse(form_has_option(mock_form, 'upload', 'them'),
                         "False if option_name is not target_value")
        self.assertFalse(form_has_option(mock_form, 'temp', 'them'),
                         "False if invalid option name")

    def test_form_has_url(self):
        self.assertTrue(1, "Testing form_has_url")

    def test_generate_download_file_response(self):
        from hedweb.utils.web_utils import generate_download_file
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/HED8.0.0-beta.1.xml')
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/temp.txt')
        copyfile(hed_file, temp_file)
        self.assertTrue(os.path.isfile(temp_file), "Dummy file exists")
        download_response = generate_download_file(temp_file)
        self.assertIsInstance(download_response, Response, "generate_download_file should generate Response")
        response_headers = download_response.headers
        self.assertIsInstance(response_headers, Headers, "generate_download_file should generate Response")
        header_content = response_headers.get_all('Content-Disposition')
        self.assertTrue(header_content[0].startswith("attachment filename="),
                        "generate_download_file should have an attachment filename")
        self.assertIsInstance(download_response, Response, "generate_download_file should generate Response")

        # TODO: seem to have an issue with the deleting temporary files
        # self.assertFalse(temp_path.is_file(), "After download temporary download file should have been deleted")
        if os.path.isfile(temp_file):
            os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file), "Dummy has been deleted")

    def test_generate_text_response(self):
        self.assertTrue(True, "Testing to be done")

    def test_generate_download_spreadsheet_excel(self):
        with self.app.test_request_context():

            from hed.models import HedInput
            from hedweb.utils.web_utils import generate_download_spreadsheet
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            '../../data/ExcelMultipleSheets.xlsx')

            spreadsheet = HedInput(filename=spreadsheet_path, worksheet_name='LKT 8Beta3',
                                   tag_columns=[5], has_column_names=True,
                                   column_prefix_dictionary={2:'Attribute/Informational/Label/',
                                                             4:'Attribute/Informational/Description/'},
                                   display_name='ExcelMultipleSheets.xlsx')
            response = generate_download_spreadsheet(spreadsheet,
                                                     display_name='ExcelMultipleSheets_download.xlsx',
                                                     msg_category='success', msg='Successful download')
            self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response')

    def test_generate_download_spreadsheet_tsv(self):
        with self.app.test_request_context():

            from hed.models import HedInput
            from hedweb.utils.web_utils import generate_download_spreadsheet
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            '../../data/LKTEventCodes8Beta3.tsv')

            spreadsheet = HedInput(filename=spreadsheet_path,
                                   tag_columns=[5], has_column_names=True,
                                   column_prefix_dictionary={2:'Attribute/Informational/Label/',
                                                             4:'Attribute/Informational/Description/'},
                                   display_name='LKTEventCodes8Beta3.tsv')
            response = generate_download_spreadsheet(spreadsheet,
                                                     display_name='LKTEventCodes8Beta3_download.tsv',
                                                     msg_category='success', msg='Successful download')
            self.assertIsInstance(response, Response, 'generate_download_spreadsheet returns a response for tsv files')
            headers_dict = dict(response.headers)
            self.assertEqual(200, response.status_code, 'generate_download_spreadsheet should return status code 200')
            self.assertEqual('text/tab-separated-values', response.mimetype,
                             "generate_download_spreadsheet should return tab-separated text for tsv files")
            x = int(headers_dict['Content-Length'])
            self.assertGreater(int(headers_dict['Content-Length']), 0,
                               "generate_download_spreadsheet download should be non-empty")
            print("to here")

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
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/HED8.0.0-beta.1.xml')
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
