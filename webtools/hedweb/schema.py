from os.path import basename
from urllib.parse import urlparse
from flask import current_app
from werkzeug.utils import secure_filename

from hed import schema as hedschema
from hed.util.file_util import get_file_extension
from hed.errors.error_reporter import get_exception_issue_string,get_printable_issue_string
from hed.errors.exceptions import HedFileError

from hedweb.web_utils import form_has_file, form_has_option, form_has_url, generate_filename, handle_error
from hedweb.constants import base_constants, file_constants

app_config = current_app.config


def get_schema(schema_path=None, schema_url=None, schema_string=None, schema_version=None, file_type=".xml"):
    hed_schema = []
    issue_str = ''
    try:
        if schema_path:
            hed_schema = hedschema.load_schema(hed_file_path=schema_path)
        elif schema_url:
            hed_schema = hedschema.load_schema(hed_url_path=schema_url)
        elif schema_string:
            hed_schema = hedschema.from_string(schema_string, file_type=file_type)
        else:
            raise HedFileError("HedSchemaNotFound", "A HED schema could not be located", "")
    except HedFileError as ex:
        issue_str = get_exception_issue_string(ex.issues,
                                               title=f"[{ex.error_type}] schema parsing issues:")
    except Exception as ex:
        issue_str = handle_error(ex, return_as_str=True)
    finally:
        return hed_schema, issue_str


def get_input_from_form(request):
    """Gets the input for schema processing from the schema form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the schema form

    Returns
    -------
    dict
        A dictionary containing input arguments for calling the underlying schema functions.
    """

    if form_has_option(request, base_constants.SCHEMA_UPLOAD_OPTIONS, base_constants.SCHEMA_FILE_OPTION) and \
            form_has_file(request, base_constants.SCHEMA_FILE, file_constants.SCHEMA_EXTENSIONS):
        f = request.files[base_constants.SCHEMA_FILE]
        schema, issue_str = get_schema(schema_string=f.read(file_constants.BYTE_LIMIT).decode('ascii'),
                                         file_type=secure_filename(f.filename))
        display_name = secure_filename(f.filename)
    elif form_has_option(request, base_constants.SCHEMA_UPLOAD_OPTIONS, base_constants.SCHEMA_URL_OPTION) and \
            form_has_url(request, base_constants.SCHEMA_URL, file_constants.SCHEMA_EXTENSIONS):
        schema_url = request.values[base_constants.SCHEMA_URL]
        schema, issue_str = get_schema(schema_url=schema_url)
        url_parsed = urlparse(schema_url)
        display_name = basename(url_parsed.path)
    else:
        raise HedFileError("NoSchemaProvided", "Must provide a loadable schema", "")

    arguments = {base_constants.SCHEMA: schema,
                 base_constants.SCHEMA_DISPLAY_NAME: display_name,
                 base_constants.COMMAND: request.form.get(base_constants.COMMAND_OPTION, ''),
                 base_constants.CHECK_FOR_WARNINGS:
                     form_has_option(request, base_constants.CHECK_FOR_WARNINGS, 'on'),
                 base_constants.ISSUE_STRING: issue_str
                 }
    return arguments


def process(arguments):
    """Perform the requested action for the schema.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the schema form

    Returns
    -------
      dict
        A dictionary with results in standard format
    """

    hed_schema = arguments.get('schema', None)
    display_name = arguments.get('schema_display_name', 'unknown_source')
    if arguments.get(base_constants.ISSUE_STRING, ''):
        file_name = generate_filename(display_name, suffix='schema_errors', extension='.txt')
        return {'command':  arguments[base_constants.COMMAND],
                'data': arguments[base_constants.ISSUE_STRING],
                'output_display_name': file_name,
                'schema_version': '', 'msg_category': 'warning',
                'msg': "Schema had syntax errors and could not load"}
    if base_constants.COMMAND not in arguments or arguments[base_constants.COMMAND] == '':
        raise HedFileError('MissingCommand', 'Command is missing', '')
    elif arguments[base_constants.COMMAND] == base_constants.COMMAND_VALIDATE:
        results = schema_validate(hed_schema, display_name)
    elif arguments[base_constants.COMMAND] == base_constants.COMMAND_CONVERT:
        results = schema_convert(hed_schema, display_name)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a schema processing method", "")
    return results


def schema_convert(hed_schema, display_name):
    """Return a string representation of hed_schema in the desired format

    Parameters
    ----------
    hed_schema: HedSchema object
        A HedSchema object containing the schema to be processed.
    display_name: str
        The display name associated with this schema object.

    Returns
    -------
    result: dict
        A dictionary in the standard results format containing the results of the operation

    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown')
    schema_format = get_file_extension(display_name)
    if schema_format == file_constants.SCHEMA_XML_EXTENSION:
        data = hed_schema.get_as_mediawiki_string()
        extension = '.mediawiki'
    else:
        data = hed_schema.get_as_xml_string()
        extension = '.xml'
    file_name = generate_filename(display_name,  extension=extension)

    return {'command': base_constants.COMMAND_CONVERT, 'data': data, 'output_display_name': file_name,
            'schema_version': schema_version, 'msg_category': 'success',
            'msg': 'Schema was successfully converted'}


def schema_validate(hed_schema, display_name):
    """Run schema compliance for HED-3G

    Parameters
    ----------
    hed_schema: HedSchema object
        A HedSchema object containing the schema to be processed.
    display_name: str
        The display name associated with this schema object.

    Returns
    -------
    result: dict
        A dictionary in the standard results format containing the results of the operation

    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown')
    issues = hed_schema.check_compliance()
    if issues:
        issue_str = get_printable_issue_string(issues, f"Schema HED 3G compliance errors for {display_name}")
        file_name = generate_filename(display_name, suffix='schema_3G_compliance_errors', extension='.txt')
        return {'command': base_constants.COMMAND_VALIDATE, 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'Schema is not HED 3G compliant'}
    else:
        return {'command': base_constants.COMMAND_VALIDATE, 'data': '', 'output_display_name': display_name,
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'Schema had no HED-3G validation errors'}
