const EXCEL_FILE_EXTENSIONS = ['xlsx', 'xls'];
const XML_FILE_EXTENSIONS = ['xml'];
const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];
const OTHER_HED_VERSION_OPTION = 'Upload File';
const URL_HED_VERSION_OPTION = 'From URL';

$(document).ready(function () {
    prepareValidationForm();
});

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareValidationForm() {
    resetForm();
    getStaticFormData();
    flashMessageOnScreen($('#hed-xml-url').val(), 'success', 'submit-flash');
    $('#hed-xml-url').val("testing!")
    //flashMessageOnScreen("Prepare 2 called!", 'success', 'submit-flash');
}

/**
 * Gets the static data that the form uses.
 */
function getStaticFormData() {
    getHEDVersions();
}

/**
 * Populates the HED version drop-down menu.
 * @param {Array} hedVersions - An array containing the HED versions.
 */
function populateHEDVersionsDropdown(hedVersions) {
    var hedVersionDropdown = $('#hed-version');
    hedVersionDropdown.append('<option value=' + hedVersions[0] + '>' + hedVersions[0] + ' (Latest)</option>');
    for (var i = 1; i < hedVersions.length; i++) {
        hedVersionDropdown.append('<option value=' + hedVersions[i] + '>' + hedVersions[i] + '</option>');
    }
    hedVersionDropdown.append('<option value=\'' + OTHER_HED_VERSION_OPTION + '\'>' + OTHER_HED_VERSION_OPTION +
        '</option>');
    hedVersionDropdown.append('<option value=\'' + URL_HED_VERSION_OPTION + '\'>' + URL_HED_VERSION_OPTION +
        '</option>');
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
                populateHEDVersionsDropdown(hedInfo['major_versions']);
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
 * Event handler function when the HED version drop-down menu changes. If Other is selected the file browser
 * underneath it will appear. If another option is selected then it will disappear.
 */
$('#hed-version').change(function () {
    flashMessageOnScreen($(this).val() , 'success', 'submit-flash');
    //flashMessageOnScreen($(this).val() , 'success', 'hed-flash');
    if ($(this).val() === OTHER_HED_VERSION_OPTION) {
        $('#other-hed-version').show();
        $('#url-hed-version').hide();
    } else if ($(this).val() === URL_HED_VERSION_OPTION) {
        $('#url-hed-version').show();
        $('#other-hed-version').hide();
    } else {
        $('#other-hed-version').hide();
        $('#url-hed-version').hide();
    }
    //flashMessageOnScreen('', 'success', 'hed-flash');
});
/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#hed-xml-filename').change(function () {
    var hed = $('#hed-xml-filename');
    flashMessageOnScreen('in change XML hed', 'error', 'hed-flash');
    var hedPath = hed.val();
    var hedFile = hed[0].files[0];
    if (fileHasValidExtension(hedPath, XML_FILE_EXTENSIONS)) {
        getVersionFromHEDFile(hedFile);
        updateHEDFileLabel(hedPath);
    } else {
        flashInvalidHEDExtensionMessage();
    }
});


/**
 * Updates the HED file label.
 * @param {String} hedPath - The path to the HED XML file.
 */
function updateHEDFileLabel(hedPath) {
    var hedFilename = hedPath.split('\\').pop();
    $('#hed-filename').text(hedFilename);
}

/**
 * Flash message when HED XML file extension is invalid.
 */
function flashInvalidHEDExtensionMessage() {
    flashMessageOnScreen('Please upload a valid HED file (.xml)', 'error', 'hed-flash');
}

/**
 * Resets the flash messages that aren't related to the form submission.
 A * @param {String} message - If true, reset the flash message related to the submit button.
 */
function resetFlashMessages(resetSubmitFlash) {
    flashMessageOnScreen('', 'success', 'hed-flash');
    if (resetSubmitFlash) {
        flashMessageOnScreen('', 'success', 'submit-flash');
    }
}



/**
 * Flash a message on the screen.
 * @param {String} message - The message that will be flashed on the screen.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 */
