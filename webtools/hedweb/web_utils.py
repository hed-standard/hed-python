import os
import json
import pathlib
import tempfile
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask import current_app, Response

from hed import schema as hedschema
from hed import models
from hed.util.exceptions import HedFileError
from hed.util.file_util import get_file_extension, delete_file_if_it_exists
from hedweb.constants import common

app_config = current_app.config


def convert_number_str_to_list(number_str):
    """Converts a string of integers to a list of integers, which is useful for hedweb forms.

    Parameters
    ----------
    number_str: str
        A string containing integers.

    Returns
    -------
    list
        A list containing numbers.
    """
    if number_str:
        return list(map(int, number_str.split(',')))
    return []


def delete_file_no_exceptions(file_path):
    try:
        return delete_file_if_it_exists(file_path)
    except:
        return False


def file_extension_is_valid(filename, accepted_file_extensions=None):
    """Checks the other extension against a list of accepted ones.

    Parameters
    ----------
    filename: string
        The name of the other.

    accepted_file_extensions: list
        A list containing all of the accepted other extensions or an empty list of all are accepted

    Returns
    -------
    boolean
        True if the other has a valid other extension.

    """
    if not accepted_file_extensions or os.path.splitext(filename.lower())[1] in accepted_file_extensions:
        return True
    else:
        return False


def find_all_str_indices_in_list(list_of_str, str_value):
    """Find the indices of a string value in a list.

    Parameters
    ----------
    list_of_str: list
        A list containing strings.
    str_value: string
        A string value.

    Returns
    -------
    list
        A list containing all of the indices where a string value occurs in a string list.

    """
    return [index + 1 for index, value in enumerate(list_of_str) if
            value.lower().replace(' ', '') == str_value.lower().replace(' ', '')]


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


def get_events(arguments, json_dictionary=None, def_dicts=None):
    if common.EVENTS_STRING in arguments:
        events = models.EventsInput(csv_string=arguments[common.EVENTS_STRING],
                                    json_def_files=json_dictionary, def_dicts=def_dicts)
    elif common.EVENTS_PATH in arguments:
        events = models.EventsInput(filename=arguments[common.EVENTS_PATH],
                                    json_def_files=json_dictionary, def_dicts=def_dicts)
    else:
        raise HedFileError('NoEventsFile', 'No events file was provided', '')
    return events


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


def get_hed_schema(arguments):
    if common.SCHEMA_STRING in arguments:
        schema_format = arguments.get(common.SCHEMA_FORMAT, ".xml")
        hed_schema = hedschema.from_string(schema_string=arguments[common.SCHEMA_STRING], file_type=schema_format)
    elif common.SCHEMA_PATH in arguments:
        hed_schema = hedschema.load_schema(hed_file_path=arguments[common.SCHEMA_PATH])
    elif common.SCHEMA_URL in arguments:
        # hed_file_path = file_util.url_to_file(arguments[common.SCHEMA_URL])
        hed_schema = hedschema.load_schema(hed_url_path=arguments[common.SCHEMA_URL])
    elif common.SCHEMA_VERSION in arguments:
        hed_file_path = hedschema.get_path_from_hed_version(arguments[common.SCHEMA_VERSION])
        hed_schema = hedschema.load_schema(hed_file_path=hed_file_path)
    else:
        raise HedFileError('NoHEDSchema', 'No valid HED schema was provided', '')
    return hed_schema


def get_json_dictionary(arguments, json_optional=False):
    if common.JSON_STRING in arguments:
        json_dictionary = models.ColumnDefGroup(json_string=arguments[common.JSON_STRING])
    elif common.JSON_PATH in arguments:
        json_dictionary = models.ColumnDefGroup(json_filename=arguments[common.JSON_PATH])
    elif json_optional:
        json_dictionary = None
    else:
        raise HedFileError('NoJSONDictionary', 'No JSON dictionary was provided', '')
    return json_dictionary


def get_optional_form_field(request, form_field_name, field_type=''):
    """Gets the specified optional form field if present.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the validation form.
    form_field_name: string
        The name of the optional form field.
    field_type: str
        Name of expected type: 'boolean' or 'string'

    Returns
    -------
    boolean or string
        A boolean or string value based on the form field type.

    """
    form_field_value = ''
    if field_type == common.BOOLEAN:
        form_field_value = False
        if form_field_name in request.form:
            form_field_value = True
    elif field_type == common.STRING:
        if form_field_name in request.form:
            form_field_value = request.form[form_field_name]
    return form_field_value


def get_spreadsheet(arguments):
    if common.SPREADSHEET_STRING in arguments:
        spreadsheet = None
    elif common.SPREADSHEET_PATH in arguments:
        spreadsheet = models.HedInput(arguments.get(common.SPREADSHEET_PATH, None),
                                      worksheet_name=arguments.get(common.WORKSHEET_SELECTED, None),
                                      tag_columns=arguments.get(common.TAG_COLUMNS, None),
                                      has_column_names=arguments.get(common.HAS_COLUMN_NAMES, None),
                                      column_prefix_dictionary=arguments.get(common.COLUMN_PREFIX_DICTIONARY, None))
    else:
        raise HedFileError('NoSpreadsheet', 'No spreadsheet was provided', '')
    return spreadsheet


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


def handle_error(ex, hed_info=None, title=None, return_as_str=True):
    """Handles an error by logging and returning a dictionary or simple string

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


def save_file_to_upload_folder(file_object, delete_on_close=False):
    """Save a file_object to the upload folder.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other that was first saved in a temporary location.
    delete_on_close: bool
        If true will delete after closing

    Returns
    -------
    string
        The path to the other that was saved to the temporary folder.

    """

    if file_object.filename:
        file_extension = get_file_extension(file_object.filename)
        temporary_upload_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=delete_on_close,
                                                            dir=current_app.config['UPLOAD_FOLDER'])
        for line in file_object:
            temporary_upload_file.write(line)
        temporary_upload_file.close()
        return temporary_upload_file.name
    else:
        raise("UnableToUploadFile", "File could not uploaded", "UnknownFile")


def save_file_to_upload_folder_no_exception(file_object, delete_on_close=False):
    """Save a other to the upload folder.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other that was first saved in a temporary location.
    delete_on_close: bool
        If true will delete after closing

    Returns
    -------
    string
        The path to the other that was saved to the temporary folder.

    """
    file_path = ''
    try:
        if file_object.filename:
            file_extension = get_file_extension(file_object.filename)
            temporary_upload_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=delete_on_close,
                                                                dir=current_app.config['UPLOAD_FOLDER'])
            for line in file_object:
                temporary_upload_file.write(line)
            file_path = temporary_upload_file.name
    except:
        file_path = ''
    return file_path


def save_text_to_upload_folder(text, filename):
    """Saves a string in the upload folder as filename.

    Parameters
    ----------
    text: string
        A printable string.
    filename: str
        File name of the issue folder

    Returns
    -------
    string
        The name of the validation output other.

    """

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    with open(file_path, 'w', encoding='utf-8') as text_file:
        text_file.write(text)
    text_file.close()
    return file_path
