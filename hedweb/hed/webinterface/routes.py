from flask import render_template, Response, request, Blueprint, current_app
import os
import json
from hed.webinterface import utils
from hed.webinterface.constants.error import error_constants
from hed.webinterface.constants.routing import page_constants, route_constants, blueprint_constants
import traceback

app_config = current_app.config
route_blueprint = Blueprint(blueprint_constants.ROUTE_BLUEPRINT, __name__)


@route_blueprint.route(route_constants.HOME_ROUTE, strict_slashes=False, methods=['GET'])
def render_home_page():
    """Handles the home page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the home page.

    """
    return render_template(page_constants.HOME_PAGE)


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
    return render_template(page_constants.COMMON_ERRORS)


@route_blueprint.route(route_constants.DELETE_FILE_ROUTE, strict_slashes=False, methods=['GET'])
def delete_file_in_upload_directory(filename):
    """Deletes the specified other from the upload other.

    Parameters
    ----------
    filename: string
        The name of the other to delete from the upload other.

    Returns
    -------

    """
    if utils.delete_file_if_it_exist(os.path.join(app_config['UPLOAD_FOLDER'], filename)):
        return Response(status=error_constants.NO_CONTENT_SUCCESS)
    else:
        return utils.handle_http_error(error_constants.NOT_FOUND_ERROR, error_constants.FILE_DOES_NOT_EXIST)


@route_blueprint.route(route_constants.DOWNLOAD_FILE_ROUTE, strict_slashes=False, methods=['GET'])
def download_file_in_upload_directory(filename):
    """Downloads the specified other from the upload other.

    Parameters
    ----------
    filename: string
        The name of the other to download from the upload other.

    Returns
    -------
    File
        The contents of a other in the upload directory to send to the client.

    """
    download_response = utils.generate_download_file_response(filename)
    if isinstance(download_response, str):
        utils.handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
    return download_response


@route_blueprint.route(route_constants.HED_VERSION_ROUTE, methods=['POST'])
def get_hed_version_in_file():
    """Gets information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    hed_info = utils.find_hed_version_in_file(request)
    if error_constants.ERROR_KEY in hed_info:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR, hed_info[error_constants.ERROR_KEY])
    return json.dumps(hed_info)


@route_blueprint.route(route_constants.MAJOR_HED_VERSION_ROUTE, methods=['GET'])
def get_major_hed_versions():
    """Gets information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    hed_info = utils.find_major_hed_versions()
    if error_constants.ERROR_KEY in hed_info:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR, hed_info[error_constants.ERROR_KEY])
    return json.dumps(hed_info)


@route_blueprint.route(route_constants.SPREADSHEET_COLUMN_INFO_ROUTE, methods=['POST'])
def get_spreadsheet_columns_info():
    """Gets information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    spreadsheet_columns_info = utils.find_spreadsheet_columns_info(request)
    if error_constants.ERROR_KEY in spreadsheet_columns_info:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                       spreadsheet_columns_info[error_constants.ERROR_KEY])
    return json.dumps(spreadsheet_columns_info)


@route_blueprint.route(route_constants.WORKSHEET_COLUMN_INFO, methods=['POST'])
def get_worksheets_info():
    """Gets information related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the Excel worksheets.

    """
    worksheets_info = {}
    try:
        worksheets_info = utils.find_worksheets_info(request)
        if error_constants.ERROR_KEY in worksheets_info:
            return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                           worksheets_info[error_constants.ERROR_KEY])
    except:
        worksheets_info[error_constants.ERROR_KEY] = traceback.format_exc()
    return json.dumps(worksheets_info)


@route_blueprint.route(route_constants.HELP_ROUTE, strict_slashes=False, methods=['GET'])
def render_help_page():
    """Handles the site help page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the help page.

    """
    return render_template(page_constants.HELP_PAGE)


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


@route_blueprint.route(route_constants.SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_validation_results():
    """Validate the spreadsheet in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    validation_status = utils.report_spreadsheet_validation_status(request)
    if error_constants.ERROR_KEY in validation_status:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                       validation_status[error_constants.ERROR_KEY])
    return json.dumps(validation_status)


@route_blueprint.route(route_constants.EEG_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_EEG_events_validation_results():
    """Validate the hed strings associated with EEG events after submission from HEDTools EEGLAB plugin and
    return json string containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the EEG events' hed-strings.
        If the validation fails then a 500 error message is returned.
    """
    validation_status = utils.report_eeg_events_validation_status(request)

    if error_constants.ERROR_KEY in validation_status:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                       validation_status[error_constants.ERROR_KEY])
    return json.dumps(validation_status)


@route_blueprint.route(route_constants.VALIDATION_ROUTE, strict_slashes=False, methods=['GET'])
def render_validation_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.VALIDATION_PAGE)


@route_blueprint.route(route_constants.EEG_VALIDATION_ROUTE, strict_slashes=False, methods=['GET'])
def render_eeg_validation_form():
    """Handles the site root and EEG Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.EEG_VALIDATION_PAGE)
