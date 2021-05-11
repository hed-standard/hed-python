const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];

$(function () {
    prepareForm();
});


/**
 * Events file handler function. Checks if the file uploaded has a valid spreadsheet extension.
 */
$('#events-file').on('change', function () {
    let events = $('#events-file');
    let eventsPath = events.val();
    let eventsFile = events[0].files[0];
    clearFlashMessages();
    removeColumnTable();
    if (cancelWasPressedInChromeFileUpload(eventsPath)) {
        clearForm();
        return;
    }
    updateFileLabel(eventsPath, '#events-display-name');
    if (fileHasValidExtension(eventsPath, TEXT_FILE_EXTENSIONS)) {
        setColumnsInfo(eventsFile, undefined, false, 'events-flash');
    } else {
        clearForm();
        flashMessageOnScreen('Please upload a tsv file (.tsv, .txt)', 'error', 'events-flash');
    }
});

/**
 * Submits the form if there is an events file and an available hed schema
 */
$('#events-submit').on('click', function () {
    if (fileIsSpecified('#events-file', 'events-flash', 'Events file is not specified.')
        && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});


/**
 * Clears the fields in the form.
 */
function clearForm() {
    $('#events-form')[0].reset();
    $('#events-display-name').text('');
    clearFlashMessages();
    hideColumnNames();
    hideOtherHEDVersionFileUpload();
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFlashMessages() {
    clearColumnInfoFlashMessages();
    clearHedSelectFlashMessages();
    clearJsonInputFlashMessages();
    flashMessageOnScreen('', 'success', 'events-flash');
    flashMessageOnScreen('', 'success', 'events-submit-flash');
}


/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getHedVersions()
    hideColumnNames();
    hideOtherHEDVersionFileUpload();
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let eventsForm = document.getElementById("events-form");
    let formData = new FormData(eventsForm);
    let prefix = 'issues';
    let eventsFile = $('#events-file')[0].files[0].name;
    let display_name = convertToResultsName(eventsFile, prefix)
    clearFlashMessages();
    flashMessageOnScreen('Worksheet is being validated ...', 'success',
        'events-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_events_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'events-submit-flash')
            },
            error: function (download, status, xhr) {
                getResponseFailure(download, xhr, display_name, 'events-submit-flash')
            }
        }
    )
}