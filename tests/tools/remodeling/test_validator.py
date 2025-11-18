import os
import json
import unittest
from copy import deepcopy
from hed.tools.remodeling.remodeler_validator import RemodelerValidator


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "..", "../data/remodel_tests/all_remodel_operations.json"
                )
            )
        ) as f:
            cls.remodel_file = json.load(f)
        cls.validator = RemodelerValidator()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_validator_build(self):
        pass

    def test_validate_valid(self):
        error_strings = self.validator.validate(self.remodel_file)
        self.assertFalse(error_strings)

    def test_validate_array(self):
        wrong_input_type = {"operation": "remove_columns"}
        error_strings = self.validator.validate(wrong_input_type)
        self.assertEqual(
            error_strings[0], "Operations must be contained in a list or array. " + "This is also true for a single operation."
        )

        no_operations = []
        error_strings = self.validator.validate(no_operations)
        self.assertEqual(
            error_strings[0], "There are no operations defined. Specify at least 1 operation for the remodeler to execute."
        )

    def test_validate_operations(self):
        invalid_operation_type = ["string"]
        error_strings = self.validator.validate(invalid_operation_type)
        self.assertEqual(
            error_strings[0], "Each operation must be defined in a dictionary: " + "string is not a dictionary object."
        )

        invalid_operation_missing = [self.remodel_file[0].copy()]
        del invalid_operation_missing[0]["description"]
        error_strings = self.validator.validate(invalid_operation_missing)
        self.assertEqual(
            error_strings[0],
            "Operation dictionary 1 is missing 'description'. "
            + "Every operation dictionary must specify the type of operation, a description, "
            + "and the operation parameters.",
        )

        invalid_operation_name = [self.remodel_file[0].copy()]
        invalid_operation_name[0]["operation"] = "unlisted_operation"
        error_strings = self.validator.validate(invalid_operation_name)
        self.assertEqual(
            error_strings[0],
            "unlisted_operation is not a known remodeler operation. " + "See the documentation for valid operations.",
        )

    def test_validate_parameters(self):
        missing_parameter = [deepcopy(self.remodel_file[0])]
        del missing_parameter[0]["parameters"]["column_names"]
        error_strings = self.validator.validate(missing_parameter)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The parameter column_names is missing. " + "column_names is a required parameter of remove_columns.",
        )

        missing_parameter_nested = [deepcopy(self.remodel_file[10])]
        del missing_parameter_nested[0]["parameters"]["new_events"]["response"]["onset_source"]
        error_strings = self.validator.validate(missing_parameter_nested)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The field onset_source is missing in response new_events. "
            + "onset_source is a required parameter of response new_events.",
        )

        invalid_parameter = [deepcopy(self.remodel_file[0])]
        invalid_parameter[0]["parameters"]["invalid"] = "invalid_value"
        error_strings = self.validator.validate(invalid_parameter)
        self.assertEqual(
            error_strings[0],
            "Operation 1: Operation parameters for remove_columns " + "contain an unexpected field 'invalid'.",
        )

        invalid_parameter_nested = [deepcopy(self.remodel_file[10])]
        invalid_parameter_nested[0]["parameters"]["new_events"]["response"]["invalid"] = "invalid_value"
        error_strings = self.validator.validate(invalid_parameter_nested)
        self.assertEqual(
            error_strings[0],
            "Operation 1: Operation parameters for response " + "new_events contain an unexpected field 'invalid'.",
        )

        invalid_type = [deepcopy(self.remodel_file[0])]
        invalid_type[0]["parameters"]["column_names"] = 0
        error_strings = self.validator.validate(invalid_type)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The value of column_names in the remove_columns operation " + "should be array. 0 is not a array.",
        )

        invalid_type_nested = [deepcopy(self.remodel_file[10])]
        invalid_type_nested[0]["parameters"]["new_events"]["response"]["onset_source"] = {"key": "value"}
        error_strings = self.validator.validate(invalid_type_nested)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The value of onset_source response new_events "
            + "in the split_rows operation should be array. {'key': 'value'} is not a array.",
        )

        empty_array = [deepcopy(self.remodel_file[0])]
        empty_array[0]["parameters"]["column_names"] = []
        error_strings = self.validator.validate(empty_array)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The list in column_names in the remove_columns " + "operation should have at least 1 item(s).",
        )

        empty_array_nested = [deepcopy(self.remodel_file[5])]
        empty_array_nested[0]["parameters"]["map_list"][0] = []
        error_strings = self.validator.validate(empty_array_nested)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The list in item 1 map_list in the remap_columns " + "operation should have at least 1 item(s).",
        )

        # invalid_value = [deepcopy(self.remodel_file[18])]
        # invalid_value[0]["parameters"]["convert_to"] = "invalid_value"
        # error_strings = validator.validate(invalid_value)
        # self.assertEqual(error_strings[0], "Operation 1: Operation parameter convert_to, in the " +
        #                  "convert_columns operation, contains and unexpected value. " +
        #                  "Value should be one of ['str', 'int', 'float', 'fixed'].")

        # value_dependency = [deepcopy(self.remodel_file[18])]
        # value_dependency[0]["parameters"]["convert_to"] = "fixed"
        # error_strings = validator.validate(value_dependency)
        # self.assertEqual(error_strings[0], "Operation 1: The parameter decimal_places is missing. " +
        #                  " The decimal_places is a required parameter of convert_columns.")

        property_dependency = [deepcopy(self.remodel_file[1])]
        del property_dependency[0]["parameters"]["factor_values"]
        error_strings = self.validator.validate(property_dependency)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The parameter factor_names is missing: "
            + "factor_names is a required parameter of factor_column when ['factor_values'] is specified.",
        )

        double_item_in_array = [deepcopy(self.remodel_file[0])]
        double_item_in_array[0]["parameters"]["column_names"] = ["response", "response"]
        error_strings = self.validator.validate(double_item_in_array)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The list in column_names in the remove_columns " + "operation should only contain unique items.",
        )

        double_item_in_array_nested = [deepcopy(self.remodel_file[10])]
        double_item_in_array_nested[0]["parameters"]["new_events"]["response"]["copy_columns"] = ["response", "response"]
        error_strings = self.validator.validate(double_item_in_array_nested)
        self.assertEqual(
            error_strings[0],
            "Operation 1: The list in copy_columns response new_events in the split_rows "
            + "operation should only contain unique items.",
        )

    def test_validate_parameter_data(self):
        factor_column_validate = [deepcopy(self.remodel_file)[1]]
        factor_column_validate[0]["parameters"]["factor_names"] = ["stopped"]
        error_strings = self.validator.validate(factor_column_validate)
        self.assertEqual(
            error_strings[0], "Operation 1 (factor_column): factor_names must be " + "same length as factor_values"
        )

        factor_hed_tags_validate = [deepcopy(self.remodel_file)[2]]
        factor_hed_tags_validate[0]["parameters"]["query_names"] = ["correct"]
        error_strings = self.validator.validate(factor_hed_tags_validate)
        self.assertEqual(
            error_strings[0],
            "Operation 1 (factor_hed_tags): QueryNamesLengthBad: "
            + "The query_names length 1 must be empty or equal to the queries length 2.",
        )

        merge_consecutive_validate = [deepcopy(self.remodel_file)[4]]
        merge_consecutive_validate[0]["parameters"]["match_columns"].append("trial_type")
        error_strings = self.validator.validate(merge_consecutive_validate)
        self.assertEqual(
            error_strings[0], "Operation 1 (merge_consecutive): column_name `trial_type` " + "cannot be a match_column."
        )

        remap_columns_validate_same_length = [deepcopy(self.remodel_file)[5]]
        remap_columns_validate_same_length[0]["parameters"]["map_list"][0] = [""]
        error_strings = self.validator.validate(remap_columns_validate_same_length)
        self.assertEqual(error_strings[0], "Operation 1 (remap_columns): all map_list arrays must be of length 3.")

        remap_columns_validate_right_length = [deepcopy(self.remodel_file[5])]
        remap_columns_validate_right_length[0]["parameters"]["map_list"] = [["string1", "string2"], ["string3", "string4"]]
        error_strings = self.validator.validate(remap_columns_validate_right_length)
        self.assertEqual(error_strings[0], "Operation 1 (remap_columns): all map_list arrays must be of length 3.")

        remap_columns_integer_sources = [deepcopy(self.remodel_file[5])]
        remap_columns_integer_sources[0]["parameters"]["integer_sources"] = ["unknown_column"]
        error_strings = self.validator.validate(remap_columns_integer_sources)
        self.assertEqual(
            error_strings[0],
            "Operation 1 (remap_columns): the integer_sources {'unknown_column'} " + "are missing from source_columns.",
        )
