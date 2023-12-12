import os
import json
from copy import deepcopy
from jsonschema import Draft7Validator
from jsonschema.exceptions import ErrorTree
from hed.tools.remodeling.operations.valid_operations import valid_operations


class RemodelerValidator():

    MESSAGE_STRINGS = {
        "0": {
            "minItems": "There are no operations defined. Specify at least 1 operation for the remodeler to execute.",
            "type": "Operations must be contained in a list or array. This is also true when you run a single operation."
        },
        "1": {
            "type": "Each operation must be defined in a dictionary. {instance} is not a dictionary object.",
            "required": "Operation dictionary {operation_index} is missing '{missing_value}'. Every operation dictionary must specify the type of operation, a description, and the operation parameters.",
            "additionalProperties": "Operation dictionary {operation_index} contains an unexpected field '{added_property}'. Every operation dictionary must specify the type of operation, a description, and the operation parameters."
        },
        "2": {
            "type": "Operation {operation_index}: {instance} is not a {validator_value}. {operation_field} should be of type {validator_value}.",
            "enum": "{instance} is not a known remodeler operation. Accepted remodeler operations can be found in the documentation.",
            "required": "Operation {operation_index}: The parameter {missing_value} is missing. {missing_value} is a required parameter of {operation_name}.",
            "additionalProperties": "Operation {operation_index}: Operation parameters for {operation_name} contain an unexpected field '{added_property}'."
        },
        "more": {
            "type": "Operation {operation_index}: The value of {parameter_path}, in the {operation_name} operation, should be a {validator_value}. {instance} is not a {validator_value}.",
            "minItems": "Operation {operation_index}: The list in {parameter_path}, in the {operation_name} operation, should have at least {validator_value} item(s).",
            "required": "Operation {operation_index}: The field {missing_value} is missing in {parameter_path}. {missing_value} is a required parameter of {parameter_path}.",
            "additionalProperties": "Operation {operation_index}: Operation parameters for {parameter_path} contain an unexpected field '{added_property}'.",
            "enum": "Operation {operation_index}: Operation parameter {parameter_path}, in the {operation_name} operation, contains and unexpected value. Value should be one of {validator_value}."

        }
    }

    BASE_ARRAY = {
        "type": "array",
        "items": {},
        "minItems": 1
    }

    OPERATION_DICT = {
        "type": "object",
        "required": [
            "operation",
            "description",
            "parameters"
        ],
        "additionalProperties": False,
        "properties": {
            "operation": {
                "type": "string",
                "enum": [],
                "default": "convert_columns"
            },
            "description": {
                "type": "string"
            },
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        "allOf": []
    }

    PARAMETER_SPECIFICATION_TEMPLATE = {
        "if": {
            "properties": {
                "operation": {
                    "const": ""
                }
            },
            "required": [
                "operation"
            ]
        },
        "then": {
            "properties": {
                "parameters": {}
            }
        }
    }

    def __init__(self):
        self.schema = self._construct_schema()
        self.validator = Draft7Validator(self.schema)

    def validate(self, operations):
        list_of_error_strings = []
        for error in sorted(self.validator.iter_errors(operations), key=lambda e: e.path):
            list_of_error_strings.append(
                self._parse_message(error, operations))
        return list_of_error_strings

    def _parse_message(self, error, operations):
        ''' Return a user friendly error message based on the jsonschema validation error

        args: 
        - errors: a list of errors returned from the validator
        - operations: the operations that were put in

        Note:
        - json schema error does not contain all necessary information to return a 
        proper error message so we also take some information directly from the operations 
        that led to the error
        '''
        error_dict = vars(error)

        level = len(error_dict["path"])
        if level > 2:
            level = "more"
        # some information is in the validation error but not directly in a field so I need to
        # modify before they can parsed in
        # if they are necessary, they are there, if they are not there, they are not necessary
        try:
            error_dict["operation_index"] = error_dict["path"][0] + 1
            error_dict["operation_field"] = error_dict["path"][1].capitalize()
            error_dict["operation_name"] = operations[int(
                error_dict["path"][0])]['operation']
            # everything except the first two values reversed
            parameter_path = [*error_dict['path']][:1:-1]
            for ind, value in enumerate(parameter_path):
                if isinstance(value, int):
                    parameter_path[ind] = f"item {value+1}"
            error_dict["parameter_path"] = ", ".join(parameter_path)
        except (IndexError, TypeError, KeyError):
            pass

        type = str(error_dict["validator"])

        # the missing value with required elements, or the wrong additional value is not known to the
        # validation error object
        # this is a known issue of jsonschema: https://github.com/python-jsonschema/jsonschema/issues/119
        # for now the simplest thing seems to be to extract it from the error message
        if type == 'required':
            error_dict["missing_value"] = error_dict["message"].split("'")[
                1::2][0]
        if type == 'additionalProperties':
            error_dict["added_property"] = error_dict["message"].split("'")[
                1::2][0]

        return self.MESSAGE_STRINGS[str(level)][type].format(**error_dict)

    def _construct_schema(self):

        schema = deepcopy(self.BASE_ARRAY)
        schema["items"] = deepcopy(self.OPERATION_DICT)

        for operation in valid_operations.items():
            schema["items"]["properties"]["operation"]["enum"].append(operation[0])

            parameter_specification = deepcopy(self.PARAMETER_SPECIFICATION_TEMPLATE)
            parameter_specification["if"]["properties"]["operation"]["const"] = operation[0]
            parameter_specification["then"]["properties"]["parameters"] = operation[1].PARAMS
            #print(parameter_specification)

            schema["items"]["allOf"].append(deepcopy(parameter_specification))
            #print(schema)

        return schema
