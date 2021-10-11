
function clearColumnInfoFlashMessages() {
    if ($('#tag_columns_flash').length) {
        flashMessageOnScreen('', 'success', 'tag_columns_flash')
    }
}

/**
 * Gets information a file with columns. This information the names of the columns in the specified
 * sheet_name and indices that contain HED tags.
 * @param {File} columnsFile - File object with columns.
 * @param {string} flashMessageLocation - ID name of the flash message element in which to display errors.
 * @param {string} worksheetName - Name of sheet_name or undefined.
 * @param {boolean} hasColumnNames - If true has column names
 * @param {string} displayType - Show boxes with indices.
 * @returns {Array} - Array of worksheet names
 */
function setColumnsInfo(columnsFile, flashMessageLocation, worksheetName=undefined, hasColumnNames=true,
                        displayType="show_columns") {
    if (columnsFile == null)
        return null
    let formData = new FormData();
    formData.append('columns_file', columnsFile);
    if (hasColumnNames) {
        formData.append('has_column_names', 'on')
    }
    if (worksheetName !== undefined) {
        formData.append('worksheet_selected', worksheetName)
    }
    let worksheet_names = null;
    $.ajax({
        type: 'POST',
        url: "{{url_for('route_blueprint.columns_info_results')}}",
        data: formData,
        contentType: false,
        processData: false,
        dataType: 'json',
        async: false,
        success: function (info) {
            if (info['message']) {
                flashMessageOnScreen(info['message'], 'error', flashMessageLocation);
            } else {
                showColumnInfo(info['column_list'], hasColumnNames, displayType);
                worksheet_names = info['worksheet_names'];
            }
        },
        error: function () {
            flashMessageOnScreen('File could not be processed.', 'error', flashMessageLocation);
        }
    });
    return worksheet_names;
}

/**
 * Hides  columns section in the form.
 * @param {string} displayType - One of show_columns, show_indices, or show_events
 */
function hideColumnInfo(displayType="show_columns") {
    let display_tag = "#" + displayType;
    if ($(display_tag).length) {
        $(display_tag).hide()
    }
}


/**
 * Clears tag column text boxes.
 * @param {string} displayType - One of show_columns, show_indices, or show_events
 */
function removeColumnInfo(displayType="show_columns") {
    let table_tag = "#" + displayType + "_table";
    if ($(table_tag).length) {
        $(table_tag).children().remove();
    }
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnList - An array containing the spreadsheet column names.
 * @param {boolean} hasColumnNames - boolean indicating whether array has column names.
 * @param {string} displayType - string indicating type of display.
 */
function showColumnInfo(columnList, hasColumnNames= true, displayType="show_columns") {
    if (hasColumnNames && displayType === "show_columns") {
        showColumns(columnList);
    } else if (displayType === "show_indices") {
        showIndices(columnList, hasColumnNames);
    } else if (hasColumnNames && displayType === "show_events") {
        showEvents(columnList);
    }
}

/**
 * Shows the column names of the columns dictionary.
 * @param {Array} columnList - An array containing the file column names.
 */
function showColumns(columnList) {
    $('#show_columns').show();
    let columnNamesRow = $('<tr/>');

    for(const key of columnList) {
        columnNamesRow.append('<td>' + key + '</td>');
    }
    let columnTable = $('#show_columns_table');
    columnTable.empty();
    columnTable.append(columnNamesRow);
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnList - An dictionary with column names
 * @param {boolean} hasColumnNames - A boolean indicating whether the first row represents column names
 */
function showIndices(columnList, hasColumnNames= true) {
    $('#show_indices').show();
    let contents = '<tr><th>Has tags</th><th>Column names</th><th>Tag prefix to use (prefixes end in /)</th></tr>'
    let i = 1;
    for(const key of columnList) {
        let column = "column_" + i;
        let columnName = key;
        if (!hasColumnNames) {
            columnName = "column_" + i;
        }
        let checkName = column + "_check";
        let checkInput = column + "_input";
        let row = '<tr><td><input type="checkbox" name="' + checkName + '" id="' + checkName + '" checked></td>' +
            '<td>' + columnName + '</td>' +
            '<td><input class="wide_text"' + ' type="text" name="' + checkInput +
            '" id="' + checkInput + '" size="50"></td></tr>';
        contents = contents + row;
        i = i + 1;
    }
    let columnTable = $('#show_indices_table');
    columnTable.empty();
    columnTable.append(contents)
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnList - An array containing the spreadsheet column names.
 * @param {boolean} hasColumnNames - A boolean indicating whether the first row represents column names
 */
function showEvents(columnList, hasColumnNames=true) {
    $('#show_events').show();
    let columnEventsTable = $('#show_events_table');
    let contents = '<tr><th>Include?</th><th>Column name (unique entries)</th><th>Categorical?</th></tr>'
    columnEventsTable.empty();
    let i = 1;
    for(const key of columnList) {
        let column = "column_" + i;
        let columnName = key;
        if (!hasColumnNames) {
            columnName = column;
        }
        let useName = column + "_use";
        let categoryName = column + "_category";
        let columnField = column + "_name"
        let row = '<tr><td><input type="checkbox" name="' + useName + '" id="' + useName + '"></td>' +
            '<td>' + columnName  + '</td>' +
            '<td><input type="checkbox" name="' + categoryName + '" id="' + categoryName + '">' +
                '<input type="text" hidden id="' + columnField + '" name="' + columnField +
                '" value="' + columnName + '"</td></tr>';
        contents = contents + row;
        i = i + 1;
    }
    columnEventsTable.append(contents + '</table>')
}