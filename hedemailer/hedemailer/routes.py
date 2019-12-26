from flask import Blueprint, current_app, request;
from hedemailer import hed_emailer, utils, constants;

app_config = current_app.config;
route_blueprint = Blueprint('route_blueprint', __name__);


@route_blueprint.route('/', methods=['POST'])
def process_hed_payload():
    """Send a email with the latest HED schema.

    Parameters
    ----------

    Returns
    -------
    string
        A JSON response.
    """
    try:
        if not utils.request_is_github_gollum_event(request):
            return constants.NO_EMAILS_SENT_RESPONSE;
        result_message = hed_emailer.send_email(request)
        if result_message is None:
            return constants.EMAIL_SENT_RESPONSE;
        else:
            return constants.generate_exception_response(result_message)
    except Exception as ex:
        return constants.generate_exception_response(ex);
