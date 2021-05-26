
function clearColumnInfoFlashMessages() {
    flashMessageOnScreen('', 'success', 'tag_columns_flash');
}
/**
 * Clears tag column text boxes.
 */
function clearTagColumnTextboxes() {
    $('.indices').val('');
}

/**
 * Checks to see if any entries in an array of names are empty.
 * @param {Array} names - An array containing a list of names.
 * @returns {boolean} - True if any of the names in the array are all empty.
 */
function columnNamesAreEmpty(names) {
    if (names !== undefined) {
        let numberOfNames = names.length;
        for (let i = 0; i < numberOfNames; i++) {
            if (!isEmptyStr(names[i].trim())) {
                return false;
            }
        }
    }
    return true;
}

/**
 * Gets information a file with columns. This information the names of the columns in the specified
 * worksheet and indices that contain HED tags.
 * @param {string} columnsFile - Name of a file with columns.
 * @param {string} flashMessageLocation - ID name of the flash message element in which to display errors.
 * @param {string} worksheetName - Name of worksheet or undefined.
 * @param {boolean} hasColumnNames - If true has column names
 * @param {boolean} repopulateWorksheet - If true repopulate the select pull down with worksheet names.
 * @param {boolean} showIndices - Show boxes with indices.
 */
function setColumnsInfo(columnsFile, flashMessageLocation, worksheetName=undefined, hasColumnNames, repopulateWorksheet=true, showIndices) {
    let formData = new FormData();
    formData.append('columns_file', columnsFile);
    if (worksheetName !== undefined) {
        formData.append('worksheet_selected', worksheetName)
    }
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.columns_info_results')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (info) {
            if (info['message'])
                flashMessageOnScreen(info['message'], 'error', flashMessageLocation)
            else {
                if (repopulateWorksheet) {
                    populateWorksheetDropdown(info['worksheet_names']);
                }
                if (hasColumnNames) {
                    showColumnNames(info['column_names'])
                }
                if (showIndices) {
                    setComponentsRelatedToColumns(info, hasColumnsNames, showIndices)
                }
            }
        },
        error: function () {
            flashMessageOnScreen('File could not be processed.', 'error', flashMessageLocation);
        }
    });
}


/**
 * Gets information a file with columns and populate the columnNames table.
 * @param {string} columnsFile - Name of the file with columns to be determined.
 * @param {string} worksheetName - Name of worksheet or undefined.
 * @param {string} flashMessageLocation - ID name of the flash message element in which to display errors.
 */
function setColumnsNameTable(columnsFile, worksheetName=undefined,  flashMessageLocation) {
    let formData = new FormData();
    formData.append('columns_file', columnsFile);
    if (worksheetName !== undefined) {
        formData.append('worksheet_selected', worksheetName)
    }
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.columns_info_results')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (info) {
        if (info['message'])
            flashMessageOnScreen(info['message'], 'error', flashMessageLocation)
        else
            showColumnNames(info['column_names'])
        },
        error: function () {
            flashMessageOnScreen('File could not be processed.', 'error', flashMessageLocation);
        }
    });
}

/**
 * Hides  columns section in the form.
 */
function hideColumnNames() {
    $('#column_names').hide();
}


/**
 * Populate the required tag column text boxes from the tag column indices found in the spreadsheet columns.
 * @param {object} requiredTagColumnIndices - A dictionary containing the required tag column indices found
 * in the spreadsheet. The keys are the column names and the values are the indices.
 */
function populateRequiredTagColumnTextboxes(requiredTagColumnIndices) {
    for (let key in requiredTagColumnIndices) {
        $('#' + key.toLowerCase() + '_column').val(requiredTagColumnIndices[key].toString());
    }
}

/**
 * Populate the tag column textbox from the tag column indices found in the spreadsheet columns.
 * @param {Array} tagColumnIndices - An integer array of tag column indices found in the spreadsheet
 * columns.
 */
function populateTagColumnsTextbox(tagColumnIndices) {
    $('#tag_columns').val(tagColumnIndices.sort().map(String));
}

/**
 * Clears tag column text boxes.
 */
function removeColumnTable() {
    $('#column_names_table').children().remove();
}

/**
 * Sets the components related to the Excel worksheet columns.
 * @param {JSON} columnsInfo - A JSON object containing information related to columns.
 * @param {boolean} hasColumns - if false then don't show the columns even if column names not empty
 * @param {boolean} showIndices -
 * This information contains the names of the columns and column indices that contain HED tags.
 */
function setComponentsRelatedToColumns(columnsInfo, hasColumns = true, showIndices = false) {
    clearTagColumnTextboxes();
    if (!hasColumns || columnNamesAreEmpty(columnsInfo['column_names']) ) {
        setComponentsRelatedToEmptyColumnNames();
    } else {
        setComponentsRelatedToNonEmptyColumnNames(columnsInfo['column_names']);
    }
    if (showIndices) {
        if (!tagColumnsIndicesAreEmpty(columnsInfo['COLUMN_INDICES'])) {
            populateTagColumnsTextbox(columnsInfo['COLUMN_INDICES']);
        }
        if (Object.keys(columnsInfo['required_column_indices']).length !== 0) {
            populateRequiredTagColumnTextboxes(columnsInfo['required_column_indices']);
        }
    }
}

/**
 * Sets the components related to Excel worksheet columns when they are all empty.
 */
function setComponentsRelatedToEmptyColumnNames() {
    clearTagColumnTextboxes();
    setHasColumnNamesCheckbox(false);
    hideColumnNames();
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function setComponentsRelatedToNonEmptyColumnNames(columnNames) {
    showColumnNames(columnNames)
    setHasColumnNamesCheckbox(true);
}

/**
 * Sets the spreadsheet has column names checkbox to false.
 * @param {boolean} value - is checked if true and unchecked if false
 */
function setHasColumnNamesCheckbox(value) {
    $('#has_column_names').prop('checked', value);
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function showColumnNames(columnNames) {
    $('#column_names').show();
    let columnTable = $('#column_names_table');
    let columnNamesRow = $('<tr/>');
    let numberOfColumnNames = columnNames.length;
    columnTable.empty();
    for (let i = 0; i < numberOfColumnNames; i++) {
        columnNamesRow.append('<td>' + columnNames[i] + '</td>');
    }
    columnTable.append(columnNamesRow);
}

/**
 * Checks to see if the worksheet tag column indices are empty.
 * @param {Array} tagColumnsIndices - An array containing the tag column indices based on the
 *                columns found in the spreadsheet.
 * @returns {boolean} - True if the spreadsheet tag column indices array is empty.
 */
function tagColumnsIndicesAreEmpty(tagColumnsIndices) {
    return tagColumnsIndices.length <= 0
}

/**
 * Checks to see if the tag columns textbox has valid input. Valid input is an integer or a comma-separated list of
 * integers that are the column indices in a Excel worksheet that contain HED tags.
 * @returns {boolean} - True if the tags columns textbox is valid.
 */
function tagColumnsTextboxIsValid() {
    let otherTagColumns = $('#tag_columns').val().trim();
    let valid = true;
    if (!isEmptyStr(otherTagColumns)) {
        let pattern = new RegExp('^([ \\d]+,)*[ \\d]+$');
        let valid = pattern.test(otherTagColumns);
        if (!valid) {
            flashMessageOnScreen('Tag column(s) must be a number or a comma-separated list of numbers',
                'error', 'tag_columns_flash')
        }
    }
    return valid;
}
