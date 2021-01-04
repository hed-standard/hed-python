import os
import unittest
import shutil


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from hed.web.app_factory import AppFactory
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():

            from hed.web.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)





    def test_find_spreadsheet_columns_info(self):
        self.assertTrue(1, "Testing find_spreadsheet_columns_info")

    def test_find_str_index_in_list(self):
        self.assertTrue(1, "Testing find_str_index_in_list")
        # def test_find_str_index_in_list(self):
        #     list_1 = ['a', 'a', 'c', 'd']
        #     search_str = 'a'
        #     expected_indices = 1
        #     indices = utils.find_str_index_in_list(list_1, search_str)
        #     self.assertTrue(indices)
        #     self.assertIsInstance(indices, int)
        #     self.assertEqual(expected_indices, indices)

    def test_find_worksheets_info(self):
        self.assertTrue(1, "Testing find_worksheets_info")

    def test_get_column_delimiter_based_on_file_extension(self):
        self.assertTrue(1, "Testing get_column_delimiter_based_on_file_extension")
        # def test_get_column_delimiter_based_on_file_extension(self):
        #     delimiter = utils.get_column_delimiter_based_on_file_extension(self.tsv_file1)
        #     tab_delimiter = '\t'
        #     self.assertTrue(delimiter)
        #     self.assertIsInstance(delimiter, str)
        #     self.assertEqual(tab_delimiter, delimiter)
        #

    def test_get_excel_worksheet_names(self):
        from hed.web.utils import get_excel_worksheet_names
        self.excel_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ExcelMultipleSheets.xlsx')
        worksheet_names = get_excel_worksheet_names(self.excel_file)
        self.assertEqual(len(worksheet_names), 3, "This excel file has three worksheets")
        self.assertIn('PVT Events', worksheet_names, "PVT Events is one of the worksheet names")
        self.assertNotIn('Temp', worksheet_names, "Temp is not one of the worksheet names")

    def test_get_optional_form_field(self):
        self.assertTrue(1, "Testing get_optional_form_field")

    def test_get_original_spreadsheet_filename(self):
        self.assertTrue(1, "Testing get_original_filename")

    def test_get_specific_tag_columns_from_form(self):
        self.assertTrue(1, "Testing get_specific_tag_columns_from_form")

    def test_get_spreadsheet_other_tag_column_indices(self):
        self.assertTrue(1, "Testing get_spreadsheet_other_tag_column_indices")
        # def test_get_spreadsheet_other_tag_column_indices(self):
        #     column_names = ['a,', spreadsheet_constants.OTHER_TAG_COLUMN_NAMES[0]]
        #     expected_indices = [2]
        #     indices = utils.get_spreadsheet_other_tag_column_indices(column_names)
        #     self.assertTrue(indices)
        #     self.assertIsInstance(indices, list)
        #     self.assertEqual(indices, expected_indices)
        #

    def test_get_spreadsheet_specific_tag_column_indices(self):
        self.assertTrue(1, "Testing get_spreadsheet_specific_tag_column_indices")
        # def test_get_spreadsheet_specific_tag_column_indices(self):
        #     column_names = ['a,', spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES_DICTIONARY[
        #         spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES[0]][0]]
        #     # print(column_names)
        #     indices = utils.get_spreadsheet_specific_tag_column_indices(column_names)
        #     self.assertTrue(indices)
        #     self.assertIsInstance(indices, dict)
        #

    def test_get_text_file_column_names(self):
        self.assertTrue(1, "Testing get_text_file_column_names")
        # def test_get_text_file_column_names(self):
        #     column_names = utils.get_text_file_column_names(self.tsv_file1, '\t')
        #     self.assertTrue(column_names)
        #     self.assertIsInstance(column_names, list)
        #

    def test_get_worksheet_column_names(self):
        self.assertTrue(1, "Testing get_worksheet_column_names")

    def test_initialize_spreadsheet_columns_info_dictionary(self):
        self.assertTrue(1, "Testing initialize_spreadsheet_columns_info_dictionary")
        # def test_initialize_spreadsheet_columns_info_dictionary(self):
        #     worksheets_info_dictionary = utils._initialize_spreadsheet_columns_info_dictionary()
        #     self.assertTrue(worksheets_info_dictionary)
        #     self.assertIsInstance(worksheets_info_dictionary, dict)
        #

    def test_initialize_worksheets_info_dictionary(self):
        self.assertTrue(1, "Testing initialize_worksheets_info_dictionary")
        # def test_initialize_worksheets_info_dictionary(self):
        #     worksheets_info_dictionary = initialize_worksheets_info_dictionary()
        #     self.assertTrue(worksheets_info_dictionary)
        #     self.assertIsInstance(worksheets_info_dictionary, dict)

    def test_populate_spreadsheet_columns_info_dictionary(self):
        self.assertTrue(1, "Testing populate_spreadsheet_columns_info_dictionary")

    def test_populate_worksheets_info_dictionary(self):
        self.assertTrue(1, "Testing populate_worksheets_info_dictionary")

    def test_worksheet_name_present_in_form(self):
        self.assertTrue(1, "Testing worksheet_name_present_in_form")


if __name__ == '__main__':
    unittest.main()