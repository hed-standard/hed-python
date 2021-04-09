
function clearColumnInfoFlashMessages() {
    flashMessageOnScreen('', 'success', 'tag-columns-flash');
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
 * Gets the columns information from a spreadsheet-like data file
 * @param {string} formID - ID of the form that is from
 * @param {string} pathID - Form ID of the path of a spreadsheet-like file with column names.
 * @returns string or array
 */

/**
 * Gets information a file with columns. This information the names of the columns in the specified
 * worksheet and indices that contain HED tags.
 * @param {Object} columnsFile - A file with columns.
 * @param {string} worksheetName - Name of worksheet or undefined.
 * @param {boolean} repopulateWorksheet - If true repopulate the select pull down with worksheet names.
 * @param {string} flashMessage - ID name of the flash message element in which to display errors.
 */
function setColumnsInfo(columnsFile, worksheetName=undefined, repopulateWorksheet=true, flashMessage) {
    let formData = new FormData();
    formData.append('columns-file', columnsFile);
    if (worksheetName !== undefined) {
        formData.append('worksheet-selected', worksheetName)
    }
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.get_columns_info_results')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        success: function (info) {
               if (info['message'])
                    flashMessageOnScreen(info['message'], 'error', flashMessage)
               else {
                   if (repopulateWorksheet) {
                       populateWorksheetDropdown(info['worksheet-names']);
                   }
                   let hasColumns = $('#has-column-names').prop('checked')
                   setComponentsRelatedToColumns(info, hasColumns, true);
               }
        },
        error: function () {
            flashMessageOnScreen('File could not be processed.', 'error', 'flashMessage');
        }
    });
}

/**
 * Hides  columns section in the form.
 */
function hideColumnNames() {
    $('#column-names').hide();
}


/**
 * Populate the required tag column textboxes from the tag column indices found in the spreadsheet columns.
 * @param {object} requiredTagColumnIndices - A dictionary containing the required tag column indices found
 * in the spreadsheet. The keys are the column names and the values are the indices.
 */
function populateRequiredTagColumnTextboxes(requiredTagColumnIndices) {
    for (let key in requiredTagColumnIndices) {
        $('#' + key.toLowerCase() + '-column').val(requiredTagColumnIndices[key].toString());
    }
}

/**
 * Populate the tag column textbox from the tag column indices found in the spreadsheet columns.
 * @param {Array} tagColumnIndices - An integer array of tag column indices found in the spreadsheet
 * columns.
 */
function populateTagColumnsTextbox(tagColumnIndices) {
    $('#tag-columns').val(tagColumnIndices.sort().map(String));
}

/**
 * Clears tag column text boxes.
 */
function removeColumnTable() {
    $('#column-names-table').children().remove();
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
    if (!hasColumns || columnNamesAreEmpty(columnsInfo['column-names']) ) {
        setComponentsRelatedToEmptyColumnNames();
    } else {
        setComponentsRelatedToNonEmptyColumnNames(columnsInfo['column-names']);
    }
    if (showIndices) {
        if (!tagColumnsIndicesAreEmpty(columnsInfo['tag-column-indices'])) {
            populateTagColumnsTextbox(columnsInfo['tag-column-indices']);
        }
        if (Object.keys(columnsInfo['required-tag-column-indices']).length !== 0) {
            populateRequiredTagColumnTextboxes(columnsInfo['required-tag-column-indices']);
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
    $('#has-column-names').prop('checked', value);
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function showColumnNames(columnNames) {
    $('#column-names').show();
    let columnTable = $('#column-names-table');
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
    let otherTagColumns = $('#tag-columns').val().trim();
    let valid = true;
    if (!isEmptyStr(otherTagColumns)) {
        let pattern = new RegExp('^([ \\d]+,)*[ \\d]+$');
        let valid = pattern.test(otherTagColumns);
        if (!valid) {
            flashMessageOnScreen('Tag column(s) must be a number or a comma-separated list of numbers',
                'error', 'tag-columns-flash')
        }
    }
    return valid;
}
