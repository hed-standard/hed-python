const JSON_FILE_EXTENSIONS = ['json'];

/**
 * Dictionary event handler function. Checks if the file uploaded has a valid dictionary extension.
 */
$('#json-file').on('change',function () {
    let jsonPath = $('#json-file').val();
    resetFormFlashMessages();
    if (cancelWasPressedInChromeFileUpload(jsonPath)) {
        resetForm();
    }
    else if (fileHasValidExtension(jsonPath, JSON_FILE_EXTENSIONS)) {
        updateFileLabel(jsonPath, '#json-display-name');
    } else {
        resetForm();
        flashMessageOnScreen('Please upload a JSON dictionary (.json)', 'error', 'json-flash');
    }
});

/**
 * Clears the dictionary file label.
 */
function clearJsonFileLabel() {
    $('#json-display-name').text('');
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function clearJsonFlashMessage() {
    flashMessageOnScreen('', 'success', 'json-flash');
}

function getJsonFileLabel() {
    return $('#json-file')[0].files[0].name;
}

/**
 * Checks to see if a dictionary has been specified.
 */
function jsonIsSpecified() {
    let jsonFile = $('#json-file');
    if (jsonFile[0].files.length === 0) {
        flashMessageOnScreen('JSON is not specified.', 'error', 'json-flash');
        return false;
    }
    return true;
}
