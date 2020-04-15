import os;
import json;
import tempfile;
import xlrd;
import traceback;
from flask import jsonify, Response;
from werkzeug.utils import secure_filename;
from hedvalidation.hed_input_reader import HedInputReader;
from flask import current_app;
from logging.handlers import RotatingFileHandler;
from logging import ERROR;
from hedvalidation.hed_dictionary import HedDictionary;
from webinterface.constants.other import file_extension_constants, spreadsheet_constants, type_constants;
from webinterface.constants.error import error_constants;
from webinterface.constants.form import python_form_constants, validation_arg_constants, js_form_constants, \
    html_form_constants;

app_config = current_app.config;
UPLOAD_DIRECTORY_KEY = 'UPLOAD_FOLDER';


def find_hed_version_in_file(form_request_object):
    """Finds the version number in a HED XML other.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing the version number information.

    """
    hed_info = {};
    try:
        if hed_file_present_in_form(form_request_object):
            hed_file = form_request_object.files[python_form_constants.HED_FILE];
            hed_file_path = save_hed_to_upload_folder(hed_file);
            hed_info[js_form_constants.HED_VERSION] = HedDictionary.get_hed_xml_version(hed_file_path);
    except:
        hed_info[error_constants.ERROR_KEY] = traceback.format_exc();
    return hed_info;


def find_major_hed_versions():
    """Finds the major HED versions that are kept on the server.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing inforamtion about the major HED versions.

    """
    hed_info = {};
    try:
        hed_info[js_form_constants.HED_MAJOR_VERSIONS] = HedInputReader.get_all_hed_versions();
    except:
        hed_info[error_constants.ERROR_KEY] = traceback.format_exc();
    return hed_info;


def find_worksheets_info(form_request_object):
    """Finds the info related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing information related to the Excel worksheets.

    """
    workbook_file_path = '';
    worksheets_info = {};
    try:
        worksheets_info = _initialize_worksheets_info_dictionary();
        if spreadsheet_present_in_form(form_request_object):
            workbook_file = form_request_object.files[python_form_constants.SPREADSHEET_FILE];
            workbook_file_path = save_spreadsheet_to_upload_folder(workbook_file);
            if workbook_file_path:
                worksheets_info = _populate_worksheets_info_dictionary(worksheets_info, workbook_file_path);
    except:
        worksheets_info[error_constants.ERROR_KEY] = traceback.format_exc();
    finally:
        delete_file_if_it_exist(workbook_file_path);
    return worksheets_info;


def find_spreadsheet_columns_info(form_request_object):
    """Finds the info associated with the spreadsheet columns.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary populated with information related to the spreadsheet columns.
    """
    spreadsheet_file_path = '';
    try:
        spreadsheet_columns_info = _initialize_spreadsheet_columns_info_dictionary();
        if spreadsheet_present_in_form(form_request_object):
            spreadsheet_file = form_request_object.files[python_form_constants.SPREADSHEET_FILE];
            spreadsheet_file_path = save_spreadsheet_to_upload_folder(spreadsheet_file);
            if spreadsheet_file_path and worksheet_name_present_in_form(form_request_object):
                worksheet_name = form_request_object.form[python_form_constants.WORKSHEET_NAME];
                spreadsheet_columns_info = _populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info,
                                                                                         spreadsheet_file_path,
                                                                                         worksheet_name);
            else:
                spreadsheet_columns_info = _populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info,
                                                                                         spreadsheet_file_path);
    except:
        spreadsheet_columns_info[error_constants.ERROR_KEY] = traceback.format_exc();
    finally:
        delete_file_if_it_exist(spreadsheet_file_path);
    return spreadsheet_columns_info;


