const EXCEL_FILE_EXTENSIONS = ['xlsx', 'xls'];
const XML_FILE_EXTENSIONS = ['xml'];
const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];
const HED_OTHER_VERSION_OPTION = 'Other';

$(document).ready(function () {
    prepareValidationForm();
});

/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#hed-xml-file').change(function () {
    let hedSchema = $('#hed-xml-file');
    let hedPath = hedSchema.val();
    let hedFile = hedSchema[0].files[0];
    if (fileHasValidExtension(hedPath, XML_FILE_EXTENSIONS)) {
        getVersionFromHEDFile(hedFile);
        updateHEDFileLabel(hedPath);
    } else {
        flashInvalidHEDExtensionMessage();
    }
});

/**
 * Event handler function when the HED version drop-down menu changes. If Other is selected the file browser
 * underneath it will appear. If another option is selected then it will disappear.
 */
$('#hed-version').change(function () {
    if ($(this).val() === HED_OTHER_VERSION_OPTION) {
        $('#hed-other-version').show();
    } else {
        $('#hed-other-version').hide();
    }
    flashMessageOnScreen('', 'success', 'hed-flash');
});

/**
 * Spreadsheet event handler function. Checks if the file uploaded has a valid spreadsheet extension.
 */
$('#spreadsheet-file').change(function () {
    let spreadsheet = $('#spreadsheet-file');
    let spreadsheetPath = spreadsheet.val();
    let spreadsheetFile = spreadsheet[0].files[0];
    resetFlashMessages(true);
    if (cancelWasPressedInChromeFileUpload(spreadsheetPath)) {
        resetForm();
    }
    else if (fileHasValidExtension(spreadsheetPath, EXCEL_FILE_EXTENSIONS)) {
        updateSpreadsheetFileLabel(spreadsheetPath);
        getWorksheetsInfo(spreadsheetFile);
    }
    else if (fileHasValidExtension(spreadsheetPath, TEXT_FILE_EXTENSIONS)) {
        updateSpreadsheetFileLabel(spreadsheetPath);
        clearWorksheetSelectbox();
        getSpreadsheetColumnsInfo(spreadsheetFile, '');
    } else {
        resetForm();
        flashInvalidExcelExtensionMessage();
    }
});


