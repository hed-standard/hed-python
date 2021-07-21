const XML_FILE_EXTENSIONS = ['xml'];
const OTHER_VERSION_OPTION = 'Other';

/**
 * Event handler function when the HED version drop-down menu changes. If Other is selected the file browser
 * underneath it will appear. If another option is selected then it will disappear.
 */
$('#schema_version').on('change',function () {
    if ($(this).val() === OTHER_VERSION_OPTION) {
        $('#schema_other_version').show();
    } else {
        hideOtherSchemaVersionFileUpload()
    }
    flashMessageOnScreen('', 'success', 'schema_select_flash');
});

/**
 * Checks if the HED file uploaded has a valid extension.
 */
$('#schema_path').on('change', function () {
    let hedSchema = $('#schema_path');
    let hedPath = hedSchema.val();
    let hedFile = hedSchema[0].files[0];
    if (fileHasValidExtension(hedPath, XML_FILE_EXTENSIONS)) {
        getVersionFromSchemaFile(hedFile);
        updateFileLabel(hedPath, '#schema_display_name');
    } else {
        flashMessageOnScreen('Please upload a valid schema file (.xml)', 'error',
            'schema_select_flash')
    }
})

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function clearSchemaSelectFlashMessages() {
    flashMessageOnScreen('', 'success', 'schema_select_flash');
}

/**
 * Gets the HED versions that are in the HED version drop-down menu.
 */
function getSchemaVersions() {
    $.ajax({
            type: 'GET',
            url: "{{url_for('route_blueprint.schema_versions_results')}}",
            contentType: false,
            processData: false,
            dataType: 'json',
            success: function (schemaInfo) {
                if (schemaInfo['schema_version_list']) {
                     populateSchemaVersionsDropdown(schemaInfo['schema_version_list']);
                } else if (schemaInfo['message'])
                    flashMessageOnScreen(schemaInfo['message'], 'error', 'schema_select_flash')
                else {
                    flashMessageOnScreen('Server could not retrieve HED versions. Please provide your own.',
                        'error', 'schema_select_flash')
                }
            },
            error: function (jqXHR) {
                flashMessageOnScreen('Server could retrieve HED schema versions. Please provide your own.',
                    'error', 'schema_select_flash');
            }
        }
    );
}

/**
 * Gets the version from the HED file that the user uploaded.
 * @param {Object} hedXMLFile - A HED XML file.
 */
function getVersionFromSchemaFile(hedXMLFile) {
    let formData = new FormData();
    formData.append('schema_path', hedXMLFile);
    $.ajax({
        type: 'POST',
        url: "{{ url_for('route_blueprint.schema_version_results')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (hedInfo) {
            if (hedInfo['schema_version']) {
                flashMessageOnScreen('Using HED version ' + hedInfo['schema_version'], 'success', 'schema_select_flash');
            } else if (hedInfo['message'])
                flashMessageOnScreen(hedInfo['message'], 'error', 'schema_select_flash')
            else {
                flashMessageOnScreen('Server could retrieve HED versions. Please provide your own.',
                        'error', 'schema_select_flash')
            }
        },
        error: function (jqXHR) {
            //console.log(jqXHR.responseJSON.message);
            flashMessageOnScreen('Could not get version number from HED XML file.',
                'error', 'schema_select_flash');
        }
    });
}


/**
 * Checks to see if a HED XML file is specified when the HED drop-down is set to "Other".
 */
function schemaSpecifiedWhenOtherIsSelected() {
    let hedFile = $('#schema_path');
    let hedFileIsEmpty = hedFile[0].files.length === 0;
    if ($('#schema_version').val() === OTHER_VERSION_OPTION && hedFileIsEmpty) {
        flashMessageOnScreen('Schema version is not specified.', 'error', 'schema_select_flash');
        return false;
    }
    return true;
}

/**
 * Hides the HED XML file upload.
 */
function hideOtherSchemaVersionFileUpload() {
    $('#schema_display_name').text('');
    $('#schema_other_version').hide();
}


/**
 * Populates the HED version drop-down menu.
 * @param {Array} hedVersions - An array containing the HED versions.
 */
function populateSchemaVersionsDropdown(hedVersions) {
    let hedVersionDropdown = $('#schema_version');
    $('#schema_version').empty()
    hedVersionDropdown.append('<option value=' + hedVersions[0] + '>' + hedVersions[0] + ' (Latest)</option>');
    for (let i = 1; i < hedVersions.length; i++) {
        hedVersionDropdown.append('<option value=' + hedVersions[i] + '>' + hedVersions[i] + '</option>');
    }
    hedVersionDropdown.append('<option value=' + OTHER_VERSION_OPTION + '>' + OTHER_VERSION_OPTION +
        '</option>');
}
