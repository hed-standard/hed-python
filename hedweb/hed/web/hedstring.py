from flask import current_app

from hed.tools.tag_format import TagFormat
from hed.util.error_reporter import get_printable_issue_string
from hed.validator.hed_validator import HedValidator
from hed.web.constants import common
from hed.web.web_utils import form_has_option, get_hed_path_from_pull_down
from hed.web.web_exceptions import HedError
app_config = current_app.config


def generate_input_from_hedstring_form(request):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying validation function.
    """
    hed_file_path, hed_display_name = get_hed_path_from_pull_down(request)
    input_arguments = {common.HED_XML_FILE: hed_file_path,
                       common.HED_DISPLAY_NAME: hed_display_name,
                       common.HEDSTRING: request.form['hedstring-input'],
                       common.HEDSTRING_VALIDATE: False,
                       common.HEDSTRING_TO_SHORT: False,
                       common.HEDSTRING_TO_LONG: False}
    if form_has_option(request, common.HEDSTRING_OPTION, common.HEDSTRING_VALIDATE):
        input_arguments[common.HEDSTRING_VALIDATE] = True
    elif form_has_option(request, common.HEDSTRING_OPTION, common.HEDSTRING_TO_SHORT):
        input_arguments[common.HEDSTRING_TO_SHORT] = True
    elif form_has_option(request, common.HEDSTRING_OPTION, common.HEDSTRING_TO_LONG):
        input_arguments[common.HEDSTRING_TO_LONG] = True
    return input_arguments


def hedstring_process(input_arguments):
    """Perform the requested action on the HED string.

    Parameters
    ----------
    input_arguments: dict
        A dictionary with the input arguments from the hedstring form

    Returns
    -------
    string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """

    if not input_arguments[common.HEDSTRING]:
        raise HedError('EmptyHEDString', "Please enter a nonempty HED string to process")
    if input_arguments[common.HEDSTRING_VALIDATE]:
        return hedstring_validate(input_arguments)
    elif input_arguments[common.HEDSTRING_TO_SHORT]:
        return hedstring_convert(input_arguments, short_to_long=False)
    elif input_arguments[common.HEDSTRING_TO_LONG]:
        return hedstring_convert(input_arguments)
    else:
        raise HedError('UnknownProcessingMethod', "Select a hedstring processing method")


def hedstring_convert(input_arguments, short_to_long=True):
    """Converts a hedstring from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments
    short_to_long: bool
        If True convert the hedstring
    Returns
    -------
    dict
        A dictionary with hedstring-results as the key
    """

    hed_file_path = input_arguments.get(common.HED_XML_FILE)
    tag_formatter = TagFormat(hed_file_path)
    if short_to_long:
        return_str, issues = tag_formatter.convert_hed_string_to_long(input_arguments.get(common.HEDSTRING))
    else:
        return_str, issues = tag_formatter.convert_hed_string_to_short(input_arguments.get(common.HEDSTRING))

    if issues:
        return_str = get_printable_issue_string(issues, "Unable to convert HED string:")
    return {'hedstring-result': return_str}


def hedstring_validate(input_arguments):
    """Validates a hedstring and returns a dictionary containing the issues or a no errors message

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments

    Returns
    -------
    dict
        A dictionary with hedstring-results as the key
    """

    hed_file_path = input_arguments.get(common.HED_XML_FILE)
    hed_validator = HedValidator(hed_xml_file=hed_file_path)
    issues = hed_validator.validate_input(input_arguments.get(common.HEDSTRING))
    if issues:
        return_str = get_printable_issue_string(issues, "HED validation errors:")
    else:
        return_str = "No validation errors found..."
    return {'hedstring-result': return_str}
