const HED_XML_EXTENSION = 'xml';
const HED_MEDIAWIKI_EXTENSION = 'mediawiki';
const HED_FILE_EXTENSIONS = [HED_XML_EXTENSION, HED_MEDIAWIKI_EXTENSION];
const DEFAULT_XML_URL = "https://raw.githubusercontent.com/hed-standard/hed-specification/HED-restructure/hedxml/HED7.1.1.xml";
const URL_HED_OPTION = 'option_url';
const UPLOAD_HED_OPTION = 'option_upload';

$(document).ready(function () {
    prepareConversionForm();
});

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareConversionForm() {
    resetForm();
    $('#hed-xml-url').val(DEFAULT_XML_URL);
}

function update_form_gui() {
     var filename = getHedFilename();
     var isXMLFilename = fileHasValidExtension(filename, [HED_XML_EXTENSION]);
     var isMediawikiFilename = fileHasValidExtension(filename, [HED_MEDIAWIKI_EXTENSION]);

     var hasValidFilename = false;
     if (isXMLFilename) {
        $('#submit').html("Convert to mediawiki")
        hasValidFilename = true;
     } else if (isMediawikiFilename) {
        $('#submit').html("Convert to XML");
        hasValidFilename = true;
     } else {
        $('#submit').html("Convert...");
     }

     var urlChecked = document.getElementById("option_url").checked;
     if (!urlChecked || hasValidFilename) {
        flashMessageOnScreen("", 'success', 'hed-flash-url')
     }
     var uploadChecked = document.getElementById("option_upload").checked;
     if (!uploadChecked || hasValidFilename) {
        flashMessageOnScreen("", 'success', 'hed-flash')
     }

     if (filename && urlChecked && !hasValidFilename) {
        flashInvalidURLHEDExtensionMessage('hed-flash-url');
     }

     if (filename && uploadChecked && !hasValidFilename) {
         flashInvalidHEDExtensionMessage();
     }

     if (!uploadChecked && !urlChecked) {
        flashMessageOnScreen('No source file specified.', 'error', 'hed-flash');
     }

     flashMessageOnScreen('', 'success', 'submit-flash')
}


/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#hed-xml-filename').change(function () {
    var hed = $('#hed-xml-filename');
    var hedPath = hed.val();
    var hedFile = hed[0].files[0];
    updateHEDFileLabel(hedPath);
    var checkboxUpload = document.getElementById("option_upload");
    checkboxUpload.checked = true;
    update_form_gui();
});

$('#hed-xml-url').change(function () {
    var hed = $('#hed-xml-url');
    var hedURL = hed.val();
    var checkboxUpload = document.getElementById("option_url");
    checkboxUpload.checked = true;
    update_form_gui();
});

$('#option_url').change(function () {
    update_form_gui();
});

$('#option_upload').change(function () {
    update_form_gui();
});

function onURLModified(event){
    var checkboxURL = document.getElementById("option_url");
    checkboxURL.checked = true;

    clearSubmitFlash();
    update_form_gui();
}

function uncheckAllRadioButtons() {
    var checkboxURL = document.getElementById("option_url");
    checkboxURL.checked = false;
    var checkboxUpload = document.getElementById("option_upload");
    checkboxUpload.checked = false;
}

/**
 * Updates the HED file label.
 * @param {String} hedPath - The path to the HED XML file.
 */
function updateHEDFileLabel(hedPath) {
    var hedFilename = hedPath.split('\\').pop();
    $('#hed-filename').text(hedFilename);
}

/**
 * Flash message when HED XML file extension is invalid.
 */
function flashInvalidHEDExtensionMessage() {
    flashMessageOnScreen('Please upload a valid HED file (.xml, .mediawiki)', 'error', 'hed-flash');
}

/**
 * Flash message when HED XML file extension is invalid.
 */
function flashInvalidURLHEDExtensionMessage() {
    flashMessageOnScreen('Please choose a valid HED url (.xml, .mediawiki)', 'error', 'hed-flash-url');
}

/**
 * Resets the flash messages that aren't related to the form submission.
 A * @param {String} message - If true, reset the flash message related to the submit button.
 */
function resetFlashMessages(resetSubmitFlash) {
    flashMessageOnScreen('', 'success', 'hed-flash');
    flashMessageOnScreen('', 'success', 'hed-flash-url');
    if (resetSubmitFlash) {
        flashMessageOnScreen('', 'success', 'submit-flash');
    }
}



/**
 * Flash a message on the screen.
 * @param {String} message - The message that will be flashed on the screen.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 */
