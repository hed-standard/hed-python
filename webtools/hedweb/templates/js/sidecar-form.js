
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
 * Submit the form on click if schema and json file specified.
 */
$('#sidecar_submit').on('click', function () {
    if (fileIsSpecified('#json_file', 'json_flash', 'JSON is not specified.' ) &&
        schemaSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#sidecar_form')[0].reset();
    setOptions();
    clearFlashMessages()
    clearJsonFileLabel();
    hideOtherSchemaVersionFileUpload()
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFlashMessages() {
    clearJsonInputFlashMessages();
    clearSchemaSelectFlashMessages();
    flashMessageOnScreen('', 'success', 'sidecar_submit_flash');
}

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getSchemaVersions()
    hideOtherSchemaVersionFileUpload();
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
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let sidecarForm = document.getElementById("sidecar_form");
    let formData = new FormData(sidecarForm);

    let sidecarFile = getJsonFileLabel();
    let display_name = convertToResultsName(sidecarFile, 'issues')
    clearFlashMessages();
    flashMessageOnScreen('Sidecar is being processed ...', 'success', 'sidecar_submit_flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.sidecar_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'sidecar_submit_flash')
            },
            error: function (xhr, status, errorThrown) {
                getResponseFailure(xhr, status, errorThrown, display_name, 'sidecar_submit_flash')
            }
        }
    )
}