/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#validation-submit').click(function () {
    if (spreadsheetIsSpecified() && tagColumnsTextboxIsValid() && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Gets the information associated with the Excel worksheet that was newly selected. This information contains
 * the names of the columns and column indices that contain HED tags.
 */
$('#worksheet-name').change(function () {
    let spreadsheetFile = $('#spreadsheet-file')[0].files[0];
    let worksheetName = $('#worksheet-name option:selected').text();
    resetFlashMessages(true);
    getSpreadsheetColumnsInfo(spreadsheetFile, worksheetName);
});


/**
 * Checks to see if the user pressed cancel in chrome's file upload browser.
 * @param {String} filePath - A path to a file.
 * @returns {boolean} - True if the user selects cancel in chrome's file upload browser.
 */
function cancelWasPressedInChromeFileUpload(filePath) {
    return isEmptyStr(filePath) && (window.chrome)
}

/**
 * Checks to see if warnings are being generated through checkbox.
 * @returns {boolean} - True if warnings are generated. False if otherwise.
 */
function checkForWarningsIsChecked() {
    return $('#check-for-warnings').prop('checked') === true;
}

/**
 * Check the number of validation issues and flash it.
 * @param {Number} rowIssueCount - Number of issues.
 * @param {Number} rowErrorCount - Number of errors.
 * @param {Number} rowWarningCount - Number of warnings.
 * @returns {boolean} - True if there are issues found. False, if otherwise.
 */
function checkIssueCount(rowIssueCount, rowErrorCount, rowWarningCount) {
    let issuesFound = false;
    if (rowIssueCount === 0) {
        flashMessageOnScreen('No issues were found.', 'success',
            'validation-submit-flash');
    } else if (checkForWarningsIsChecked()) {
        flashMessageOnScreen(rowIssueCount.toString() + ' issues found. ' + rowErrorCount.toString() +
            ' errors, ' + rowWarningCount.toString() + ' warnings. Creating attachment.', 'error',
            'validation-submit-flash');
        issuesFound = true;
    } else {
        flashMessageOnScreen(rowIssueCount.toString() + ' errors found. Creating attachment.', 'error',
            'validation-submit-flash');
        issuesFound = true;
    }
    return issuesFound;
}

/**
 * Clears the spreadsheet file label.
 */
function clearSpreadsheetFileLabel() {
    $('#spreadsheet-display-name').text('');
}


/**
 * Clears tag column text boxes.
 */
function clearTagColumnTextboxes() {
    $('.textbox-group input[type="text"]').val('');
}

/**
 * Clears the worksheet select box.
 */
function clearWorksheetSelectbox() {
    $('#worksheet-name').empty();
}


/**
 * Deletes the uploaded spreadsheet after the validation is done.
 * @param {string} uploadedSpreadsheetFile - The name of the uploaded spreadsheet.
 */
function deleteUploadedSpreadsheet(uploadedSpreadsheetFile) {
    $.ajax({
            type: 'GET',
            url: "{{url_for('route_blueprint.delete_file_in_upload_directory', filename='')}}" +
                uploadedSpreadsheetFile,
            data: {},
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function () {
            },
            error: function (jqXHR) {
                console.log(jqXHR.responseJSON.message);
            }
        }
    )
    ;
}




/**
 * Checks to see if a dictionary is empty
 * @param {Array} dictionary - A dictionary
 * @returns {boolean} - True if the dictionary is empty. False, if otherwise.
 */
function dictionaryIsEmpty(dictionary) {
    return Object.keys(dictionary).length === 0;
}


/**
 * Downloads the validation output file.
 * @param {string} downloadFile - The name of the download file.
 */
function downloadValidationOutputFile(downloadFile) {
    window.location = "{{url_for('route_blueprint.download_file_in_upload_directory', filename='')}}" + downloadFile;
}


/**
 * Checks to see if a string is empty. Empty meaning null or a length of zero.
 * @param {String} str - A string.
 * @returns {boolean} - True if the string is null or its length is 0.
 */
function isEmptyStr(str) {
    if (str === null || str.length === 0) {
        return true;
    }
    return false;
}

/**
 * Compares the file extension of the file at the specified path to an Array of accepted file extensions.
 * @param {String} filePath - A path to a file.
 * @param {Array} acceptedFileExtensions - An array of accepted file extensions.
 * @returns {boolean} - True if the file has an accepted file extension.
 */
function fileHasValidExtension(filePath, acceptedFileExtensions) {
    let fileExtension = filePath.split('.').pop();
    if ($.inArray(fileExtension.toLowerCase(), acceptedFileExtensions) != -1) {
        return true;
    }
    return false;
}



/**
 * Flash message when Excel workbook file extension is invalid.
 */
function flashInvalidExcelExtensionMessage() {
    flashMessageOnScreen('Please upload a excel or text spreadsheet (.xlsx, .xls, .tsv, .txt)',
        'error', 'spreadsheet-flash');
}

/**
 * Flash message when HED XML file extension is invalid.
 */
function flashInvalidHEDExtensionMessage() {
    flashMessageOnScreen('Please upload a valid HED file (.xml)', 'error', 'hed-flash');
}


/**
 * Flash a message on the screen.
 * @param {String} message - The message that will be flashed on the screen.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 * @param {String} flashMessageElementId - ID of the flash element
 */
function flashMessageOnScreen(message, category, flashMessageElementId) {
    let flashMessage = document.getElementById(flashMessageElementId);
    flashMessage.innerHTML = message;
    setFlashMessageCategory(flashMessage, category);
}

/**
 * Flash a message showing the number of column columns that contain tags.
 * @param {Array} TagColumnIndices - An array containing the indices of the column columns that
 * contain tags.
 */
function flashSpreadsheetTagColumnCountMessage(TagColumnIndices, requiredTagColumnIndices) {
    let numberOfTagColumns = (TagColumnIndices.length + Object.keys(requiredTagColumnIndices).length).toString();
    if (numberOfTagColumns === '0') {
        flashMessageOnScreen('Warning: No tag column(s) found... Using the 2nd column', 'warning',
            'tag-columns-flash');
    } else {
        flashMessageOnScreen(numberOfTagColumns + ' tag column(s) found', 'success',
            'tag-columns-flash');
    }
}

/**
 * Flash a submit message.
 * @param {Array} worksheetNames - An array containing the names of Excel workbook worksheets.
 */
function flashSubmitMessage() {
    resetFlashMessages(false);
    flashMessageOnScreen('Worksheet is being validated ...', 'success',
        'validation-submit-flash')
}

/**
 * Flash a message showing the number of worksheets in an Excel workbook.
 * @param {Array} worksheetNames - An array containing the names of Excel workbook worksheets.
 */
function flashWorksheetNumberMessage(worksheetNames) {
    let numberOfWorksheets = worksheetNames.length.toString();
    flashMessageOnScreen(numberOfWorksheets + ' worksheet(s) found',
        'success', 'worksheet-flash');
}



/**
 * Gets the HED versions that are in the HED version drop-down menu.
 */
function getHEDVersions() {
    $.ajax({
            type: 'GET',
            url: "{{url_for('route_blueprint.get_major_hed_versions')}}",
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (hedInfo) {
                populateHEDVersionsDropdown(hedInfo['hed-major-versions']);
            },
            error: function (jqXHR) {
                console.log(jqXHR.responseJSON.message);
                flashMessageOnScreen('Major HED versions could not be retrieved. Please provide your own.',
                    'error', 'spreadsheet-flash');
            }
        }
    );
}


/**
 * Gets the spreadsheet columns.
 * @param {Object} spreadsheetFile - A spreadsheet file.
 * @param {String} worksheetName - An Excel worksheet name.
 */
function getSpreadsheetColumnsInfo(spreadsheetFile, worksheetName) {
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
        success: function (spreadsheetColumnsInfo) {
            setComponentsRelatedToSpreadsheetColumns(spreadsheetColumnsInfo);
            flashSpreadsheetTagColumnCountMessage(spreadsheetColumnsInfo['tag-column-indices'],
                spreadsheetColumnsInfo['required-tag-column-indices']);
        },
        error: function (jqXHR) {
            console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Spreadsheet could not be processed.', 'error',
                'spreadsheet-flash');
        }
    });
}



