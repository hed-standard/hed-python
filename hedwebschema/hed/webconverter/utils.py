import os

import tempfile
import traceback
import urllib
from flask import jsonify, Response
from werkzeug.utils import secure_filename
from flask import current_app
from logging.handlers import RotatingFileHandler
from logging import ERROR

from hed.webconverter.constants.other import file_extension_constants
from hed.webconverter.constants.error import error_constants
from hed.webconverter.constants.form import conversion_arg_constants, js_form_constants

from hed.schema import xml2wiki, wiki2xml
from hed.schema.utils import SchemaError
from hed.utilities import map_schema
from hed.schema import constants as converter_constants

UPLOAD_DIRECTORY_KEY = 'UPLOAD_FOLDER'

def url_to_file(resource_url):
    """Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters
    ----------
    resource_url: string
        The URL to the resource.

    Returns
    -------
    string: The local temporary filename for downloaded file
    """
    url_request = urllib.request.urlopen(resource_url)
    suffix = _get_file_extension(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)
        return opened_file.name


def _get_uploaded_file_paths_from_forms(form_request_object):
    """Gets the other paths of the uploaded files in the form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    string
        The local file path, if exists.
    """
    hed_file_path = ''
    if hed_present_in_form(form_request_object) and _file_has_valid_extension(
            form_request_object.files[js_form_constants.HED_FILE], file_extension_constants.HED_FILE_EXTENSIONS):
        hed_file_path = _save_hed_to_upload_folder_if_present(
            form_request_object.files[js_form_constants.HED_FILE])
    elif url_present_in_form(form_request_object):
        hed_file_path = url_to_file(form_request_object.values[js_form_constants.HED_URL])
    return hed_file_path



def _run_conversion(hed_file_path):
    """Runs the appropriate xml<>mediawiki converter depending on input filetype.

    returns: A dictionary with converter.constants filled in.
    """
    input_extension = _get_file_extension(hed_file_path)
    if input_extension == file_extension_constants.HED_XML_EXTENSION:
        conversion_function = xml2wiki.convert_hed_xml_2_wiki
    elif input_extension == file_extension_constants.HED_WIKI_EXTENSION:
        conversion_function = wiki2xml.convert_hed_wiki_2_xml
    else:
        raise ValueError(f"Invalid extension type: {input_extension}")

    return conversion_function(None, hed_file_path)

def _run_tag_compare(local_xml_path):
    """Runs tag compare for the given XML file.

    returns: A dictionary with converter.constants filled in.
    """
    input_extension = _get_file_extension(local_xml_path)
    if input_extension != file_extension_constants.HED_XML_EXTENSION:
        raise ValueError(f"Invalid extension type: {input_extension}")

    return map_schema.check_for_duplicate_tags(local_xml_path)


def run_conversion(form_request_object):
    """Run conversion(wiki2xml or xml2wiki from converter)

    returns: Response or string.
        Non empty string is an error
        Response is a download success.
    """
    hed_file_path = ''
    try:
        conversion_input_arguments = _generate_input_arguments_from_conversion_form(form_request_object)
        hed_file_path = conversion_input_arguments[conversion_arg_constants.HED_XML_PATH]
        result_dict = _run_conversion(hed_file_path)
        filename = result_dict[converter_constants.HED_OUTPUT_LOCATION_KEY]
        download_response = generate_download_file_response_and_delete(filename)
        if isinstance(download_response, str):
            return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
        return download_response
    except urllib.error.URLError:
        return error_constants.INVALID_URL_ERROR
    except urllib.error.HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except SchemaError as e:
        return e.message
    except:
        return traceback.format_exc()
    finally:
        delete_file_if_it_exist(hed_file_path)


def run_tag_compare(form_request_object):
    """Run tag comparison(map_schema from converter)

    returns: Response or string.
        Empty string is success, but nothing to download.
        Non empty string is an error
        Response is a download success.
    """
    hed_file_path = ''
    try:
        conversion_input_arguments = _generate_input_arguments_from_conversion_form(form_request_object)
        hed_file_path = conversion_input_arguments[conversion_arg_constants.HED_XML_PATH]
        if hed_file_path.endswith(".mediawiki"):
            new_file_path = _run_conversion(hed_file_path)[converter_constants.HED_OUTPUT_LOCATION_KEY]
            if new_file_path:
                delete_file_if_it_exist(hed_file_path)
                hed_file_path = new_file_path
        result_dict = _run_tag_compare(hed_file_path)
        if result_dict[converter_constants.HED_OUTPUT_LOCATION_KEY]:
            filename = result_dict[converter_constants.HED_OUTPUT_LOCATION_KEY]
            download_response = generate_download_file_response_and_delete(filename)
            if isinstance(download_response, str):
                return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
            return download_response
    except urllib.error.URLError:
        return error_constants.INVALID_URL_ERROR
    except urllib.error.HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except SchemaError as e:
        return e.message
    finally:
        delete_file_if_it_exist(hed_file_path)
    return ""


