"""
This module is used to report errors found in the tag conversion.
"""

INVALID_PARENT_NODE = "invalidParent"
NO_VALID_TAG_FOUND = "invalidTag"
INVALID_SCHEMA = 'invalidSchema'
EMPTY_TAG_FOUND = 'emptyTag'

ERROR_PREFIX = "ERROR: "

def report_error_type(error_type, hed_string, error_index=0, error_index_end=0, expected_parent_tag=None):
    """Reports the abc error based on the type of error.

    Parameters
    ----------
    error_type: str
        The type of abc error.
    Returns
    -------
    list of dict
        A singleton list containing a dictionary with the error type and error message related to a particular type of
        error.

    """
    problem_tag = hed_string[error_index:error_index_end]

    error_types = {
        INVALID_PARENT_NODE: f"{ERROR_PREFIX}'{problem_tag}' appears as '{expected_parent_tag}' and cannot be used "
                             f"as an extension.  {error_index}, {error_index_end}",
        NO_VALID_TAG_FOUND : f"{ERROR_PREFIX}'{problem_tag}' is not a valid base hed tag.  {error_index}, {error_index_end} ",
        EMPTY_TAG_FOUND    : f"{ERROR_PREFIX}'Empty tag cannot be converted.",
        INVALID_SCHEMA     : f"{ERROR_PREFIX}'Source hed schema is invalid as it contains duplicate tags.  "
                             f"Please fix if you wish to be abe to convert tags. {error_index}, {error_index_end}"
    }
    default_error_message = f'{ERROR_PREFIX}Internal Error'
    error_message = error_types.get(error_type, default_error_message)

    error_object = {'code': error_type, 'message': error_message, 'source_string': hed_string}

    # Debug printing
    # print(f"{hed_string}")
    # print(error_message)

    return error_object


def add_row_and_column(error_object, row, col):
    old_error_msg = error_object['message']
    old_trimmed_msg = old_error_msg[len(ERROR_PREFIX):]
    new_error_msg = f"ERROR on {row}, {col}: {old_trimmed_msg}"
    error_object["message"] = new_error_msg
    error_object["row_number"] = row
    error_object["column_number"] = col
