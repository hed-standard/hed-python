import os
import pathlib
import shutil
from shutil import copyfile
import unittest
from unittest import mock

from flask import Response
from werkzeug.datastructures import Headers
from hed.web.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed.web.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_check_if_option_in_form(self):
        self.assertTrue(1, "Testing check_if_option_in_form")
        from hed.web.web_utils import check_if_option_in_form
        mock_form = mock.Mock()
        mock_dict = {'upload': 'me', 'download:': 'them'}
        mock_form.values = mock_dict
        self.assertTrue(check_if_option_in_form(mock_form, 'upload', 'me'),
                        "True if option_name has target_value")
        self.assertFalse(check_if_option_in_form(mock_form, 'upload', 'them'),
                         "False if option_name is not target_value")
        self.assertFalse(check_if_option_in_form(mock_form, 'temp', 'them'),
                         "False if invalid option name")

    def test_convert_number_str_to_list(self):
        from hed.web.web_utils import convert_number_str_to_list
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

    def test_file_extension_is_valid(self):
        from hed.web import web_utils
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
        from hed.web.web_utils import find_all_str_indices_in_list
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

    def test_find_hed_version_in_uploaded_file(self):
        self.assertTrue(1, "Testing find_hed_version_in_uploaded_file")

    def test_generate_download_file_response(self):
        from hed.web.web_utils import generate_download_file_response
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/temp.txt')
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

    def test_get_hed_path_from_pull_down(self):
        from hed.web.constants import common_constants
        from hed.web.web_utils import get_hed_path_from_pull_down
        mock_form = mock.Mock()
        mock_form.values = {}
        # hed_file_path, hed_display_name = get_hed_path_from_pull_down(mock_form)
        # self.assertFalse(hed_file_path,
        #                  'When hed-version is not in form get_hed_path_from_pull_down returns empty hed_file_path')
        # mock_dict1 = {'form': {common_constants.HED_VERSION: '7.1.1'}}
        # hed_file_path, hed_display_name = get_hed_path_from_pull_down(mock_form)
        # self.assertTrue(hed_file_path,
        #                 'When hed-version is in form get_hed_path_from_pull_down returns a hed_file_path')


    def test_get_uploaded_file_path_from_form(self):
        self.assertTrue(1, "Testingget_uploaded_file_path_from_form")

    def test_handle_http_error(self):
        error_code = "CODE"
        error_message = "Test"

        self.assertTrue(1, "Testing handle_http_error")

    def test_save_file_to_upload_folder(self):
        from hed.web.web_utils import save_file_to_upload_folder, app_config
        temp_name = save_file_to_upload_folder('')
        self.assertEqual(temp_name, '', "A file with empty name cnnot be copied copied")
        some_file = '3k32j23kj1.txt'
        temp_name = save_file_to_upload_folder(some_file)
        self.assertEqual(temp_name, '', "A file that does not exist cannot be copied")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        self.assertTrue(os.path.exists(hed_file), "The HED.xml file should exist in the data directory")
        mock_file = mock.Mock()
        mock_file.filename = hed_file
        # TODO: Context not working this is not tested
        # with Test.app_context():
        #     temp_name = save_file_to_upload_folder(mock_file)
        # self.assertNotEqual(mock_file, '', "It should create an actual file in the upload directory")
        # self.assertTrue(os.path.isfile(temp_name), "File should exist after it is uploaded")


if __name__ == '__main__':
    unittest.main()
