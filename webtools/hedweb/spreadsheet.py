from flask import current_app

from hed.util.error_reporter import get_printable_issue_string
from hed.util.exceptions import HedFileError
from hed.util.hed_file_input import HedFileInput
from hed.validator.hed_validator import HedValidator
from hedweb.constants import common, file_constants
from hedweb.web_utils import convert_number_str_to_list, form_has_option,\
    generate_filename, generate_download_file_response, \
    get_hed_path_from_pull_down, get_uploaded_file_path_from_form, \
    get_optional_form_field, save_text_to_upload_folder, generate_text_response
from hedweb.spreadsheet_utils import get_specific_tag_columns_from_form

app_config = current_app.config


def generate_input_from_spreadsheet_form(request):
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
    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(request, common.SPREADSHEET_FILE, file_constants.SPREADSHEET_FILE_EXTENSIONS)

    arguments = {
        common.HED_XML_FILE: hed_file_path,
        common.HED_DISPLAY_NAME: hed_display_name,
        common.SPREADSHEET_PATH: uploaded_file_name,
        common.SPREADSHEET_FILE: original_file_name,
        common.TAG_COLUMNS: convert_number_str_to_list(request.form[common.TAG_COLUMNS]),
        common.COLUMN_PREFIX_DICTIONARY: get_specific_tag_columns_from_form(request),
        common.WORKSHEET_SELECTED: get_optional_form_field(request, common.WORKSHEET_SELECTED, common.STRING),
        common.HAS_COLUMN_NAMES: get_optional_form_field(request, common.HAS_COLUMN_NAMES, common.BOOLEAN)
    }
    if form_has_option(request, common.HED_OPTION, common.HED_OPTION_VALIDATE):
        arguments[common.HED_OPTION_VALIDATE] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_SHORT):
        arguments[common.HED_OPTION_TO_SHORT] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_LONG):
        arguments[common.HED_OPTION_TO_LONG] = True
    return arguments


def spreadsheet_process(arguments):
    """Perform the requested action for the spreadsheet.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the dictionary form

    Returns
    -------
      Response
        Downloadable response object.
    """

    if not arguments[common.SPREADSHEET_PATH]:
        raise HedFileError('EmptySpreadsheetFile', "Please upload a spreadsheet to process", "")
    if arguments.get(common.HED_OPTION_VALIDATE, None):
        return spreadsheet_validate(arguments)
    elif arguments.get(common.HED_OPTION_TO_SHORT, None):
        return spreadsheet_convert(arguments, short_to_long=False)
    elif arguments.get(common.HED_OPTION_TO_LONG, None):
        return spreadsheet_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a spreadsheet processing method", "")


def spreadsheet_convert(arguments, short_to_long=True, hed_schema=None):
    """Converts a spreadsheet from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    short_to_long: bool
        If True convert the dictionary to long form, otherwise convert to short form
    hed_schema:str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    Response
        A downloadable spreadsheet file or a file containing warnings
    """

    return generate_text_response('Not available', category='warning', msg='Spreadsheet conversion not implemented yet')
    #
    # if not hed_schema:
    #     hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))
    # error_handler = ErrorHandler()
    # tag_formatter = TagFormat(hed_schema=hed_schema, error_handler=error_handler)
    # issues = []
    # for column_def in json_dictionary:
    #     for hed_string, position in column_def.hed_string_iter(include_position=True):
    #         if short_to_long:
    #             new_hed_string, errors = tag_formatter.convert_hed_string_to_long(hed_string)
    #         else:
    #             new_hed_string, errors = tag_formatter.convert_hed_string_to_short(hed_string)
    #         issues = issues + errors
    #         column_def.set_hed_string(new_hed_string, position)
    # if short_to_long:
    #     suffix = '_to_long'
    # else:
    #     suffix = '_to_short'
    # issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
    # display_name = arguments.get(common.JSON_FILE, '')
    # if issues:
    #     display_name = arguments.get(common.JSON_FILE, '')
    #     issue_str = get_printable_issue_string(issues, f"JSON conversion for {display_name} was unsuccessful")
    #     file_name = generate_filename(display_name, suffix=f"{suffix}_conversion_errors", extension='.txt')
    #     issue_file = save_text_to_upload_folder(issue_str, file_name)
    #     return generate_download_file_response(issue_file, display_name=file_name, category='warning',
    #                                            msg='JSON dictionary had conversion errors')
    # else:
    #     file_name = generate_filename(display_name, suffix=suffix, extension='.json')
    #     file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
    #     json_dictionary.save_as_json(file_path)
    #     return generate_download_file_response(file_path, display_name=file_name, category='success',
    #                                            msg='JSON dictionary was successfully converted')


def spreadsheet_validate(arguments, hed_validator=None):
    """ Validates the spreadsheet.

    Parameters
    ----------
    arguments: dictionary
        A dictionary containing the arguments for the validation function.
    hed_validator: HedValidator
        Validator passed if previously created in another phase
    Returns
    -------
    HedValidator object
        A HedValidator object containing the validation results.
    """

    file_input = HedFileInput(arguments.get(common.SPREADSHEET_PATH, None),
                              worksheet_name=arguments.get(common.WORKSHEET_SELECTED, None),
                              tag_columns=arguments.get(common.TAG_COLUMNS, None),
                              has_column_names=arguments.get(common.HAS_COLUMN_NAMES, None),
                              column_prefix_dictionary=arguments.get(common.COLUMN_PREFIX_DICTIONARY,
                                                                     None))
    if not hed_validator:
        hed_validator = HedValidator(hed_xml_file=arguments.get(common.HED_XML_FILE, ''),
                                     check_for_warnings=arguments.get(common.CHECK_FOR_WARNINGS, False))

    issues = hed_validator.validate_input(file_input)

    if issues:
        display_name = arguments.get(common.SPREADSHEET_FILE, None)
        worksheet_name = arguments.get(common.WORKSHEET_SELECTED, None)
        title_string = display_name
        suffix = 'validation_errors'
        if worksheet_name:
            title_string = display_name + ' [worksheet ' + worksheet_name + ']'
            suffix = '_worksheet_' + worksheet_name + '_' + suffix
        issue_str = get_printable_issue_string(issues, f"{title_string} HED validation errors")

        file_name = generate_filename(display_name, suffix=suffix, extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='Spreadsheet had validation errors')
    else:
        return generate_text_response("", msg='Spreadsheet had no validation errors')
