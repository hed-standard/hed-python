from flask import render_template, Response, request, Blueprint, current_app
from hed.webconverter import utils
from hed.webconverter.constants.error import error_constants
from hed.webconverter.constants.routing import page_constants, route_constants, blueprint_constants

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
    conversion_response = utils.run_conversion(request)
    # Success
    if isinstance(conversion_response, Response):
        return conversion_response
    if isinstance(conversion_response, str):
        return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                       conversion_response,
                                       as_text=True)

    return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                   "Invalid response type in get_duplicate_tag_results.  This should not happen.",
                                   as_text=True)


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
    comparison_response = utils.run_tag_compare(request)
    # Success
    if isinstance(comparison_response, Response):
        return comparison_response
    if isinstance(comparison_response, str):
        if comparison_response:
            return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                           comparison_response,
                                           as_text=True)
        else:
            return ""

    return utils.handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                   "Invalid response type in get_duplicate_tag_results.  This should not happen.",
                                   as_text=True)



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

