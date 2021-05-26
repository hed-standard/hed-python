from flask import render_template, request, Blueprint, current_app
import json

from hed.util import hed_cache
from hed.schema import hed_schema_file
from hedweb.constants import common, page_constants
from hedweb.constants import route_constants
from hedweb.web_utils import delete_file_no_exceptions, \
   handle_http_error, handle_error, save_file_to_upload_folder
from hedweb import dictionary, events, schema, spreadsheet, services
from hedweb.strings import generate_input_from_string_form, string_process
from hedweb.spreadsheet_utils import generate_input_columns_info, get_columns_info

app_config = current_app.config
route_blueprint = Blueprint(route_constants.ROUTE_BLUEPRINT, __name__)


@route_blueprint.route(route_constants.COLUMN_INFO_ROUTE, methods=['POST'])
def columns_info_results():
    """Gets the names of the spreadsheet columns and column indices that contain HED tags.

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    input_arguments = {}
    try:
        input_arguments = generate_input_columns_info(request)
        columns_info = get_columns_info(input_arguments)
        return json.dumps(columns_info)
    except Exception as ex:
        return handle_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.COLUMNS_PATH, ''))


@route_blueprint.route(route_constants.DICTIONARY_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def dictionary_results():
    """Process the JSON dictionary in the form after submission and return an attachment containing the output.

    Returns
    -------
        download file
        A text file with the validation errors.
    """
    input_arguments = {}
    try:
        input_arguments = dictionary.generate_input_from_dictionary_form(request)
        a = dictionary.dictionary_process(input_arguments)
        return a
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.JSON_PATH, ''))


@route_blueprint.route(route_constants.EVENTS_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def events_results():
    """Process the events file and JSON sidecar in the form and return an attachment with results.

    Returns
    -------
        downloadable file
        Contains the results of processing
    """
    input_arguments = {}
    try:
        input_arguments = events.generate_input_from_events_form(request)
        a = events.events_process(input_arguments)
        return a
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.EVENTS_PATH, ''))
        delete_file_no_exceptions(input_arguments.get(common.JSON_PATH, ''))


@route_blueprint.route(route_constants.SCHEMA_VERSION_ROUTE, methods=['POST'])
def schema_version_results():
    """Finds the information about the HED version of a file and returns as JSON.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """

    try:
        hed_info = {}
        if common.SCHEMA_PATH in request.files:
            hed_file_path = save_file_to_upload_folder(request.files[common.SCHEMA_PATH])
            hed_info[common.SCHEMA_VERSION] = hed_schema_file.get_hed_xml_version(hed_file_path)
        return json.dumps(hed_info)
    except Exception as ex:
        return handle_error(ex)
    finally:
        delete_file_no_exceptions(request.files[common.SCHEMA_PATH])


@route_blueprint.route(route_constants.SCHEMA_VERSIONS_ROUTE, methods=['GET', 'POST'])
def schema_versions_results():
    """Gets a list of hed versions from the hed_cache and returns as a serialized JSON string

    Returns
    -------
    string
        A serialized JSON string containing a list of the HED versions.

    """

    try:
        hed_cache.cache_all_hed_xml_versions()
        hed_info = {common.SCHEMA_VERSION_LIST: hed_cache.get_all_hed_versions()}
        return json.dumps(hed_info)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.SERVICES_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def services_results():
    """Perform the requested web service and return the results in JSON.

    Returns
    -------
        string
        A serialized JSON string containing processed information.
    """
    try:
        form_data = request.data
        form_string = form_data.decode()
        arguments = json.loads(form_string)
        status = services.services_process(arguments)
        return json.dumps(status)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.SCHEMA_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def schema_results():
    """Get the results of schema processing.

    Returns
    -------
        downloadable file

    """
    input_arguments = {}
    try:
        input_arguments = schema.generate_input_from_schema_form(request)
        return schema.schema_process(input_arguments)
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.SCHEMA_PATH, ''))


@route_blueprint.route(route_constants.SPREADSHEET_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def spreadsheet_results():
    """Process the spreadsheet in the form and return an attachment with the results.

    Returns
    -------
        string
        Validation errors in readable format.
    """
    input_arguments = {}
    try:
        input_arguments = spreadsheet.generate_input_from_spreadsheet_form(request)
        return spreadsheet.spreadsheet_process(input_arguments)
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.SPREADSHEET_PATH, ''))


@route_blueprint.route(route_constants.STRING_SUBMIT_ROUTE, strict_slashes=False, methods=['GET', 'POST'])
def string_results():
    """Process hed strings entered in a text box.

    Returns
    -------
        A serialized JSON string

    """

    try:
        input_arguments = generate_input_from_string_form(request)
        a = json.dumps(string_process(input_arguments))
        return a
        # return json.dumps(string_process(input_arguments))
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.ADDITIONAL_EXAMPLES_ROUTE, strict_slashes=False, methods=['GET'])
def render_additional_examples_page():
    """The site additional examples page.

    Returns
    -------
    Rendered template
        A rendered template for the additional examples page.

    """
    return render_template(page_constants.ADDITIONAL_EXAMPLES_PAGE)


@route_blueprint.route(route_constants.COMMON_ERRORS_ROUTE, strict_slashes=False, methods=['GET'])
def render_common_errors_page():
    """The common errors page.

    Returns
    -------
    Rendered template
        A rendered template for a page explaining common errors.

    """
    return render_template(page_constants.COMMON_ERRORS_PAGE)


@route_blueprint.route(route_constants.DICTIONARY_ROUTE, strict_slashes=False, methods=['GET'])
def render_dictionary_form():
    """Page with the dictionary processing form.

    Returns
    -------
    Rendered template
        A rendered template for the dictionary form.

    """
    return render_template(page_constants.DICTIONARY_PAGE)


@route_blueprint.route(route_constants.EVENTS_ROUTE, strict_slashes=False, methods=['GET'])
def render_events_form():
    """The form for BIDS event file (with JSON sidecar) processing.

    Returns
    -------
    Rendered template
        A rendered template for the events form.

    """
    return render_template(page_constants.EVENTS_PAGE)


@route_blueprint.route(route_constants.SERVICES_ROUTE, strict_slashes=False, methods=['GET'])
def render_hed_services_form():
    """Landing page for HED hedweb services designed to be called from programs such as MATLAB.

    Returns
    -------
    Rendered template
        A dummy rendered template so that the service can get a csrf token.

    """
    return render_template(page_constants.SERVICES_PAGE)


@route_blueprint.route(route_constants.STRING_ROUTE, strict_slashes=False, methods=['GET'])
def render_string_form():
    """Renders a form for different hed string operations.

    Returns
    -------
    Rendered template
        A rendered template for the hedstring form.

    """
    return render_template(page_constants.STRING_PAGE)


@route_blueprint.route(route_constants.HED_TOOLS_HELP_ROUTE, strict_slashes=False, methods=['GET'])
def render_help_page():
    """The site help page.

    Returns
    -------
    Rendered template
        A rendered template for the help page.

    """
    return render_template(page_constants.HED_TOOLS_HELP_PAGE)


@route_blueprint.route(route_constants.HED_TOOLS_HOME_ROUTE, strict_slashes=False, methods=['GET'])
def render_home_page():
    """The home page.

    Returns
    -------
    Rendered template
        A rendered template for the home page.

    """
    return render_template(page_constants.HED_TOOLS_HOME_PAGE)


@route_blueprint.route(route_constants.SCHEMA_ROUTE, strict_slashes=False, methods=['GET'])
def render_schema_form():
    """Handles the site root and conversion tab functionality.

    Returns
    -------
    Rendered template
        A rendered template for the schema processing form.

    """
    return render_template(page_constants.SCHEMA_PAGE)


@route_blueprint.route(route_constants.SPREADSHEET_ROUTE, strict_slashes=False, methods=['GET'])
def render_spreadsheet_form():
    """Displays the spreadsheet Validation form.

    Returns
    -------
    Rendered template
        A rendered template for the spreadsheet hed tags form.

    """
    return render_template(page_constants.SPREADSHEET_PAGE)
