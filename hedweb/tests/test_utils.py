import unittest
from hed import webinterface
from hed.webinterface.app_factory import AppFactory
from hed.webinterface.constants.other import file_extension_constants, spreadsheet_constants, type_constants
import os


class Test(unittest.TestCase):
    def setUp(self):
        self.create_test_app()
        self.major_version_key = 'major_versions'
        self.hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        self.tsv_file1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/tsv_file1.txt')

    def create_test_app(self):
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed.webinterface.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            self.app = app.test_client()

    def test_find_major_hed_versions(self):
        hed_info = webinterface.utils.find_major_hed_versions()
        self.assertTrue(self.major_version_key in hed_info)

    def test_file_extension_is_valid(self):
        file_name = 'abc.' + spreadsheet_constants.SPREADSHEET_FILE_EXTENSIONS[0]
        is_valid = webinterface.utils._file_extension_is_valid(file_name,
                                                      spreadsheet_constants.SPREADSHEET_FILE_EXTENSIONS)
        self.assertTrue(is_valid)

    def test_generate_spreadsheet_validation_filename(self):
        spreadsheet_filename = 'abc.xls'
        expected_spreadsheet_filename = 'validated_' + spreadsheet_filename.rsplit('.')[0] + '.txt'
        validation_file_name = webinterface.utils._generate_spreadsheet_validation_filename(spreadsheet_filename,
                                                                                   worksheet_name='')
        self.assertTrue(validation_file_name)
        self.assertEqual(expected_spreadsheet_filename, validation_file_name)

    def test_get_file_extension(self):
        spreadsheet_filename = 'abc.xls'
        expected_extension = 'xls'
        file_extension = webinterface.utils._get_file_extension(spreadsheet_filename)
        self.assertTrue(file_extension)
        self.assertEqual(expected_extension, file_extension)

    def test_convert_other_tag_columns_to_list(self):
        other_tag_columns_str = '1,2,3'
        expected_other_columns = [1, 2, 3]
        other_tag_columns = webinterface.utils._convert_other_tag_columns_to_list(other_tag_columns_str)
        self.assertTrue(other_tag_columns)
        self.assertEqual(expected_other_columns, other_tag_columns)

    def test_delete_file_if_it_exist(self):
        some_file = '3k32j23kj.txt'
        deleted = webinterface.utils.delete_file_if_it_exist(some_file)
        self.assertFalse(deleted)

    def test_create_folder_if_needed(self):
        some_folder = '3k32j23kj'
        created = webinterface.utils._create_folder_if_needed(some_folder)
        self.assertTrue(created)
        os.rmdir(some_folder)

    def test_copy_file_line_by_line(self):
        some_file1 = '3k32j23kj1.txt'
        some_file2 = '3k32j23kj2.txt'
        success = webinterface.utils._copy_file_line_by_line(some_file1, some_file2)
        self.assertFalse(success)

    def test_initialize_worksheets_info_dictionary(self):
        worksheets_info_dictionary = webinterface.utils._initialize_worksheets_info_dictionary()
        self.assertTrue(worksheets_info_dictionary)
        self.assertIsInstance(worksheets_info_dictionary, dict)

    def test_initialize_spreadsheet_columns_info_dictionary(self):
        worksheets_info_dictionary = webinterface.utils._initialize_spreadsheet_columns_info_dictionary()
        self.assertTrue(worksheets_info_dictionary)
        self.assertIsInstance(worksheets_info_dictionary, dict)

    def test_get_text_file_column_names(self):
        column_names = webinterface.utils._get_text_file_column_names(self.tsv_file1, '\t')
        self.assertTrue(column_names)
        self.assertIsInstance(column_names, list)

    def test_get_column_delimiter_based_on_file_extension(self):
        delimiter = webinterface.utils._get_column_delimiter_based_on_file_extension(self.tsv_file1)
        tab_delimiter = '\t'
        self.assertTrue(delimiter)
        self.assertIsInstance(delimiter, str)
        self.assertEqual(tab_delimiter, delimiter)

    def test_get_spreadsheet_other_tag_column_indices(self):
        column_names = ['a,', spreadsheet_constants.OTHER_TAG_COLUMN_NAMES[0]]
        expected_indices = [2]
        indices = webinterface.utils._get_spreadsheet_other_tag_column_indices(column_names)
        self.assertTrue(indices)
        self.assertIsInstance(indices, list)
        self.assertEqual(indices, expected_indices)

    def test_get_spreadsheet_specific_tag_column_indices(self):
        column_names = ['a,', spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES_DICTIONARY[
            spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES[0]][0]]
        #print(column_names)
        indices = webinterface.utils._get_spreadsheet_specific_tag_column_indices(column_names)
        self.assertTrue(indices)
        self.assertIsInstance(indices, dict)

    def test_find_all_str_indices_in_list(self):
        list_1 = ['a', 'a', 'c', 'd']
        search_str = 'a'
        expected_indices = [1, 2]
        indices = webinterface.utils._find_all_str_indices_in_list(list_1, search_str)
        self.assertTrue(indices)
        self.assertIsInstance(indices, list)
        self.assertEqual(expected_indices, indices)

    def test_find_str_index_in_list(self):
        list_1 = ['a', 'a', 'c', 'd']
        search_str = 'a'
        expected_indices = 1
        indices = webinterface.utils._find_str_index_in_list(list_1, search_str)
        self.assertTrue(indices)
        self.assertIsInstance(indices, int)
        self.assertEqual(expected_indices, indices)


if __name__ == '__main__':
    unittest.main()
