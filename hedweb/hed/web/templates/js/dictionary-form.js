
$(function () {
    prepareForm();
});

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#dictionary-validation-submit').on('click', function () {
    if (jsonIsSpecified() && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    resetForm();
    getHEDVersions()
    hideOtherHEDVersionFileUpload();
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function resetFormFlashMessages() {
    clearJsonFlashMessage();
    clearHEDFlashMessage();
    flashMessageOnScreen('', 'success', 'dictionary-validation-submit-flash');
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#dictionary-form')[0].reset();
    clearJsonFileLabel();
    hideOtherHEDVersionFileUpload()
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let dictionaryForm = document.getElementById("dictionary-form");
    let formData = new FormData(dictionaryForm);

    let dictionaryFile = getJsonFileLabel();
    let display_name = convertToResultsName(dictionaryFile, 'issues')
    resetFormFlashMessages();
    flashMessageOnScreen('Dictionary is being validated ...', 'success', 'dictionary-validation-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_dictionary_validation_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (downloaded_file) {
                  if (downloaded_file) {
                      flashMessageOnScreen('', 'success', 'dictionary-validation-submit-flash');
                      triggerDownloadBlob(downloaded_file, display_name);
                  } else {
                      flashMessageOnScreen('No errors found.', 'success', 'dictionary-validation-submit-flash');
                  }
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error', 'dictionary-validation-submit-flash');
                } else {
                    flashMessageOnScreen('Dictionary not processed', 'error','dictionary-validation-submit-flash');
                }
            }
        }
    )
}
