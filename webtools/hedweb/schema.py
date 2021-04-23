from os.path import basename, splitext
from urllib.parse import urlparse
from flask import current_app

from hed.schema.hed_schema_file import load_schema, convert_schema_to_format
from hed.util.file_util import url_to_file, get_file_extension
from hed.util.error_reporter import get_printable_issue_string
from hed.util.exceptions import HedFileError

from hedweb.web_utils import form_has_file, form_has_option, form_has_url, \
    generate_download_file_response, generate_filename, generate_text_response, \
    save_file_to_upload_folder, save_text_to_upload_folder

from hedweb.constants import common, file_constants

app_config = current_app.config


def generate_input_from_schema_form(request):
    """Gets the conversion function input arguments from a request object associated with the conversion form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying schema functions.
    """
    arguments = {}
   
    if form_has_option(request, common.SCHEMA_UPLOAD_OPTIONS,
                       common.SCHEMA_FILE_OPTION) and \
            form_has_file(request, common.SCHEMA_FILE, file_constants.SCHEMA_EXTENSIONS):
        schema_file = request.files[common.SCHEMA_FILE]
        arguments[common.SCHEMA_PATH] = save_file_to_upload_folder(schema_file)
        arguments[common.SCHEMA_DISPLAY_NAME] = schema_file.filename
    elif form_has_option(request, common.SCHEMA_UPLOAD_OPTIONS,
                         common.SCHEMA_URL_OPTION) and \
            form_has_url(request, common.SCHEMA_URL, file_constants.SCHEMA_EXTENSIONS):
        schema_url = request.values[common.SCHEMA_URL]
        arguments[common.SCHEMA_PATH] = url_to_file(schema_url)
        url_parsed = urlparse(schema_url)
        arguments[common.SCHEMA_DISPLAY_NAME] = basename(url_parsed.path)
    if form_has_option(request, common.SCHEMA_OPTION, common.SCHEMA_OPTION_CHECK):
        arguments[common.SCHEMA_OPTION_CHECK] = True
    elif form_has_option(request, common.SCHEMA_OPTION, common.SCHEMA_OPTION_CONVERT):
        arguments[common.SCHEMA_OPTION_CONVERT] = True
    return arguments


def schema_process(arguments):
    """Perform the requested action for the dictionary.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the dictionary form

    Returns
    -------
      Response
        Downloadable response object.
    """

    if not arguments[common.SCHEMA_PATH]:
        raise HedFileError('EmptySCHEMAFile', "Please give a schema to process", "")
    if arguments.get(common.SCHEMA_OPTION_CHECK, None):
        return schema_check(arguments)
    elif arguments.get(common.SCHEMA_OPTION_CONVERT, None):
        return schema_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a schema processing method", "")


def schema_check(arguments):
    """Run tag comparison(map_schema from converter)

    returns: Response or string.
        Empty string is success, but nothing to download.
        Non empty string is an error
        Response is a download success.
    """

    hed_file_path = arguments.get(common.SCHEMA_PATH, '')
    this_schema = load_schema(hed_file_path)
    issues = this_schema.check_compliance()
    if issues:
        display_name = arguments.get(common.SCHEMA_DISPLAY_NAME)
        issue_str = get_printable_issue_string(issues, f"Schema HED 3G compliance errors for {display_name}")
        file_name = generate_filename(display_name, suffix='schema_3G_compliance_errors', extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='Schema is not HED 3G compliant')
    else:
        return generate_text_response("", msg='Schema had no HED-3G validation errors')


def schema_convert(arguments):
    """Run conversion(wiki2xml or xml2wiki from converter)

    returns: Response or string.
        Non empty string is an error
        Response is a download success.
    """
    schema_file_path = arguments.get(common.SCHEMA_PATH)
    display_name = arguments.get(common.SCHEMA_DISPLAY_NAME)
    input_extension = get_file_extension(schema_file_path)
    save_wiki = input_extension == file_constants.SCHEMA_XML_EXTENSION
    schema_file, issues = convert_schema_to_format(local_hed_file=schema_file_path, check_for_issues=False,
                                                   display_filename=display_name, save_as_mediawiki=save_wiki)
    if issues:
        issue_str = get_printable_issue_string(issues, f"Schema conversion errors for {display_name}")
        file_name = generate_filename(display_name, suffix='conversion_errors', extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='Schema had validation errors and could not be converted')
    else:
        schema_name, schema_ext = splitext(schema_file)
        file_name = generate_filename(display_name,  extension=schema_ext)
        return generate_download_file_response(schema_file, display_name=file_name, category='success',
                                               msg='Schema was successfully converted')
