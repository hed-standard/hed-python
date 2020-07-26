from flask import render_template, Response, request, Blueprint, current_app
import os
import json
from hed.webconverter import utils
from hed.webconverter.constants.error import error_constants
from hed.webconverter.constants.routing import page_constants, route_constants, blueprint_constants
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
    display_name = request.args.get("display_name")
    download_response = utils.generate_download_file_response(filename, display_name)
    if isinstance(download_response, str):
        utils.handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
    return download_response


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
def get_conversion_results():
    """Convert the given HED specification and return an attachment with the result.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related file to convert. If the conversion fails then a
        500 error message is returned.
    """
    conversion_status = utils.run_conversion(request)
    if error_constants.ERROR_KEY in conversion_status:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                       conversion_status[error_constants.ERROR_KEY])
    return json.dumps(conversion_status)


@route_blueprint.route(route_constants.SUBMIT_TAG_ROUTE, strict_slashes=False, methods=['POST'])
def get_duplciate_tag_results():
    """Check the HED specification in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing the hed specification to check. If the conversion fails then a
        500 error message is returned.
    """
    conversion_status = utils.run_tag_compare(request)
    if error_constants.ERROR_KEY in conversion_status:
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                       conversion_status[error_constants.ERROR_KEY])
    return json.dumps(conversion_status)



@route_blueprint.route(route_constants.CONVERSION_ROUTE, strict_slashes=False, methods=['GET'])
def render_conversion_form():
    """Handles the site root and conversion tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the conversion form. If the HTTP method is a GET then the conversion form will be
        displayed. If the HTTP method is a POST then the conversion form is submitted.

    """
    return render_template(page_constants.CONVERSION_PAGE)

