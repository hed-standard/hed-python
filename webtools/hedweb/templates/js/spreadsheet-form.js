const EXCEL_FILE_EXTENSIONS = ['xlsx', 'xls'];
const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];
const VALID_FILE_EXTENSIONS = ['xlsx', 'xls', 'tsv', 'txt']

$(function () {
    prepareForm();
});

$('#has_column_names').on('change', function() {
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0];
    let worksheetName = $('#worksheet_name option:selected').text();
    if ($("#has_column_names").is(':checked')) {
            setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, true, false, true)
        } else  {
            setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, false, false, true)
        }
    }
);

/**
 * Spreadsheet event handler function. Checks if the file uploaded has a valid spreadsheet extension.
 */
$('#spreadsheet_file').on('change', function () {
    let spreadsheet = $('#spreadsheet_file');
    let spreadsheetPath = spreadsheet.val();
    let spreadsheetFile = spreadsheet[0].files[0];
    clearFlashMessages();
    removeColumnInfo(true)
    if (!fileHasValidExtension(spreadsheetPath, VALID_FILE_EXTENSIONS)) {
        clearForm();
        flashMessageOnScreen('Upload a valid spreadsheet (.xlsx, .xls, .tsv, .txt)', 'error', 'spreadsheet_flash');
        return
    }
    updateFileLabel(spreadsheetPath, '#spreadsheet_display_name');
    let worksheetName = undefined
    if (fileHasValidExtension(spreadsheetPath, EXCEL_FILE_EXTENSIONS)) {
        worksheetName = $('#worksheet_name option:selected').text();
        $('#worksheet_select').show();;
    }
    else if (fileHasValidExtension(spreadsheetPath, TEXT_FILE_EXTENSIONS)) {
        $('#worksheet_name').empty();
        $('#worksheet_select').hide();
    }
    if ($("#has_column_names").is(':checked')) {
        setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, true, true, true)
    } else {
        setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, false, true, true)
    }
});

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#spreadsheet_submit').on('click', function () {
    if (fileIsSpecified('#spreadsheet_file', 'spreadsheet_flash', 'Spreadsheet is not specified.') &&
        schemaSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Gets the information associated with the Excel worksheet that was newly selected. This information contains
 * the names of the columns and column indices that contain HED tags.
 */
$('#worksheet_name').on('change', function () {
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0];
    let worksheetName = $('#worksheet_name option:selected').text();
    let hasColumnNames = $("#has_column_names").is(':checked')
    clearFlashMessages();
    setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, hasColumnNames,false, true);
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#spreadsheet_form')[0].reset();
    $('#spreadsheet_display_name').text('');
    $('#worksheet_name').empty();
    hideColumnInfo(true);
    hideWorksheetSelect()
    hideOtherSchemaVersionFileUpload()
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFlashMessages() {
    clearColumnInfoFlashMessages();
    clearSchemaSelectFlashMessages();
    flashMessageOnScreen('', 'success', 'spreadsheet_flash');
    flashMessageOnScreen('', 'success', 'spreadsheet_submit_flash');
}

/**
 * Hides  worksheet select section in the form.
 */
function hideWorksheetSelect() {
    $('#worksheet_select').hide();
}

/**
 * Populate the Excel worksheet select box.
 * @param {Array} worksheetNames - An array containing the Excel worksheet names.
 */
function populateWorksheetDropdown(worksheetNames) {
    if (Array.isArray(worksheetNames) && worksheetNames.length > 0) {
        let worksheetDropdown = $('#worksheet_name');
        $('#worksheet_select').show();
        worksheetDropdown.empty();
        for (let i = 0; i < worksheetNames.length; i++) {
            $('#worksheet_name').append(new Option(worksheetNames[i], worksheetNames[i]) );
        }
    }
}

/**
 * Prepare the spreadsheet form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getSchemaVersions()
    hideColumnInfo(true);
    hideWorksheetSelect();
    hideOtherSchemaVersionFileUpload();
}


/**
 * Show the worksheet select section.
 */
function showWorksheetSelect() {
    $('#worksheet_select').show();
}


/**
 * Submit the form and return the results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let spreadsheetForm = document.getElementById("spreadsheet_form");
    let formData = new FormData(spreadsheetForm);
    let worksheetName = $('#worksheet_select option:selected').text();
    formData.append('worksheet_selected', worksheetName)
    let prefix = 'issues';
    if(worksheetName) {
        prefix = prefix + '_worksheet_' + worksheetName;
    }
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0].name;
    let display_name = convertToResultsName(spreadsheetFile, prefix)
    clearFlashMessages();
    flashMessageOnScreen('Worksheet is being validated ...', 'success',
        'spreadsheet_submit_flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.spreadsheet_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'spreadsheet_submit_flash')
            },
            error: function (download, status, xhr) {
                getResponseFailure(download, xhr, display_name, 'spreadsheet_submit_flash')
            }
        }
    )
}
