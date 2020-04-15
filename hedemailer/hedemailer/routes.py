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
        if not utils.request_is_github_push_event(request):
            return constants.NO_EMAILS_SENT_RESPONSE;

        hed_emailer.send_email(request)
        return constants.EMAIL_SENT_RESPONSE;
    except Exception as ex:
        return constants.generate_exception_response(ex);
