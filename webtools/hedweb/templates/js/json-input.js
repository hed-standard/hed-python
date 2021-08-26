const JSON_FILE_EXTENSIONS = ['json'];

/**
 * Sidecar event handler function. Checks if the file uploaded has a valid sidecar extension.
 */
$('#json_file').on('change',function () {
    let jsonPath = $('#json_file').val();
    clearFlashMessages();
    if (cancelWasPressedInChromeFileUpload(jsonPath)) {
        clearForm();
    }
    else if (fileHasValidExtension(jsonPath, JSON_FILE_EXTENSIONS)) {
        updateFileLabel(jsonPath, '#json_display_name');
    } else {
        clearForm();
        flashMessageOnScreen('Please upload a JSON sidecar (.json)', 'error', 'json_flash');
    }
});

/**
 * Clears the sidecar file label.
 */
function clearJsonFileLabel() {
    $('#json_display_name').text('');
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function clearJsonInputFlashMessages() {
    flashMessageOnScreen('', 'success', 'json_flash');
}

function getJsonFileLabel() {
    return $('#json_file')[0].files[0].name;
}

