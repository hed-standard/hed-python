import os
import shutil
import unittest
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
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_convert_number_str_to_list(self):
        print('str_to_list')

    def test_delete_file_no_exceptions(self):
        print('delete_file_no_exceptions')

    def test_file_extension_is_valid(self):
        print('file_extension_is_valid')

    def test_find_all_str_indices_in_list(self):
        print('find_all_str_indices_in_list')

    def test_form_has_file(self):
        print('form_has_file')

    def test_form_has_option(self):
        print('form_has_option')

    def test_form_has_url(self):
        print('form_has_url')

    def test_generate_response_download_file_from_text(self):
        print('generate_response_download_file_from_text')

    def test_generate_download_file_response(self):
        print('generate_download_file')

    def test_generate_filename(self):
        print('generate_filename')

    def test_generate_text_response(self):
        print('generate_text_response')

    def test_get_events(self):
        print('get_events')

    def test_get_hed_path_from_pull_down(self):
        print('get_hed_path_from_pull_down')

    def test_get_hed_schema(self):
        print('get_hed_schema')

    def test_get_json_dictionary(self):
        print('get_json_dictionary')

    def test_get_optional_form_field(self):
        print('get_optional_form_field')

    def test_get_spreadsheet(self):
        print('get_spreadsheet')

    def test_get_json_dictionary(self):
        print('get_json_dictionary')

    def test_get_uploaded_file_path_from_form(self):
        print('get_uploaded_file_path_from_form')

    def test_handle_error(self):
        print('handle_error')

    def test_handle_http_error(self):
        print('handle_http_error')

    def test_save_file_to_upload_folder(self):
        print('save_file_to_upload_folder')

    def test_save_file_to_upload_folder_no_exception(self):
        print('save_file_to_upload_folder_no_exception')

    def test_save_text_to_upload_folder(self):
        print('save_text_to_upload_folder')


if __name__ == '__main__':
    unittest.main()
