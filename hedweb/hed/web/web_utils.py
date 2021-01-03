import os
import pathlib
import tempfile
import traceback

from flask import current_app, jsonify, Response
from logging.handlers import RotatingFileHandler
from logging import ERROR

from hed.util import hed_cache
from hed.util.file_util import get_file_extension, delete_file_if_it_exist
from hed.util.hed_dictionary import HedDictionary
from hed.web.constants import common_constants, error_constants

app_config = current_app.config


def check_if_option_in_form(form_request_object, option_name, target_value):
    """Checks if the given option has a specific value. This is used for radio buttons.

    Parameters
    ----------
    form_request_object: Request
        A Request object produced by the post of a form
    option_name: str
        String containing the name of the radio button group in the web form
    target_value: str
        String containing the name of the selected radio button option

    Returns
    -------
    Bool
        True if the target radio button has been set and false otherwise
    """

    if option_name in form_request_object.values and form_request_object.values[option_name] == target_value:
        return True
    return False


# def copy_file_line_by_line(file_object_1, file_object_2):
#     """Copy the contents of one other to the other other.
#
#     Parameters
#     ----------
#     file_object_1: File object
#         A other object that points to a other that will be copied.
#     file_object_2: File object
#         A other object that points to a other that will copy the other other.
#
#     Returns
#     -------
#     boolean
#        True if the other was copied successfully, False if it wasn't.
#
#     """
#     try:
#         for line in file_object_1:
#             file_object_2.write(line)
#         return True
#     except:
#         return False


def convert_number_str_to_list(number_str):
    """Converts a string of integers to a list of integers, which is useful for web forms.

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


def create_upload_directory(upload_directory):
    """Creates the upload directory.

    """

    folder_needed_to_be_created = False
    if not os.path.exists(upload_directory):
        os.makedirs(upload_directory)
        folder_needed_to_be_created = True
    return folder_needed_to_be_created


def file_extension_is_valid(filename, accepted_file_extensions=None):
    """Checks the other extension against a list of accepted ones.

    Parameters
    ----------
    filename: string
        The name of the other.

    accepted_file_extensions: list
        A list containing all of the accepted other extensions or an empty list of all are acceted

    Returns
    -------
    boolean
        True if the other has a valid other extension.

    """
    if not accepted_file_extensions or os.path.splitext(filename.lower())[1] in accepted_file_extensions:
        return True
    else:
        return False


def find_all_str_indices_in_list(list_of_strs, str_value):
    """Find the indices of a string value in a list.

    Parameters
    ----------
    list_of_strs: list
        A list containing strings.
    str_value: string
        A string value.

    Returns
    -------
    list
        A list containing all of the indices where a string value occurs in a string list.

    """
    return [index + 1 for index, value in enumerate(list_of_strs) if
            value.lower().replace(' ', '') == str_value.lower().replace(' ', '')]


def find_hed_version_in_uploaded_file(form_request_object, key_name=common_constants.HED_XML_FILE):
    """Finds the version number in an HED XML other.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data
    key_name: str
        Name of the key for the HED XML file in the form_request_object

    Returns
    -------
    string
        A serialized JSON string containing the version number information.

    """
    hed_info = {}
    try:
        if key_name in form_request_object.files:
            hed_file_path = save_file_to_upload_folder(form_request_object.files[key_name])
            hed_info[common_constants.HED_VERSION] = HedDictionary.get_hed_xml_version(hed_file_path)
    except:
        hed_info[error_constants.ERROR_KEY] = traceback.format_exc()
    return hed_info


def find_major_hed_versions():
    """Finds the major HED versions that are kept on the server.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information about the major HED versions.

    """
    hed_info = {}
    try:
        hed_cache.cache_all_hed_xml_versions()
        hed_info[common_constants.HED_MAJOR_VERSIONS] = hed_cache.get_all_hed_versions()
    except:
        hed_info[error_constants.ERROR_KEY] = traceback.format_exc()
    return hed_info


def generate_download_file_response(download_file, display_name=None, header=None):
    """Generates a download other response.

    Parameters
    ----------
    download_file: str
        Local path of the file to be downloaded into the response.
    display_name: str
        Name to be assigned to the file in the response
    header: str
        Optional header -- usually given for error message downloads

    Returns
    -------
    response object
        A response object containing the downloaded file.

    """
    if not display_name:
        display_name = download_file
    try:
        #full_filename = os.path.join(app_config.get('UPLOAD_FOLDER'), download_file_name)
        if not download_file:
            return f"No download file given"

        print(download_file)
        if not pathlib.Path(download_file).is_file():
            print("help", download_file)
            return f"File {download_file} not found"

        def generate():
            with open(download_file, 'r', encoding='utf-8') as download:
                if header:
                    yield header
                for line in download:
                    yield line
            delete_file_if_it_exist(download_file)
        return Response(generate(), mimetype='text/plain charset=utf-8',
                        headers={'Content-Disposition': f"attachment filename={display_name}"})
    except:
        return traceback.format_exc()


# def get_file_from_form(form_request_object, file_key):
#     """Checks to see if a spreadsheet other is present in a request object from validation form.
#
#     Parameters
#     ----------
#     form_request_object: Request object
#         A Request object containing user data from a form.
#     file_key: str
#         String with the key in the form_request_object.files dictionary
#
#     Returns
#     -------
#     file_object or None
#         Returns None if there isn't one.
#
#     """
#     return form_request_object.files.get(file_key, None)


