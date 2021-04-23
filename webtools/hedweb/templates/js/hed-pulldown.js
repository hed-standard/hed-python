const XML_FILE_EXTENSIONS = ['xml'];
const HED_OTHER_VERSION_OPTION = 'Other';

/**
 * Event handler function when the HED version drop-down menu changes. If Other is selected the file browser
 * underneath it will appear. If another option is selected then it will disappear.
 */
$('#hed-version').on('change',function () {
    if ($(this).val() === HED_OTHER_VERSION_OPTION) {
        $('#hed-other-version').show();
    } else {
        hideOtherHEDVersionFileUpload()
    }
    flashMessageOnScreen('', 'success', 'hed-select-flash');
});

/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#hed-xml-file').on('change', function () {
    let hedSchema = $('#hed-xml-file');
    let hedPath = hedSchema.val();
    let hedFile = hedSchema[0].files[0];
    if (fileHasValidExtension(hedPath, XML_FILE_EXTENSIONS)) {
        getVersionFromHEDFile(hedFile);
        updateFileLabel(hedPath, '#hed-display-name');
    } else {
        flashMessageOnScreen('Please upload a valid HED file (.xml)', 'error',
            'hed-select-flash')
    }
})

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function clearHedSelectFlashMessages() {
    flashMessageOnScreen('', 'success', 'hed-select-flash');
}

/**
 * Gets the HED versions that are in the HED version drop-down menu.
 */
function getHedVersions() {
    $.ajax({
            type: 'GET',
            url: "{{url_for('route_blueprint.get_major_hed_versions')}}",
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (hedInfo) {
                if (hedInfo['hed-major-versions']) {
                     populateHEDVersionsDropdown(hedInfo['hed-major-versions']);
                } else if (hedInfo['message'])
                    flashMessageOnScreen(hedInfo['message'], 'error', 'hed-select-flash')
                else {
                    flashMessageOnScreen('Server could retrieve HED versions. Please provide your own.',
                        'error', 'hed-select-flash')
                }
            },
            error: function (jqXHR) {
                flashMessageOnScreen('Server could retrieve HED versions. Please provide your own.',
                    'error', 'hed-select-flash');
            }
        }
    );
}

/**
 * Gets the version from the HED file that the user uploaded.
 * @param {Object} hedXMLFile - A HED XML file.
 */
function getVersionFromHEDFile(hedXMLFile) {
    let formData = new FormData();
    formData.append('hed-xml-file', hedXMLFile);
    $.ajax({
        type: 'POST',
        url: "{{ url_for('route_blueprint.get_hed_version')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (hedInfo) {
            if (hedInfo['hed-version']) {
                flashMessageOnScreen('Using HED version ' + hedInfo['hed-version'], 'success', 'hed-select-flash');
            } else if (hedInfo['message'])
                flashMessageOnScreen(hedInfo['message'], 'error', 'hed-select-flash')
            else {
                flashMessageOnScreen('Server could retrieve HED versions. Please provide your own.',
                        'error', 'hed-select-flash')
            }
        },
        error: function (jqXHR) {
            //console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Could not get version number from HED XML file.',
                'error', 'hed-select-flash');
        }
    });
}


/**
 * Checks to see if a HED XML file is specified when the HED drop-down is set to "Other".
 */
function hedSpecifiedWhenOtherIsSelected() {
    let hedFile = $('#hed-xml-file');
    let hedFileIsEmpty = hedFile[0].files.length === 0;
    if ($('#hed-version').val() === HED_OTHER_VERSION_OPTION && hedFileIsEmpty) {
        flashMessageOnScreen('HED version is not specified.', 'error', 'hed-select-flash');
        return false;
    }
    return true;
}

/**
 * Hides the HED XML file upload.
 */
function hideOtherHEDVersionFileUpload() {
    $('#hed-display-name').text('');
    $('#hed-other-version').hide();
}


/**
 * Populates the HED version drop-down menu.
 * @param {Array} hedVersions - An array containing the HED versions.
 */
function populateHEDVersionsDropdown(hedVersions) {
    let hedVersionDropdown = $('#hed-version');
    $('#hed-version').empty()
    hedVersionDropdown.append('<option value=' + hedVersions[0] + '>' + hedVersions[0] + ' (Latest)</option>');
    for (let i = 1; i < hedVersions.length; i++) {
        hedVersionDropdown.append('<option value=' + hedVersions[i] + '>' + hedVersions[i] + '</option>');
    }
    hedVersionDropdown.append('<option value=' + HED_OTHER_VERSION_OPTION + '>' + HED_OTHER_VERSION_OPTION +
        '</option>');
}
