
/**
 * Checks to see if the user pressed cancel in chrome's file upload browser.
 * @param {String} filePath - A path to a file.
 * @returns {boolean} - True if the user selects cancel in chrome's file upload browser.
 */
function cancelWasPressedInChromeFileUpload(filePath) {
    return isEmptyStr(filePath) && (window.chrome)
}


/**
 * Converts a path and prefix to a text results name
 * @param {String} filename - Pathname of the original file
 * @param {String} prefix - Prefix to be appended to the file name of original file
 * @returns {String} - File name of the
 */
function convertToResultsName(filename, prefix) {
    let parts = getFilenameAndExtension(filename);
    return prefix + "_" + parts[0] + ".txt"
}


/**
 * Compares the file extension of the file at the specified path to an Array of accepted file extensions.
 * @param {String} filePath - A path to a file.
 * @param {Array} acceptedFileExtensions - An array of accepted file extensions.
 * @returns {boolean} - True if the file has an accepted file extension.
 */
function fileHasValidExtension(filePath, acceptedFileExtensions) {
    let fileExtension = filePath.split('.').pop();
    return $.inArray(fileExtension.toLowerCase(), acceptedFileExtensions) != -1
}


/**
 * Checks to see if a file has been specified.
 * @param {string} nameID - #id of the element holding the name
 * @param {string} flashID - id of the flash element to display error message
 * @param {string} errorMsg - error message to be displayed if file isn't in form
 * @returns {boolean} - returns true if file is specified
 */
function fileIsSpecified(nameID, flashID, errorMsg) {
    let theFile = $(nameID);
    if (theFile[0].files.length === 0) {
        flashMessageOnScreen(errorMsg, 'error', flashID);
        return false;
    }
    return true;
}

/**
 * Flash a message on the screen.
 * @param {String} message - The message that will be flashed on the screen.
 * @param {String} category - The msg_category of the message. The categories are 'error', 'success', and 'other'.
 * @param {String} flashMessageElementId - ID of the flash element
 */
function flashMessageOnScreen(message, category, flashMessageElementId) {
    let flashMessage = document.getElementById(flashMessageElementId);
    flashMessage.innerHTML = message;
    setFlashMessageCategory(flashMessage, category);
}


function getFilenameAndExtension(pathname){

  let clean = pathname.toString().replace(/^.*[\\\/]/, '');
  if (!clean) {
      return ['', '']
  }

  let filename = clean.substring(0, clean.lastIndexOf('.'));
  let ext = clean.split('.').pop();
  return [filename, ext];
}


/**
 * Gets the file download name from a Response header
 * @param {Object} xhr - Dictionary containing Response header information
 * @param {String} default_name - The default name to use
 * @returns {String} - Name of the save file
 */
function getFilenameFromResponseHeader(xhr, default_name) {
    let disposition = xhr.getResponseHeader('Content-Disposition')

    let filename = "";
    if (disposition && disposition.indexOf('attachment') !== -1) {
        let filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        let matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
            filename = matches[1].replace(/['"]/g, '');
        }
    }
    if (!filename) {
        filename = default_name;
    }
    return filename
}


/**
 * Gets standard failure response for download
 * @param {Object} xhr - Dictionary containing Response header information
 * @param {String} status - a status text message
 * @param {String} errorThrown - name of the error thrown
 * @param {String} display_name - Name used for the downloaded blob file
 * @param {String} flash_location - ID of the flash location element for displaying response Message
 */
function getResponseFailure( xhr, status, errorThrown, display_name, flash_location) {
    let info = xhr.getResponseHeader('Message');
    let category =  xhr.getResponseHeader('Category');
    if (!info) {
        info = 'Unknown processing error occurred';
    }
    info = info + '[Source: ' + display_name + ']' + '[Status:' + status + ']' + '[Error:' + errorThrown + ']';
    flashMessageOnScreen(info, category, flash_location);
}

/**
 * Downloads a response as a file if there is data.
 * @param {String} download - The downloaded data to be turned into a file.
 * @param {Object} xhr - http response header
 * @param {String} display_name - Download filename to use if not included in the downloaded response.
 * @param {String} flash_location - Name of the field in which to write messages if available.
 */
function getResponseSuccess(download, xhr, display_name, flash_location) {
    let info = xhr.getResponseHeader('Message');
    let category =  xhr.getResponseHeader('Category');
    let contentType = xhr.getResponseHeader('Content-type');
    if (download) {
        let filename = getFilenameFromResponseHeader(xhr, display_name)
        triggerDownloadBlob(download, filename, contentType);
    }
    if (info) {
        flashMessageOnScreen(info, category, flash_location);
    } else {
        flashMessageOnScreen('', 'success', flash_location);
    }
}


/**
 * Checks to see if a string is empty. Empty meaning null or a length of zero.
 * @param {String} str - A string.
 * @returns {boolean} - True if the string is null or its length is 0.
 */
function isEmptyStr(str) {
    return (str === null || str.length === 0)
}


/**
 * Flash a message on the screen.
 * @param {Object} flashMessage - The li element containing the flash message.
 * @param {String} category - The msg_category of the message. The categories are 'error', 'success', and 'other'.
 */
function setFlashMessageCategory(flashMessage, category) {
    if ("error" === category) {
        flashMessage.style.backgroundColor = 'lightcoral';
    } else if ("success" === category) {
        flashMessage.style.backgroundColor = 'palegreen';
    } else if ("warning" === category) {
        flashMessage.style.backgroundColor = 'orange';
    } else {
        flashMessage.style.backgroundColor = '#f0f0f5';
    }
}

/**
 * Returns the extension of a file.
 * @param {string} filename - The filename of the file whose extension should be split off.
 * @returns string - The file extension or an empty string if there is no extension.
 *
 */
function splitExt(filename) {
    const index = filename.lastIndexOf('.');
    return (-1 !== index) ? [filename.substring(0, index), filename.substring(index + 1)] : [filename, ''];
}


/**
 * Trigger the "save as" dialog for a text blob to save as a file with display name.
 * @param {String} download_blob - Bytes to put in the file
 * @param {String} display_name - File name to use if none provided in the downloaded content
 * @param {String} content_type - Type of file to create
 */
function triggerDownloadBlob(download_blob, display_name, content_type) {
    const url = URL.createObjectURL(new Blob([download_blob], {type:content_type}));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', display_name);
    document.body.appendChild(link);
    link.click();
}

/**
 * Updates a file label.
 * @param {String} filePath - The path to the dictionary.
 * @param {String} displayName - The ID of the label field to set
 */
function updateFileLabel(filePath, displayName) {
    let filename = filePath.split('\\').pop();
    $(displayName).text(filename);
}