def generate_download_file_response_and_delete(full_filename, display_filename=None):
    """Generates a download other response.

    Parameters
    ----------
    full_filename: string
        The download other name.
    display_filename: string
        What the save as window should show for filename.  If none use download file name.

    Returns
    -------
    response object or string.
        A response object containing the download, or a string on error.

    """
    if display_filename is None:
        display_filename = full_filename
    try:
        def generate():
            with open(full_filename, 'r', encoding='utf-8') as download_file:
                for line in download_file:
                    yield line
            delete_file_if_it_exist(full_filename)

        return Response(generate(), mimetype='text/plain charset=utf-8',
                        headers={'Content-Disposition': f"attachment; filename={display_filename}"})
    except:
        return traceback.format_exc()


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


def create_upload_directory(upload_directory):
    """Creates the upload directory.

    """
    _create_folder_if_needed(upload_directory)


def _file_extension_is_valid(filename, accepted_file_extensions):
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
    return os.path.splitext(filename)[1] in accepted_file_extensions


def _save_hed_to_upload_folder_if_present(hed_file_object):
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
        hed_file_extension = _get_file_extension(hed_file_object.filename)
        hed_file_path = _save_file_to_upload_folder(hed_file_object, hed_file_extension)
    return hed_file_path


def _file_has_valid_extension(file_object, accepted_file_extensions):
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
    return file_object and _file_extension_is_valid(file_object.filename, accepted_file_extensions)


def _get_file_extension(file_name_or_path):
    """Get the other extension from the specified filename. This can be the full path or just the name of the other.

       Parameters
       ----------
       file_name_or_path: string
           The name or full path of a other.

       Returns
       -------
       string
           The extension of the other.
       """
    return os.path.splitext(file_name_or_path)[1]


def _generate_input_arguments_from_conversion_form(form_request_object):
    """Gets the conversion function input arguments from a request object associated with the conversion form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying conversion function.
    """
    conversion_input_arguments = {}
    hed_file_path = _get_uploaded_file_paths_from_forms(form_request_object)
    conversion_input_arguments[conversion_arg_constants.HED_XML_PATH] = hed_file_path
    return conversion_input_arguments


def delete_file_if_it_exist(file_path):
    """Deletes a other if it exist.

    Parameters
    ----------
    file_path: string
        The path to a other.

    Returns
    -------
    boolean
        True if the other exist and was deleted.
    """
    if os.path.isfile(file_path):
        os.remove(file_path)
        return True
    return False


def _create_folder_if_needed(folder_path):
    """Checks to see if the upload folder exist. If it doesn't then it creates it.

    Parameters
    ----------
    folder_path: string
        The path of the folder that you want to create.

    Returns
    -------
    boolean
        True if the upload folder needed to be created, False if otherwise.

    """
    folder_needed_to_be_created = False
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        folder_needed_to_be_created = True
    return folder_needed_to_be_created


def _save_file_to_upload_folder(file_object, file_suffix=""):
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
    temporary_upload_file = tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False,
                                                        dir=current_app.config[UPLOAD_DIRECTORY_KEY])
    _copy_file_line_by_line(file_object, temporary_upload_file)
    return temporary_upload_file.name


def _copy_file_line_by_line(file_object_1, file_object_2):
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


def url_present_in_form(conversion_form_request_object):
    """Checks to see if a HED XML URL is present in a request object from conversion form.

    Parameters
    ----------
    conversion_form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the conversion form.

    """
    return _check_if_option_in_form(conversion_form_request_object, js_form_constants.OPTIONS_GROUP,
                                    js_form_constants.OPTION_URL) \
                                    and js_form_constants.HED_URL in conversion_form_request_object.values


def _check_if_option_in_form(conversion_form_request_object, option_name, target_value):
    """Checks if the given option has a specific value.
       This is used for radio buttons.
    """
    if option_name in conversion_form_request_object.values:
        if conversion_form_request_object.values[option_name] == target_value:
            return True

    return False


def hed_present_in_form(conversion_form_request_object):
    """Checks to see if a HED XML other is present in a request object from conversion form.

    Parameters
    ----------
    conversion_form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the conversion form.

    """
    return _check_if_option_in_form(conversion_form_request_object, js_form_constants.OPTIONS_GROUP,
                                    js_form_constants.OPTION_UPLOAD) \
                                    and js_form_constants.HED_FILE in conversion_form_request_object.files


