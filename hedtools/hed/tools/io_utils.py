import os

import pandas as pd
from werkzeug.utils import secure_filename
from hed.errors.exceptions import HedFileError


def generate_filename(base_name, prefix=None, suffix=None, extension=None):
    """Generates a filename for the attachment of the form prefix_basename_suffix + extension.

    Parameters
    ----------
   base_name: str
        The name of the base, usually the name of the file that the issues were generated from
    prefix: str
        The prefix prepended to the front of the base_name
    suffix: str
        The suffix appended to the end of the base_name
    Returns
    -------
    string
        The name of the attachment other containing the issues.
    """

    pieces = []
    if prefix:
        pieces = pieces + [secure_filename(prefix)]
    if base_name:
        pieces.append(os.path.splitext(secure_filename(base_name))[0])
    if suffix:
        pieces = pieces + [secure_filename(suffix)]

    if not pieces:
        return ''
    filename = pieces[0]
    for name in pieces[1:]:
        filename = filename + '_' + name
    if extension:
        filename = filename + '.' + secure_filename(extension)
    return filename


def get_file_list(path, prefix=None, types=None, suffix=None):
    """ Traverses a directory tree and returns a list of paths to files ending with a particular suffix.

    Args:
        path (str):       The full path of the directory tree to be traversed (no ending slash)
        prefix (str):     An optional prefix for the base filename
        types (list):     A list of extensions to be selected
        suffix (str):     The suffix of the paths to be extracted

    Returns:
        list:             A list of full paths
    """
    file_list = []
    for r, d, f in os.walk(path):
        for r_file in f:
            file_split = os.path.splitext(r_file)
            if types and file_split[1] not in types:
                continue
            elif suffix and not file_split[0].endswith(suffix):
                continue
            elif prefix and not file_split[0].startswith(prefix):
                continue
            file_list.append(os.path.join(r, r_file))
    return file_list


def get_new_dataframe(data):
    """ Returns a new dataframe representing an event file or template

    Args:
        data (DataFrame or str):      DataFrame or filename representing an events file

    Returns:
        DataFrame containing with a tsv file

    """

    if isinstance(data, str):
        df = pd.read_csv(data, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise HedFileError("BadDataFrame", "get_new_dataframe could not extract DataFrame from data", "")
    return df


def make_file_dict(file_list, indices=[0, -2], separator='_'):
    """ Return a dictionary with keys that are simplified file names and values that are full paths

    This function is used for cross listing BIDS style files for different studies.

    Args:
        file_list (list):      List containing full paths of files of interest
        indices (list):  List of indices into base file names of pieces to assemble for the key
        separator (str):       Character used to separate pieces of key name
    Returns:
        dict:  A dictionary of simplified, path-independent key names and full paths values.
    """
    file_dict = {}
    for file in file_list:
        base = os.path.basename(file)
        key = make_key(base, indices=indices, separator=separator)
        file_dict[key] = file
    return file_dict


def make_info_dataframe(col_info, selected_col):
    """ Return a dataframe containing the column information for the selected column

    Args:
        col_info (dict):      Dictionary of column values and counts
        selected_col (str):   Name of the column

    Returns:
        dataframe:  A dictionary of simplified, path-independent key names and full paths values.
    """
    col_dict = col_info.get(selected_col, None)
    if not col_dict:
        return None
    col_values = col_dict.keys()
    df = pd.DataFrame(sorted(list(col_values)), columns=[selected_col])
    return df


def make_key(key_string, indices=[0, -2], separator='_'):
    key_value = ''
    pieces = key_string.split(separator)
    for index in indices:
        key_value += pieces[index] + separator
    return key_value[:-1]


def remove_quotes(df):
    """ Remove quotes from the entries of the specified columns in a dataframe or from all columns if no list provided.

    Args:
        df (Dataframe):             Dataframe to process by removing specified quotes
    """

    col_types = df.dtypes
    for index, col in enumerate(df.columns):
        if col_types.iloc[index] in ['string', 'object']:
            df.iloc[:, index] = df.iloc[:, index].str.replace('"', '')
            df.iloc[:, index] = df.iloc[:, index].str.replace("'", "")


def reorder_columns(data, col_order, skip_missing=True):
    """ Takes a dataframe or filename representing event file and reorders columns to desired order

    Args:
        data (DataFrame, str) :        Represents mapping
        col_order (list):              List of column names for desired order
        skip_missing (bool):           If true, col_order columns missing from data are skipped, otherwise error

    Returns:
        DataFrame                      A new reordered dataframe
    """
    df = get_new_dataframe(data)
    present_cols, missing_cols = separate_columns(df.columns.values.tolist(), col_order)
    if missing_cols and not skip_missing:
        raise HedFileError("MissingKeys", f"Events file must have columns {str(missing_cols)}", "")
    df = df[present_cols]
    return df


def separate_columns(base_cols, target_cols):
    """ Takes a list of column names and a list of target columns and returns list of present and missing targets.

    Computes the set difference of target_cols and base_cols and returns a list of columns of
    target_cols that are in df and a list of those missing.

     Args:
         base_cols (list) :        List of columns in base object
         target_cols (list):       List of desired column names

     Returns:
         tuple (list, list):            Returns two lists one with
     """

    if not target_cols:
        return [], []
    elif not base_cols:
        return [], target_cols
    missing_cols = []
    present_cols = []
    for col in target_cols:
        if col not in base_cols:
            missing_cols.append(col)
        else:
            present_cols.append(col)
    return present_cols, missing_cols