def report_spreadsheet_validation_status(form_request_object):
    """Reports the spreadsheet validation status.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    validation_status = {};
    spreadsheet_file_path = '';
    hed_file_path = '';
    try:
        spreadsheet_file_path, hed_file_path = _get_uploaded_file_paths_from_forms(form_request_object);
        original_spreadsheet_filename = _get_original_spreadsheet_filename(form_request_object);
        validation_input_arguments = _generate_input_arguments_from_validation_form(
            form_request_object, spreadsheet_file_path, hed_file_path);
        hed_input_reader = validate_spreadsheet(validation_input_arguments);
        tag_validator = hed_input_reader.get_tag_validator();
        validation_issues = hed_input_reader.get_validation_issues();
        validation_status[js_form_constants.DOWNLOAD_FILE] = _save_validation_issues_to_file_in_upload_folder(
            original_spreadsheet_filename, validation_issues,
            validation_input_arguments[validation_arg_constants.WORKSHEET_NAME]);
        validation_status[js_form_constants.ISSUE_COUNT] = tag_validator.get_issue_count();
        validation_status[js_form_constants.ERROR_COUNT] = tag_validator.get_error_count();
        validation_status[js_form_constants.WARNING_COUNT] = tag_validator.get_warning_count();
    except:
        validation_status[error_constants.ERROR_KEY] = traceback.format_exc();
    finally:
        delete_file_if_it_exist(spreadsheet_file_path);
        delete_file_if_it_exist(hed_file_path);
    return validation_status;

def report_EEG_events_validation_status(request):
    """Reports validation status of hed strings associated with EEG events
       received from EEGLAB plugin HEDTools

    Parameters
    ----------
    request: Request object
        A Request object containing user data submitted by HEDTools.
        Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    string
        A serialized JSON string containing information related to the hed strings validation result. If the validation fails then a
        500 error message is returned.
    """
    validation_status = {}

    # Parse uploaded data
    form_data = request.form
    check_for_warnings = form_data["check_for_warnings"] == '1' if "check_for_warnings" in form_data else False
    # if hed_xml_file was submitted, it's accessed by request.files, otherwise empty
    if "hed_xml_file" in request.files and _get_file_extension(request.files["hed_xml_file"].filename) == "xml":
        hed_xml_file = _save_hed_to_upload_folder_if_present(request.files["hed_xml_file"])
    else:
        hed_xml_file = ''

    try:
        # parse hed_strings from json
        hed_strings = json.loads(form_data["hed_strings"])
        hed_strings = hed_strings["hed_strings"]
        hed_input_reader = HedInputReader(hed_strings, check_for_warnings=check_for_warnings, hed_xml_file=hed_xml_file)
        issues = hed_input_reader.get_validation_issues()

        # Prepare response
        validation_status["issues"] = issues # expect issues to be a string array, each array is in form "Issue in event _: issue"
    except:
        validation_status[error_constants.ERROR_KEY] = traceback.format_exc()
    finally:
        delete_file_if_it_exist(hed_xml_file);

    return validation_status

def _get_uploaded_file_paths_from_forms(form_request_object):
    """Gets the other paths of the uploaded files in the form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    tuple
        A tuple containing the other paths. The two other paths are for the spreadsheet and a optional HED XML other.
    """
    spreadsheet_file_path = '';
    hed_file_path = '';
    if spreadsheet_present_in_form(form_request_object) and _file_has_valid_extension(
            form_request_object.files[js_form_constants.SPREADSHEET_FILE],
            spreadsheet_constants.SPREADSHEET_FILE_EXTENSIONS):
        spreadsheet_file_path = save_spreadsheet_to_upload_folder(
            form_request_object.files[js_form_constants.SPREADSHEET_FILE]);
    if hed_present_in_form(form_request_object) and _file_has_valid_extension(
            form_request_object.files[js_form_constants.HED_FILE], spreadsheet_constants.HED_FILE_EXTENSIONS):
        hed_file_path = _save_hed_to_upload_folder_if_present(
            form_request_object.files[js_form_constants.HED_FILE]);
    return spreadsheet_file_path, hed_file_path;


def _get_original_spreadsheet_filename(form_request_object):
    """Gets the original name of the spreadsheet.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        The name of the spreadsheet.
    """
    if spreadsheet_present_in_form(form_request_object) and _file_has_valid_extension(
            form_request_object.files[js_form_constants.SPREADSHEET_FILE],
            spreadsheet_constants.SPREADSHEET_FILE_EXTENSIONS):
        return form_request_object.files[js_form_constants.SPREADSHEET_FILE].filename;
    return '';


def generate_download_file_response(download_file_name):
    """Generates a download other response.

    Parameters
    ----------
    download_file_name: string
        The download other name.

    Returns
    -------
    response object
        A response object containing the download other.

    """
    try:
        def generate():
            full_filename = os.path.join(app_config[UPLOAD_DIRECTORY_KEY], download_file_name)
            with open(full_filename, 'r', encoding='utf-8') as download_file:
                for line in download_file:
                    yield line;
            delete_file_if_it_exist(full_filename);

        return Response(generate(), mimetype='text/plain; charset=utf-8',
                        headers={'Content-Disposition': "attachment; filename=%s" % download_file_name});
    except:
        return traceback.format_exc();


def handle_http_error(error_code, error_message):
    """Handles an http error.

    Parameters
    ----------
    error_code: string
        The code associated with the error.
    error_message: string
        The message associated with the error.

    Returns
    -------
    boolean
        A tuple containing a HTTP response object and a code.

    """
    current_app.logger.error(error_message);
    return jsonify(message=error_message), error_code;


def setup_logging():
    """Sets up the current_application logging. If the log directory does not exist then there will be no logging.

    """
    if not current_app.debug and os.path.exists(current_app.config['LOG_DIRECTORY']):
        file_handler = RotatingFileHandler(current_app.config['LOG_FILE'], maxBytes=10 * 1024 * 1024, backupCount=5);
        file_handler.setLevel(ERROR);
        current_app.logger.addHandler(file_handler);


def create_upload_directory(upload_directory):
    """Creates the upload directory.

    """
    _create_folder_if_needed(upload_directory);


def _file_extension_is_valid(filename, accepted_file_extensions):
    """Checks the other extension against a list of accepted ones.

    Parameters
    ----------
    filename: string
        The name of the other.

    accepted_file_extensions: list
        A list containing all of the accepted other extensions.

    Returns
    -------
    boolean
        True if the other has a valid other extension.

    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in accepted_file_extensions;


