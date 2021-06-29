import os
import pathlib
from urllib.parse import urlparse
from flask import current_app, Response
from werkzeug.utils import secure_filename

from hed import schema as hedschema
from hed.errors.exceptions import HedFileError
from hedweb.constants import common, file_constants
from hedweb.utils.io_utils import delete_file_no_exceptions, file_extension_is_valid, save_file_to_upload_folder

app_config = current_app.config


def form_has_file(request, file_field, valid_extensions):
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
    """Checks if the given option has a specific value. This is used for radio buttons.

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

    if option_name in request.values and request.values[option_name] == target_value:
        return True
    return False


def form_has_url(request, url_field, valid_extensions):
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
    parsed_url = urlparse(request.form.get(url_field))
    return file_extension_is_valid(parsed_url.path, valid_extensions)


def generate_response_download_file_from_text(download_text, display_name=None,
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
        raise HedFileError('EmptyDownloadText', f"No download text given", "")

    def generate():
        if header:
            yield header
        for issue in download_text.splitlines(True):
            yield issue

    return Response(generate(), mimetype='text/plain charset=utf-8',
                    headers={'Content-Disposition': f"attachment filename={display_name}",
                             'Category': msg_category, 'Message': msg})


def generate_download_file_response(download_file, display_name=None, header=None, category='success', msg=''):
    """Generates a download other response.

    Parameters
    ----------
    download_file: str
        Local path of the file to be downloaded into the response.
    display_name: str
        Name to be assigned to the file in the response
    header: str
        Optional header -- header for download file blob
    category: str
        Category of the message to be displayed ('Success', 'Error', 'Warning')
    msg: str
        Optional message to be displayed in the submit-flash-field

    Returns
    -------
    response object
        A response object containing the downloaded file.

    """
    if not display_name:
        display_name = download_file

    if not download_file:
        raise HedFileError('FileInvalid', f"No download file given", "")

    if not pathlib.Path(download_file).is_file():
        raise HedFileError('FileDoesNotExist', f"File {download_file} not found", "")

    def generate():
        with open(download_file, 'r', encoding='utf-8') as download:
            if header:
                yield header
            for line in download:
                yield line
            delete_file_no_exceptions(download_file)

    return Response(generate(), mimetype='text/plain charset=utf-8',
                    headers={'Content-Disposition': f"attachment filename={display_name}",
                             'Category': category, 'Message': msg})


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


def get_hed_path_from_pull_down(request):
    """Gets the hed path from a section of form that uses a pull-down box and hed_cache
    Parameters
    ----------
    request: Request object
        A Request object containing user data from a form.

    Returns
    -------
    tuple: str, str
        The HED XML local path and the HED display file name
    """
    if common.SCHEMA_VERSION not in request.form:
        hed_file_path = ''
        schema_display_name = ''
    elif request.form[common.SCHEMA_VERSION] != common.OTHER_VERSION_OPTION:
        hed_file_path = hedschema.get_path_from_hed_version(request.form[common.SCHEMA_VERSION])
        schema_display_name = os.path.basename(hed_file_path)
    elif request.form[common.SCHEMA_VERSION] == common.OTHER_VERSION_OPTION and common.SCHEMA_PATH in request.files:
        hed_file_path = save_file_to_upload_folder(request.files[common.SCHEMA_PATH])
        schema_display_name = request.files[common.SCHEMA_PATH].filename
    else:
        hed_file_path = ''
        schema_display_name = ''
    return hed_file_path, schema_display_name


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

    if common.SCHEMA_VERSION not in request.form:
        raise HedFileError("NoSchemaError", "Must provide a valid schema or schema version", "")
    elif request.form[common.SCHEMA_VERSION] != common.OTHER_VERSION_OPTION:
        hed_file_path = hedschema.get_path_from_hed_version(request.form[common.SCHEMA_VERSION])
        hed_schema = hedschema.load_schema(hed_file_path=hed_file_path)
    elif request.form[common.SCHEMA_VERSION] == common.OTHER_VERSION_OPTION and common.SCHEMA_PATH in request.files:
        f = request.files[common.SCHEMA_PATH]
        hed_schema = hedschema.from_string(f.read(file_constants.BYTE_LIMIT).decode('ascii'),
                                           file_type=secure_filename(f.filename))
    else:
        raise HedFileError("NoSchemaFile", "Must provide a valid schema for upload if other chosen", "")
    return hed_schema


def get_uploaded_file_path_from_form(request, file_key, valid_extensions=None):
    """Gets the other paths of the uploaded files in the form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from a form.
    file_key: str
        key name in the files dictionary of the Request object
    valid_extensions: list of str
        List of valid extensions

    Returns
    -------
    tuple
        A tuple containing the other paths. The two other paths are for the spreadsheet and a optional HED XML other.
    """
    uploaded_file_name = ''
    original_file_name = ''
    if form_has_file(request, file_key, valid_extensions):
        uploaded_file_name = save_file_to_upload_folder(request.files[file_key])
        original_file_name = request.files[file_key].filename
        request.files[file_key].close()
    return uploaded_file_name, original_file_name


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
    current_app.logger.error(error_message)
    return generate_text_response('', msg_category='error', msg=error_message)


def package_results(results):
    msg = results.get('msg', '')
    msg_category = results.get('msg_category', 'success')

    if results['data']:
        display_name = results.get('output_display_name', '')
        return generate_response_download_file_from_text(results['data'], display_name=display_name,
                                                         msg_category=msg_category, msg=msg)
    else:
        return generate_text_response("", msg=msg, msg_category=msg_category)
