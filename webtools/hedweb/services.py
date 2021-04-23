import os
import json

from flask import current_app
from hed.schema import hed_schema_file
from hed.util import hed_cache
from hed.util.error_reporter import get_printable_issue_string
from hed.validator.hed_validator import HedValidator
from hed.util.column_def_group import ColumnDefGroup


app_config = current_app.config


def services_process(arguments):
    """
    Reports validation status of hed strings associated with EEG events received from EEGLAB plugin HEDTools

    Parameters
    ----------
    arguments dict
        a dictionary of arguments
        Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    string
        A serialized JSON string containing information related to the hed strings validation result.
        If the validation fails then a 500 error message is returned.
    """
    response = {"result": "", "error_type": "", "message": ""}
    service = arguments.get("service", "")
    supported_services = get_services()
    if not service:
        response["error_type"] = 'HEDServiceMissing'
        response["message"] = "Must specify a valid service"
    elif service not in supported_services.keys():
        response["error_type"] = 'HEDServiceNotSupported'
        response["message"] = f"{service} not supported"
    elif service == "get_services":
        response["result"] = {"supported_services": supported_services}
    elif service == "validate_json":
        response["result"] = get_validate_dictionary(arguments)
    elif service == "validate_strings":
        response["result"] = get_validate_strings(arguments)
    else:
        response["errors"] = f"{service} not implemented"
    return response


def get_services():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    the_path = os.path.join(dir_path, 'static/resources/services.json')
    with open(the_path) as f:
        service_info = json.load(f)
    return service_info


def get_validate_dictionary(arguments):
    """
    Reports validation status of hed strings

    Parameters
    ----------
    arguments: dict
         A dictionary of user data submitted by HEDTools.
         Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    dict
         A serialized JSON string containing information related to the hed strings validation result.
    """
    hed_file_path = arguments.get('hed_file_path', None)
    if not hed_file_path:
        hed = arguments.get("hed_version", "")
        hed_file_path = hed_cache.get_path_from_hed_version(hed)
    hed_schema = hed_schema_file.load_schema(hed_file_path)
    json_text = arguments.get("json_dictionary", "")
    json_dictionary = ColumnDefGroup(json_string=json_text)
    issues = json_dictionary.validate_entries(hed_schema)
    if issues:
        issue_str = get_printable_issue_string(issues, f"HED validation errors")
        category = 'warning'
    else:
        issue_str = ''
        category = 'success'
    # TODO: hed_schema needs to know its version
    version = hed_schema.schema_attributes.get('version', 'Unknown version')
    result = {'hed_version': version, 'validation_errors': issue_str, 'category': category}
    return result


def get_validate_strings(arguments):
    """
    Reports validation status of hed strings

    Parameters
    ----------
    arguments: dict
         A dictionary of user data submitted data
         Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    list of dict
         A serialized JSON string containing information related to the hed strings validation result.
    """
    hed_file_path = arguments.get('hed_file_path', None)
    if not hed_file_path:
        hed = arguments.get("hed_version", "")
        hed_file_path = hed_cache.get_path_from_hed_version(hed)
    hed_schema = hed_schema_file.load_schema(hed_file_path)
    hed_strings = arguments.get("hed_strings", "")
    hed_validator = HedValidator(hed_schema=hed_schema)
    issues = hed_validator.validate_input(hed_strings)
    validation_errors = []
    for i in range(len(hed_strings)):
        issue = issues[i]
        if issue:
            validation_errors.append(get_printable_issue_string(issue, f"Errors for HED string {i+1}:"))
    if validation_errors:
        category = 'warning'
    else:
        category = 'success'
    version = hed_schema.schema_attributes.get('version', 'Unknown version')
    return {'hed_version': version, 'validation_errors': validation_errors, 'category': category}
