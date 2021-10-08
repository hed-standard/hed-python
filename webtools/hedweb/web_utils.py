import io
import json
import os
from urllib.parse import urlparse
from flask import current_app, Response, make_response
from werkzeug.utils import secure_filename

from hed import schema as hedschema
from hed.errors.exceptions import HedFileError
from hedweb.constants import base_constants, file_constants

app_config = current_app.config


def file_extension_is_valid(filename, accepted_file_extensions=None):
    """Checks the other extension against a list of accepted ones.
    Parameters
    ----------
    filename: string
        The name of the other.
    accepted_file_extensions: list
        A list containing all of the accepted other extensions.
    Returns
    -------
    boolean
        True if the other has a valid other extension.
    """
    return not accepted_file_extensions or os.path.splitext(filename.lower())[1] in accepted_file_extensions


def form_has_file(request, file_field, valid_extensions=None):
    """Checks to see if a file name with valid extension is present in the request object.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the schema form.
    file_field: str
        Name of the form field containing the file name
    valid_extensions: list of str
        List of valid extensions

    Returns
    -------
    boolean
        True if a file is present in a request object.

    """

    if file_field in request.files and file_extension_is_valid(request.files[file_field].filename, valid_extensions):
        return True
    else:
        return False


def form_has_option(request, option_name, target_value):
    """Checks if the given option has a specific value. This is used for radio buttons and check boxes.

    Parameters
    ----------
    request: Request
        A Request object produced by the post of a form
    option_name: str
        String containing the name of the radio button group in the hedweb form
    target_value: str
        String containing the name of the selected radio button option

    Returns
    -------
    Bool
        True if the target radio button has been set and false otherwise
    """

    if option_name in request.form and request.form[option_name] == target_value:
        return True
    return False


def form_has_url(request, url_field, valid_extensions=None):
    """Checks to see if the url_field has a value with a valid extension.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from a form.
    url_field: str
        The name of the value field in the form containing the URL to be parsed.
    valid_extensions: list of str
        List of valid extensions

    Returns
    -------
    boolean
        True if a URL is present in request object.

    """
    if url_field not in request.form:
        return False
    parsed_url = urlparse(request.form.get(url_field))
    return file_extension_is_valid(parsed_url.path, valid_extensions)


def generate_download_file_from_text(download_text, display_name=None,
                                     header=None, msg_category='success', msg=''):
    """Generates a download other response.

    Parameters
    ----------
    download_text: str
        Text with newlines for iterating.
    display_name: str
        Name to be assigned to the file in the response
    header: str
        Optional header -- header for download file blob
    msg_category: str
        Category of the message to be displayed ('Success', 'Error', 'Warning')
    msg: str
        Optional message to be displayed in the submit-flash-field

    Returns
    -------
    response object
        A response object containing the downloaded file.

    """
    if not display_name:
        display_name = 'download.txt'

    if not download_text:
        raise HedFileError('EmptyDownloadText', "No download text given", "")

    def generate():
        if header:
            yield header
        for issue in download_text.splitlines(True):
            yield issue

    return Response(generate(), mimetype='text/plain charset=utf-8',
                    headers={'Content-Disposition': f"attachment filename={display_name}",
                             'Category': msg_category, 'Message': msg})


def generate_download_spreadsheet(results,  msg_category='success', msg=''):
    # return generate_download_test()
    spreadsheet = results[base_constants.SPREADSHEET]
    display_name = results[base_constants.OUTPUT_DISPLAY_NAME]

    if not spreadsheet.loaded_workbook:
        return generate_download_file_from_text(spreadsheet.to_csv(), display_name=display_name,
                                                msg_category=msg_category, msg=msg)
    buffer = io.BytesIO()
    spreadsheet.to_excel(buffer)
    buffer.seek(0)
    response = make_response()
    response.data = buffer.read()
    response.headers['Content-Disposition'] = 'attachment; filename=' + display_name
    response.headers['Category'] = msg_category
    response.headers['Message'] = msg
    response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response


