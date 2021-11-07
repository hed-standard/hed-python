from flask import render_template, request, Blueprint, current_app
from werkzeug.utils import secure_filename
import json

from hed import schema as hedschema
from hedweb.constants import base_constants, page_constants
from hedweb.constants import route_constants, file_constants
from hedweb.web_utils import handle_http_error, package_results, handle_error
from hedweb import sidecar, events, spreadsheet, services, strings, schema
from hedweb.columns import get_columns_request

app_config = current_app.config
route_blueprint = Blueprint(route_constants.ROUTE_BLUEPRINT, __name__)


@route_blueprint.route(route_constants.COLUMNS_INFO_ROUTE, methods=['POST'])
def columns_info_results():
    """Gets the names of the spreadsheet columns and sheet_name names if any.

    Returns
    -------
    string
        A serialized JSON string containing information related to the column and sheet_name information.

    """
    try:
        columns_info = get_columns_request(request)
        return json.dumps(columns_info)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.EVENTS_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def events_results():
    """Process the events file and JSON sidecar in the form and return an attachment with results.

    Returns
    -------
        downloadable file
        Contains the results of processing
    """

    try:
        input_arguments = events.get_input_from_events_form(request)
        a = events.process(input_arguments)
        return package_results(a)
    except Exception as ex:
        return handle_http_error(ex)


@route_blueprint.route(route_constants.SCHEMA_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def schema_results():
    """Get the results of schema processing.

    Returns
    -------
        downloadable file if schema errors on validation or conversion was successful

    """
    try:
        arguments = schema.get_input_from_form(request)
        a = schema.process(arguments)
        return package_results(a)
    except Exception as ex:
        return handle_http_error(ex)


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
        if base_constants.SCHEMA_PATH in request.files:
            f = request.files[base_constants.SCHEMA_PATH]
            hed_schema = hedschema.from_string(f.stream.read(file_constants.BYTE_LIMIT).decode('ascii'),
                                               file_type=secure_filename(f.filename))
            hed_info[base_constants.SCHEMA_VERSION] = hed_schema.header_attributes['version']
        return json.dumps(hed_info)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.SCHEMA_VERSIONS_ROUTE, methods=['GET', 'POST'])
def schema_versions_results():
    """Gets a list of hed versions from the hed_cache and returns as a serialized JSON string

    Returns
    -------
    string
        A serialized JSON string containing a list of the HED versions.

    """

    try:
        hedschema.cache_all_hed_xml_versions()
        hed_info = {base_constants.SCHEMA_VERSION_LIST: hedschema.get_all_hed_versions()}
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
    response = {}
    try:
        arguments = services.get_input_from_request(request)
        response = services.process(arguments)
        return json.dumps(response)
    except Exception as ex:
        errors = handle_error(ex)
        response['error_type'] = errors['error_type']
        response['error_msg'] = errors['error_msg']
        return handle_error(ex)


@route_blueprint.route(route_constants.SIDECAR_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def sidecar_results():
    """Process the JSON sidecar after form submission and return an attachment containing the output.

    Returns
    -------
        download file
        A text file with the validation errors.
    """

    try:
        input_arguments = sidecar.get_input_from_form(request)
        a = sidecar.process(input_arguments)
        return package_results(a)
    except Exception as ex:
        return handle_http_error(ex)


@route_blueprint.route(route_constants.SPREADSHEET_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def spreadsheet_results():
    """Process the spreadsheet in the form and return an attachment with the results.

    Returns
    -------
        string
        Validation errors in readable format.
    """

    try:
        arguments = spreadsheet.get_input_from_form(request)
        a = spreadsheet.process(arguments)
        response = package_results(a)
        return response
    except Exception as ex:
        return handle_http_error(ex)


@route_blueprint.route(route_constants.STRING_SUBMIT_ROUTE, strict_slashes=False, methods=['GET', 'POST'])
def string_results():
    """Process hed strings entered in a text box.

    Returns
    -------
        A serialized JSON string

    """

    try:
        input_arguments = strings.get_input_from_form(request)
        a = strings.process(input_arguments)
        return json.dumps(a)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.EVENTS_ROUTE, strict_slashes=False, methods=['GET'])
def render_events_form():
    """The form for BIDS event file (with JSON sidecar) processing.

    Returns
    -------
    Rendered template
        A rendered template for the events form.

    """
    return render_template(page_constants.EVENTS_PAGE)


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


@route_blueprint.route(route_constants.SERVICES_ROUTE, strict_slashes=False, methods=['GET'])
def render_services_form():
    """Landing page for HED hedweb services designed to be called from programs such as MATLAB.

    Returns
    -------
    Rendered template
        A dummy rendered template so that the service can get a csrf token.

    """
    return render_template(page_constants.SERVICES_PAGE)


@route_blueprint.route(route_constants.SIDECAR_ROUTE, strict_slashes=False, methods=['GET'])
def render_sidecar_form():
    """Page with the sidecar processing form.

    Returns
    -------
    Rendered template
        A rendered template for the sidecar form.

    """
    return render_template(page_constants.SIDECAR_PAGE)


@route_blueprint.route(route_constants.SPREADSHEET_ROUTE, strict_slashes=False, methods=['GET'])
def render_spreadsheet_form():
    """Displays the spreadsheet Validation form.

    Returns
    -------
    Rendered template
        A rendered template for the spreadsheet hed tags form.

    """
    return render_template(page_constants.SPREADSHEET_PAGE)


@route_blueprint.route(route_constants.STRING_ROUTE, strict_slashes=False, methods=['GET'])
def render_string_form():
    """Renders a form for different hed string operations.

    Returns
    -------
    Rendered template
        A rendered template for the hedstring form.

    """
    return render_template(page_constants.STRING_PAGE)