function flashMessageOnScreen(message, category, flashMessageElementId) {
    var flashMessage = document.getElementById(flashMessageElementId);
    flashMessage.innerHTML = message;
    setFlashMessageCategory(flashMessage, category);
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
 * Checks to see if the user pressed cancel in chrome's file upload browser.
 * @param {String} filePath - A path to a file.
 * @returns {boolean} - True if the user selects cancel in chrome's file upload browser.
 */
function cancelWasPressedInChromeFileUpload(filePath) {
    return isEmptyStr(filePath) && (window.chrome)
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#validation-form')[0].reset();
    hideOtherHEDVersionFileUpload();
    hideUrlHEDVersionFileUpload();
}



/**
 * Flash a submit message.
 * @param {Array} worksheetNames - An array containing the names of Excel workbook worksheets.
 */
function flashSubmitMessage() {
    resetFlashMessages(false);
    flashMessageOnScreen('Worksheet is being validated ...', 'success', 'submit-flash')
}

/**
 * Checks to see if a HED XML file is specified when the HED drop-down is set to "Other".
 */
function hedSpecifiedWhenOtherIsSelected() {
    var hedFile = $('#hed-xml-filename');
    var hedFileIsEmpty = hedFile[0].files.length === 0;
    if ($('#hed-version').val() === OTHER_HED_VERSION_OPTION && hedFileIsEmpty) {
        flashMessageOnScreen('HED version is not specified.', 'error', 'hed-flash');
        return false;
    }
    var hedUrl = $('#hed-xml-url').val();
    var hedUrlIsEmpty = hedUrl === "";
    if ($('#hed-version').val() === URL_HED_VERSION_OPTION) {
        if (hedUrlIsEmpty) {
            flashMessageOnScreen('URL not specified.', 'error', 'hed-flash-url');
            return false;
        } else {
            flashMessageOnScreen(hedUrl, 'error', 'hed-flash-url');
        }
    }
    return true;
}

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#submit').click(function () {
    if (hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    var validationForm = document.getElementById("validation-form");
    var formData = new FormData(validationForm);
    //flashMessageOnScreen('HED version is not specified.', 'error', 'submit-flash');
    flashSubmitMessage();
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_conversion_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (validationStatus) {
                flashMessageOnScreen('Trying to download1.', 'success', 'submit-flash');
                if (checkIssueCount(validationStatus['issueCount'], validationStatus['errorCount'],
                    validationStatus['warningCount'])) {
                    flashMessageOnScreen('Trying to download.', 'success', 'submit-flash');
                    downloadValidationOutputFile(validationStatus['downloadFile']);
                } else {
                    deleteUploadedSpreadsheet(validationStatus['downloadFile']);
                }
            },
            error: function (jqXHR) {
                console.log(jqXHR.responseJSON.message);
                flashMessageOnScreen('XML could not be processed', 'error',
                    'submit-flash');
            }
        }
    )
    ;
}

/**
 * Downloads the validation output file.
 * @param {string} downloadFile - The name of the download file.
 */
function downloadValidationOutputFile(downloadFile) {
    window.location = "{{url_for('route_blueprint.download_file_in_upload_directory', filename='')}}" + downloadFile;
}


/**
 * Deletes the uploaded spreadsheet after the validation is done.
 * @param {string} uploadedSpreadsheetFile - The name of the uploaded spreadsheet.
 */
function deleteUploadedSpreadsheet(uploadedSpreadsheetFile) {
    $.ajax({
            type: 'GET',
            url: "{{url_for('route_blueprint.delete_file_in_upload_directory', filename='')}}" + uploadedSpreadsheetFile,
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
 * Check the number of validation issues and flash it.
 * @param {Number} rowIssueCount - Number of issues.
 * @param {Number} rowErrorCount - Number of errors.
 * @param {Number} rowWarningCount - Number of warnings.
 * @returns {boolean} - True if there are issues found. False, if otherwise.
 */
function checkIssueCount(rowIssueCount, rowErrorCount, rowWarningCount) {
    var issuesFound = false;
    if (rowWarningCount === 0) {
        flashMessageOnScreen('No issues were found.', 'success', 'submit-flash');
    } else if (generateWarningsIsChecked()) {
        flashMessageOnScreen(rowIssueCount.toString() + ' issues found. ' + rowErrorCount.toString() + ' errors, '
            + rowWarningCount.toString() + ' warnings. Creating attachment.', 'error', 'submit-flash');
        issuesFound = true;
    } else {
        flashMessageOnScreen(rowIssueCount.toString() + ' errors found. Creating attachment.', 'error', 'submit-flash');
        issuesFound = true;
    }
    return issuesFound;
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
    var fileExtension = filePath.split('.').pop();
    if ($.inArray(fileExtension.toLowerCase(), acceptedFileExtensions) != -1) {
        return true;
    }
    return false;
}

/**
 * Gets the version from the HED file that the user uploaded.
 * @param {Object} hedXMLFile - A HED XML file.
 */
function getVersionFromHEDFile(hedXMLFile) {
    var formData = new FormData();
    formData.append('hed_file', hedXMLFile);
    $.ajax({
        type: 'POST',
        url: "{{ url_for('route_blueprint.get_hed_version_in_file')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (hedInfo) {
            resetFlashMessages(true);
            flashMessageOnScreen('Using HED version ' + hedInfo['version'], 'success', 'hed-flash');
        },
        error: function (jqXHR) {
            console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Could not get version number from HED XML file.', 'error', 'hed-flash');
        }
    });
}

/**
 * Hides the HED XML file upload.
 */
function hideUrlHEDVersionFileUpload() {
    $('#url-hed-version').hide();
}

/**
 * Hides the HED XML file upload.
 */
function hideOtherHEDVersionFileUpload() {
    $('#other-hed-version').hide();
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
 * Checks to see if warnings are being generated through checkbox.
 * @returns {boolean} - True if warnings are generated. False if otherwise.
 */
function generateWarningsIsChecked() {
    return $('#generate-warnings').prop('checked') === true;
}
