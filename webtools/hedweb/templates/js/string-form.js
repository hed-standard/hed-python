
$(function () {
    prepareForm();
});

/**
 * Set the options according to the action specified.
 */
$('#process_actions').change(function(){
    setOptions();
});

/**
 * Submits the form for tag comparison if we have a valid file.
 */
$('#string_submit').on('click', function () {
   if (!stringIsSpecified()) {
        flashMessageOnScreen('Must give a non-empty string.  See above.', 'error', 'string_submit_flash')
    } else {
        submitStringForm();
    }
});

/**
 * Resets the fields in the form.
 */
function clearForm() {
    $('#string_form')[0].reset();
    clearFormFlashMessages();
    setOptions();
    hideOtherSchemaVersionFileUpload()
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFormFlashMessages() {
    clearSchemaSelectFlashMessages();
    flashMessageOnScreen('', 'success', 'string_flash');
    flashMessageOnScreen('', 'success', 'string_submit_flash');
}

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getSchemaVersions()
    hideOtherSchemaVersionFileUpload()
}

/**
 * Set the options for the events depending on the action
 */
function setOptions() {
    if ($("#validate").is(":checked")) {
        hideOption("expand_defs");
        showOption("check_for_warnings");
    } else if ($("#to_long").is(":checked")) {
        hideOption("check_for_warnings");
        showOption("expand_defs");
    } else if ($("#to_short").is(":checked")) {
        hideOption("check_for_warnings");
        showOption("expand_defs");
    }
}

/**
 * Checks to see if a hedstring has been specified.
 */
function stringIsSpecified() {
/*    let jsonFile = $('#json_file');
    if (jsonFile[0].files.length === 0) {
        flashMessageOnScreen('JSON is not specified.', 'error', 'json_flash');
        return false;
    }*/
    return true;
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitStringForm() {
    let stringForm = document.getElementById("string_form");
    let formData = new FormData(stringForm);
    clearFormFlashMessages();
    flashMessageOnScreen('HED string is being processed ...', 'success', 'string_submit_flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.string_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (hedInfo) {
                clearFormFlashMessages();
                if (hedInfo['data']) {
                    $('#string_result').val(hedInfo['data'])
                } else {
                    $('#string_result').val('')
                }
                flashMessageOnScreen(hedInfo['msg'], hedInfo['msg_category'], 'string_submit_flash')
            },
            error: function (jqXHR) {
                flashMessageOnScreen(jqXHR.responseJSON.message, 'error', 'string_submit_flash')
            }
        }
    )
}