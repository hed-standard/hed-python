import json;

EMAILS_SENT = 'Email(s) correctly sent';
EMAIL_SUBJECT_KEY = 'Subject';
EMAIL_FROM_KEY = 'From';
CONFIG_EMAIL_FROM_KEY = 'FROM';
CONFIG_EMAIL_LIST = 'EMAIL_LIST';
CONFIG_EMAIL_TO_KEY = 'TO';
EMAIL_TO_KEY = 'To';
EMAIL_BCC_KEY = 'Bcc';
EMAIL_LIST_DELIMITER = ', ';
EMAIL_SENT_RESPONSE = json.dumps({'success': True, 'message': EMAILS_SENT}), 200, {'ContentType': 'application/json'};
PUSH = 'push';
NO_EMAILS_SENT = 'No email(s) sent. Not in the correct format. Content type needs to be in JSON and X-GitHub-Event' + \
' must be push';
NO_EMAILS_SENT_RESPONSE = json.dumps({'success': True, 'message': NO_EMAILS_SENT}), 200, {
    'ContentType': 'application/json'};
NO_VALID_EMAIL_ADDRESSES_IN_FILE = "Email list file contains no valid addresses."
HEADER_EVENT_TYPE = 'X-GitHub-Event';
HEADER_CONTENT_TYPE = 'content-type';
CONTENT_DISPOSITION_HEADER = 'Content-Disposition';
ATTACHMENT_CONTENT_DISPOSITION_HEADER = 'attachment';
JSON_CONTENT_TYPE = 'application/json';
HED_XML_LOCATION_KEY = 'hed_xml_file_location';
HED_WIKI_LOCATION_KEY = 'hed_wiki_file_location';
CONFIG_HED_WIKI_URL_KEY = 'HED_WIKI_URL'
HED_XML_TREE_KEY = 'hed_xml_tree';
HED_XML_VERSION_KEY = 'version';
HED_CHANGE_LOG_KEY = 'hed_change_log';
HED_WIKI_PAGE_KEY = 'HED_WIKI_PAGE'
WIKI_REPOSITORY_KEY = 'repository';
WIKI_REPOSITORY_FULL_NAME_KEY = 'full_name';
WIKI_NOTIFICATIONS_TEXT = 'Wiki notifications';
HED_ATTACHMENT_TEXT = '\n\n Also, the latest HED schema is attached.';
HED_VERSION_TEXT = '\n\nVersion\n';
CHANGE_LOG_TEXT = '\n\nChange log\n';
HED_XML_ATTACHMENT_NAME = 'HED.xml';
PUSH_COMMITS_KEY = 'commits'
PUSH_MODIFIED_KEY = 'modified'
PUSH_COMMITS_URL_KEY = 'url'
PUSH_COMMITS_MESSAGE_KEY = 'message'
CONFIG_HED_WIKI_PAGE_KEY = 'HED_WIKI_PAGE';
LOCALHOST = 'localhost';
HELLO_WIKI_TEXT = 'Hello,\nThe wiki page ';
WIKI_TITLE_KEY = 'title';
HAS_BEEN_TEXT = ' has been ';
CHECK_OUT_CHANGES_TEXT = '. Please checkout the changes at ';
SOURCE_MEDIAWIKI_TEXT = 'Media wiki source file located at '
NO_CHANGES_DETECTED_EMAIL = 'No relevant changes found in most recent push event.'
WIKI_HTML_URL_KEY = 'html_url';
PERIOD_TEXT = '.';
WIKI_ACTION_KEY = 'action';


def generate_exception_response(ex):
    return json.dumps({'success': False, 'message': ex}), 500, {'ContentType': 'application/json'};
