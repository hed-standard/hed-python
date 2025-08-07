""" Validator for remodeler input files. """
import jsonschema
from copy import deepcopy
from hed.tools.remodeling.operations.valid_operations import valid_operations


class RemodelerValidator:
    """ Validator for remodeler input files. """

    MESSAGE_STRINGS = {
        "0": {
            "minItems": "There are no operations defined. Specify at least 1 operation for the remodeler to execute.",
            "type": "Operations must be contained in a list or array. This is also true for a single operation."
        },
        "1": {
            "type": "Each operation must be defined in a dictionary: {instance} is not a dictionary object.",
            "required": "Operation dictionary {operation_index} is missing '{missing_value}'. " +
                        "Every operation dictionary must specify the type of operation, " +
                        "a description, and the operation parameters.",
            "additionalProperties": "Operation dictionary {operation_index} contains an unexpected field " +
                                    "'{added_property}'. Every operation dictionary must specify the type " +
                                    "of operation, a description, and the operation parameters."
        },
        "2": {
            "type": "Operation {operation_index}: {instance} is not a {validator_value}. " +
                    "{operation_field} should be of type {validator_value}.",
            "enum": "{instance} is not a known remodeler operation. See the documentation for valid operations.",
            "required": "Operation {operation_index}: The parameter {missing_value} is missing. {missing_value} " +
                        "is a required parameter of {operation_name}.",
            "additionalProperties": "Operation {operation_index}: Operation parameters for {operation_name} " +
                                    "contain an unexpected field '{added_property}'.",
            "dependentRequired": "Operation {operation_index}: The parameter {missing_value} is missing: " +
                                 "{missing_value} is a required parameter of {operation_name} " +
                                 "when {dependent_on} is specified."
        },
        "more": {
            "type": "Operation {operation_index}: The value of {parameter_path} in the {operation_name} operation " +
                    "should be {validator_value}. {instance} is not a {validator_value}.",
            "minItems": "Operation {operation_index}: The list in {parameter_path} in the {operation_name} " +
                        "operation should have at least {validator_value} item(s).",
            "required": "Operation {operation_index}: The field {missing_value} is missing in {parameter_path}. " +
                        "{missing_value} is a required parameter of {parameter_path}.",
            "additionalProperties": "Operation {operation_index}: Operation parameters for {parameter_path} " +
                                    "contain an unexpected field '{added_property}'.",
            "enum": "Operation {operation_index}: Operation parameter {parameter_path} in the {operation_name} " +
                    "operation contains and unexpected value. Value should be one of {validator_value}.",
            "uniqueItems": "Operation {operation_index}: The list in {parameter_path} in the {operation_name} " +
                           "operation should only contain unique items.",
            "minProperties": "Operation {operation_index}: The dictionary in {parameter_path} in the " +
                             "{operation_name} operation should have at least {validator_value} key(s)."
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
        """ Constructor for remodeler Validator. """
        self.schema = self._construct_schema()  # The compiled json schema against which remodeler files are validated.
        self.validator = jsonschema.Draft202012Validator(self.schema)  # The instantiated json schema validator.

    def validate(self, operations) -> list[str]:
        """ Validate remodeler operations against the json schema specification and specific op requirements.

        Parameters:
            operations (list[dict]): List of di with input operations to run through the remodeler.

        Returns:
            list[str]: List with the error messages for errors identified by the validator.
        """

        list_of_error_strings = []
        for error in sorted(self.validator.iter_errors(operations), key=lambda e: e.path):
            list_of_error_strings.append( self._parse_message(error, operations))
        if list_of_error_strings:
            return list_of_error_strings

        operation_by_parameters = [(operation["operation"], operation["parameters"]) for operation in operations]

        for index, operation in enumerate(operation_by_parameters):
            error_strings = valid_operations[operation[0]].validate_input_data(operation[1])
            for error_string in error_strings:
                list_of_error_strings.append(f"Operation {index + 1} ({operation[0]}): {error_string}")

        return list_of_error_strings

    def _parse_message(self, error, operations):
        """ Return a user-friendly error message based on the jsonschema validation error.

        Parameters:
            error (ValidationError): A validation error from jsonschema validator.
            operations (list of dict): The operations that were validated.

        Note:
        - json schema error does not contain all necessary information to return a
          proper error message so, we also take some information directly from the operations
          that led to the error.

        - all necessary information is gathered into an error dict, message strings are predefined
          in a dictionary which are formatted with additional information.
        """
        error_dict = vars(error)

        level = len(error_dict["path"])
        if level > 2:
            level = "more"
        # some information is in the validation error but not directly in a field, so I need to
        # modify before they can be parsed in
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
            error_dict["parameter_path"] = " ".join(parameter_path)
        except (IndexError, TypeError, KeyError):
            pass

        attr_type = str(error_dict["validator"])

        # the missing value with required elements, or the wrong additional value is not known to the
        # validation error object
        # this is a known issue of jsonschema: https://github.com/python-jsonschema/jsonschema/issues/119
        # for now the simplest thing seems to be to extract it from the error message
        if attr_type == 'required':
            error_dict["missing_value"] = error_dict["message"].split("'")[
                1::2][0]
        if attr_type == 'additionalProperties':
            error_dict["added_property"] = error_dict["message"].split("'")[
                1::2][0]

        # dependent is required, provided both the missing value and the reason it is required in one dictionary
        # it is split over two for the error message
        if attr_type == 'dependentRequired':
            error_dict["missing_value"] = list(error_dict["validator_value"].keys())[0]
            error_dict["dependent_on"] = list(error_dict["validator_value"].values())[0]

        return self.MESSAGE_STRINGS[str(level)][attr_type].format(**error_dict)

    def _construct_schema(self):
        """ Return a schema specialized to the operations.

        Returns:
            dict: Array of schema operations.

        """
        schema = deepcopy(self.BASE_ARRAY)
        schema["items"] = deepcopy(self.OPERATION_DICT)

        for operation in valid_operations.items():
            schema["items"]["properties"]["operation"]["enum"].append(operation[0])

            parameter_specification = deepcopy(self.PARAMETER_SPECIFICATION_TEMPLATE)
            parameter_specification["if"]["properties"]["operation"]["const"] = operation[0]
            parameter_specification["then"]["properties"]["parameters"] = operation[1].PARAMS

            schema["items"]["allOf"].append(deepcopy(parameter_specification))

        return schema