function flashMessageOnScreen(message, category, flashMessageElementId) {
    var flashMessage = document.getElementById(flashMessageElementId);
    flashMessage.innerHTML = message;
    setFlashMessageCategory(flashMessage, category);
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

/**
 * Checks to see if the user pressed cancel in chrome's file upload browser.
 * @param {String} filePath - A path to a file.
 * @returns {boolean} - True if the user selects cancel in chrome's file upload browser.
 */
function cancelWasPressedInChromeFileUpload(filePath) {
    return isEmptyStr(filePath) && (window.chrome)
}

/**
 * Resets the fields in the form.
 */
function resetForm() {
    $('#conversion-form')[0].reset();
    uncheckAllRadioButtons();
}



/**
 * Flash a submit message.
 * @param {Array} worksheetNames - An array containing the names of Excel workbook worksheets.
 */
function flashSubmitMessage() {
    resetFlashMessages(false);
    flashMessageOnScreen('Specification is being converted...', 'success', 'submit-flash')
}

function clearSubmitFlash() {
    flashMessageOnScreen('', 'success', 'submit-flash')
}

function getHedFilename() {
    var checkRadio = document.querySelector('input[name="upload_options"]:checked');
    if (checkRadio == null) {
        flashMessageOnScreen('No source file specified.', 'error', 'hed-flash');
        return "";
    }
    var checkRadioVal = checkRadio.id
    var hedFile = $('#hed-xml-filename');
    var hedFileIsEmpty = hedFile[0].files.length === 0;
    if (checkRadioVal == "option_upload") {
        if (hedFileIsEmpty) {
            flashMessageOnScreen('HED file is not specified.', 'error', 'hed-flash');
            return '';
        }
        return hedFile[0].files[0].name;
    }

    var hedUrl = $('#hed-xml-url').val();
    var hedUrlIsEmpty = hedUrl === "";
    if (checkRadioVal == "option_url") {
        if (hedUrlIsEmpty) {
            flashMessageOnScreen('URL not specified.', 'error', 'hed-flash-url');
            return '';
        }
        return urlFileBasename(hedUrl);
    }
    return '';
}

/**
 * Checks to see if a HED XML file is specified when the HED drop-down is set to "Other".
 */
function hedSpecifiedWhenOtherIsSelected() {
    var filename = getHedFilename()

    if (filename === "") {
        return false
    }
    return true
}

/**
 * Submits the form for conversion if we have a valid file.
 */
$('#submit').click(function () {
    if (hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    } else {
        flashMessageOnScreen('No valid source input file.  See above.', 'error', 'submit-flash')
    }
});

/**
 * Submits the form for tag comparison if we have a valid file.
 */
$('#submit_tag').click(function () {
    if (hedSpecifiedWhenOtherIsSelected()) {
        submitForm_tag_compare();
    } else {
        flashMessageOnScreen('No valid source input file.  See above.', 'error', 'submit-flash')
    }
});

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

/**
 * Submit the form and return the conversion results as an attachment
 */
function submitForm() {
    var conversionForm = document.getElementById("conversion-form");
    var formData = new FormData(conversionForm);
    var download_display_name = convert_to_output_name(getHedFilename())
    flashSubmitMessage();
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_conversion_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: "text",
            success: function (downloaded_file) {
                  flashMessageOnScreen('', 'success', 'submit-flash');
                  triggerDownloadBlob(downloaded_file, download_display_name);
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error','submit-flash');
                } else {
                    flashMessageOnScreen('XML could not be processed', 'error','submit-flash');
                }
            }
        }
    )
    ;
}

function submitForm_tag_compare() {
    var conversionForm = document.getElementById("conversion-form");
    var formData = new FormData(conversionForm);
    var download_display_name = convert_to_results_name(getHedFilename())
    flashSubmitMessage();
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_duplciate_tag_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (downloaded_file) {
                  if (downloaded_file) {
                      flashMessageOnScreen('', 'success', 'submit-flash');
                      triggerDownloadBlob(downloaded_file, download_display_name);
                  } else {
                      flashMessageOnScreen('No duplicate tags found.', 'success', 'submit-flash');
                  }
            },
            error: function (download_response) {
                console.log(download_response.responseText);
                if (download_response.responseText.length < 100) {
                    flashMessageOnScreen(download_response.responseText, 'error','submit-flash');
                } else {
                    flashMessageOnScreen('XML could not be processed', 'error','submit-flash');
                }
            }
        }
    )
    ;
}

/**
 * Checks to see if a string is empty. Empty meaning null or a length of zero.
 * @param {String} str - A string.
 * @returns {boolean} - True if the string is null or its length is 0.
 */
function isEmptyStr(str) {
    if (str === null || str.length === 0) {
        return true;
    }
    return false;
}

/**
 * Compares the file extension of the file at the specified path to an Array of accepted file extensions.
 * @param {String} filePath - A path to a file.
 * @param {Array} acceptedFileExtensions - An array of accepted file extensions.
 * @returns {boolean} - True if the file has an accepted file extension.
 */
function fileHasValidExtension(filePath, acceptedFileExtensions) {
    var fileExtension = filePath.split('.').pop();
    if ($.inArray(fileExtension.toLowerCase(), acceptedFileExtensions) != -1) {
        return true;
    }
    return false;
}

function split_ext(filename) {
    const index = filename.lastIndexOf('.');
    return (-1 !== index) ? [filename.substring(0, index), filename.substring(index + 1)] : [filename, ''];
}

function convert_to_output_name(original_filename) {
    var file_parts = split_ext(original_filename);
    var basename = file_parts[0]
    var extension = file_parts[1]
    if (extension == HED_XML_EXTENSION) {
        new_extension = HED_MEDIAWIKI_EXTENSION
    } else if (extension == HED_MEDIAWIKI_EXTENSION) {
        new_extension = HED_XML_EXTENSION
    }

    final_name = basename + "." + new_extension
    return final_name
}

function convert_to_results_name(original_filename) {
    var file_parts = split_ext(original_filename);
    var basename = file_parts[0]
    new_extension = "txt"
    final_name = "duplicate_tags_" + basename + "." + new_extension
    return final_name
}

function urlFileBasename(url) {
    try {
        var urlObj = new URL(url)
    } catch (err) {
        if (err instanceof TypeError) {
            flashMessageOnScreen(err.message, 'error', 'hed-flash-url');
            return ""
        } else {
            flashMessageOnScreen(err.message, 'error', 'hed-flash-url');
            return ""
        }
    }
    const pathname = urlObj.pathname;
    const index = pathname.lastIndexOf('/');
    return (-1 !== index) ? pathname.substring(index + 1) : pathname;
}

