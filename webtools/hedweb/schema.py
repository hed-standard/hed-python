from os.path import basename
from urllib.parse import urlparse
from flask import current_app
from werkzeug.utils import secure_filename

from hed import schema as hedschema
from hed.schema import schema_compliance
from hed.util.file_util import get_file_extension
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError

from hedweb.utils.web_utils import form_has_file, form_has_option, form_has_url, package_results
from hedweb.utils.io_utils import generate_filename
from hedweb.constants import common, file_constants

app_config = current_app.config


def get_input_from_schema_form(request):
    """Gets the input for schema processing from the schema form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the schema form

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying schema functions.
    """
   
    if form_has_option(request, common.SCHEMA_UPLOAD_OPTIONS, common.SCHEMA_FILE_OPTION) and \
            form_has_file(request, common.SCHEMA_FILE, file_constants.SCHEMA_EXTENSIONS):
        f = request.files[common.SCHEMA_FILE]
        schema = hedschema.from_string(f.read(file_constants.BYTE_LIMIT).decode('ascii'),
                                       file_type=secure_filename(f.filename))
        display_name = secure_filename(f.filename)
    elif form_has_option(request, common.SCHEMA_UPLOAD_OPTIONS, common.SCHEMA_URL_OPTION) and \
            form_has_url(request, common.SCHEMA_URL, file_constants.SCHEMA_EXTENSIONS):
        schema_url = request.values[common.SCHEMA_URL]
        schema = hedschema.load_schema(hed_url_path=schema_url)
        url_parsed = urlparse(schema_url)
        display_name = basename(url_parsed.path)
    else:
        raise HedFileError("NoSchemaProvided", "Must provide a loadable schema", "")

    arguments = {common.SCHEMA: schema,
                 common.SCHEMA_DISPLAY_NAME: display_name,
                 common.COMMAND: request.values.get(common.COMMAND_OPTION, ''),
                 common.CHECK_FOR_WARNINGS: form_has_option(request, common.CHECK_FOR_WARNINGS, 'on')
                 }
    return arguments


def schema_process(arguments):
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
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    if common.COMMAND not in arguments or arguments[common.COMMAND] == '':
        raise HedFileError('MissingCommand', 'Command is missing', '')
    elif arguments[common.COMMAND] == common.COMMAND_VALIDATE:
        results = schema_validate(hed_schema, display_name)
    elif arguments[common.COMMAND] == common.COMMAND_CONVERT:
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
    issues = hed_schema.issues
    if issues:
        issue_str = get_printable_issue_string(issues, f"Schema syntax errors for {display_name}")
        file_name = generate_filename(display_name, suffix='schema_errors', extension='.txt')
        return {'command': 'command_convert', 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': "Schema had syntax errors"}

    schema_format = get_file_extension(display_name)
    if schema_format == file_constants.SCHEMA_XML_EXTENSION:
        data = hed_schema.get_as_mediawiki_string()
        extension = '.mediawiki'
    else:
        data = hed_schema.get_as_xml_string()
        extension = '.xml'
    file_name = generate_filename(display_name,  extension=extension)

    return {'command': 'command_convert', 'data': data, 'output_display_name': file_name,
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
    issues = schema_compliance.check_compliance(hed_schema)
    if issues:
        issue_str = get_printable_issue_string(issues, f"Schema HED 3G compliance errors for {display_name}")
        file_name = generate_filename(display_name, suffix='schema_3G_compliance_errors', extension='.txt')
        return {'command': 'command_validate', 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'Schema is not HED 3G compliant'}
    else:
        return {'command': 'command_validate', 'data': '', 'output_display_name': display_name,
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'Schema had no HED-3G validation errors'}