def _save_hed_to_upload_folder_if_present(hed_file_object):
    """Save a HED XML other to the upload folder.

    Parameters
    ----------
    hed_file_object: File object
        A other object that points to a HED XML other that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the HED XML other that was saved to the upload folder.

    """
    hed_file_path = '';
    if hed_file_object.filename:
        hed_file_extension = '.' + _get_file_extension(hed_file_object.filename);
        hed_file_path = _save_file_to_upload_folder(hed_file_object, hed_file_extension);
    return hed_file_path;


def _save_validation_issues_to_file_in_upload_folder(spreadsheet_filename, validation_issues, worksheet_name=''):
    """Saves the validation issues found to a other in the upload folder.

    Parameters
    ----------
    spreadsheet_filename: string
        The name to the spreadsheet.
    worksheet_name: string
        The name of the spreadsheet worksheet.
    validation_issues: string
        A string containing the validation issues.

    Returns
    -------
    string
        The name of the validation output other.

    """
    validation_issues_filename = _generate_spreadsheet_validation_filename(spreadsheet_filename, worksheet_name);
    validation_issues_file_path = os.path.join(current_app.config[UPLOAD_DIRECTORY_KEY], validation_issues_filename);
    with open(validation_issues_file_path, 'w', encoding='utf-8') as validation_issues_file:
        validation_issues_file.write(validation_issues);
    return validation_issues_filename;


def _file_has_valid_extension(file_object, accepted_file_extensions):
    """Checks to see if a other has a valid other extension.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other.
    accepted_file_extensions: list
        A list of other extensions that are accepted

    Returns
    -------
    boolean
        True if the other has a valid other extension.

    """
    return file_object and _file_extension_is_valid(file_object.filename, accepted_file_extensions);


def _generate_spreadsheet_validation_filename(spreadsheet_filename, worksheet_name=''):
    """Generates a filename for the attachment that will contain the spreadsheet validation issues.

    Parameters
    ----------
    spreadsheet_filename: string
        The name of the spreadsheet other.
    worksheet_name: string
        The name of the spreadsheet worksheet.
    Returns
    -------
    string
        The name of the attachment other containing the validation issues.
    """
    if worksheet_name:
        return file_extension_constants.VALIDATION_OUTPUT_FILE_PREFIX + \
               secure_filename(spreadsheet_filename).rsplit('.')[0] + '_' + \
               secure_filename(worksheet_name) + file_extension_constants.TEXT_EXTENSION;
    return file_extension_constants.VALIDATION_OUTPUT_FILE_PREFIX + secure_filename(spreadsheet_filename).rsplit('.')[
        0] + file_extension_constants.TEXT_EXTENSION;


