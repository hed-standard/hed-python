import os
import json
import traceback
from flask import current_app

from hed.schema import hed_schema_file
from hed.util import hed_cache
from hed.util.file_util import delete_file_if_it_exists
from hed.validator.hed_validator import HedValidator
from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_types import ErrorContext


app_config = current_app.config


def report_services_status(request):
    """
    Reports validation status of hed strings associated with EEG events received from EEGLAB plugin HEDTools

    Parameters
    ----------
    request: Request object
        A Request object containing user data submitted by HEDTools.
        Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    string
        A serialized JSON string containing information related to the hed strings validation result.
        If the validation fails then a 500 error message is returned.
    """
    response = {"result": "", "errors": "", "error_details": ""}
    hed_xml_file = ''
    try:
        form_data = request.data
        form_string = form_data.decode()
        param_dict = json.loads(form_string)
        service = param_dict.get("service", "")
        supported_services = get_services()
        if not service:
            response["errors"] = "Must specify a service"
        elif service not in supported_services.keys():
            response["errors"] = f"{service} not supported"
        elif service == "get_services":
            response["result"] = {"supported_services": supported_services}
        elif service == "validate_json":
            response["result"] = get_validate_dictionary(param_dict)
        elif service == "validate_strings":
            response["result"] = get_validate_strings(param_dict)
        else:
            response["errors"] = f"{service} not implemented"
    except:
        response["error_details"] = traceback.format_exc()
        response["errors"] = "An exception thrown during execution of service"
    finally:
        delete_file_if_it_exists(hed_xml_file)

    return response


def get_services():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    the_path = os.path.join(dir_path, 'static/resources/services.json')
    with open(the_path) as f:
        service_info = json.load(f)
    return service_info


def get_validate_dictionary(params):
    """
    Reports validation status of hed strings

    Parameters
    ----------
    params: dict
         A Request object containing user data submitted by HEDTools.
         Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    dict
         A serialized JSON string containing information related to the hed strings validation result.
    """
    hed = params.get("hed_version", "")
    hed_file_path = hed_cache.get_path_from_hed_version(hed)
    hed_schema = hed_schema_file.load_schema(hed_file_path)
    json_text = params.get("json_dictionary", "")
    json_dictionary = ColumnDefGroup(json_string=json_text)
    issues = json_dictionary.validate_entries(hed_schema)
    issue_list = []
    for issue in issues:
        code = issue.get('code', "")
        message = issue.get('message', "")
        column_name = issue.get(ErrorContext.SIDECAR_COLUMN_NAME, "")
        if column_name:
            column_name = column_name[0]
        key_name = issue.get(ErrorContext.SIDECAR_KEY_NAME, "")
        if key_name:
            key_name = key_name[0]
        hed_string = issue.get(ErrorContext.SIDECAR_HED_STRING, "")
        if hed_string:
            hed_string = hed_string[0]
        issue_dict = {"code": code, "message": message, "column_name": column_name,
                      "key_name": key_name, "hed_string": hed_string}
        issue_list.append(issue_dict)
    result = {'hed_version': hed, 'validation_errors': issue_list}
    return result


def get_validate_strings(params):
    """
    Reports validation status of hed strings

    Parameters
    ----------
    params: dict
         A Request object containing user data submitted by HEDTools.
         Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    list of dict
         A serialized JSON string containing information related to the hed strings validation result.
    """
    hed = params.get("hed_version", "")
    hed_file_path = hed_cache.get_path_from_hed_version(hed)
    hed_strings = params.get("hed_strings", "")
    hed_validator = HedValidator(hed_xml_file=hed_file_path)
    validation_issues = {}
    str_num = 1
    for hed_string in hed_strings:
        issue = hed_validator.validate_input(hed_string)
        if issue:
            validation_issues[f"String_{str_num}"] = issue
        str_num += 1
    return {'hed_version': hed, 'validation_errors': validation_issues}
