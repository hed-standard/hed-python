
$(function () {
    prepareForm();
});

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#spreadsheet-validation-submit').on('click', function () {
    if (spreadsheetIsSpecified() && tagColumnsTextboxIsValid() && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});


/**
 * Clears tag column text boxes.
 */
function clearTagColumnTextboxes() {
    $('.textbox-group input[type="text"]').val('');
}

/**
 * Flash a message showing the number of column columns that contain tags.
 * @param {Array} tagColumnIndices - An array of indices of columns containing tags
 * @param {Array} requiredTagColumnIndices - An array of indices of columns containing required tags
 * contain tags.
 */
function flashTagColumnCountMessage(tagColumnIndices, requiredTagColumnIndices) {
    let numberOfTagColumns = (tagColumnIndices.length + Object.keys(requiredTagColumnIndices).length).toString();
    if (numberOfTagColumns === '0') {
        flashMessageOnScreen('Warning: No tag column(s) found... Using the 2nd column', 'warning',
            'tag-columns-flash');
    } else {
        flashMessageOnScreen(numberOfTagColumns + ' tag column(s) found', 'success',
            'tag-columns-flash');
    }
}

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
            flashTagColumnCountMessage(columnsInfo['tag-column-indices'],
                columnsInfo['required-tag-column-indices']);
        },
        error: function (jqXHR) {
            console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Spreadsheet could not be processed.', 'error',
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
            flashTagColumnCountMessage(worksheetsInfo['tag-column-indices'],
                worksheetsInfo['required-tag-column-indices']);
        },
        error: function (jqXHR) {
            console.log(jqXHR);
            // console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Spreadsheet could not be processed.', 'error',
                'spreadsheet-validation-submit-flash');
        }
    });
}


/**
 * Populate the required tag column textboxes from the tag column indices found in the spreadsheet columns.
 * @param {object} requiredTagColumnIndices - A dictionary containing the required tag column indices found
 * in the spreadsheet. The keys are the column names and the values are the indices.
 */
function populateRequiredTagColumnTextboxes(requiredTagColumnIndices) {
    for (let key in requiredTagColumnIndices) {
        $('#' + key.toLowerCase() + '-column').val(requiredTagColumnIndices[key].toString());
    }
}

/**
 * Populate the tag column textbox from the tag column indices found in the spreadsheet columns.
 * @param {Array} tagColumnIndices - An integer array of tag column indices found in the spreadsheet
 * columns.
 */
function populateTagColumnsTextbox(tagColumnIndices) {
    $('#tag-columns').val(tagColumnIndices.sort().map(String));
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
    resetTagColumnMessages();
    flashMessageOnScreen('', 'success', 'hed-flash');
    flashMessageOnScreen('', 'success', 'spreadsheet-validation-submit-flash');
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#spreadsheet-form')[0].reset();
    clearSpreadsheetFileLabel();
    clearWorksheetSelectbox();
    hideColumnNames();
    hideOtherHEDVersionFileUpload()
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function resetTagColumnMessages() {
    flashMessageOnScreen('', 'success', 'tag-columns-flash');
}

/**
 * Sets the components related to Excel worksheet columns when they are all empty.
 */
function setComponentsRelatedToEmptyColumnNames() {
    clearTagColumnTextboxes();
    setHasColumnNamesCheckbox(false);
    hideColumnNames();
}

/**
 * Sets the components related to the spreadsheet tag column indices when they are empty.
 */
function setComponentsRelatedToEmptyTagColumnIndices() {
    $('#tag-columns').val('2');
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
    clearTagColumnTextboxes();
    if (columnNamesAreEmpty(columnsInfo['column-names'])) {
        setComponentsRelatedToEmptyColumnNames();
    } else {
        setComponentsRelatedToNonEmptyColumnNames(columnsInfo['column-names']);
    }
    if (tagColumnsIndicesAreEmpty(columnsInfo['tag-column-indices'])) {
        setComponentsRelatedToEmptyTagColumnIndices();
    } else {
        populateTagColumnsTextbox(columnsInfo['tag-column-indices']);
    }
    if (Object.keys(columnsInfo['required-tag-column-indices']).length !== 0) {
        populateRequiredTagColumnTextboxes(columnsInfo['required-tag-column-indices']);
    }
}

/**
 * Sets the spreadsheet has column names checkbox to false.
 * @param {boolean} Box is checked if true and unchecked if false
 */
function setHasColumnNamesCheckbox(value) {
    $('#has-column-names').prop('checked', value);
}

/**
 * Checks to see if the worksheet tag column indices are empty.
 * @param {Array} tagColumnsIndices - An array containing the tag column indices based on the
 *                columns found in the spreadsheet.
 * @returns {boolean} - True if the spreadsheet tag column indices array is empty.
 */
function tagColumnsIndicesAreEmpty(tagColumnsIndices) {
    if (tagColumnsIndices.length > 0) {
        return false;
    }
    return true;
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let spreadsheetForm = document.getElementById("spreadsheet-form");
    let formData = new FormData(spreadsheetForm);
    let worksheetName = $('#worksheet-name option:selected').text();
    let prefix = 'issues';
    if(worksheetName) {
        prefix = prefix + '_worksheet_' + worksheetName;
    }
    let spreadsheetFile = $('#spreadsheet-file')[0].files[0].name;
    let display_name = convertToResultsName(spreadsheetFile, prefix)
    resetFormFlashMessages();
    flashMessageOnScreen('Worksheet is being validated ...', 'success',
        'spreadsheet-validation-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_spreadsheet_validation_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'spreadsheet-validation-submit-flash')
            },
            error: function (download, status, xhr) {
                getResponseFailure(download, xhr, display_name, 'spreadsheet-validation-submit-flash')
            }
        }
    )
}

/**
 * Checks to see if the tag columns textbox has valid input. Valid input is an integer or a comma-separated list of
 * integers that are the column indices in a Excel worksheet that contain HED tags.
 * @returns {boolean} - True if the tags columns textbox is valid.
 */
function tagColumnsTextboxIsValid() {
    let otherTagColumns = $('#tag-columns').val().trim();
    let valid = true;
    if (!isEmptyStr(otherTagColumns)) {
        let pattern = new RegExp('^([ \\d]+,)*[ \\d]+$');
        let valid = pattern.test(otherTagColumns);
        if (!valid) {
            flashMessageOnScreen('Tag column(s) must be a number or a comma-separated list of numbers',
                'error', 'tag-columns-flash')
        }
    }
    return valid;
}