def _get_file_extension(file_name_or_path):
    """Get the other extension from the specified filename. This can be the full path or just the name of the other.

       Parameters
       ----------
       file_name_or_path: string
           The name or full path of a other.

       Returns
       -------
       string
           The extension of the other.
       """
    return secure_filename(file_name_or_path).rsplit('.')[-1];


def _generate_input_arguments_from_validation_form(form_request_object, spreadsheet_file_path,
                                                   hed_file_path):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.
    spreadsheet_file_path: string
        The path to the workbook other.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying validation function.
    """
    validation_input_arguments = {};
    validation_input_arguments[validation_arg_constants.SPREADSHEET_PATH] = spreadsheet_file_path;
    validation_input_arguments[validation_arg_constants.HED_XML_PATH] = _get_hed_path_from_validation_form(
        form_request_object, hed_file_path);
    validation_input_arguments[validation_arg_constants.TAG_COLUMNS] = \
        _convert_other_tag_columns_to_list(form_request_object.form[html_form_constants.TAG_COLUMNS]);
    validation_input_arguments[validation_arg_constants.REQUIRED_TAG_COLUMNS] = \
        _get_specific_tag_columns_from_validation_form(form_request_object);
    validation_input_arguments[validation_arg_constants.WORKSHEET_NAME] = _get_optional_validation_form_field(
        form_request_object, html_form_constants.WORKSHEET_NAME, type_constants.STRING);
    validation_input_arguments[validation_arg_constants.HAS_COLUMN_NAMES] = _get_optional_validation_form_field(
        form_request_object, html_form_constants.HAS_COLUMN_NAMES, type_constants.BOOLEAN);
    validation_input_arguments[validation_arg_constants.CHECK_FOR_WARNINGS] = _get_optional_validation_form_field(
        form_request_object, html_form_constants.CHECK_FOR_WARNINGS, type_constants.BOOLEAN);
    return validation_input_arguments;


def _get_hed_path_from_validation_form(form_request_object, hed_file_path):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.
    hed_file_path: string
        The path to the HED XML other.

    Returns
    -------
    string
        The HED XML other path.
    """
    if _hed_version_in_form(form_request_object) and \
            (form_request_object.form[
                 html_form_constants.HED_VERSION] != spreadsheet_constants.OTHER_HED_VERSION_OPTION or not hed_file_path):
        return HedInputReader.get_path_from_hed_version(form_request_object.form['hed-version']);
    return hed_file_path;


def _hed_version_in_form(form_request_object):
    """Checks to see if the hed version is in the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if the hed version is in the validation form. False, if otherwise.
    """
    return html_form_constants.HED_VERSION in form_request_object.form;


def _convert_other_tag_columns_to_list(other_tag_columns):
    """Gets the other tag columns from the validation form.

    Parameters
    ----------
    other_tag_columns: str
        A string containing the other tag columns.

    Returns
    -------
    list
        A list containing the other tag columns.
    """
    if other_tag_columns:
        return list(map(int, other_tag_columns.split(',')));
    return [];


def _get_specific_tag_columns_from_validation_form(form_request_object):
    """Gets the specific tag columns from the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary containing the required tag columns. The keys will be the column numbers and the values will be
        the name of the column.
    """
    required_tag_columns = {};
    for tag_column_name in spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES:
        form_tag_column_name = tag_column_name.lower() + html_form_constants.COLUMN_POSTFIX;
        if form_tag_column_name in form_request_object.form:
            tag_column_name_index = form_request_object.form[form_tag_column_name].strip();
            if tag_column_name_index:
                tag_column_name_index = int(tag_column_name_index);
                required_tag_columns[tag_column_name_index] = tag_column_name;
    return required_tag_columns;


def _get_optional_validation_form_field(validation_form_request_object, form_field_name, type=''):
    """Gets the specified optional form field if present.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.
    form_field_name: string
        The name of the optional form field.

    Returns
    -------
    boolean or string
        A boolean or string value based on the form field type.

    """
    if type == type_constants.BOOLEAN:
        form_field_value = False;
        if form_field_name in validation_form_request_object.form:
            form_field_value = True;
    elif type == type_constants.STRING:
        form_field_value = '';
        if form_field_name in validation_form_request_object.form:
            form_field_value = validation_form_request_object.form[form_field_name];
    return form_field_value;


