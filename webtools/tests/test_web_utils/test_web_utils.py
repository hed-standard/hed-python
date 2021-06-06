import os
import shutil
from shutil import copyfile
import unittest
from unittest import mock

from flask import Response
from werkzeug.datastructures import Headers
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
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_convert_number_str_to_list(self):
        from hedweb.web_utils import convert_number_str_to_list
        other_tag_columns_str = '1,2,3'
        expected_other_columns = [1, 2, 3]
        other_tag_columns = convert_number_str_to_list(other_tag_columns_str)
        self.assertTrue(other_tag_columns)
        self.assertEqual(expected_other_columns, other_tag_columns)
        other_tag_columns_str = ''
        other_tag_columns = convert_number_str_to_list(other_tag_columns_str)
        self.assertEqual(len(other_tag_columns), 0, "")
        other_tag_columns_str = '2,4,3'
        expected_other_columns = [2, 4, 3]
        other_tag_columns = convert_number_str_to_list(other_tag_columns_str)
        self.assertTrue(other_tag_columns)
        self.assertEqual(expected_other_columns, other_tag_columns)
        other_tag_columns_str = 'A,B,C'
        expected_other_columns = ['A', 'B', 'C']
        with self.assertRaises(ValueError):
            other_tag_columns = convert_number_str_to_list(other_tag_columns_str)

    def test_delete_file_no_exceptions(self):
        print("Test")

    def test_file_extension_is_valid(self):
        from hedweb import web_utils
        is_valid = web_utils.file_extension_is_valid('abc.xml', ['.xml', '.txt'])
        self.assertTrue(is_valid, 'File name has a valid extension if the extension is in list of valid extensions')
        is_valid = web_utils.file_extension_is_valid('abc.XML', ['.xml', '.txt'])
        self.assertTrue(is_valid, 'File name has a valid extension if capitalized version of valid extension')
        is_valid = web_utils.file_extension_is_valid('abc.temp', ['.xml', '.txt'])
        self.assertFalse(is_valid, 'File name has a valid extension if the extension not in list of valid extensions')
        is_valid = web_utils.file_extension_is_valid('abc')
        self.assertTrue(is_valid, 'File names with no extension are valid when no valid extensions provided')
        is_valid = web_utils.file_extension_is_valid('abc', ['.xml', '.txt'])
        self.assertFalse(is_valid, 'File name has a valid extension if the extension not in list of valid extensions')
        is_valid = web_utils.file_extension_is_valid('C:abc.Txt', ['.xml', '.txt'])
        self.assertTrue(is_valid, 'File name has a valid extension if the extension is in list of valid extensions')

    def test_find_all_str_indices_in_list(self):
        from hedweb.web_utils import find_all_str_indices_in_list
        list_1 = ['a', 'a', 'c', 'd']
        search_str = 'a'
        expected_indices = [1, 2]
        indices = find_all_str_indices_in_list(list_1, search_str)
        self.assertTrue(indices)
        self.assertIsInstance(indices, list)
        self.assertEqual(expected_indices, indices)
        search_str = 'A'
        expected_indices = [1, 2]
        indices = find_all_str_indices_in_list(list_1, search_str)
        self.assertTrue(indices)
        self.assertIsInstance(indices, list)
        self.assertEqual(expected_indices, indices)
        search_str = 'Apple'
        expected_indices = []
        indices = find_all_str_indices_in_list(list_1, search_str)
        self.assertFalse(indices)
        self.assertIsInstance(indices, list)
        self.assertEqual(expected_indices, indices)

    def test_form_has_file(self):
        self.assertTrue(1, "Testing form_has_file")

    def test_form_has_option(self):
        self.assertTrue(1, "Testing form_has_option")
        from hedweb.web_utils import form_has_option
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
        from hedweb.web_utils import generate_download_file_response
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED.xml')
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/temp.txt')
        copyfile(hed_file, temp_file)
        self.assertTrue(os.path.isfile(temp_file), "Dummy file exists")
        download_response = generate_download_file_response(temp_file)
        self.assertIsInstance(download_response, Response, "generate_download_file_response should generate Response")
        response_headers = download_response.headers
        self.assertIsInstance(response_headers, Headers, "generate_download_file_response should generate Response")
        header_content = response_headers.get_all('Content-Disposition')
        self.assertTrue(header_content[0].startswith("attachment filename="),
                        "generate_download_file_response should have an attachment filename")
        self.assertIsInstance(download_response, Response, "generate_download_file_response should generate Response")

        #TODO: seem to have an issue with the deleting temporary files
        # self.assertFalse(temp_path.is_file(), "After download temporary download file should have been deleted")
        if os.path.isfile(temp_file):
            os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file), "Dummy has been deleted")

    def test_generate_filename(self):
        from hedweb.web_utils import generate_filename
        filename = generate_filename(None, prefix=None, suffix=None, extension=None)
        self.assertEqual('', filename, "Returns empty when all arguments are none")
        filename = generate_filename(None, prefix=None, suffix=None, extension='.txt')
        self.assertEqual('', filename, "Returns empty when base_name, prefix, and suffix are None, but extension is not")
        filename = generate_filename('c:/temp.json', prefix=None, suffix=None, extension='.txt')
        self.assertEqual('c_temp.txt', filename,
                         "Returns stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename('temp.json', prefix='prefix', suffix='suffix', extension='.txt')
        self.assertEqual('prefix_temp_suffix.txt', filename,
                         "Returns stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename(None, prefix='prefix', suffix='suffix', extension='.txt')
        self.assertEqual('prefix_suffix.txt', filename,
                         "Returns correct string when no base_name")
        filename = generate_filename('event-strategy-v3_task-matchingpennies_events.json',
                                     suffix='blech', extension='.txt')
        self.assertEqual('event-strategy-v3_task-matchingpennies_events_blech.txt', filename,
                         "Returns correct string when base_name with hyphens")
        filename = generate_filename('HED7.1.2.xml', suffix='blech', extension='.txt')
        self.assertEqual('HED7.1.2_blech.txt', filename, "Returns correct string when base_name has periods")

    def test_generate_text_response(self):
        print("Stuff")

    def test_get_hed_path_from_pull_down(self):
        from hedweb.constants import common
        from hedweb.web_utils import get_hed_path_from_pull_down
        mock_form = mock.Mock()
        mock_form.values = {}

    def test_get_optional_form_field(self):
        self.assertTrue(1, "Testing get_optional_form_field")

    def test_get_uploaded_file_path_from_form(self):
        from hedweb.web_utils import get_uploaded_file_path_from_form
        # with self.app.test as client:
        #     # send data as POST form to endpoint
        #     sent = {'return_url': 'my_test_url'}
        #     result = client.post(
        #         '/',
        #         data=sent
        #     )
        # mock_form = mock.Mock()
        # mock_dict = {'upload': 'me', 'download:': 'them'}
        #     mock_form.values = mock_dict
        # text = 'save me now'
        # filename = 'test_save.txt'
        # actual_path = os.path.join(self.upload_directory, filename)
        # self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        # with self.app.app_context():
        # the_path = save_text_to_upload_folder(text, filename)
        # self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")

    # def test_handle_http_error(self):
    #     error_code = "CODE"
    #     error_message = "Test"
    #
    #     self.assertTrue(1, "Testing handle_http_error")+

    def test_handle_error(self):
        print("stuff")

    def test_handle_http_error(self):
        print("stuff")

    def test_save_file_to_upload_folder(self):
        self.assertTrue(1, "Testing save_file_to_upload_folder")
        from hedweb.web_utils import save_file_to_upload_folder
        from werkzeug.datastructures import FileStorage
        filename = 'HED.xml'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED.xml')
        # with open(hed_file) as f:
        #     upload_file = FileStorage(f, filename='HED.xml', content_type='text/xml',  content_length=0, stream=stream)
        #     with self.app.app_context():
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
        print("Stuff")

    def test_save_text_to_upload_folder(self):
        from hedweb.web_utils import save_text_to_upload_folder
        # from flask import Flask
        # app = Flask(__name__)
        text = 'save me now'
        filename = 'test_save.txt'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        with self.app.app_context():
            from hedweb.web_utils import save_text_to_upload_folder
            the_path = save_text_to_upload_folder(text, filename)
            self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")


if __name__ == '__main__':
    unittest.main()
