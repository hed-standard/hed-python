from flask import current_app

from hed.tools.tag_format import TagFormat
from hed.util.error_reporter import get_printable_issue_string
from hed.util.exceptions import HedFileError
from hed.validator.hed_validator import HedValidator
from hed.web.constants import common
from hed.web.web_utils import form_has_option, get_hed_path_from_pull_down
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
                       common.HED_OPTION_VALIDATE: False,
                       common.HED_OPTION_TO_SHORT: False,
                       common.HED_OPTION_TO_LONG: False}
    if form_has_option(request, common.HED_OPTION, common.HED_OPTION_VALIDATE):
        input_arguments[common.HED_OPTION_VALIDATE] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_SHORT):
        input_arguments[common.HED_OPTION_TO_SHORT] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_LONG):
        input_arguments[common.HED_OPTION_TO_LONG] = True
    return input_arguments


def hedstring_process(input_arguments):
    """Perform the requested action on the HED string.

    Parameters
    ----------
    input_arguments: dict
        A dictionary with the input arguments from the hedstring form

    Returns
    -------
    Response
        Downloadable response object.
    """

    if not input_arguments.get(common.HEDSTRING, None):
        raise HedFileError('EmptyHEDString', "Please enter a nonempty HED string to process", "")
    if input_arguments.get(common.HED_OPTION_VALIDATE, None):
        return hedstring_validate(input_arguments)
    elif input_arguments.get(common.HED_OPTION_TO_SHORT, None):
        return hedstring_convert(input_arguments, short_to_long=False)
    elif input_arguments.get(common.HED_OPTION_TO_LONG, None):
        return hedstring_convert(input_arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a hedstring processing method", "")


def hedstring_convert(input_arguments, short_to_long=True):
    """Converts a hedstring from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments
    short_to_long: bool
        If True convert the hedstring to long form, otherwise convert to short form
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
