const SCHEMA_XML_EXTENSION = 'xml';
const SCHEMA_MEDIAWIKI_EXTENSION = 'mediawiki';
const DEFAULT_XML_URL = "https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml";

$(function () {
    prepareForm();
});

/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#schema-file').on('change', function () {
    updateFileLabel($('#schema-file').val(), '#schema-file-display-name');
    $('#schema-file-option').prop('checked', true);
    clearSchemaSubmitFlash()
    updateForm();
});

$('#schema-url').on('change', function () {
    updateFileLabel($('#schema-url').val(), '#schema-url-display-name');
    $('#schema-url-option').prop('checked', true);
    clearSchemaSubmitFlash()
    updateForm();
});

/**
 * Submits the form for conversion if we have a valid file.
 */
$('#schema-submit').on('click', function () {
    if (getSchemaFilename() === "") {
        flashMessageOnScreen('No valid source input file.  See above.', 'error',
            'schema-submit-flash')
    } else {
        submitSchemaForm();
    }
});


$('#schema-file-option').on('change', function () {
    updateForm();
});

$('#schema-url-option').on('change',function () {
    updateForm();
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#schema-form')[0].reset();
    $('#schema-url-option').prop('checked', false);
    $('#schema-file-option').prop('checked', false);
}

/**
 * Resets the flash messages that aren't related to the form submission.
 A * @param {String} message - If true, reset the flash message related to the submit button.
 */
function clearFormFlashMessages(resetSubmitFlash) {
    flashMessageOnScreen('', 'success', 'schema-file-flash');
    flashMessageOnScreen('', 'success', 'schema-url-flash');
    if (resetSubmitFlash) {
        flashMessageOnScreen('', 'success', 'schema-submit-flash');
    }
}

function clearSchemaSubmitFlash() {
    flashMessageOnScreen('', 'success', 'schema-submit-flash')
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
    let checkRadio = document.querySelector('input[name="schema-upload-options"]:checked');
    if (checkRadio == null) {
        flashMessageOnScreen('No source file specified.', 'error', 'schema-url-flash');
        return "";
    }
    let checkRadioVal = checkRadio.id
    let schemaFile = $('#schema-file');
    let schemaFileIsEmpty = schemaFile[0].files.length === 0;
    if (checkRadioVal === "schema-file-option") {
        if (schemaFileIsEmpty) {
            flashMessageOnScreen('Schema file not specified.', 'error', 'schema-file-flash');
            return '';
        }

        return schemaFile[0].files[0].name;
    }

    let schemaUrl = $('#schema-url').val();
    let schemaUrlIsEmpty = schemaUrl === "";
    if (checkRadioVal === "schema-url-option") {
        if (schemaUrlIsEmpty) {
            flashMessageOnScreen('URL not specified.', 'error', 'schema-url-flash');
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
    $('#schema-url').val(DEFAULT_XML_URL);
}


/**
 * Submit the form and return the conversion results as an attachment
 */
function submitSchemaForm() {
    let schemaForm = document.getElementById("schema-form");
    let formData = new FormData(schemaForm);
    let display_name = convertToOutputName(getSchemaFilename())
    clearFormFlashMessages(false);
    flashMessageOnScreen('Schema is being processed...', 'success',
        'schema-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_schema_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: "text",
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'schema-submit-flash')
            },
            error: function (download, status, xhr) {
                getResponseFailure(download, xhr, display_name, 'schema-submit-flash')
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

     let urlChecked = document.getElementById("schema-url-option").checked;
     if (!urlChecked || hasValidFilename) {
        flashMessageOnScreen("", 'success', 'schema-url-flash')
     }
     let uploadChecked = document.getElementById("schema-file-option").checked;
     if (!uploadChecked || hasValidFilename) {
        flashMessageOnScreen("", 'success', 'schema-file-flash')
     }

     if (filename && urlChecked && !hasValidFilename) {
        flashMessageOnScreen('Please choose a valid schema url (.xml, .mediawiki)', 'error',
        'schema-url-flash');
     }

     if (filename && uploadChecked && !hasValidFilename) {
         flashMessageOnScreen('Please upload a valid schema file (.xml, .mediawiki)', 'error',
        'schema-file-flash');
     }

     if (!uploadChecked && !urlChecked) {
        flashMessageOnScreen('No source file specified.', 'error', 'schema-file-flash');
     }

     flashMessageOnScreen('', 'success', 'schema-submit-flash')
}


function urlFileBasename(url) {
    let urlObj = null
    try {
        urlObj = new URL(url)
    } catch (err) {
        if (err instanceof TypeError) {
            flashMessageOnScreen(err.message, 'error', 'schema-url-flash');
            return ""
        } else {
            flashMessageOnScreen(err.message, 'error', 'schema-file-flash');
            return ""
        }
    }
    let pathname = urlObj.pathname;
    let index = pathname.lastIndexOf('/');
    return (-1 !== index) ? pathname.substring(index + 1) : pathname;
}
