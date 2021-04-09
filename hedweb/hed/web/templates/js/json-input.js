const JSON_FILE_EXTENSIONS = ['json'];

/**
 * Dictionary event handler function. Checks if the file uploaded has a valid dictionary extension.
 */
$('#json-file').on('change',function () {
    let jsonPath = $('#json-file').val();
    clearFlashMessages();
    if (cancelWasPressedInChromeFileUpload(jsonPath)) {
        clearForm();
    }
    else if (fileHasValidExtension(jsonPath, JSON_FILE_EXTENSIONS)) {
        updateFileLabel(jsonPath, '#json-display-name');
    } else {
        clearForm();
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
function clearJsonInputFlashMessages() {
    flashMessageOnScreen('', 'success', 'json-flash');
}

function getJsonFileLabel() {
    return $('#json-file')[0].files[0].name;
}

