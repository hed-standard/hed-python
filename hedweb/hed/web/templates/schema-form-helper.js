const SCHEMA_XML_EXTENSION = 'xml';
const SCHEMA_MEDIAWIKI_EXTENSION = 'mediawiki';
const DEFAULT_XML_URL = "https://raw.githubusercontent.com/hed-standard/hed-specification/HED-restructure/hedxml/HED7.1.1.xml";

$(document).ready(function () {
    prepareSchemaForm();
});

/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#schema-file').change(function () {
    updateSchemaFileLabel($('#schema-file').val());
    $('#schema-file-option').prop('checked', true);
    clearSchemaSubmitFlash()
    updateFormGui();
});

$('#schema-url').change(function () {
    updateSchemaUrlLabel($('#schema-url').val());
    $('#schema-url-option').prop('checked', true);
    clearSchemaSubmitFlash()
    updateFormGui();
});

/**
 * Submits the form for conversion if we have a valid file.
 */
$('#schema-conversion-submit').click(function () {
    if (getSchemaFilename() === "") {
        flashMessageOnScreen('No valid source input file.  See above.', 'error',
            'schema-submit-flash')
    } else {
        submitSchemaConversionForm();
    }
});

/**
 * Submits the form for tag comparison if we have a valid file.
 */
$('#schema-duplicate-tag-submit').click(function () {
   if (getSchemaFilename() === "") {
        flashMessageOnScreen('No valid source schema file.  See above.', 'error',
            'schema-submit-flash')
    } else {
        submitSchemaDuplicateTagForm();
    }
});

$('#schema-file-option').change(function () {
    updateFormGui();
});

$('#schema-url-option').change(function () {
    updateFormGui();
});

function clearSchemaSubmitFlash() {
    flashMessageOnScreen('', 'success', 'schema-submit-flash')
}

function convertToOutputName(original_filename) {
    let file_parts = splitExt(original_filename);
    let basename = file_parts[0]
    let extension = file_parts[1]
    let new_extension = 'bad'
    if (extension == SCHEMA_XML_EXTENSION) {
        new_extension = SCHEMA_MEDIAWIKI_EXTENSION
    } else if (extension == SCHEMA_MEDIAWIKI_EXTENSION) {
        new_extension = SCHEMA_XML_EXTENSION
    }

    return basename + "." + new_extension
}

function convertToResultsName(original_filename) {
    let file_parts = splitExt(original_filename);
    let basename = file_parts[0]
    return "duplicate_tags_" + basename + ".txt"
}

/**
 * Compares the file extension of the file at the specified path to an Array of accepted file extensions.
 * @param {String} filePath - A path to a file.
 * @param {Array} acceptedFileExtensions - An array of accepted file extensions.
 * @returns {boolean} - True if the file has an accepted file extension.
 */
function fileHasValidExtension(filePath, acceptedFileExtensions) {
    let fileExtension = filePath.split('.').pop();
    if ($.inArray(fileExtension.toLowerCase(), acceptedFileExtensions) != -1) {
        return true;
    }
    return false;
}

/**
 * Flash a message on the screen.
 * @param {String} message - The message that will be flashed on the screen.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 */
function flashMessageOnScreen(message, category, flashMessageElementId) {
    let flashMessage = document.getElementById(flashMessageElementId);
    flashMessage.innerHTML = message;
    setFlashMessageCategory(flashMessage, category);
}

