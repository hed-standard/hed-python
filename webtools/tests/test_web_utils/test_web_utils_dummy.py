import os
import shutil
import unittest
from flask import Response
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

    def test_convert_number_str_to_list(self):
        from hedweb.web_utils import convert_number_str_to_list
        print('str_to_list')

    def test_delete_file_no_exceptions(self):
        from hedweb.web_utils import delete_file_no_exceptions
        print('delete_file_no_exceptions')

    def test_file_extension_is_valid(self):
        from hedweb.web_utils import file_extension_is_valid
        print('file_extension_is_valid')

    def test_find_all_str_indices_in_list(self):
        from hedweb.web_utils import find_all_str_indices_in_list
        print('find_all_str_indices_in_list')

    def test_form_has_file(self):
        from hedweb.web_utils import form_has_file
        print('form_has_file')

    def test_form_has_option(self):
        from hedweb.web_utils import form_has_option
        print('form_has_option')

    def test_form_has_url(self):
        from hedweb.web_utils import form_has_url
        print('form_has_url')

    def test_generate_response_download_file_from_text(self):
        from hedweb.web_utils import generate_response_download_file_from_text
        print('generate_response_download_file_from_text')

    def test_generate_download_file_response(self):
        from hedweb.web_utils import generate_download_file_response
        print('generate_download_file_response')

    def test_generate_filename(self):
        from hedweb.web_utils import generate_filename
        print('generate_filename')

    def test_generate_text_response(self):
        from hedweb.web_utils import generate_text_response
        print('generate_text_response')

    def test_get_events(self):
        from hedweb.web_utils import get_events
        print('get_events')

    def test_get_hed_path_from_pull_down(self):
        from hedweb.web_utils import get_hed_path_from_pull_down
        print('get_hed_path_from_pull_down')

    def test_get_hed_schema(self):
        from hedweb.web_utils import get_hed_schema
        print('get_hed_schema')

    def test_get_json_dictionary(self):
        from hedweb.web_utils import get_json_dictionary
        print('get_json_dictionary')

    def test_get_optional_form_field(self):
        from hedweb.web_utils import get_optional_form_field
        print('get_optional_form_field')

    def test_get_spreadsheet(self):
        from hedweb.web_utils import get_spreadsheet
        print('get_spreadsheet')

    def test_get_json_dictionary(self):
        from hedweb.web_utils import get_json_dictionary
        print('get_json_dictionary')

    def test_get_uploaded_file_path_from_form(self):
        from hedweb.web_utils import get_uploaded_file_path_from_form
        print('get_uploaded_file_path_from_form')

    def test_handle_error(self):
        from hedweb.web_utils import handle_error
        print('handle_error')

    def test_handle_http_error(self):
        from hedweb.web_utils import handle_http_error
        print('handle_http_error')

    def test_save_file_to_upload_folder(self):
        from hedweb.web_utils import save_file_to_upload_folder
        print('save_file_to_upload_folder')

    def test_save_file_to_upload_folder_no_exception(self):
        from hedweb.web_utils import save_file_to_upload_folder_no_exception
        print('save_file_to_upload_folder_no_exception')

    def test_save_text_to_upload_folder(self):
        from hedweb.web_utils import save_text_to_upload_folder
        print('save_text_to_upload_folder')

if __name__ == '__main__':
    unittest.main()
