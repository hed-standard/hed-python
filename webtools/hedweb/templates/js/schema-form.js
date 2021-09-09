const SCHEMA_XML_EXTENSION = 'xml';
const SCHEMA_MEDIAWIKI_EXTENSION = 'mediawiki';
const DEFAULT_XML_URL = "https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml";

$(function () {
    prepareForm();
});

/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#schema_file').on('change', function () {
    updateFileLabel($('#schema_file').val(), '#schema_file_display_name');
    $('#schema_file_option').prop('checked', true);
    clearSchemaSubmitFlash()
    updateForm();
});

$('#schema_url').on('change', function () {
    updateFileLabel($('#schema_url').val(), '#schema_url_display_name');
    $('#schema_url_option').prop('checked', true);
    clearSchemaSubmitFlash()
    updateForm();
});

/**
 * Submits the form for conversion if we have a valid file.
 */
$('#schema_submit').on('click', function () {
    if (getSchemaFilename() === "") {
        flashMessageOnScreen('No valid source input file.  See above.', 'error',
            'schema_submit_flash')
    } else {
        submitSchemaForm();
    }
});


$('#schema_file_option').on('change', function () {
    updateForm();
});

$('#schema_url_option').on('change',function () {
    updateForm();
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#schema_form')[0].reset();
    $('#schema_url_option').prop('checked', false);
    $('#schema_file_option').prop('checked', false);
}

/**
 * Resets the flash messages that aren't related to the form submission.
 A * @param {String} message - If true, reset the flash message related to the submit button.
 */
function clearFormFlashMessages(resetSubmitFlash) {
    flashMessageOnScreen('', 'success', 'schema_file_flash');
    flashMessageOnScreen('', 'success', 'schema_url_flash');
    if (resetSubmitFlash) {
        flashMessageOnScreen('', 'success', 'schema_submit_flash');
    }
}

function clearSchemaSubmitFlash() {
    flashMessageOnScreen('', 'success', 'schema_submit_flash')
}

function convertToOutputName(original_filename) {
    let file_parts = splitExt(original_filename);
    let basename = file_parts[0]
    let extension = file_parts[1]
    let new_extension = 'bad'
    if (extension === SCHEMA_XML_EXTENSION) {
        new_extension = SCHEMA_MEDIAWIKI_EXTENSION
    } else if (extension === SCHEMA_MEDIAWIKI_EXTENSION) {
        new_extension = SCHEMA_XML_EXTENSION
    }

    return basename + "." + new_extension
}

function getSchemaFilename() {
    let checkRadio = document.querySelector('input[name="schema_upload_options"]:checked');
    if (checkRadio == null) {
        flashMessageOnScreen('No source file specified.', 'error', 'schema_url_flash');
        return "";
    }
    let checkRadioVal = checkRadio.id
    let schemaFile = $('#schema_file');
    let schemaFileIsEmpty = schemaFile[0].files.length === 0;
    if (checkRadioVal === "schema_file_option") {
        if (schemaFileIsEmpty) {
            flashMessageOnScreen('Schema file not specified.', 'error', 'schema_file_flash');
            return '';
        }

        return schemaFile[0].files[0].name;
    }

    let schemaUrl = $('#schema_url').val();
    let schemaUrlIsEmpty = schemaUrl === "";
    if (checkRadioVal === "schema_url_option") {
        if (schemaUrlIsEmpty) {
            flashMessageOnScreen('URL not specified.', 'error', 'schema_url_flash');
            return '';
        }
        return urlFileBasename(schemaUrl);
    }
    return '';
}

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    $('#schema_url').val(DEFAULT_XML_URL);
}


/**
 * Submit the form and return the conversion results as an attachment
 */
function submitSchemaForm() {
    let schemaForm = document.getElementById("schema_form");
    let formData = new FormData(schemaForm);
    let display_name = convertToOutputName(getSchemaFilename())
    clearFormFlashMessages(false);
    flashMessageOnScreen('Schema is being processed...', 'success',
        'schema_submit_flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.schema_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: "text",
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'schema_submit_flash')
            },
            error: function (xhr, status, errorThrown) {
                getResponseFailure(xhr, status, errorThrown, display_name, 'schema_submit_flash')
            }
        }
    )
    ;
}


function updateForm() {
     let filename = getSchemaFilename();
     let isXMLFilename = fileHasValidExtension(filename, [SCHEMA_XML_EXTENSION]);
     let isMediawikiFilename = fileHasValidExtension(filename, [SCHEMA_MEDIAWIKI_EXTENSION]);

     let hasValidFilename = false;
     if (isXMLFilename) {
        $('#schema-conversion-submit').html("Convert to mediawiki")
        hasValidFilename = true;
     } else if (isMediawikiFilename) {
        $('#schema-conversion-submit').html("Convert to XML");
        hasValidFilename = true;
     } else {
        $('#schema-conversion-submit').html("Convert Format");
     }

     let urlChecked = document.getElementById("schema_url_option").checked;
     if (!urlChecked || hasValidFilename) {
        flashMessageOnScreen("", 'success', 'schema_url_flash')
     }
     let uploadChecked = document.getElementById("schema_file_option").checked;
     if (!uploadChecked || hasValidFilename) {
        flashMessageOnScreen("", 'success', 'schema_file_flash')
     }

     if (filename && urlChecked && !hasValidFilename) {
        flashMessageOnScreen('Please choose a valid schema url (.xml, .mediawiki)', 'error',
        'schema_url_flash');
     }

     if (filename && uploadChecked && !hasValidFilename) {
         flashMessageOnScreen('Please upload a valid schema file (.xml, .mediawiki)', 'error',
        'schema_file_flash');
     }

     if (!uploadChecked && !urlChecked) {
        flashMessageOnScreen('No source file specified.', 'error', 'schema_file_flash');
     }

     flashMessageOnScreen('', 'success', 'schema_submit_flash')
}


function urlFileBasename(url) {
    let urlObj = null
    try {
        urlObj = new URL(url)
    } catch (err) {
        if (err instanceof TypeError) {
            flashMessageOnScreen(err.message, 'error', 'schema_url_flash');
            return ""
        } else {
            flashMessageOnScreen(err.message, 'error', 'schema_file_flash');
            return ""
        }
    }
    let pathname = urlObj.pathname;
    let index = pathname.lastIndexOf('/');
    return (-1 !== index) ? pathname.substring(index + 1) : pathname;
}
