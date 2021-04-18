from flask import current_app

from hed.schema.hed_schema_file import load_schema
from hed.util.error_reporter import get_printable_issue_string
from hed.util.hed_string import HedString
from hed.util.exceptions import HedFileError
from hed.validator.hed_validator import HedValidator
from hedweb.constants import common
from hedweb.web_utils import form_has_option, get_hed_path_from_pull_down
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
    arguments = {common.HED_XML_FILE: hed_file_path,
                 common.HED_DISPLAY_NAME: hed_display_name,
                 common.HEDSTRING: request.form['hedstring-input'],
                 common.HED_OPTION_VALIDATE: False,
                 common.HED_OPTION_TO_SHORT: False,
                 common.HED_OPTION_TO_LONG: False}
    if form_has_option(request, common.HED_OPTION, common.HED_OPTION_VALIDATE):
        arguments[common.HED_OPTION_VALIDATE] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_SHORT):
        arguments[common.HED_OPTION_TO_SHORT] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_LONG):
        arguments[common.HED_OPTION_TO_LONG] = True
    return arguments


def hedstring_process(arguments):
    """Perform the requested action on the HED string.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the hedstring form

    Returns
    -------
    Response
        Downloadable response object.
    """

    if not arguments.get(common.HEDSTRING, None):
        raise HedFileError('EmptyHEDString', "Please enter a nonempty HED string to process", "")
    if arguments.get(common.HED_OPTION_VALIDATE, None):
        return hedstring_validate(arguments)
    elif arguments.get(common.HED_OPTION_TO_SHORT, None):
        return hedstring_convert(arguments, short_to_long=False)
    elif arguments.get(common.HED_OPTION_TO_LONG, None):
        return hedstring_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a hedstring processing method", "")


def hedstring_convert(arguments, short_to_long=True, hed_schema=None):
    """Converts a hedstring from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    short_to_long: bool
        If True convert the hedstring to long form, otherwise convert to short form
    hed_schema: HedSchema object

    Returns
    -------
    dict
        A dictionary with hedstring-results as the key
    """

    if not hed_schema:
        hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))
    hed_string_obj = HedString(arguments.get(common.HEDSTRING))
    if short_to_long:
        issues = hed_string_obj.convert_to_long(hed_schema)
    else:
        issues = hed_string_obj.convert_to_short(hed_schema)

    if issues:
        return_str = get_printable_issue_string(issues, "Unable to convert HED string:")
        category = 'warning'
    else:
        return_str = str(hed_string_obj)
        category = 'success'
    return {'hedstring-result': return_str, 'category': category}


def hedstring_validate(arguments):
    """Validates a hedstring and returns a dictionary containing the issues or a no errors message

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments

    Returns
    -------
    dict
        A dictionary with hedstring-results as the key
    """

    hed_file_path = arguments.get(common.HED_XML_FILE)
    hed_validator = HedValidator(hed_xml_file=hed_file_path)
    issues = hed_validator.validate_input(arguments.get(common.HEDSTRING))
    if issues:
        return_str = get_printable_issue_string(issues, "HED validation errors:")
        category = 'warning'
    else:
        return_str = "No validation errors found..."
        category = 'success'
    return {'hedstring-result': return_str, 'category': category}
