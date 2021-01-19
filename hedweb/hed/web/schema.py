from os.path import basename
import traceback
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from flask import current_app, Response

from hed.schema import xml2wiki, wiki2xml, schema_validator
from hed.util.file_util import delete_file_if_it_exist, url_to_file, get_file_extension, write_errors_to_file
from hed.util.exceptions import SchemaFileError

from hed.web.web_utils import file_extension_is_valid, form_has_file, form_has_option, form_has_url, \
    handle_http_error, save_file_to_upload_folder, generate_download_file_response

from hed.web.constants import common_constants, error_constants, file_constants

app_config = current_app.config


def generate_input_from_schema_form(form_request_object):
    """Gets the conversion function input arguments from a request object associated with the conversion form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the conversion form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying schema functions.
    """
    arguments = {}
   
    if form_has_option(form_request_object, common_constants.SCHEMA_UPLOAD_OPTIONS,
                       common_constants.SCHEMA_FILE_OPTION) and \
            form_has_file(form_request_object, common_constants.SCHEMA_FILE, file_constants.SCHEMA_EXTENSIONS):
        schema_file = form_request_object.files[common_constants.SCHEMA_FILE]
        arguments[common_constants.SCHEMA_PATH] = save_file_to_upload_folder(schema_file)
        arguments[common_constants.SCHEMA_DISPLAY_NAME] = schema_file.filename
    elif form_has_option(form_request_object, common_constants.SCHEMA_UPLOAD_OPTIONS,
                         common_constants.SCHEMA_URL_OPTION) and \
            form_has_url(form_request_object, common_constants.SCHEMA_URL, file_constants.SCHEMA_EXTENSIONS):
        schema_url = form_request_object.values[common_constants.SCHEMA_URL]
        arguments[common_constants.SCHEMA_PATH] = url_to_file(schema_url)
        url_parsed = urlparse(schema_url)
        arguments[common_constants.SCHEMA_DISPLAY_NAME] = basename(url_parsed.path)
    return arguments


def get_schema_conversion(schema_local_path):
    """Runs the appropriate xml<>mediawiki converter depending on input filetype.

    returns: A dictionary with converter.constants filled in.
    """

    try:
        if not schema_local_path:
            raise ValueError(f"Invalid input schema path")
        input_extension = get_file_extension(schema_local_path)

        if input_extension == file_constants.SCHEMA_XML_EXTENSION:
            conversion_function = xml2wiki.convert_hed_xml_2_wiki
        elif input_extension == file_constants.SCHEMA_WIKI_EXTENSION:
            conversion_function = wiki2xml.convert_hed_wiki_2_xml
        else:
            raise ValueError(f"Invalid extension type: {input_extension}")
        converted_schema_path, errors = conversion_function(None, schema_local_path, check_for_issues=False)
    except ValueError as error:
        errors = format(error)
        converted_schema_path = ''

    return converted_schema_path, errors


def run_schema_compliance_check(form_request_object):
    """Run tag comparison(map_schema from converter)

    returns: Response or string.
        Empty string is success, but nothing to download.
        Non empty string is an error
        Response is a download success.
    """
    hed_file_path = ''
    try:
        conversion_input_arguments = generate_input_from_schema_form(form_request_object)
        hed_file_path = conversion_input_arguments.get(common_constants.SCHEMA_PATH, '')
        if hed_file_path and hed_file_path.endswith(".mediawiki"):
            new_file_path, errors = get_schema_conversion(hed_file_path)
            if new_file_path:
                delete_file_if_it_exist(hed_file_path)
                hed_file_path = new_file_path

        if not hed_file_path or not file_extension_is_valid(hed_file_path, [file_constants.SCHEMA_XML_EXTENSION]):
            return f"Invalid file name {hed_file_path}"
        issues = schema_validator.validate_schema(hed_file_path)

        if issues:
            #issue_file = write_text_iter_to_file(issues)
            issue_file = write_errors_to_file(issues, extension=".txt")
            download_response = generate_download_file_response(issue_file, f"HED-3G format issues for: {hed_file_path}")
            if isinstance(download_response, str):
                return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
            return download_response
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except SchemaFileError as e:
        return e.message
    except Exception as e:
        return "Unexpected processing error: " + str(e)
    finally:
        delete_file_if_it_exist(hed_file_path)
    return ""


def run_schema_conversion(form_request_object):
    """Run conversion(wiki2xml or xml2wiki from converter)

    returns: Response or string.
        Non empty string is an error
        Response is a download success.
    """
    hed_file_path = ''
    try:
        arguments = generate_input_from_schema_form(form_request_object)
        hed_file_path = arguments.get(common_constants.SCHEMA_PATH)
        schema_file, errors = get_schema_conversion(hed_file_path)
        if errors:
            download_response = errors
        else:
            download_response = generate_download_file_response(schema_file)
        if isinstance(download_response, Response):
            return download_response
        elif isinstance(download_response, str):
            return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
        else:
            raise Exception("Unable to download schema file for unknown reasons")
    except SchemaFileError as e:
        return e.message
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except:
        return traceback.format_exc()
    finally:
        delete_file_if_it_exist(hed_file_path)
