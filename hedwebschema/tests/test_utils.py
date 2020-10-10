import unittest
import shutil

from hed.webconverter import utils
from hed.webconverter.app_factory import AppFactory
from hed.webconverter.constants.other import file_extension_constants
from hed.schema import constants


import os

class Test(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.create_test_app()
        cls.hed_xml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        cls.hed_wiki_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.mediawiki')
        cls.default_test_url = """https://raw.githubusercontent.com/hed-standard/hed-specification/HED-restructure/hedxml/HED7.1.1.xml"""
        cls.dummy_directory_name = "test_dir_23409823098"
        cls.test_text_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/test_text_file.txt')
        cls.test_text_dest_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/test_text_file_out.txt')

    @classmethod
    def create_test_app(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed.webconverter.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            utils.create_upload_directory(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_file_extension_is_valid(self):
        file_name = 'abc.' + file_extension_constants.HED_XML_EXTENSION
        is_valid = utils._file_extension_is_valid(file_name,file_extension_constants.HED_FILE_EXTENSIONS)
        self.assertTrue(is_valid)

    def test_url_to_file(self):
        downloaded_file = utils.url_to_file(self.default_test_url)
        self.assertTrue(downloaded_file)
        utils.delete_file_if_it_exist(downloaded_file)


    def test__run_conversion(self):
        result_dict = utils._run_conversion(self.hed_xml_file)
        assert(result_dict[constants.HED_OUTPUT_LOCATION_KEY])
        utils.delete_file_if_it_exist(result_dict[constants.HED_OUTPUT_LOCATION_KEY])

        result_dict = utils._run_conversion(self.hed_wiki_file)
        assert (result_dict[constants.HED_OUTPUT_LOCATION_KEY])
        utils.delete_file_if_it_exist(result_dict[constants.HED_OUTPUT_LOCATION_KEY])

    def test__run_tag_compare(self):
        result_dict = utils._run_tag_compare(self.hed_xml_file)
        assert (result_dict[constants.HED_OUTPUT_LOCATION_KEY])
        utils.delete_file_if_it_exist(result_dict[constants.HED_OUTPUT_LOCATION_KEY])

    def test_generate_download_file_response_and_delete(self):
        result_dict = utils._run_tag_compare(self.hed_xml_file)
        temp_file = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
        assert (temp_file)

        try:
            response = utils.generate_download_file_response_and_delete(temp_file)
            assert(response.status_code == 200)
        except:
            utils.delete_file_if_it_exist(temp_file)
            raise

    def test_handle_http_error(self):
        with self.app.app_context():
            response, status_code = utils.handle_http_error("404", "Fake Error from unit tests(ignore)", as_text=False)
            assert(status_code == "404")

    def test__file_extension_is_valid(self):
        expected_extension = '.xml'
        ext_equal = utils._file_extension_is_valid(self.hed_xml_file, [expected_extension])
        self.assertTrue(ext_equal)

    def test__save_hed_to_upload_folder_if_present(self):
        with self.app.app_context():
            upload_folder_file = None
            with open(self.hed_xml_file, "r") as f:
                f.filename = self.hed_xml_file
                upload_folder_file = utils._save_hed_to_upload_folder_if_present(f)

            self.assertTrue(upload_folder_file)
            utils.delete_file_if_it_exist(upload_folder_file)

    def test__file_has_valid_extension(self):
        accepted_file_extensions = [".xml"]
        ext_equal = False
        with open(self.hed_xml_file, "r") as f:
            f.filename = self.hed_xml_file
            ext_equal = utils._file_has_valid_extension(f, accepted_file_extensions)
        self.assertTrue(ext_equal)

    def test_get_file_extension(self):
        expected_extension = '.xml'
        file_extension = utils._get_file_extension(self.hed_xml_file)
        self.assertTrue(file_extension)
        self.assertEqual(expected_extension, file_extension)

    def test_delete_file_if_it_exist(self):
        some_file = '3k32j23kj.txt'
        deleted = utils.delete_file_if_it_exist(some_file)
        self.assertFalse(deleted)

    def test_create_folder_if_needed(self):
        some_folder = self.dummy_directory_name
        created = utils._create_folder_if_needed(some_folder)
        self.assertTrue(created)
        os.rmdir(some_folder)

    def test_copy_file_line_by_line(self):
        some_file1 = self.test_text_file
        some_file2 = self.test_text_dest_file
        with open(some_file1, "r") as f1, open(some_file2, "w") as f2:
            success = utils._copy_file_line_by_line(f1, f2)
        self.assertTrue(success)
        utils.delete_file_if_it_exist(some_file2)

    # More elaborate to handle test cases for these as the interact with the forms...

    # def test__get_uploaded_file_paths_from_forms(self):
    #     utils._get_uploaded_file_paths_from_forms(form_request_object)
    # def test__generate_input_arguments_from_conversion_form(self):
    #     utils._generate_input_arguments_from_conversion_form(form_request_object)
    # def test_run_conversion(self):
    #     utils.run_conversion(form_request_object)
    # def test_run_tag_compare(self):
    #     utils.run_tag_compare(form_request_object)
    # def test_url_present_in_form(self):
    #     utils.url_present_in_form(conversion_form_request_object)
    # def test__check_if_option_in_form(self):
    #     utils._check_if_option_in_form(conversion_form_request_object, option_name, target_value)
    # def test_hed_present_in_form(self):
    #     utils.hed_present_in_form(conversion_form_request_object)


if __name__ == '__main__':
    unittest.main()
