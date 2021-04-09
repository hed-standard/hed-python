
$(function () {
    prepareForm();
});

/**
 * Submits the form for tag comparison if we have a valid file.
 */
$('#hedstring-submit').on('click', function () {
   if (!hedStringIsSpecified()) {
        flashMessageOnScreen('Must give a non-empty hedstring.  See above.', 'error',
            'hedstring-submit-flash')
    } else {
        submitHedStringForm();
    }
});

/**
 * Resets the fields in the form.
 */
function clearForm() {
    $('#hedstring-form')[0].reset();
    clearFormFlashMessages();
    hideOtherHEDVersionFileUpload()
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFormFlashMessages() {
    clearHedSelectFlashMessages();
    flashMessageOnScreen('', 'success', 'hedstring-flash');
    flashMessageOnScreen('', 'success', 'hedstring-submit-flash');
}

/**
 * Checks to see if a hedstring has been specified.
 */
function hedStringIsSpecified() {
/*    let jsonFile = $('#json-file');
    if (jsonFile[0].files.length === 0) {
        flashMessageOnScreen('JSON is not specified.', 'error', 'json-flash');
        return false;
    }*/
    return true;
}

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getHedVersions()
    hideOtherHEDVersionFileUpload()
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitHedStringForm() {
    let stringForm = document.getElementById("hedstring-form");
    let formData = new FormData(stringForm);
    clearFormFlashMessages();
    flashMessageOnScreen('HED string is being processed ...', 'success', 'hedstring-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_hedstring_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (hedInfo) {
                clearFormFlashMessages();
                if (hedInfo['hedstring-result']) {
                    $('#hedstring-result').val(hedInfo['hedstring-result'])
                    flashMessageOnScreen('Processing completed', 'success', 'hedstring-submit-flash')
                } else if (hedInfo['message'])
                    flashMessageOnScreen(hedInfo['message'], 'error', 'hedstring-submit-flash')
                else {
                    flashMessageOnScreen('Server could not respond to this request', 'error', 'hedstring-submit-flash')
                }
            },
            error: function (jqXHR) {
                flashMessageOnScreen(jqXHR.responseJSON.message, 'error', 'hedstring-submit-flash')
            }
        }
    )
}