def get_original_filename(form_request_object, file_key, valid_extensions = None):
    """Gets the original name of the file if it has a valid extension.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from a posted form.
    file_key: str
        Key string in the files dictionary of the form_request_object
    valid_extensions: list of str
        List containing the valid extensions

    Returns
    -------
    string
        The name of the uploaded file.
    """
    if file_key in form_request_object.files and \
            file_extension_is_valid(form_request_object.files[file_key].filename, valid_extensions):
        return form_request_object.files[file_key].filename
    return ''


def get_hed_path_from_form(form_request_object, hed_file_path):
    """Gets the hed path from a section of form that uses a pull-down box and hed_cache
    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from a form.
    hed_file_path: string
        The path to the HED XML other.

    Returns
    -------
    string
        The HED XML other path.
    """
    if common_constants.HED_VERSION in form_request_object.form and \
        (form_request_object.form[common_constants.HED_VERSION] != common_constants.HED_OTHER_VERSION_OPTION
         or not hed_file_path):
        return hed_cache.get_path_from_hed_version(form_request_object.form[common_constants.HED_VERSION])
    return hed_file_path


def handle_http_error(error_code, error_message, as_text=False):
    """Handles an http error.

    Parameters
    ----------
    error_code: string
        The code associated with the error.
    error_message: string
        The message associated with the error.
    as_text: Bool
        If we should encode this as text or json.
    Returns
    -------
    boolean
        A tuple containing a HTTP response object and a code.

    """
    current_app.logger.error(error_message)
    if as_text:
        return error_message, error_code
    return jsonify(message=error_message), error_code


def save_file_to_upload_folder(file_object):
    """Save a other to the upload folder.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the other that was saved to the temporary folder.

    """
    file_path = ''
    try:
        if file_object.filename:
            file_extension = get_file_extension(file_object.filename)
            temporary_upload_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False,
                                                                dir=current_app.config['UPLOAD_FOLDER'])
            for line in file_object:
                temporary_upload_file.write(line)
            file_path = temporary_upload_file.name
    except:
        file_path = ''
    return file_path


def setup_logging():
    """Sets up the current_application logging. If the log directory does not exist then there will be no logging.

    """
    if not current_app.debug and os.path.exists(current_app.config['LOG_DIRECTORY']):
        file_handler = RotatingFileHandler(current_app.config['LOG_FILE'], maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setLevel(ERROR)
        current_app.logger.addHandler(file_handler)


