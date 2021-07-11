const EXCEL_FILE_EXTENSIONS = ['xlsx', 'xls'];
const TEXT_FILE_EXTENSIONS = ['tsv', 'txt'];
const VALID_FILE_EXTENSIONS = ['xlsx', 'xls', 'tsv', 'txt']

$(function () {
    prepareForm();
});

$('#has_column_names').on('change', function() {
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0];
    let worksheetName = $('#worksheet_name option:selected').text();
    if ($("#has_column_names").is(':checked')) {
            setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, true, false, true)
        } else  {
            setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, false, false, true)
        }
    }
);

/**
 * Spreadsheet event handler function. Checks if the file uploaded has a valid spreadsheet extension.
 */
$('#spreadsheet_file').on('change', function () {
    let spreadsheet = $('#spreadsheet_file');
    let spreadsheetPath = spreadsheet.val();
    let spreadsheetFile = spreadsheet[0].files[0];
    clearFlashMessages();
    removeColumnInfo(true)
    if (!fileHasValidExtension(spreadsheetPath, VALID_FILE_EXTENSIONS)) {
        clearForm();
        flashMessageOnScreen('Upload a valid spreadsheet (.xlsx, .tsv, .txt)', 'error', 'spreadsheet_flash');
        return
    }
    updateFileLabel(spreadsheetPath, '#spreadsheet_display_name');
    let worksheetName = undefined
    if (fileHasValidExtension(spreadsheetPath, EXCEL_FILE_EXTENSIONS)) {
        worksheetName = $('#worksheet_name option:selected').text();
        $('#worksheet_select').show();
    }
    else if (fileHasValidExtension(spreadsheetPath, TEXT_FILE_EXTENSIONS)) {
        $('#worksheet_name').empty();
        $('#worksheet_select').hide();
    }
    if ($("#has_column_names").is(':checked')) {
        setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, true, true, true)
    } else {
        setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, false, true, true)
    }
});

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#spreadsheet_submit').on('click', function () {
    if (fileIsSpecified('#spreadsheet_file', 'spreadsheet_flash', 'Spreadsheet is not specified.') &&
        schemaSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Gets the information associated with the Excel worksheet that was newly selected. This information contains
 * the names of the columns and column indices that contain HED tags.
 */
$('#worksheet_name').on('change', function () {
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0];
    let worksheetName = $('#worksheet_name option:selected').text();
    let hasColumnNames = $("#has_column_names").is(':checked')
    clearFlashMessages();
    setColumnsInfo(spreadsheetFile, 'spreadsheet_flash', worksheetName, hasColumnNames,false, true);
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#spreadsheet_form')[0].reset();
    $('#spreadsheet_display_name').text('');
    $('#worksheet_name').empty();
    $('#worksheet_select').hide();
    hideColumnInfo(true);
    hideOtherSchemaVersionFileUpload()
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFlashMessages() {
    clearColumnInfoFlashMessages();
    clearSchemaSelectFlashMessages();
    flashMessageOnScreen('', 'success', 'spreadsheet_flash');
    flashMessageOnScreen('', 'success', 'spreadsheet_submit_flash');
}

/**
 * Hides  worksheet select section in the form.
 */
function hideWorksheetSelect() {
    $('#worksheet_select').hide();
}

/**
 * Populate the Excel worksheet select box.
 * @param {Array} worksheetNames - An array containing the Excel worksheet names.
 */
function populateWorksheetDropdown(worksheetNames) {
    if (Array.isArray(worksheetNames) && worksheetNames.length > 0) {
        let worksheetDropdown = $('#worksheet_name');
        $('#worksheet_select').show();
        worksheetDropdown.empty();
        for (let i = 0; i < worksheetNames.length; i++) {
            $('#worksheet_name').append(new Option(worksheetNames[i], worksheetNames[i]) );
        }
    }
}

/**
 * Prepare the spreadsheet form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getSchemaVersions()
}

/**
 * Show the worksheet select section.
 */
function showWorksheetSelect() {
    $('#worksheet_select').show();
}

/**
 * Submit the form and return the results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let spreadsheetForm = document.getElementById("spreadsheet_form");
    let formData = new FormData(spreadsheetForm);
    let worksheetName = $('#worksheet_select option:selected').text();
    formData.append('worksheet_selected', worksheetName)
    let prefix = 'issues';
    if(worksheetName) {
        prefix = prefix + '_worksheet_' + worksheetName;
    }
    let spreadsheetFile = $('#spreadsheet_file')[0].files[0].name;
    let display_name = convertToResultsName(spreadsheetFile, prefix)
    clearFlashMessages();
    flashMessageOnScreen('Spreadsheet is being processed ...', 'success',
        'spreadsheet_submit_flash')
    if (fileHasValidExtension(spreadsheetFile, EXCEL_FILE_EXTENSIONS) &&
        !$("#command_validate").prop("checked")) {
        $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.spreadsheet_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            // xhrFields:{
            //     responseType: 'blob'
            // },
            xhr: function () {
                let xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function () {
                    if (xhr.readyState == 2) {
                        if (xhr.status == 200) {
                            xhr.responseType = "blob";
                        } else {
                            xhr.responseType = "text";
                        }
                    }
                };
                return xhr;
            },
            success: function (data, status, xqXHR) {
                //Convert the Byte Data to BLOB object.
                let bData = data;
                let types = xqXHR.getAllResponseHeaders();
                let type = xqXHR.getResponseHeader("Content-type");
                let url = window.URL || window.webkitURL;
                let blob = new Blob([bData], {type: type});
                let link = url.createObjectURL(blob);
                let a = $("<a />");
                a.attr("download", "temp.xlsx");
                a.attr("href", link);
                $("body").append(a);
                a[0].click();
                // let downloadUrl = URL.createObjectURL(data);
                // let ab = document.createElement("a");
                // ab.href = downloadUrl;
                // ab.download = "downloadFile.xlsx";
                // document.body.appendChild(ab);
            }
        })
        // $.ajax({
        //     type: 'POST',
        //     url: "{{url_for('route_blueprint.spreadsheet_results')}}",
        //     data: formData,
        //     contentType: false,
        //     processData: false,
        //     xhr: function () {
        //         let xhr = new XMLHttpRequest();
        //         xhr.onreadystatechange = function () {
        //             if (xhr.readyState == 2) {
        //                 if (xhr.status == 200) {
        //                     xhr.responseType = "blob";
        //                 } else {
        //                     xhr.responseType = "text";
        //                 }
        //             }
        //         };
        //         return xhr;
        //     },
        //     success: function (data, status, xqXHR) {
        //         //Convert the Byte Data to BLOB object.
        //         let bdata = data;
        //         let types = xqXHR.getAllResponseHeaders();
        //         let type = xqXHR.getResponseHeader("Content-type");
        //         // let bytes = new Array(bdata.length);
        //         // for (let i = 0; i < bdata.length; i++) {
        //         //     bytes[i] = bdata.charCodeAt(i);
        //         // }
        //         // let binData = new Uint8Array(bytes);
        //         let binData = data;
        //
        //         // let blob = new Blob([data], {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
        //         let blob = new Blob([binData], {type: type});
        //         let url = window.URL || window.webkitURL;
        //         let link = url.createObjectURL(blob);
        //         let a = $("<a />");
        //         a.attr("download", "temp.xlsx");
        //         a.attr("href", link);
        //         $("body").append(a);
        //         a[0].click();
        //         // $("body").remove(a);
        //     }
        // })
       // $.ajax({
       //          type: 'POST',
       //          url: "{{url_for('route_blueprint.spreadsheet_results')}}",
       //          data: formData,
       //          contentType: false,
       //          processData: false,
       //          dataType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
       //          success: function (data, status, xhr) {
       //              let x = status
       //              getResponseSuccessA(data, xhr, display_name, 'spreadsheet_submit_flash')
       //          },
       //          error: function (xhr, status, errorThrown) {
       //              getResponseFailure(xhr, status, errorThrown, display_name, 'spreadsheet_submit_flash')
       //          }
       //      }
    } else {
        $.ajax({
                type: 'POST',
                url: "{{url_for('route_blueprint.spreadsheet_results')}}",
                data: formData,
                contentType: false,
                processData: false,
                dataType: 'text',
                success: function (download, status, xhr) {
                    getResponseSuccess(download, xhr, display_name, 'spreadsheet_submit_flash')
                },
                error: function (xhr, status, errorThrown) {
                    getResponseFailure(xhr, status, errorThrown, display_name, 'spreadsheet_submit_flash')
                }
            }
        )
    }
}

function save(name, data, type, isBinary) {
    if (isBinary) {
        var bytes = new Array(data.length);
        for (var i = 0; i < data.length; i++) {
            bytes[i] = data.charCodeAt(i);
        }
        data = new Uint8Array(bytes);
    }
}