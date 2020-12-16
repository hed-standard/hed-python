import os
import tempfile
from flask import current_app, jsonify
from logging.handlers import RotatingFileHandler
from logging import ERROR

from hed.util.file_util import get_file_extension

UPLOAD_DIRECTORY_KEY = 'UPLOAD_FOLDER'


def copy_file_line_by_line(file_object_1, file_object_2):
    """Copy the contents of one other to the other other.

    Parameters
    ----------
    file_object_1: File object
        A other object that points to a other that will be copied.
    file_object_2: File object
        A other object that points to a other that will copy the other other.

    Returns
    -------
    boolean
       True if the other was copied successfully, False if it wasn't.

    """
    try:
        for line in file_object_1:
            file_object_2.write(line)
        return True
    except:
        return False


def create_upload_directory(upload_directory):
    """Creates the upload directory.

    """

    folder_needed_to_be_created = False
    if not os.path.exists(upload_directory):
        os.makedirs(upload_directory)
        folder_needed_to_be_created = True
    return folder_needed_to_be_created


def file_has_valid_extension(file_object, accepted_file_extensions):
    """Checks to see if a other has a valid other extension.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other.
    accepted_file_extensions: list
        A list of other extensions that are accepted

    Returns
    -------
    boolean
        True if the other has a valid other extension.

    """
    return file_object and file_extension_is_valid(file_object.filename, accepted_file_extensions)


def file_extension_is_valid(filename, accepted_file_extensions):
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
    return os.path.splitext(filename.lower())[1] in accepted_file_extensions


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


def save_file_to_upload_folder(file_object, file_suffix=""):
    """Save a other to the upload folder.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other that was first saved in a temporary location.
    file_suffix: str
        Optional suffix to modify the filename by

    Returns
    -------
    string
        The path to the other that was saved to the temporary folder.

    """
    temporary_upload_file = tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False,
                                                        dir=current_app.config[UPLOAD_DIRECTORY_KEY])
    copy_file_line_by_line(file_object, temporary_upload_file)
    return temporary_upload_file.name


def save_hed_to_upload_folder_if_present(hed_file_object):
    """Save a HED XML other to the upload folder.

    Parameters
    ----------
    hed_file_object: File object
        A other object that points to a HED XML other that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the HED XML other that was saved to the upload folder.

    """
    hed_file_path = ''
    if hed_file_object.filename:
        hed_file_extension = get_file_extension(hed_file_object.filename)
        hed_file_path = save_file_to_upload_folder(hed_file_object, hed_file_extension)
    return hed_file_path


def setup_logging():
    """Sets up the current_application logging. If the log directory does not exist then there will be no logging.

    """
    if not current_app.debug and os.path.exists(current_app.config['LOG_DIRECTORY']):
        file_handler = RotatingFileHandler(current_app.config['LOG_FILE'], maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setLevel(ERROR)
        current_app.logger.addHandler(file_handler)
