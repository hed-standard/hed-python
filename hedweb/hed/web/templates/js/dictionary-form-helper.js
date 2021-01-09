const DICTIONARY_FILE_EXTENSIONS = ['json'];
const XML_FILE_EXTENSIONS = ['xml'];
const HED_OTHER_VERSION_OPTION = 'Other';

$(document).ready(function () {
    prepareDictionaryValidationForm();
});

/**
 * Event handler function when the HED version drop-down menu changes. If Other is selected the file browser
 * underneath it will appear. If another option is selected then it will disappear.
 */
$('#hed-version').change(function () {
    if ($(this).val() === HED_OTHER_VERSION_OPTION) {
        $('#hed-other-version').show();
    } else {
        hideOtherHEDVersionFileUpload()
    }
    flashMessageOnScreen('', 'success', 'hed-flash');
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
        flashMessageOnScreen('Please upload a valid HED file (.xml)', 'error',
            'hed-flash')
    }
});

/**
 * Dictionary event handler function. Checks if the file uploaded has a valid dictionary extension.
 */
$('#dictionary-file').change(function () {
    let dictionary = $('#dictionary-file');
    let dictionaryPath = dictionary.val();
    resetFlashMessages();
    if (cancelWasPressedInChromeFileUpload(dictionaryPath)) {
        resetForm();
    }
    else if (fileHasValidExtension(dictionaryPath, DICTIONARY_FILE_EXTENSIONS)) {
        updateDictionaryFileLabel(dictionaryPath);
    } else {
        resetForm();
        flashMessageOnScreen('Please upload a JSON dictionary (.json)',
            'error', 'dictionary-flash');
    }
});

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#dictionary-validation-submit').click(function () {
    if (dictionaryIsSpecified() && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Clears the dictionary file label.
 */
function clearDictionaryFileLabel() {
    $('#dictionary-display-name').text('');
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
                    'error', 'dictionary-flash');
            }
        }
    );
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
            resetFlashMessages();
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
 * Hides the HED XML file upload.
 */
function hideOtherHEDVersionFileUpload() {
    $('#hed-display-name').text('');
    $('#hed-other-version').hide();
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
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareDictionaryValidationForm() {
    resetForm();
    getHEDVersions()
    hideOtherHEDVersionFileUpload();
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function resetFlashMessages() {
    flashMessageOnScreen('', 'success', 'dictionary-flash');
    flashMessageOnScreen('', 'success', 'hed-flash');
    flashMessageOnScreen('', 'success', 'dictionary-validation-submit-flash');
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#dictionary-form')[0].reset();
    clearDictionaryFileLabel();
    hideOtherHEDVersionFileUpload()
}

/**
 * Checks to see if a dictionary has been specified.
 */
function dictionaryIsSpecified() {
    let dictionaryFile = $('#dictionary-file');
    if (dictionaryFile[0].files.length === 0) {
        flashMessageOnScreen('Dictionary is not specified.', 'error',
            'dictionary-flash');
        return false;
    }
    return true;
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let dictionaryForm = document.getElementById("dictionary-form");
    let formData = new FormData(dictionaryForm);
    let prefix = 'validation_issues';

    let dictionaryFile = $('#dictionary-file')[0].files[0].name;
    let display_name = convertToResultsName(dictionaryFile, prefix)
    resetFlashMessages();
    flashMessageOnScreen('Dictionary is being validated ...', 'success',
        'dictionary-validation-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_dictionary_validation_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (downloaded_file) {
                  if (downloaded_file) {
                      flashMessageOnScreen('', 'success',
                          'dictionary-validation-submit-flash');
                      triggerDownloadBlob(downloaded_file, display_name);
                  } else {
                      flashMessageOnScreen('No validation errors found.', 'success',
                          'dictionary-validation-submit-flash');
                  }
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error',
                        'dictionary-validation-submit-flash');
                } else {
                    flashMessageOnScreen('Dictionary could not be processed',
                        'error','dictionary-validation-submit-flash');
                }
            }
        }
    )
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
 * Updates the dictionary file label.
 * @param {String} dictionaryPath - The path to the dictionary.
 */
function updateDictionaryFileLabel(dictionaryPath) {
    let dictionaryFilename = dictionaryPath.split('\\').pop();
    $('#dictionary-display-name').text(dictionaryFilename);
}