function getSchemaFilename() {
    let checkRadio = document.querySelector('input[name="schema-upload-options"]:checked');
    if (checkRadio == null) {
        flashMessageOnScreen('No source file specified.', 'error',
            'schema-url-flash');
        return "";
    }
    let checkRadioVal = checkRadio.id
    let schemaFile = $('#schema-file');
    let schemaFileIsEmpty = schemaFile[0].files.length === 0;
    if (checkRadioVal == "schema-file-option") {
        if (schemaFileIsEmpty) {
            flashMessageOnScreen('Schema file not specified.', 'error',
                'schema-file-flash');
            return '';
        }
        return schemaFile[0].files[0].name;
    }

    let schemaUrl = $('#schema-url').val();
    let schemaUrlIsEmpty = schemaUrl === "";
    if (checkRadioVal == "schema-url-option") {
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
function prepareSchemaForm() {
    resetForm();
    $('#schema-url').val(DEFAULT_XML_URL);
}

/**
 * Resets the flash messages that aren't related to the form submission.
 A * @param {String} message - If true, reset the flash message related to the submit button.
 */
function resetFlashMessages(resetSubmitFlash) {
    flashMessageOnScreen('', 'success', 'schema-file-flash');
    flashMessageOnScreen('', 'success', 'schema-url-flash');
    if (resetSubmitFlash) {
        flashMessageOnScreen('', 'success', 'schema-submit-flash');
    }
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#schema-form')[0].reset();
    $('#schema-url-option').prop('checked', false);
    $('#schema-file-option').prop('checked', false);
}

/**
 * Flash a message on the screen.
 * @param {Object} flashMessage - The li element containing the flash message.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 */
function setFlashMessageCategory(flashMessage, category) {
    if ("error" === category) {
        flashMessage.style.backgroundColor = 'lightcoral';
    } else if ("success" === category) {
        flashMessage.style.backgroundColor = 'palegreen';
    } else if ("warning" === category) {
        flashMessage.style.backgroundColor = 'darkorange';
    } else {
        flashMessage.style.backgroundColor = '#f0f0f5';
    }
}

function splitExt(filename) {
    const index = filename.lastIndexOf('.');
    return (-1 !== index) ? [filename.substring(0, index), filename.substring(index + 1)] : [filename, ''];
}

/**
 * Submit the form and return the conversion results as an attachment
 */
function submitSchemaConversionForm() {
    let schemaForm = document.getElementById("schema-form");
    let formData = new FormData(schemaForm);
    let download_display_name = convertToOutputName(getSchemaFilename())
    resetFlashMessages(false);
    flashMessageOnScreen('Specification is being converted...', 'success',
        'schema-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_schema_conversion_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: "text",
            success: function (downloaded_file) {
                  flashMessageOnScreen('', 'success', 'schema-submit-flash');
                  triggerDownloadBlob(downloaded_file, download_display_name);
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error',
                        'schema-submit-flash');
                } else {
                    flashMessageOnScreen('XML could not be processed', 'error',
                        'schema-submit-flash');
                }
            }
        }
    )
    ;
}

function submitSchemaDuplicateTagForm() {
    let schemaForm = document.getElementById("schema-form");
    let formData = new FormData(schemaForm);
    let download_display_name = convertToResultsName(getSchemaFilename())
    resetFlashMessages(false);
    flashMessageOnScreen('Searching for duplicates in schema...', 'success',
        'schema-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_duplicate_tag_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (downloaded_file) {
                  if (downloaded_file) {
                      flashMessageOnScreen('', 'success', 'schema-submit-flash');
                      triggerDownloadBlob(downloaded_file, download_display_name);
                  } else {
                      flashMessageOnScreen('No duplicate tags found.', 'success',
                          'schema-submit-flash');
                  }
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error',
                        'schema-submit-flash');
                } else {
                    flashMessageOnScreen('XML could not be processed',
                        'error','schema-submit-flash');
                }
            }
        }
    )
    ;
}


/**
 * Trigger the "save as" dialog for a text blob to save as a file with display name.
 */
function triggerDownloadBlob(download_text_blob, display_name) {
    const url = window.URL.createObjectURL(new Blob([download_text_blob]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', display_name);
    document.body.appendChild(link);
    link.click();
}

function updateFormGui() {
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

/**
 * Updates the HED file label.
 * @param {String} hedPath - The path to the HED XML file.
 */
function updateSchemaFileLabel(hedPath) {
    let hedFilename = hedPath.split('\\').pop();
    $('#schema-file-display-name').text(hedFilename);
}

/**
 * Updates the HED file label.
 * @param {String} hedPath - The path to the HED XML file.
 */
function updateSchemaUrlLabel(hedPath) {
    let hedFilename = hedPath.split('\\').pop();
    $('#schema-url-display-name').text(hedFilename);
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