/**
 * Gets the static data that the form uses.
 */
function getStaticFormData() {
    getHEDVersions();
}

/**
 * Gets the version from the HED file that the user uploaded.
 * @param {Object} hedXMLFile - A HED XML file.
 */
function getVersionFromHEDFile(hedXMLFile) {
    let formData = new FormData();
    formData.append('hed-xml-file', hedXMLFile);
    $.ajax({
        type: 'POST',
        url: "{{ url_for('route_blueprint.get_hed_version_in_file')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (hedInfo) {
            resetFlashMessages(true);
            flashMessageOnScreen('Using HED version ' + hedInfo['hed-version'],
                'success', 'hed-flash');
        },
        error: function (jqXHR) {
            console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Could not get version number from HED XML file.',
                'error', 'hed-flash');
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
            setComponentsRelatedToWorksheets(worksheetsInfo);
            flashWorksheetNumberMessage(worksheetsInfo['worksheet-names']);
            flashSpreadsheetTagColumnCountMessage(worksheetsInfo['tag-column-indices'],
                worksheetsInfo['required-tag-column-indices']);
        },
        error: function (jqXHR) {
            console.log(jqXHR);
            // console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Spreadsheet could not be processed.', 'error',
                'validation-submit-flash');
        }
    });
}


/**
 * Checks to see if a HED XML file is specified when the HED drop-down is set to "Other".
 */
function hedSpecifiedWhenOtherIsSelected() {
    let hedFile = $('#hed-xml-file');
    let hedFileIsEmpty = hedFile[0].files.length === 0;
    if ($('#hed-version').val() === HED_OTHER_VERSION_OPTION && hedFileIsEmpty) {
        flashMessageOnScreen('HED version is not specified.', 'error', 'hed-flash');
        return false;
    }
    return true;
}

/**
 * Hides spreadsheet columns section in the form.
 */
function hideSpreadsheetColumnNamesTable() {
    $('#column-names').hide();
}

/**
 * Hides the HED XML file upload.
 */
function hideOtherHEDVersionFileUpload() {
    $('#other-hed-version').hide();
}


/**
 * Populates the HED version drop-down menu.
 * @param {Array} hedVersions - An array containing the HED versions.
 */
function populateHEDVersionsDropdown(hedVersions) {
    let hedVersionDropdown = $('#hed-version');
    hedVersionDropdown.append('<option value=' + hedVersions[0] + '>' + hedVersions[0] + ' (Latest)</option>');
    for (let i = 1; i < hedVersions.length; i++) {
        hedVersionDropdown.append('<option value=' + hedVersions[i] + '>' + hedVersions[i] + '</option>');
    }
    hedVersionDropdown.append('<option value=' + HED_OTHER_VERSION_OPTION + '>' + HED_OTHER_VERSION_OPTION +
        '</option>');
}



