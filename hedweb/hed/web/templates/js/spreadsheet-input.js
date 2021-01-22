/**
 * This code handles the input of a spreadsheet name and worksheet names and displays table headers. It has
 * the form handling for spreadsheet-input.html.
 * @type {string[]}
 */
const EXCEL_FILE_EXTENSIONS = ['xlsx', 'xls'];
const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];
const spreadsheetInputIDs = ['spreadsheet-file', 'spreadsheet-display-name', 'spreadsheet-flash',
                             'worksheet-name', 'columns-names-table']

/**
 * Spreadsheet event handler function. Checks if the file uploaded has a valid spreadsheet extension.
 */
$('#spreadsheet-file').on('change', function () {
    let spreadsheet = $('#spreadsheet-file');
    let spreadsheetPath = spreadsheet.val();
    let spreadsheetFile = spreadsheet[0].files[0];
    resetFormFlashMessages();
    if (cancelWasPressedInChromeFileUpload(spreadsheetPath)) {
        resetForm();
    }
    else if (fileHasValidExtension(spreadsheetPath, EXCEL_FILE_EXTENSIONS)) {
        updateFileLabel(spreadsheetPath, '#spreadsheet-display-name');
        getWorksheetsInfo(spreadsheetFile);
    }
    else if (fileHasValidExtension(spreadsheetPath, TEXT_FILE_EXTENSIONS)) {
        updateFileLabel(spreadsheetPath, '#spreadsheet-display-name');
        clearWorksheetSelectbox();
        getColumnsInfo(spreadsheetFile, '');
    } else {
        resetForm();
        flashMessageOnScreen('Please upload a excel or text spreadsheet (.xlsx, .xls, .tsv, .txt)',
            'error', 'spreadsheet-flash');
    }
});


/**
 * Gets the information associated with the Excel worksheet that was newly selected. This information contains
 * the names of the columns and column indices that contain HED tags.
 */
$('#worksheet-name').on('change', function () {
    let spreadsheetFile = $('#spreadsheet-file')[0].files[0];
    let worksheetName = $('#worksheet-name option:selected').text();
    resetFormFlashMessages();
    getColumnsInfo(spreadsheetFile, worksheetName);
});

/**
 * Clears the spreadsheet file label.
 */
function clearSpreadsheetFileLabel() {
    $('#spreadsheet-display-name').text('');
}

/**
 * Clears the worksheet select box.
 */
function clearWorksheetSelectbox() {
    $('#worksheet-name').empty();
}

/**
 * Flash a message showing the number of worksheets in an Excel workbook.
 * @param {Array} worksheetNames - An array containing the names of Excel workbook worksheets.
 */
function flashWorksheetNumberMessage(worksheetNames) {
    let numberOfWorksheets = worksheetNames.length.toString();
    flashMessageOnScreen(numberOfWorksheets + ' worksheet(s) found',
        'success', 'worksheet-flash');
}

/**
 * Hides  columns section in the form.
 */
function hideColumnNames() {
    $('#column-names').hide();
}

/**
 * Populates a table containing one row.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 * @param {String} tableID - String containing the ID of the table
 */
function populateTableHeaders(columnNames, tableID) {
    let columnTable = $('#columns-names-table');
    let columnNamesRow = $('<tr/>');
    let numberOfColumnNames = columnNames.length;
    columnTable.empty();
    for (let i = 0; i < numberOfColumnNames; i++) {
        columnNamesRow.append('<td>' + columnNames[i] + '</td>');
    }
    columnTable.append(columnNamesRow);
}

/**
 * Populate the Excel worksheet select box.
 * @param {Array} worksheetNames - An array containing the Excel worksheet names.
 */
function populateWorksheetSelectbox(worksheetNames) {
    let worksheetSelectbox = $('#worksheet-name');
    let numberOfWorksheetNames = worksheetNames.length;
    worksheetSelectbox.empty();
    for (let i = 0; i < numberOfWorksheetNames; i++) {
        worksheetSelectbox.append(new Option(worksheetNames[i], worksheetNames[i]));
    }
}

/**
 * Resets the flash messages that aren't related to the form submission.
 */
function resetSpreadsheetFlashMessage() {
    flashMessageOnScreen('', 'success', 'spreadsheet-flash');
}

/**
 * Sets the components related to the spreadsheet columns when they are not empty.
 * @param {Array} columnNames - An array containing the spreadsheet column names.
 */
function showColumnNames(columnNames) {
    populateTableHeaders(columnNames);
    $('#column-names').show();
}

/**
 * Checks to see if a spreadsheet has been specified.
 */
function spreadsheetIsSpecified() {
    let spreadsheetFile = $('#spreadsheet-file');
    if (spreadsheetFile[0].files.length === 0) {
        flashMessageOnScreen('Spreadsheet is not specified.', 'error',
            'spreadsheet-flash');
        return false;
    }
    return true;
}