def generate_filename(base_name, prefix=None, suffix=None, extension=None):
    """Generates a filename for the attachment of the form prefix_basename_suffix + extension.

    Parameters
    ----------
   base_name: str
        The name of the base, usually the name of the file that the issues were generated from
    prefix: str
        The prefix prepended to the front of the base_name
    suffix: str
        The suffix appended to the end of the base_name
    Returns
    -------
    string
        The name of the attachment other containing the issues.
    """

    pieces = []
    if prefix:
        pieces = pieces + [secure_filename(prefix)]
    if base_name:
        pieces.append(os.path.splitext(secure_filename(base_name))[0])
    if suffix:
        pieces = pieces + [secure_filename(suffix)]

    if not pieces:
        return ''
    filename = pieces[0]
    for name in pieces[1:]:
        filename = filename + '_' + name
    # if not extension and base_name:
    #     extension = os.path.splitext(secure_filename(base_name))[1]
    # else:
    #     extension = ''
    # filename = filename + '.' + secure_filename(extension)
    if extension:
        filename = filename + '.' + secure_filename(extension)
    return filename


def generate_text_response(download_text, msg_category='success', msg=''):
    """Generates a download other response.

    Parameters
    ----------
    download_text: str
        Text to be downloaded as part of the response.
    msg_category: str
        Category of the message to be displayed ('Success', 'Error', 'Warning')
    msg: str
        Optional message to be displayed in the submit-flash-field

    Returns
    -------
    response object
        A response object containing the downloaded file.

    """
    headers = {'Category': msg_category, 'Message': msg}
    if len(download_text) > 0:
        headers['Content-Length'] = len(download_text)
    return Response(download_text, mimetype='text/plain charset=utf-8', headers=headers)


def get_hed_schema_from_pull_down(request):
    """Creates a HedSchema object from a section of form that uses a pull-down box and hed_cache
    Parameters
    ----------
    request: Request object
        A Request object containing user data from a form.

    Returns
    -------
    tuple: str
        A HedSchema object
    """

    if base_constants.SCHEMA_VERSION not in request.form:
        raise HedFileError("NoSchemaError", "Must provide a valid schema or schema version", "")
    elif request.form[base_constants.SCHEMA_VERSION] != base_constants.OTHER_VERSION_OPTION:
        hed_file_path = hedschema.get_path_from_hed_version(request.form[base_constants.SCHEMA_VERSION])
        hed_schema = hedschema.load_schema(hed_file_path=hed_file_path)
    elif request.form[base_constants.SCHEMA_VERSION] == \
            base_constants.OTHER_VERSION_OPTION and base_constants.SCHEMA_PATH in request.files:
        f = request.files[base_constants.SCHEMA_PATH]
        hed_schema = hedschema.from_string(f.read(file_constants.BYTE_LIMIT).decode('ascii'),
                                           file_type=secure_filename(f.filename))
    else:
        raise HedFileError("NoSchemaFile", "Must provide a valid schema for upload if other chosen", "")
    return hed_schema


def handle_error(ex, hed_info=None, title=None, return_as_str=True):
    """Handles an error by returning a dictionary or simple string

    Parameters
    ----------
    ex: Exception
        The exception raised.
    hed_info: dict
        A dictionary of information.
    title: str
        A title to be included with the message.
    return_as_str: bool
        If true return as string otherwise as dictionary
    Returns
    -------
    str or dict

    """

    if not hed_info:
        hed_info = {}
    if hasattr(ex, 'error_type'):
        error_code = ex.error_type
    else:
        error_code = type(ex).__name__

    if not title:
        title = ''
    if hasattr(ex, 'message'):
        message = ex.message
    else:
        message = str(ex)

    hed_info['message'] = f"{title}[{error_code}: {message}]"
    if return_as_str:
        return json.dumps(hed_info)
    else:
        return hed_info


def handle_http_error(ex):
    """Handles an http error.

    Parameters
    ----------
    ex: Exception
        A class that extends python Exception class
    Returns
    -------
    Response
        A response object indicating the field_type of error


    """
    if hasattr(ex, 'error_type'):
        error_code = ex.error_type
    else:
        error_code = type(ex).__name__
    if hasattr(ex, 'message'):
        message = ex.message
    else:
        message = str(ex)
    error_message = f"{error_code}: [{message}]"
    return generate_text_response('', msg_category='error', msg=error_message)


def package_results(results):
    msg = results.get('msg', '')
    msg_category = results.get('msg_category', 'success')
    display_name = results.get('output_display_name', '')
    if results['data']:
        return generate_download_file_from_text(results['data'], display_name=display_name,
                                                msg_category=msg_category, msg=msg)
    elif not results.get('spreadsheet', None):
        return generate_text_response("", msg=msg, msg_category=msg_category)
    else:
        return generate_download_spreadsheet(results, msg_category=msg_category, msg=msg)