/**
 * Populate the required tag column textboxes from the tag column indices found in the spreadsheet columns.
 * @param {Dictionary} requiredTagColumnIndices - A dictionary containing the required tag column indices found
 * in the spreadsheet. The keys are the column names and the values are the indices.
 */
function populateRequiredTagColumnTextboxes(requiredTagColumnIndices) {
    for (let key in requiredTagColumnIndices) {
        $('#' + key.toLowerCase() + '-column').val(requiredTagColumnIndices[key].toString());
    }
}


/**
 * Populates a table containing the spreadsheet columns.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function populateSpreadsheetColumnNamesTable(columnNames) {
    let columnNamesTable = $('#columns-names-table');
    let columnNamesRow = $('<tr/>');
    let numberOfColumnNames = columnNames.length;
    columnNamesTable.empty();
    for (let i = 0; i < numberOfColumnNames; i++) {
        columnNamesRow.append('<td>' + columnNames[i] + '</td>');
    }
    columnNamesTable.append(columnNamesRow);
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
 * Populate the Excel worksheet select box.
 * @param {Array} worksheetNames - An array containing the Excel worksheet names.
 */
function populateWorksheetSelectbox(worksheetNames) {
    let worksheetSelectbox = $('#worksheet-name');
    let numberOfWorksheetNames = worksheetNames.length;
    worksheetSelectbox.empty();
    for (let i = 0; i < numberOfWorksheetNames; i++) {
        worksheetSelectbox.append(new Option(worksheetNames[i], worksheetNames[i]));
    }
}


/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareValidationForm() {
    resetForm();
    getStaticFormData();
    hideSpreadsheetColumnNamesTable();
    hideOtherHEDVersionFileUpload();
}


/**
 * Resets the flash messages that aren't related to the form submission.
 A * @param {String} message - If true, reset the flash message related to the validation-submit button.
 */
function resetFlashMessages(resetSubmitFlash) {
    flashMessageOnScreen('', 'success', 'spreadsheet-flash');
    flashMessageOnScreen('', 'success', 'worksheet-flash');
    flashMessageOnScreen('', 'success', 'tag-columns-flash');
    flashMessageOnScreen('', 'success', 'hed-flash');
    if (resetSubmitFlash) {
        flashMessageOnScreen('', 'success', 'validation-submit-flash');
    }
}


/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#validation-form')[0].reset();
    clearSpreadsheetFileLabel();
    clearWorksheetSelectbox();
    hideSpreadsheetColumnNamesTable();
    hideOtherHEDVersionFileUpload();
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function setComponentsRelatedToNonEmptySpreadsheetColumnNames(columnNames) {
    populateSpreadsheetColumnNamesTable(columnNames);
    setHasColumnNamesCheckboxToTrue();
    showSpreadsheetColumnNamesTable();
}

/**
 * Sets the components related to the spreadsheet tag column indices when they are empty.
 */
function setComponentsRelatedToEmptySpreadsheetTagColumnIndices() {
    $('#tag-columns').val('2');
}

/**
 * Sets the components related to Excel worksheet columns when they are all empty.
 */
function setComponentsRelatedToEmptySpreadsheetColumnNames() {
    clearTagColumnTextboxes();
    setHasColumnNamesCheckboxToFalse();
    hideSpreadsheetColumnNamesTable();
}


/**
 * Sets the components related to the Excel worksheet columns.
 * @param {JSON} spreadsheetColumnsInfo - A JSON object containing information related to the spreadsheet
 * columns.
 * This information contains the names of the columns and column indices that contain HED tags.
 */
function setComponentsRelatedToSpreadsheetColumns(spreadsheetColumnsInfo) {
    clearTagColumnTextboxes();
    if (spreadsheetColumnNamesAreEmpty(spreadsheetColumnsInfo['column-names'])) {
        setComponentsRelatedToEmptySpreadsheetColumnNames();
    } else {
        setComponentsRelatedToNonEmptySpreadsheetColumnNames(spreadsheetColumnsInfo['column-names']);
    }
    if (spreadsheetTagColumnsIndicesAreEmpty(spreadsheetColumnsInfo['tag-column-indices'])) {
        setComponentsRelatedToEmptySpreadsheetTagColumnIndices();
    } else {
        populateTagColumnsTextbox(spreadsheetColumnsInfo['tag-column-indices']);
    }
    if (!dictionaryIsEmpty(spreadsheetColumnsInfo['required-tag-column-indices'])) {
        populateRequiredTagColumnTextboxes(spreadsheetColumnsInfo['required-tag-column-indices']);
    }
}