def delete_file_if_it_exist(file_path):
    """Deletes a other if it exist.

    Parameters
    ----------
    file_path: string
        The path to a other.

    Returns
    -------
    boolean
        True if the other exist and was deleted.
    """
    if os.path.isfile(file_path):
        os.remove(file_path);
        return True;
    return False;


def _create_folder_if_needed(folder_path):
    """Checks to see if the upload folder exist. If it doesn't then it creates it.

    Parameters
    ----------
    folder_path: string
        The path of the folder that you want to create.

    Returns
    -------
    boolean
        True if the upload folder needed to be created, False if otherwise.

    """
    folder_needed_to_be_created = False;
    if not os.path.exists(folder_path):
        os.makedirs(folder_path);
        folder_needed_to_be_created = True;
    return folder_needed_to_be_created;


def _save_file_to_upload_folder(file_object, file_suffix=""):
    """Save a other to the upload folder.

    Parameters
    ----------
    file_object: File object
        A other object that points to a other that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the other that was saved to the temporary folder.

    """
    temporary_upload_file = tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False, \
                                                        dir=current_app.config[UPLOAD_DIRECTORY_KEY]);
    _copy_file_line_by_line(file_object, temporary_upload_file);
    return temporary_upload_file.name;


def _copy_file_line_by_line(file_object_1, file_object_2):
    """Copy the contents of one other to the other other.

    Parameters
    ----------
    file_object_1: File object
        A other object that points to a other that will be copied.
    file_object_2: File object
        A other object that points to a other that will copy the other other.

    Returns
    -------
    boolean
       True if the other was copied successfully, False if it wasn't.

    """
    try:
        for line in file_object_1:
            file_object_2.write(line);
        return True;
    except:
        return False;


def validate_spreadsheet(validation_arguments):
    """Validates the spreadsheet.

    Parameters
    ----------
    validation_arguments: dictionary
        A dictionary containing the arguments for the validation function.

    Returns
    -------
    HedInputReader object
        A HedInputReader object containing the validation results.
    """
    return HedInputReader(validation_arguments[validation_arg_constants.SPREADSHEET_PATH],
                          tag_columns=validation_arguments[validation_arg_constants.TAG_COLUMNS],
                          has_column_names=validation_arguments[validation_arg_constants.HAS_COLUMN_NAMES],
                          required_tag_columns=validation_arguments[validation_arg_constants.REQUIRED_TAG_COLUMNS],
                          worksheet_name=validation_arguments[validation_arg_constants.WORKSHEET_NAME],
                          check_for_warnings=validation_arguments[validation_arg_constants.CHECK_FOR_WARNINGS],
                          hed_xml_file=validation_arguments[validation_arg_constants.HED_XML_PATH]);


def spreadsheet_present_in_form(validation_form_request_object):
    """Checks to see if a spreadsheet other is present in a request object from validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a spreadsheet other is present in a request object from the validation form.

    """
    return js_form_constants.SPREADSHEET_FILE in validation_form_request_object.files;


def hed_present_in_form(validation_form_request_object):
    """Checks to see if a HED XML other is present in a request object from validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the validation form.

    """
    return js_form_constants.HED_FILE in validation_form_request_object.files;


def hed_file_present_in_form(validation_form_request_object):
    """Checks to see if a HED XML other is present in a request object from validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the validation form.

    """
    return python_form_constants.HED_FILE in validation_form_request_object.files;


def _initialize_worksheets_info_dictionary():
    """Initializes a dictionary that will hold information related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------

    Returns
    -------
    dictionary
        A dictionary that will hold information related to the Excel worksheets.

    """
    worksheets_info = {js_form_constants.WORKSHEET_NAMES: [], js_form_constants.COLUMN_NAMES: [],
                       js_form_constants.TAG_COLUMN_INDICES: []};
    return worksheets_info;


def _initialize_spreadsheet_columns_info_dictionary():
    """Initializes a dictionary that will hold information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    dictionary
        A dictionary that will hold information related to the spreadsheet columns.

    """
    worksheet_columns_info = {js_form_constants.COLUMN_NAMES: [], js_form_constants.TAG_COLUMN_INDICES: []};
    return worksheet_columns_info;


