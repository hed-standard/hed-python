from hedconversion import wiki2xml;
from email.mime.multipart import MIMEMultipart;
from email.mime.text import MIMEText;
from flask import current_app;
import os;
import urllib.request;
from hedemailer import constants;

app_config = current_app.config;

def create_standard_email(github_payload_dictionary, email_list):
    """Create a standard part of the HED schema email.

    Parameters
    ----------
    github_payload_dictionary: dictionary
        A dictionary containing a Github push payload.
    email_list: string
        A list containing the emails from a file.

    Returns
    -------
    tuple
        A tuple containing a MIMEBase object used to create the email and a string containing the main body text of the
        email.
    """
    mime_email = MIMEMultipart();
    mime_email[constants.EMAIL_SUBJECT_KEY] = '[' + github_payload_dictionary[constants.WIKI_REPOSITORY_KEY][
        constants.WIKI_REPOSITORY_FULL_NAME_KEY] + '] ' + constants.WIKI_NOTIFICATIONS_TEXT;
    mime_email[constants.EMAIL_FROM_KEY] = app_config[constants.CONFIG_EMAIL_FROM_KEY];
    mime_email[constants.EMAIL_TO_KEY] = app_config[constants.CONFIG_EMAIL_TO_KEY];
    mime_email[constants.EMAIL_BCC_KEY] = constants.EMAIL_LIST_DELIMITER.join(email_list);
    main_body_text = constants.HELLO_WIKI_TEXT + \
                     "HED-schema.mediawiki" + \
                     constants.HAS_BEEN_TEXT + \
                     "modified" + \
                     constants.CHECK_OUT_CHANGES_TEXT + \
                     github_payload_dictionary[constants.PUSH_COMMITS_KEY][0][constants.PUSH_COMMITS_URL_KEY] + \
                     constants.PERIOD_TEXT + \
                     "\n\n" + \
                     github_payload_dictionary[constants.PUSH_COMMITS_KEY][0][constants.PUSH_COMMITS_MESSAGE_KEY]

    return mime_email, main_body_text;

def create_hed_schema_email(mime_email, main_body_text):
    """Create HED schema email.
    Parameters
    ----------
    mime_email: MIMEBase object
        A MIMEBase object used to create an email.
    main_body_text: string
        The main body text of the email.
    Returns
    -------
    dictionary
        A dictionary containing resources used to create the email.
    """
    hed_resource_dictionary = {};
    try:
        hed_resource_dictionary = wiki2xml.convert_hed_wiki_2_xml();
        main_body_text = add_hed_xml_attachment_text(main_body_text, hed_resource_dictionary);
        main_body = MIMEText(main_body_text);
        mime_email.attach(main_body);
        hed_xml_attachment = create_hed_xml_attachment(hed_resource_dictionary[constants.HED_XML_LOCATION_KEY]);
        mime_email.attach(hed_xml_attachment);
    finally:
        clean_up_hed_resources(hed_resource_dictionary);
    return hed_resource_dictionary;


def clean_up_hed_resources(hed_resource_dictionary):
    """Cleans up hed resources by deleting files used to generate the email.

    Parameters
    ----------
    hed_resource_dictionary: dictionary
        A dictionary containing resources used to create the email.

    Returns
    -------
    """
    if hed_resource_dictionary:
        if constants.HED_XML_LOCATION_KEY in hed_resource_dictionary:
            delete_file_if_exist(hed_resource_dictionary[constants.HED_XML_LOCATION_KEY]);
        if constants.HED_WIKI_LOCATION_KEY in hed_resource_dictionary:
            delete_file_if_exist(hed_resource_dictionary[constants.HED_WIKI_LOCATION_KEY]);

def push_page_is_hed_schema(github_payload_dictionary):
    """Checks to see if the commited page is the wiki page..

    Parameters
    ----------
    github_payload_dictionary: dictionary
        A dictionary containing a Github push payload.

    Returns
    -------
    boolean
        True if the WIKI page is a HED schema WIKI page.
    """
    return github_payload_dictionary and app_config[constants.CONFIG_HED_WIKI_PAGE_KEY] == \
           github_payload_dictionary[constants.PUSH_COMMITS_KEY][0][constants.PUSH_MODIFIED_KEY][0];


#
def request_is_github_gollum_event(request):
    """Checks to see if the request is a gollum event type.

    Parameters
    ----------
    request: Request object
        A Request object containing a Github payload.

    Returns
    -------
    boolean
        True if the request is a github gollum event. False, if otherwise.
    """
    return request.headers.get(constants.HEADER_CONTENT_TYPE) == constants.JSON_CONTENT_TYPE and \
           request.headers.get(constants.HEADER_EVENT_TYPE) == constants.GOLLUM;


def add_hed_xml_attachment_text(main_body_text, hed_resource_dictionary):
    """Add message body text for HED XML attachment.

    Parameters
    ----------
    main_body_text: string
        The main body text of the email.
    hed_resource_dictionary: dictionary
        A dictionary containing resources used to create the email.

    Returns
    -------
    string
        The main body text of the email with the appended HED attachment text.
    """
    main_body_text += constants.HED_ATTACHMENT_TEXT;
#     main_body_text += constants.HED_VERSION_TEXT + hed_resource_dictionary[constants.HED_XML_TREE_KEY].get(
#         constants.HED_XML_VERSION_KEY);
#     main_body_text += constants.CHANGE_LOG_TEXT + hed_resource_dictionary[constants.HED_CHANGE_LOG_KEY][0];
    return main_body_text;


def create_hed_xml_attachment(hed_xml_file_path):
    """Creates HED XML email attachment file.
    Parameters
    ----------

    hed_xml_file_path: string
        The path to the HED XML file.

    Returns
    -------
    MIMEText object
        A MIMEText object containing the HED XML attachment.
    """
    with open(hed_xml_file_path, 'r', encoding='utf-8') as hed_xml_file:
        hed_xml_string = hed_xml_file.read();
        hed_xml_attachment = MIMEText(hed_xml_string, 'plain', 'utf-8');
        hed_xml_attachment.add_header(constants.CONTENT_DISPOSITION_HEADER,
                                      constants.ATTACHMENT_CONTENT_DISPOSITION_HEADER,
                                      filename=constants.HED_XML_ATTACHMENT_NAME);
    return hed_xml_attachment;


def get_email_list_from_file(email_file_path):
    """Gets a email list from a file. Each email needs to be on a separate line.

    Parameters
    ----------
    email_file_path: string
        The path to a file containing emails.

    Returns
    -------
    list
        A list containing the emails from a file.
    """
    email_list = [];
    with open(email_file_path, 'r') as email_file:
        for email_address in email_file:
            email_list.append(email_address.strip());
    return email_list;


def url_to_file(resource_url, file_path):
    """Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters
    ----------
    resource_url: string
        The URL to the resource.
    file_path: string
        A file path

    Returns
    -------
    """
    url_request = urllib.request.urlopen(resource_url);
    url_data = str(url_request.read(), 'utf-8');
    with open(file_path, 'w', encoding='utf-8') as opened_file:
        opened_file.write(url_data);


def delete_file_if_exist(file_path):
    """Deletes a file if it exists.

    Parameters
    ----------
    file_path: string
        A file path

    Returns
    -------
    """
    if os.path.isfile(file_path):
        os.remove(file_path);
        return True;
    return False;
