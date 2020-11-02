"""
This module is used to report errors found in the tag conversion.
"""

INVALID_PARENT_NODE = "invalidParent"
NO_VALID_TAG_FOUND = "invalidTag"
INVALID_SCHEMA = 'invalidSchema'
EMPTY_TAG_FOUND = 'emptyTag'


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
        INVALID_PARENT_NODE: f"ERROR: '{problem_tag}' appears as '{expected_parent_tag}' and cannot be used "
                             f"as an extension.  {error_index}, {error_index_end}",
        NO_VALID_TAG_FOUND : f"ERROR: '{problem_tag}' is not a valid base hed tag.  {error_index}, {error_index_end} ",
        EMPTY_TAG_FOUND    : f"ERROR: 'Empty tag cannot be converted.",
        INVALID_SCHEMA     : f"ERROR: 'Source hed schema is invalid as it contains duplicate tags.  "
                             f"Please fix if you wish to be abe to convert tags. {error_index}, {error_index_end}"
    }
    default_error_message = 'ERROR: Internal Error'
    error_message = error_types.get(error_type, default_error_message)

    error_object = {'code': error_type, 'message': error_message, 'source_string': hed_string}

    # Debug printing
    # print(f"{hed_string}")
    # print(error_message)

    return error_object