def _populate_worksheets_info_dictionary(worksheets_info, spreadsheet_file_path):
    """Populate dictionary with information related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------
    worksheets_info: dictionary
        A dictionary that contains information related to the Excel worksheets.
    spreadsheet_file_path: string
        The full path to an Excel workbook other.

    Returns
    -------
    dictionary
        A dictionary populated with information related to the Excel worksheets.

    """
    worksheets_info[js_form_constants.WORKSHEET_NAMES] = _get_excel_worksheet_names(spreadsheet_file_path);
    worksheets_info[js_form_constants.COLUMN_NAMES] = \
        _get_worksheet_column_names(spreadsheet_file_path, worksheets_info[js_form_constants.WORKSHEET_NAMES][0]);
    worksheets_info[js_form_constants.TAG_COLUMN_INDICES] = _get_spreadsheet_other_tag_column_indices(
        worksheets_info[js_form_constants.COLUMN_NAMES]);
    worksheets_info[js_form_constants.REQUIRED_TAG_COLUMN_INDICES] = \
        _get_spreadsheet_specific_tag_column_indices(worksheets_info[js_form_constants.COLUMN_NAMES]);
    return worksheets_info;


def _populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info, spreadsheet_file_path,
                                                  worksheet_name=''):
    """Populate dictionary with information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------
    spreadsheet_columns_info: dictionary
        A dictionary that contains information related to the spreadsheet column.
    spreadsheet_file_path: string
        The full path to a spreadsheet other.
    worksheet_name: string
        The name of an Excel worksheet.

    Returns
    -------
    dictionary
        A dictionary populated with information related to the spreadsheet columns.

    """
    if worksheet_name:
        spreadsheet_columns_info[js_form_constants.COLUMN_NAMES] = _get_worksheet_column_names(
            spreadsheet_file_path,
            worksheet_name);
    else:
        column_delimiter = _get_column_delimiter_based_on_file_extension(spreadsheet_file_path);
        spreadsheet_columns_info[js_form_constants.COLUMN_NAMES] = _get_text_file_column_names(
            spreadsheet_file_path,
            column_delimiter);
    spreadsheet_columns_info[js_form_constants.TAG_COLUMN_INDICES] = \
        _get_spreadsheet_other_tag_column_indices(spreadsheet_columns_info[js_form_constants.COLUMN_NAMES]);
    spreadsheet_columns_info[js_form_constants.REQUIRED_TAG_COLUMN_INDICES] = \
        _get_spreadsheet_specific_tag_column_indices(spreadsheet_columns_info[js_form_constants.COLUMN_NAMES]);
    return spreadsheet_columns_info;


def _get_text_file_column_names(text_file_path, column_delimiter):
    """Gets the text spreadsheet column names.

    Parameters
    ----------
    text_file_path: string
        The path to a text other.
    column_delimiter: string
        The spreadsheet column delimiter.

    Returns
    -------
    string
        The spreadsheet column delimiter based on the other extension.

    """
    with open(text_file_path, 'r', encoding='utf-8') as opened_text_file:
        first_line = opened_text_file.readline();
        text_file_columns = first_line.split(column_delimiter);
    return text_file_columns;


def _get_column_delimiter_based_on_file_extension(file_name_or_path):
    """Gets the spreadsheet column delimiter based on the other extension.

    Parameters
    ----------
    file_name_or_path: string
        A other name or path.

    Returns
    -------
    string
        The spreadsheet column delimiter based on the other extension.

    """
    column_delimiter = '';
    file_extension = _get_file_extension(file_name_or_path);
    if file_extension in spreadsheet_constants.SPREADSHEET_FILE_EXTENSION_TO_DELIMITER_DICTIONARY:
        column_delimiter = spreadsheet_constants.SPREADSHEET_FILE_EXTENSION_TO_DELIMITER_DICTIONARY.get(file_extension);
    return column_delimiter;


def worksheet_name_present_in_form(validation_form_request_object):
    """Checks to see if a worksheet name is present in a request object from the validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a worksheet name is present in a request object from the validation form.

    """
    return python_form_constants.WORKSHEET_NAME in validation_form_request_object.form;


def save_spreadsheet_to_upload_folder(spreadsheet_file_object):
    """Save an spreadsheet other to the upload folder.

    Parameters
    ----------
    spreadsheet_file_object: File object
        A other object that points to a spreadsheet that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the spreadsheet that was saved to the upload folder.

    """
    spreadsheet_file_extension = '.' + _get_file_extension(spreadsheet_file_object.filename);
    spreadsheet_file_path = _save_file_to_upload_folder(spreadsheet_file_object, spreadsheet_file_extension);
    return spreadsheet_file_path;


