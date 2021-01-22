
$(function () {
    prepareForm();
});

/**
 * Submits the form if there is a spreadsheet file and an available hed schema
 */
$('#events-validation-submit').on('click', function () {
    if (spreadsheetIsSpecified()  && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Gets the spreadsheet columns.
 * @param {Object} spreadsheetFile - A spreadsheet file.
 * @param {String} worksheetName - An Excel worksheet name.
 */
function getColumnsInfo(spreadsheetFile, worksheetName) {
    let formData = new FormData();
    formData.append('spreadsheet-file', spreadsheetFile);
    if (typeof worksheetName !== 'undefined') {
        formData.append('worksheet-name', worksheetName);
    }
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.get_spreadsheet_columns_info')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (columnsInfo) {
            setComponentsRelatedToColumns(columnsInfo);
        },
        error: function (jqXHR) {
            console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Event annotations could not be processed.', 'error',
                'spreadsheet-flash');
        }
    });
}

/**
 * Gets information associated with the Excel workbook worksheets. This information contains the names of the
 * worksheets, the names of the columns in the first worksheet, and column indices that contain HED tags in the
 * first worksheet.
 * @param {Object} workbookFile - An Excel workbook file.
 */
function getWorksheetsInfo(workbookFile) {
    let formData = new FormData();
    formData.append('spreadsheet-file', workbookFile);
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.get_worksheets_info')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (worksheetsInfo) {
            populateWorksheetSelectbox(worksheetsInfo['worksheet-names']);
            setComponentsRelatedToColumns(worksheetsInfo);
            flashWorksheetNumberMessage(worksheetsInfo['worksheet-names']);
        },
        error: function (jqXHR) {
            console.log(jqXHR);
            // console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Event annotations could not be processed.', 'error',
                'events-validation-submit-flash');
        }
    });
}


/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    resetForm();
    getHEDVersions()
    hideColumnNames();
    hideOtherHEDVersionFileUpload();
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function resetFormFlashMessages() {
    flashMessageOnScreen('', 'success', 'spreadsheet-flash');
    flashMessageOnScreen('', 'success', 'worksheet-flash');
    flashMessageOnScreen('', 'success', 'hed-flash');
    flashMessageOnScreen('', 'success', 'events-validation-submit-flash');
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#events-form')[0].reset();
    clearSpreadsheetFileLabel();
    clearWorksheetSelectbox();
    hideColumnNames();
    hideOtherHEDVersionFileUpload()
}

/**
 * Sets the components related to Excel worksheet columns when they are all empty.
 */
function setComponentsRelatedToEmptyColumnNames() {
    setHasColumnNamesCheckbox(false);
    hideColumnNames();
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function setComponentsRelatedToNonEmptyColumnNames(columnNames) {
    showColumnNames(columnNames)
    setHasColumnNamesCheckbox(true);
}

/**
 * Sets the components related to the Excel worksheet columns.
 * @param {JSON} columnsInfo - A JSON object containing information related to the spreadsheet
 * columns.
 * This information contains the names of the columns and column indices that contain HED tags.
 */
function setComponentsRelatedToColumns(columnsInfo) {
    if (columnNamesAreEmpty(columnsInfo['column-names'])) {
        setComponentsRelatedToEmptyColumnNames();
    } else {
        setComponentsRelatedToNonEmptyColumnNames(columnsInfo['column-names']);
    }
}

/**
 * Checks or unchecks the spreadsheet column names checkbox to false.
 * @param {boolean} value  sets the checkbox to checked if true
 */
function setHasColumnNamesCheckbox(value) {
    $('#has-column-names').prop('checked', value);
}


/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let eventsForm = document.getElementById("events-form");
    let formData = new FormData(eventsForm);
    let worksheetName = $('#worksheet-name option:selected').text();
    let prefix = 'issues';
    if(worksheetName) {
        prefix = prefix + '_worksheet_' + worksheetName;
    }
    let spreadsheetFile = $('#spreadsheet-file')[0].files[0].name;
    let display_name = convertToResultsName(spreadsheetFile, prefix)
    resetFormFlashMessages();
    flashMessageOnScreen('Worksheet is being validated ...', 'success',
        'events-validation-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_events_validation_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (downloaded_file) {
                  if (downloaded_file) {
                      flashMessageOnScreen('', 'success',
                          'events-validation-submit-flash');
                      triggerDownloadBlob(downloaded_file, display_name);
                  } else {
                      flashMessageOnScreen('No validation errors found.', 'success',
                          'events-validation-submit-flash');
                  }
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error',
                        'events-validation-submit-flash');
                } else {
                    flashMessageOnScreen('Event annotations could not be processed',
                        'error','events-validation-submit-flash');
                }
            }
        }
    )
    ;
}