import io
import os
import unittest
from flask import Response
from tests.test_web_base import TestWebBase
from hedweb.constants import base_constants


class Test(TestWebBase):
    def test_spreadsheet_results_empty_data(self):
        response = self.app.test.post('/spreadsheet_submit')
        self.assertEqual(200, response.status_code, 'HED spreadsheet request succeeds even when no data')
        self.assertTrue(isinstance(response, Response),
                        'spreadsheet_submit to short should return a Response when no data')
        header_dict = dict(response.headers)
        self.assertEqual("error", header_dict["Category"], "The header msg_category when no spreadsheet is error ")
        self.assertFalse(response.data, "The response data for empty spreadsheet request is empty")

    def test_spreadsheet_results_validate_valid(self):
        with self.app.app_context():
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            '../data/ExcelMultipleSheets.xlsx')
            with open(spreadsheet_path, 'rb') as sc:
                x = sc.read()
            spreadsheet_buffer = io.BytesIO(bytes(x))

            input_data = {base_constants.SCHEMA_VERSION: '7.2.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_VALIDATE,
                          base_constants.WORKSHEET_NAME: 'LKT Events',
                          base_constants.WORKSHEET_SELECTED: 'LKT Events',
                          base_constants.HAS_COLUMN_NAMES: 'on',
                          'column_1_input': '',
                          'column_2_check': 'on',
                          'column_2_input': 'Event/Label/',
                          'column_3_input': '',
                          'column_4_check': 'on',
                          'column_4_input': 'Event/Description/',
                          'column_5_check': 'on',
                          'column_5_input': '',
                          base_constants.SPREADSHEET_FILE: (spreadsheet_buffer, 'ExcelMultipleSheets.xlsx'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/spreadsheet_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'spreadsheet_submit should return a Response when valid dictionary')
            self.assertEqual(200, response.status_code, 'Validation of a valid dictionary has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("success", headers_dict["Category"],
                             "The valid spreadsheet should validate successfully")
            self.assertFalse(response.data, "The response for validated spreadsheet should be empty")
            spreadsheet_buffer.close()

    def test_spreadsheet_results_validate_invalid(self):
        with self.app.app_context():
            spreadsheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            '../data/ExcelMultipleSheets.xlsx')
            with open(spreadsheet_path, 'rb') as sc:
                x = sc.read()
            spreadsheet_buffer = io.BytesIO(bytes(x))

            input_data = {base_constants.SCHEMA_VERSION: '8.0.0',
                          base_constants.COMMAND_OPTION: base_constants.COMMAND_VALIDATE,
                          base_constants.WORKSHEET_NAME: 'LKT Events',
                          base_constants.WORKSHEET_SELECTED: 'LKT Events',
                          base_constants.HAS_COLUMN_NAMES: 'on',
                          'column_1_input': '',
                          'column_2_check': 'on',
                          'column_2_input': 'Event/Label/',
                          'column_3_input': '',
                          'column_4_check': 'on',
                          'column_4_input': 'Event/Description/',
                          'column_5_check': 'on',
                          'column_5_input': '',
                          base_constants.SPREADSHEET_FILE: (spreadsheet_buffer, 'ExcelMultipleSheets.xlsx'),
                          base_constants.CHECK_FOR_WARNINGS: 'on'}
            response = self.app.test.post('/spreadsheet_submit', content_type='multipart/form-data', data=input_data)
            self.assertTrue(isinstance(response, Response),
                            'spreadsheet_submit validate should return a response object when invalid spreadsheet')
            self.assertEqual(200, response.status_code,
                             'Validation of an invalid spreadsheet to short has a valid status code')
            headers_dict = dict(response.headers)
            self.assertEqual("warning", headers_dict["Category"],
                             "Validation of an invalid spreadsheet to short generates a warning")
            self.assertTrue(response.data,
                            "The response data for invalid validation should have error messages")
            spreadsheet_buffer.close()


if __name__ == '__main__':
    unittest.main()
