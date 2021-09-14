const EXCEL_FILE_EXTENSIONS = ['xlsx', 'xls'];
const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];
const VALID_FILE_EXTENSIONS = ['xlsx', 'xls', 'tsv', 'txt']

$(function () {
    prepareForm();
});

$('#has_column_names').on('change', function() {
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0];
    let worksheetName = $('#worksheet_name option:selected').text();
    let hasColumnNames = $("#has_column_names").is(':checked')
    setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, hasColumnNames, "show_indices")
})

/**
 * Spreadsheet event handler function. Checks if the file uploaded has a valid spreadsheet extension.
 */
$('#spreadsheet_file').on('change', function () {
    let spreadsheet = $('#spreadsheet_file');
    let spreadsheetPath = spreadsheet.val();
    let spreadsheetFile = spreadsheet[0].files[0];
    clearFlashMessages();
    removeColumnInfo("show_indices")
    if (!fileHasValidExtension(spreadsheetPath, VALID_FILE_EXTENSIONS)) {
        clearForm();
        flashMessageOnScreen('Upload a valid spreadsheet (.xlsx, .tsv, .txt)', 'error', 'spreadsheet_flash');
        return
    }
    updateFileLabel(spreadsheetPath, '#spreadsheet_display_name');
    let hasColumnNames = $("#has_column_names").is(':checked')
    let worksheetNames = setColumnsInfo(spreadsheetFile, 'spreadsheet_flash',  undefined, hasColumnNames, "show_indices")
    if (fileHasValidExtension(spreadsheetPath, EXCEL_FILE_EXTENSIONS)) {
        populateWorksheetDropdown(worksheetNames);
    } else if (fileHasValidExtension(spreadsheetPath, TEXT_FILE_EXTENSIONS)) {
        $('#worksheet_name').empty();
        $('#worksheet_select').hide();
    }
})

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
 * Gets the information associated with the Excel sheet_name that was newly selected. This information contains
 * the names of the columns and column indices that contain HED tags.
 */
$('#worksheet_name').on('change', function () {
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0];
    let worksheetName = $('#worksheet_name option:selected').text();
    let hasColumnNames = $("#has_column_names").is(':checked')
    clearFlashMessages();
    setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, hasColumnNames, "show_indices");
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#spreadsheet_form')[0].reset();
    $('#spreadsheet_display_name').text('');
    $('#worksheet_name').empty();
    $('#worksheet_select').hide();
    hideColumnInfo("show_indices");
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
 * Populate the Excel sheet_name select box.
 * @param {Array} worksheetNames - An array containing the Excel sheet_name names.
 */
function populateWorksheetDropdown(worksheetNames) {
    if (Array.isArray(worksheetNames) && worksheetNames.length > 0) {
        $('#worksheet_select').show();
        $('#worksheet_name').empty();
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
    flashMessageOnScreen('Spreadsheet is being processed ...', 'success',
        'spreadsheet_submit_flash')
    let isExcel = fileHasValidExtension(spreadsheetFile, EXCEL_FILE_EXTENSIONS) &&
            !$("#validate").prop("checked");
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.spreadsheet_results')}}",
        data: formData,
        contentType: false,
        processData: false,
        xhr: function () {
            let xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function () {
                if (xhr.readyState == 2) {
                    if (xhr.status == 200 && isExcel) {
                        xhr.responseType = "blob";
                    } else {
                        xhr.responseType = "text";
                    }
                }
            };
            return xhr;
        },
        success: function (data, status, xqXHR) {
            getResponseSuccess(data, xqXHR, display_name, 'spreadsheet_submit_flash')
        },
        error: function (xhr, status, errorThrown) {
            getResponseFailure(xhr, status, errorThrown, display_name, 'spreadsheet_submit_flash')
        }
    })
}
