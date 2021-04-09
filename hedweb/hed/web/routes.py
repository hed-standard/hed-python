from flask import render_template, Response, request, Blueprint, current_app
import json

from hed.util import hed_cache
from hed.schema import hed_schema_file
from hed.web.constants import common, page_constants, route_constants
from hed.web.web_utils import delete_file_no_exceptions, \
   handle_http_error, handle_error, save_file_to_upload_folder
from hed.web import dictionary, events, schema, spreadsheet, services
from hed.web.hedstring import generate_input_from_hedstring_form, hedstring_process
from hed.web.spreadsheet_utils import generate_input_columns_info, get_columns_info

app_config = current_app.config
route_blueprint = Blueprint(route_constants.ROUTE_BLUEPRINT, __name__)


@route_blueprint.route(route_constants.COLUMN_INFO_ROUTE, methods=['POST'])
def get_columns_info_results():
    """Gets information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

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


@route_blueprint.route(route_constants.DICTIONARY_VALIDATION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_dictionary_validation_results():
    """Validate the JSON dictionary in the form after submission and return an attachment containing the output.

    Parameters
    ----------

    Returns
    -------
        download file
        A text file with the validation errors.
    """
    input_arguments = {}
    try:
        input_arguments = dictionary.generate_input_from_dictionary_form(request)
        return dictionary.dictionary_validate(input_arguments)
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.JSON_PATH, ''))


@route_blueprint.route(route_constants.EVENTS_VALIDATION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_events_validation_results():
    """Validate the spreadsheet in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    input_arguments = {}
    try:
        input_arguments = events.generate_input_from_events_form(request)
        a = events.events_validate(input_arguments)
        return a
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.SPREADSHEET_PATH, ''))
        delete_file_no_exceptions(input_arguments.get(common.JSON_PATH, ''))


@route_blueprint.route(route_constants.HED_SERVICES_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_hed_services_results():
    """Validate the hed strings associated with EEG events after submission from HEDTools EEGLAB plugin and
    return json string containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the EEG events' hedstrings.
        If the validation fails then a 500 error message is returned.
    """
    try:
        form_data = request.data
        status = services.report_services_status(form_data)
        return json.dumps(status)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.HEDSTRING_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_hedstring_results():
    """Process hed strings entered in a text box.

    Parameters
    ----------

    Returns
    -------
        Response

    """
    # return hedstring_process(request)

    try:
        input_arguments = generate_input_from_hedstring_form(request)
        return json.dumps(hedstring_process(input_arguments))
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.HED_VERSION_ROUTE, methods=['POST'])
def get_hed_version():
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
        if common.HED_XML_FILE in request.files:
            hed_file_path = save_file_to_upload_folder(request.files[common.HED_XML_FILE])
            hed_info[common.HED_VERSION] = hed_schema_file.get_hed_xml_version(hed_file_path)
        return json.dumps(hed_info)
    except Exception as ex:
        return handle_error(ex)
    finally:
        delete_file_no_exceptions(request.files[common.HED_XML_FILE])


@route_blueprint.route(route_constants.HED_MAJOR_VERSION_ROUTE, methods=['GET'])
def get_major_hed_versions():
    """Gets a list of major hed versions from the hed_cache and returns as a serialized JSON string

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing a list of the HED versions.

    """

    try:
        hed_cache.cache_all_hed_xml_versions()
        hed_info = {common.HED_MAJOR_VERSIONS: hed_cache.get_all_hed_versions()}
        return json.dumps(hed_info)
    except Exception as ex:
        return handle_error(ex)


@route_blueprint.route(route_constants.SCHEMA_COMPLIANCE_CHECK_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_schema_compliance_check_results():
    """Check the HED specification in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing the hed specification to check. If the conversion fails then a
        500 error message is returned.
    """
    input_arguments = {}
    try:
        input_arguments = schema.generate_input_from_schema_form(request)
        return schema.schema_check(input_arguments)
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.SCHEMA_PATH, ''))


@route_blueprint.route(route_constants.SCHEMA_CONVERSION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_schema_conversion_results():
    """Convert the given HED specification and return an attachment with the result.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related file to convert. If the conversion fails then a
        500 error message is returned.
    """
    input_arguments = {}
    try:
        input_arguments = schema.generate_input_from_schema_form(request)
        return schema.schema_convert(input_arguments)
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.SCHEMA_PATH, ''))


@route_blueprint.route(route_constants.SPREADSHEET_VALIDATION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_spreadsheet_validation_results():
    """Validate the spreadsheet in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    input_arguments = {}
    try:
        input_arguments = spreadsheet.generate_input_from_spreadsheet_form(request)
        return spreadsheet.spreadsheet_validate(input_arguments)
    except Exception as ex:
        return handle_http_error(ex)
    finally:
        delete_file_no_exceptions(input_arguments.get(common.SPREADSHEET_PATH, ''))


@route_blueprint.route(route_constants.ADDITIONAL_EXAMPLES_ROUTE, strict_slashes=False, methods=['GET'])
def render_additional_examples_page():
    """Handles the site additional examples page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the additional examples page.

    """
    return render_template(page_constants.ADDITIONAL_EXAMPLES_PAGE)


@route_blueprint.route(route_constants.COMMON_ERRORS_ROUTE, strict_slashes=False, methods=['GET'])
def render_common_error_page():
    """Handles the common errors page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the home page.

    """
    return render_template(page_constants.COMMON_ERRORS_PAGE)


@route_blueprint.route(route_constants.DICTIONARY_ROUTE, strict_slashes=False, methods=['GET'])
def render_dictionary_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.DICTIONARY_VALIDATION_PAGE)
    # return render_template(page_constants.DICTIONARY_VALIDATION_PAGE)


@route_blueprint.route(route_constants.EVENTS_ROUTE, strict_slashes=False, methods=['GET'])
def render_events_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.EVENTS_PAGE)


@route_blueprint.route(route_constants.HED_SERVICES_ROUTE, strict_slashes=False, methods=['GET'])
def render_hed_services_form():
    """Handles the site root and EEG Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.HED_SERVICES_PAGE)


@route_blueprint.route(route_constants.HEDSTRING_ROUTE, strict_slashes=False, methods=['GET'])
def render_hedstring_form():
    """Renders a form for different hedstring operations.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the hed_string_form. If the HTTP method is a GET then the form will be
        displayed. If the HTTP method is a POST then the form is submitted.

    """
    return render_template(page_constants.HEDSTRING_PAGE)


@route_blueprint.route(route_constants.HED_TOOLS_HELP_ROUTE, strict_slashes=False, methods=['GET'])
def render_help_page():
    """Handles the site help page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the help page.

    """
    return render_template(page_constants.HED_TOOLS_HELP_PAGE)


@route_blueprint.route(route_constants.HED_TOOLS_HOME_ROUTE, strict_slashes=False, methods=['GET'])
def render_home_page():
    """Handles the home page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the home page.

    """
    return render_template(page_constants.HED_TOOLS_HOME_PAGE)


@route_blueprint.route(route_constants.SCHEMA_ROUTE, strict_slashes=False, methods=['GET'])
def render_schema_form():
    """Handles the site root and conversion tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the conversion form. If the HTTP method is a GET then the conversion form will be
        displayed. If the HTTP method is a POST then the conversion form is submitted.

    """
    return render_template(page_constants.SCHEMA_PAGE)


@route_blueprint.route(route_constants.SPREADSHEET_ROUTE, strict_slashes=False, methods=['GET'])
def render_spreadsheet_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.SPREADSHEET_PAGE)
