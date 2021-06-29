
function clearColumnInfoFlashMessages() {
    flashMessageOnScreen('', 'success', 'tag_columns_flash');
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
function setColumnsInfo(columnsFile, flashMessageLocation, worksheetName=undefined, hasColumnNames=true, repopulateWorksheet=true, showIndices=true) {
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
                if (hasColumnNames && !showIndices) {
                    showColumnNames(info['column_names']);
                }
                if (showIndices) {
                   showColumnPrefixes(info['column_names'], hasColumnNames);
                }
            }
        },
        error: function () {
            flashMessageOnScreen('File could not be processed.', 'error', flashMessageLocation);
        }
    });
}

/**
 * Hides  columns section in the form.
 */
function hideColumnInfo(showIndices = true) {
    if (showIndices) {
        $('#column_prefixes').hide()
    } else {
        $('#column_names').hide();
    }
}


/**
 * Clears tag column text boxes.
 */
function removeColumnInfo(showIndices = true) {
    if (showIndices) {
        $('#column_prefix_table').children().remove();
    } else {
        $('#column_names_table').children().remove();
    }
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
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 * @param {bool} hasColumnNames - A boolean indicating whether the first row represents column names
 */
function showColumnPrefixes(columnNames, hasColumnNames=true) {
    $('#column_prefixes').show();
    let columnPrefixTable = $('#column_prefix_table');
    let columnHeader = '<table><tr><th>Has tags</th><th>Column names</th><th>Tag prefix to use</th></tr>'
    let numberOfColumnNames = columnNames.length;
    columnPrefixTable.empty();
    let contents = columnHeader;
    for (let i = 1; i <= numberOfColumnNames; i++) {
        let column = "Column_" + i
        let columnName = columnNames[i-1]
        if (!hasColumnNames || columnNames[i-1] === "") {
            columnName = column
        }
        let checkName = column + "_check";
        let checkInput = column + "_input";
        let row = '<tr><td><input type="checkbox" name="' + checkName + '" id="' + checkName + '" checked></td>' +
            '<td>' + columnName + '</td>' +
            '<td><input class="wide_text" type="text" name="' + checkInput + '" id="' + checkInput + '" size="50"></td></tr>';
        contents = contents + row;
    }
    columnPrefixTable.append(contents + '</table>')
}