/**
 * Sets components related to an Excel worksheet.
 * @param {JSON} worksheetsInfo - A JSON object containing information related to the Excel worksheet. This
 * information contains the names of the worksheets in a workbook, the names of the columns in the first worksheet,
 * and column indices that contain HED tags in the first worksheet.
 */
function setComponentsRelatedToWorksheets(worksheetsInfo) {
    populateWorksheetSelectbox(worksheetsInfo['worksheet-names']);
    setComponentsRelatedToSpreadsheetColumns(worksheetsInfo);
}


/**
 * Sets the spreadsheet has column names checkbox to false.
 */
function setHasColumnNamesCheckboxToFalse() {
    $('#has-column-names').prop('checked', false);
}

/**
 * Sets the spreadsheet has column names checkbox to true.
 */
function setHasColumnNamesCheckboxToTrue() {
    $('#has-column-names').prop('checked', true);
}


/**
 * Flash a message on the screen.
 * @param {Object} flashMessage - The li element containing the flash message.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 */
function setFlashMessageCategory(flashMessage, category) {
    if ("error" === category) {
        flashMessage.style.backgroundColor = 'lightcoral';
    } else if ("success" === category) {
        flashMessage.style.backgroundColor = 'palegreen';
    } else if ("warning" === category) {
        flashMessage.style.backgroundColor = 'darkorange';
    } else {
        flashMessage.style.backgroundColor = '#f0f0f5';
    }
}

/**
 * Shows spreadsheet columns section in the form.
 */
function showSpreadsheetColumnNamesTable() {
    $('#column-names').show();
}

/**
 * Checks to see if the spreadsheet columns are empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 * @returns {boolean} - True if the spreadsheet columns are all empty.
 */
function spreadsheetColumnNamesAreEmpty(columnNames) {
    let numberOfColumnNames = columnNames.length;
    for (let i = 0; i < numberOfColumnNames; i++) {
        if (!isEmptyStr(columnNames[i].trim())) {
            return false;
        }
    }
    return true;
}


/**
 * Checks to see if a spreadsheet has been specified.
 */
function spreadsheetIsSpecified() {
    let spreadsheetFile = $('#spreadsheet-file');
    if (spreadsheetFile[0].files.length === 0) {
        flashMessageOnScreen('Spreadsheet is not specified.', 'error',
            'spreadsheet-flash');
        return false;
    }
    return true;
}

/**
 * Checks to see if the spreadsheet tag column indices are empty.
 * @param {Array} tagColumnsIndices - An array containing the tag column indices based on the
 *                columns found in the spreadsheet.
 * @returns {boolean} - True if the spreadsheet tag column indices array is empty.
 */
function spreadsheetTagColumnsIndicesAreEmpty(tagColumnsIndices) {
    let numberOfTagColumnIndices = tagColumnsIndices.length;
    if (numberOfTagColumnIndices > 0) {
        return false;
    }
    return true;
}


/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let validationForm = document.getElementById("validation-form");
    let formData = new FormData(validationForm);
    flashSubmitMessage();
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_validation_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (validationStatus) {
                if (checkIssueCount(validationStatus['issue-count'], validationStatus['error-count'],
                    validationStatus['warning-count'])) {
                    downloadValidationOutputFile(validationStatus['download-file']);
                } else {
                    deleteUploadedSpreadsheet(validationStatus['download-file']);
                }
            },
            error: function (jqXHR) {
                console.log(jqXHR.responseJSON.message);
                flashMessageOnScreen('Spreadsheet could not be processed', 'error',
                    'validation-submit-flash');
            }
        }
    )
    ;
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


/**
 * Updates the HED file label.
 * @param {String} hedPath - The path to the HED XML file.
 */
function updateHEDFileLabel(hedPath) {
    let hedFilename = hedPath.split('\\').pop();
    $('#hed-display-name').text(hedFilename);
}

/**
 * Updates the spreadsheet file label.
 * @param {String} spreadsheetPath - The path to the spreadsheet.
 */
function updateSpreadsheetFileLabel(spreadsheetPath) {
    let spreadsheetFilename = spreadsheetPath.split('\\').pop();
    $('#spreadsheet-display-name').text(spreadsheetFilename);
}
