import os
import json
import unittest
from copy import deepcopy
from hed.tools.remodeling.validator import RemodelerValidator
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '../data/remodel_tests/all_remodel_operations.json'))) as f:
            cls.remodel_file = json.load(f)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_validator_build(self):
        validator = RemodelerValidator()

    def test_validate_valid(self):
        validator = RemodelerValidator()
        error_strings = validator.validate(self.remodel_file)
        self.assertFalse(error_strings)

    def test_validate_array(self):
        validator = RemodelerValidator()
        wrong_input_type = {"operation": "remove_columns"}
        error_strings = validator.validate(wrong_input_type)
        self.assertEqual(error_strings[0], "Operations must be contained in a list or array. This is also true when you run a single operation.")

        no_operations = []
        error_strings = validator.validate(no_operations)
        self.assertEqual(error_strings[0], "There are no operations defined. Specify at least 1 operation for the remodeler to execute.")

    def test_validate_operations(self):
        validator = RemodelerValidator()
        
        invalid_operation_type = ["string"]
        error_strings = validator.validate(invalid_operation_type)
        self.assertEqual(error_strings[0], "Each operation must be defined in a dictionary. string is not a dictionary object.")

        invalid_operation_missing = [self.remodel_file[0].copy()]
        del invalid_operation_missing[0]["description"]  
        error_strings = validator.validate(invalid_operation_missing)
        self.assertEqual(error_strings[0], "Operation dictionary 1 is missing 'description'. Every operation dictionary must specify the type of operation, a description, and the operation parameters.")

        invalid_operation_name = [self.remodel_file[0].copy()]  
        invalid_operation_name[0]["operation"] = "unlisted_operation"
        error_strings = validator.validate(invalid_operation_name)
        self.assertEqual(error_strings[0], "unlisted_operation is not a known remodeler operation. Accepted remodeler operations can be found in the documentation.")

    def test_validate_parameters(self):
        validator = RemodelerValidator()
        
        missing_parameter = [deepcopy(self.remodel_file[0])]
        del missing_parameter[0]["parameters"]["column_names"]
        error_strings = validator.validate(missing_parameter)
        self.assertEqual(error_strings[0], "Operation 1: The parameter column_names is missing. column_names is a required parameter of remove_columns.")

        missing_parameter_nested = [deepcopy(self.remodel_file[10])]
        del missing_parameter_nested[0]["parameters"]["new_events"]["response"]["onset_source"]
        error_strings = validator.validate(missing_parameter_nested)
        self.assertEqual(error_strings[0], "Operation 1: The field onset_source is missing in response, new_events. onset_source is a required parameter of response, new_events.")

        invalid_parameter = [deepcopy(self.remodel_file[0])]
        invalid_parameter[0]["parameters"]["invalid"] = "invalid_value"
        error_strings = validator.validate(invalid_parameter)
        self.assertEqual(error_strings[0], "Operation 1: Operation parameters for remove_columns contain an unexpected field 'invalid'.")

        invalid_parameter_nested = [deepcopy(self.remodel_file[10])]
        invalid_parameter_nested[0]["parameters"]["new_events"]["response"]["invalid"] = "invalid_value"
        error_strings = validator.validate(invalid_parameter_nested)
        self.assertEqual(error_strings[0], "Operation 1: Operation parameters for response, new_events contain an unexpected field 'invalid'.")

        invalid_type = [deepcopy(self.remodel_file[0])]
        invalid_type[0]["parameters"]["column_names"] = 0
        error_strings = validator.validate(invalid_type)
        self.assertEqual(error_strings[0], "Operation 1: The value of column_names, in the remove_columns operation, should be a array. 0 is not a array.")

        invalid_type_nested = [deepcopy(self.remodel_file[10])]
        invalid_type_nested[0]["parameters"]["new_events"]["response"]["onset_source"] = {"key": "value"}
        error_strings = validator.validate(invalid_type_nested)
        self.assertEqual(error_strings[0], "Operation 1: The value of onset_source, response, new_events, in the split_rows operation, should be a array. {'key': 'value'} is not a array.")

        empty_array = [deepcopy(self.remodel_file[0])]
        empty_array[0]["parameters"]["column_names"] = []
        error_strings = validator.validate(empty_array)
        self.assertEqual(error_strings[0], "Operation 1: The list in column_names, in the remove_columns operation, should have at least 1 item(s).")
       
        empty_array_nested = [deepcopy(self.remodel_file[5])]
        empty_array_nested[0]["parameters"]["map_list"][0] = []
        error_strings = validator.validate(empty_array_nested)
        self.assertEqual(error_strings[0], "Operation 1: The list in item 1, map_list, in the remap_columns operation, should have at least 1 item(s).")        

        # invalid_value = [deepcopy(self.remodel_file[18])]
        # invalid_value[0]["parameters"]["convert_to"] = "invalid_value"
        # error_strings = validator.validate(invalid_value)
        # self.assertEqual(error_strings[0], "Operation 1: Operation parameter convert_to, in the convert_columns operation, contains and unexpected value. Value should be one of ['str', 'int', 'float', 'fixed'].")