def save_hed_to_upload_folder(hed_file_object):
    """Save an spreadsheet other to the upload folder.

    Parameters
    ----------
    hed_file_object: File object
        A other object that points to a HED XML other that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the HED XML other that was saved to the upload folder.

    """
    hed_file_extension = '.' + _get_file_extension(hed_file_object.filename);
    hed_file_path = _save_file_to_upload_folder(hed_file_object, hed_file_extension);
    return hed_file_path;


def _get_excel_worksheet_names(workbook_file_path):
    """Gets the worksheet names in an Excel workbook.

    Parameters
    ----------
    workbook_file_path: string
        The full path to an Excel workbook other.

    Returns
    -------
    list
        A list containing the worksheet names in an Excel workbook.

    """
    opened_workbook_file = xlrd.open_workbook(workbook_file_path);
    worksheet_names = opened_workbook_file.sheet_names();
    return worksheet_names;


def _get_spreadsheet_other_tag_column_indices(column_names):
    """Gets the other tag column indices in a spreadsheet. The indices found will be one-based.

    Parameters
    ----------
    column_names: list
        A list containing the column names in a spreadsheet.

    Returns
    -------
    list
        A list containing the tag column indices found in a spreadsheet.

    """
    tag_column_indices = [];
    for tag_column_name in spreadsheet_constants.OTHER_TAG_COLUMN_NAMES:
        found_indices = _find_all_str_indices_in_list(column_names, tag_column_name);
        if found_indices:
            tag_column_indices.extend(found_indices);
    return tag_column_indices;


def _get_spreadsheet_specific_tag_column_indices(column_names):
    """Gets the required tag column indices in a spreadsheet. The indices found will be one-based.

    Parameters
    ----------
    column_names: list
        A list containing the column names in a spreadsheet.

    Returns
    -------
    dictionary
        A dictionary containing the required tag column indices found in a spreadsheet.

    """
    specific_tag_column_indices = {};
    specific_tag_column_names = spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES_DICTIONARY.keys();
    for specific_tag_column_name in specific_tag_column_names:
        alternative_specific_tag_column_names = spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES_DICTIONARY[
            specific_tag_column_name];
        for alternative_specific_tag_column_name in alternative_specific_tag_column_names:
            specific_tag_column_index = _find_str_index_in_list(column_names, alternative_specific_tag_column_name);
            if specific_tag_column_index != -1:
                specific_tag_column_indices[specific_tag_column_name] = specific_tag_column_index;
    return specific_tag_column_indices;


def _find_all_str_indices_in_list(list_of_strs, str_value):
    """Find the indices of a string value in a list.

    Parameters
    ----------
    list_of_strs: list
        A list containing strings.
    str_value: string
        A string value.

    Returns
    -------
    list
        A list containing all of the indices where a string value occurs in a string list.

    """
    return [index + 1 for index, value in enumerate(list_of_strs) if
            value.lower().replace(' ', '') == str_value.lower().replace(' ', '')];


def _find_str_index_in_list(list_of_strs, str_value):
    """Find the index of a string value in a list.

    Parameters
    ----------
    list_of_strs: list
        A list containing strings.
    str_value: string
        A string value.

    Returns
    -------
    integer
        An positive integer if the string value was found in the list. A -1 is returned if the string value was not
        found.

    """
    try:
        return [s.lower().replace(' ', '') for s in list_of_strs].index(str_value.lower().replace(' ', '')) + 1;
    except ValueError:
        return -1;


def _get_worksheet_column_names(workbook_file_path, worksheet_name):
    """Get the worksheet columns in a Excel workbook.

    Parameters
    ----------
    workbook_file_path : string
        The full path to an Excel workbook other.
    worksheet_name : string
        The name of an Excel worksheet.

    Returns
    -------
    list
        A list containing the worksheet columns in an Excel workbook.

    """
    opened_workbook_file = xlrd.open_workbook(workbook_file_path);
    opened_worksheet = opened_workbook_file.sheet_by_name(worksheet_name);
    worksheet_column_names = [opened_worksheet.cell(0, col_index).value for col_index in range(opened_worksheet.ncols)];
    return worksheet_column_names;
