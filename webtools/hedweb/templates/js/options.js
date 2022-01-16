
/**
 * Hides  option in the form.
 * @param {string} optionName - Name of the option checkbox to be hidden
 */
function hideOption(optionName) {
    $("#" + optionName).prop('checked', false)
    $("#" + optionName + "_option").hide()
}

/**
 * Show  option in the form.
 * @param {string} optionName - Name of the option checkbox to be hidden
 */
function showOption(optionName) {
    $("#" + optionName + "_option").show()
}

