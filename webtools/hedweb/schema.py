from os.path import basename
from urllib.parse import urlparse
from flask import current_app

from hed.schema import schema_compliance
from hed.util.file_util import get_file_extension
from hed.util.error_reporter import get_printable_issue_string
from hed.util.exceptions import HedFileError

from hedweb.web_utils import form_has_file, form_has_option, form_has_url, \
    generate_response_download_file_from_text, get_hed_schema, \
    generate_filename, generate_text_response, save_file_to_upload_folder
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
        arguments[common.SCHEMA_URL] = schema_url
        url_parsed = urlparse(schema_url)
        arguments[common.SCHEMA_DISPLAY_NAME] = basename(url_parsed.path)
    if form_has_option(request, common.COMMAND_OPTION, common.COMMAND_CONVERT):
        arguments[common.COMMAND] = common.COMMAND_CONVERT
    elif form_has_option(request, common.COMMAND_OPTION, common.COMMAND_VALIDATE):
        arguments[common.COMMAND] = common.COMMAND_VALIDATE
    arguments[common.CHECK_FOR_WARNINGS] = form_has_option(request, common.CHECK_FOR_WARNINGS, 'on')
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

    if common.COMMAND not in arguments:
        raise HedFileError('MissingCommand', 'Command is missing', '')
    elif arguments[common.COMMAND] == common.COMMAND_VALIDATE:
        results = schema_validate(arguments)
    elif arguments[common.COMMAND] == common.COMMAND_CONVERT:
        results = schema_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a schema processing method", "")
    msg = results.get('msg', '')
    msg_category = results.get('msg_category', 'success')

    if results['data']:
        return generate_response_download_file_from_text(results['data'],
                                                         display_name=results.get('output_display_name', ''),
                                                         msg_category=msg_category, msg=msg)
    else:
        return generate_text_response("", msg=msg, msg_category=msg_category)


def schema_convert(arguments):
    """Run conversion(wiki2xml or xml2wiki from converter)

    returns: Response or string.
        Non empty string is an error
        Response is a download success.
    """
    hed_schema = get_hed_schema(arguments)
    display_name = arguments.get(common.SCHEMA_DISPLAY_NAME)
    schema_version = hed_schema.header_attributes.get('version', 'Unknown')
    issues = hed_schema.issues
    if issues:
        issue_str = get_printable_issue_string(issues, f"Schema syntax errors for {display_name}")
        file_name = generate_filename(display_name, suffix='schema_errors', extension='.txt')
        return {'command': arguments.get('command', ''), 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': "Schema had syntax errors"}
    if common.SCHEMA_FORMAT in arguments:
        schema_format = common.SCHEMA_FORMAT
    else:
        schema_format = get_file_extension(display_name)
    if schema_format == file_constants.SCHEMA_XML_EXTENSION:
        data = hed_schema.get_as_mediawiki_string()
        extension = '.mediawiki'
    else:
        data = hed_schema.get_as_xml_string()
        extension = '.xml'
    file_name = generate_filename(display_name,  extension=extension)

    return {'command': arguments.get('command', ''), 'data': data, 'output_display_name': file_name,
            'schema_version': schema_version, 'msg_category': 'success',
            'msg': 'Schema was successfully converted'}


def schema_validate(arguments):
    """Run tag comparison(map_schema from converter)

    returns: Response or string.
        Empty string is success, but nothing to download.
        Non empty string is an error
        Response is a download success.
    """
    hed_schema = get_hed_schema(arguments)
    display_name = arguments.get(common.SCHEMA_DISPLAY_NAME)
    schema_version = hed_schema.header_attributes.get('version', 'Unknown')
    issues = schema_compliance.check_compliance(hed_schema)
    if issues:
        issue_str = get_printable_issue_string(issues, f"Schema HED 3G compliance errors for {display_name}")
        file_name = generate_filename(display_name, suffix='schema_3G_compliance_errors', extension='.txt')
        return {'command': arguments.get('command', ''), 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'Schema is not HED 3G compliant'}
    else:
        return {'command': arguments.get('command', ''), 'data': '', 'output_display_name': display_name,
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'Schema had no HED-3G validation errors'}
