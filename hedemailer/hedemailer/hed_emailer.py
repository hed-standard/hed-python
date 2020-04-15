'''
This module is a webhook implementation that sends out an email whenever there is an update to the Wiki HED schema.

Created on Mar 8, 2017

@author: Jeremy Cockfield
'''
import smtplib;
import json;
from email.mime.text import MIMEText;
from flask import current_app;
from hedemailer import utils, constants;

app_config = current_app.config;


def send_email(request):
    """Send a email with the latest HED schema.

    Parameters
    ----------
    request: Request object
        A Request object containing a Github payload.

    Returns
    -------
    dictionary
        A dictionary containing information about the HED
    """
    github_payload_string = str(request.data, 'utf-8');
    github_payload_dictionary = json.loads(github_payload_string);
    email_list = utils.get_email_list_from_file(app_config[constants.CONFIG_EMAIL_LIST]);
    if not email_list:
        raise Exception(constants.NO_VALID_EMAIL_ADDRESSES_IN_FILE)
    mime_email, hed_resource_dictionary = _create_email(github_payload_dictionary,
                                                        app_config[constants.CONFIG_EMAIL_LIST]);
    _send_email_from_smtp_server(mime_email, email_list);

    return hed_resource_dictionary


def _create_email(github_payload_dictionary, email_list):
    """Creates a email with the latest HED schema.

    Parameters
    ----------
    github_payload_dictionary: dictionary
        A dictionary containing a Github payload.
    email_list: string
        A list containing the emails from a file.

    Returns
    -------
    tuple
        A tuple containing a MIMEBase object used to create the email and a dictionary containing resources used to
        create the email.
    """
    hed_resource_dictionary = {};
    mime_email, main_body_text = utils.create_standard_email(github_payload_dictionary, email_list);
    if utils.push_page_is_hed_schema(github_payload_dictionary):
        hed_resource_dictionary = utils.create_hed_schema_email(mime_email, main_body_text);
    else:
        main_body = MIMEText(main_body_text);
        mime_email.attach(main_body);
    return mime_email, hed_resource_dictionary;


#
def _send_email_from_smtp_server(mime_email, email_list):
    """Send the message via our own SMTP server.

    Parameters
    ----------
    mime_email: MIMEBase object
        A MIMEBase object used to create the email
    email_list: string
        A list containing the emails from a file.
    Returns
    -------

    """
    smtp_server = smtplib.SMTP(constants.LOCALHOST);
    smtp_server.sendmail(app_config[constants.CONFIG_EMAIL_FROM_KEY], email_list, mime_email.as_string());
    smtp_server.quit();
