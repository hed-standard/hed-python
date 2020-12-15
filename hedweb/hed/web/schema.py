import traceback
from urllib.error import URLError, HTTPError
from flask import current_app, Response

from hed.schematools import xml2wiki, wiki2xml, constants as converter_constants
from hed.tools.duplicate_tags import check_for_duplicate_tags
from hed.util.file_util import delete_file_if_it_exist, url_to_file, get_file_extension
from hed.util.exceptions import SchemaError
from hed.web.utils import check_if_option_in_form
from hed.web.web_utils import handle_http_error, save_hed_to_upload_folder_if_present, file_has_valid_extension, \
    file_extension_is_valid
from hed.web.constants import common_constants, error_constants, file_constants

app_config = current_app.config


def get_schema_conversion_function(schema_local_path):
    """Runs the appropriate xml<>mediawiki converter depending on input filetype.

    returns: A dictionary with converter.constants filled in.
    """
    input_extension = get_file_extension(schema_local_path)
    if input_extension == file_constants.SCHEMA_XML_EXTENSION:
        conversion_function = xml2wiki.convert_hed_xml_2_wiki
    elif input_extension == file_constants.SCHEMA_WIKI_EXTENSION:
        conversion_function = wiki2xml.convert_hed_wiki_2_xml
    else:
        raise ValueError(f"Invalid extension type: {input_extension}")

    return conversion_function(None, schema_local_path)


def get_uploaded_file_paths_from_schema_form(form_request_object):
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
    schema_local_path = ''
    if hed_present_in_form(form_request_object) and file_has_valid_extension(
            form_request_object.files[common_constants.SCHEMA_FILE], file_constants.SCHEMA_EXTENSIONS):
        schema_local_path = save_hed_to_upload_folder_if_present(
            form_request_object.files[common_constants.SCHEMA_FILE])
    elif url_present_in_form(form_request_object):
        schema_local_path = url_to_file(form_request_object.values[common_constants.SCHEMA_URL])
    return schema_local_path


def run_schema_conversion(form_request_object):
    """Run conversion(wiki2xml or xml2wiki from converter)

    returns: Response or string.
        Non empty string is an error
        Response is a download success.
    """
    hed_file_path = ''
    try:
        conversion_arguments = generate_input_arguments_from_schema_form(form_request_object)
        hed_file_path = conversion_arguments[common_constants.SCHEMA_PATH]
        result_dict = get_schema_conversion_function(hed_file_path)
        filename = result_dict[converter_constants.HED_OUTPUT_LOCATION_KEY]
        download_response = generate_download_file_response_and_delete(filename)
        if isinstance(download_response, str):
            return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
        return download_response
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except SchemaError as e:
        return e.message
    except:
        return traceback.format_exc()
    finally:
        delete_file_if_it_exist(hed_file_path)


def run_schema_duplicate_tag_detection(form_request_object):
    """Run tag comparison(map_schema from converter)

    returns: Response or string.
        Empty string is success, but nothing to download.
        Non empty string is an error
        Response is a download success.
    """
    hed_file_path = ''
    try:
        conversion_input_arguments = generate_input_arguments_from_schema_form(form_request_object)
        hed_file_path = conversion_input_arguments[common_constants.SCHEMA_PATH]
        if hed_file_path.endswith(".mediawiki"):
            new_file_path = get_schema_conversion_function(hed_file_path)[converter_constants.HED_OUTPUT_LOCATION_KEY]
            if new_file_path:
                delete_file_if_it_exist(hed_file_path)
                hed_file_path = new_file_path

        if not file_extension_is_valid(hed_file_path, [file_constants.SCHEMA_XML_EXTENSION]):
            raise ValueError(f"Invalid extension on file: {hed_file_path}")
        result_dict = check_for_duplicate_tags(hed_file_path)
        if result_dict[converter_constants.HED_OUTPUT_LOCATION_KEY]:
            filename = result_dict[converter_constants.HED_OUTPUT_LOCATION_KEY]
            download_response = generate_download_file_response_and_delete(filename)
            if isinstance(download_response, str):
                return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
            return download_response
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except HTTPError:
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


def generate_input_arguments_from_schema_form(form_request_object):
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
    hed_file_path = get_uploaded_file_paths_from_schema_form(form_request_object)
    conversion_input_arguments[common_constants.SCHEMA_PATH] = hed_file_path
    return conversion_input_arguments


def url_present_in_form(form_request_object):
    """Checks to see if a HED XML URL is present in a request object from conversion form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the conversion form.

    """
    url_checked = check_if_option_in_form(form_request_object, common_constants.SCHEMA_UPLOAD_OPTIONS,
                                          common_constants.SCHEMA_URL_OPTION)
    return url_checked and common_constants.SCHEMA_URL in form_request_object.values


def hed_present_in_form(form_request_object):
    """Checks to see if a HED XML other is present in a request object from conversion form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the conversion form.

    """
    return check_if_option_in_form(form_request_object, common_constants.SCHEMA_UPLOAD_OPTIONS,
                                   common_constants.SCHEMA_FILE_OPTION) and \
        common_constants.SCHEMA_FILE in form_request_object.files
