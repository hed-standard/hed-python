import os
import pandas as pd
from werkzeug.utils import secure_filename
from hed.errors.exceptions import HedFileError


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


def get_columns_info(dataframe, skip_cols=None):
    """ Extracts the number of times each unique value appears in each column.

    Args:
        dataframe (DataFrame):    The DataFrame to be analyzed
        skip_cols(list):          List of names of columns to be skipped in the extraction

    Returns: 
        dict:   A dictionary with keys that are column names and values that are dictionaries of unique value counts
    """
    col_info = dict()

    for col_name, col_values in dataframe.iteritems():
        if skip_cols and col_name in skip_cols:
            continue
        col_info[col_name] = col_values.value_counts(ascending=True).to_dict()
    return col_info


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


def get_key_counts(root_dir, skip_cols=None):
    file_list = get_file_list(root_dir, types=[".tsv"], suffix="_events")
    count_dicts = {}
    for file in file_list:
        dataframe = get_new_dataframe(file)
        for col_name, col_values in dataframe.iteritems():
            if skip_cols and col_name in skip_cols:
                continue
            update_dict_counts(count_dicts, col_name, col_values)
    return count_dicts


def get_key_hash(key_tuple):
    """ Calculates the key_hash for key_tuple. If the key_hash in map_dict, also return the key value.

    Args:
        key_tuple (tuple):       A tuple with the key values in the correct order for lookup

    Returns:
        key_hash (int)              Hash key for the tuple

    """

    return hash(tuple(key_tuple))


def get_row_hash(row, key_list):
    columns_present, columns_missing = separate_columns(list(row.index.values), key_list)
    if columns_missing:
        raise HedFileError("lookup_row", f"row must have all keys, missing{str(columns_missing)}", "")
    return get_key_hash(row[key_list])


def make_dataframe(col_info, selected_col):
    col_dict = col_info.get(selected_col, None)
    if not col_dict:
        return None
    col_values = col_dict.keys()
    df = pd.DataFrame(sorted(list(col_values)), columns=[selected_col])
    return df


def print_columns_info(columns_info, skip_cols=None):

    for col_name, col_counts in columns_info.items():
        if skip_cols and col_name in skip_cols:
            continue
        print(f"\n{col_name}:")
        sorted_counts = sorted(col_counts.items())

        for key, value in sorted_counts:
            print(f"\t{key}: {value}")


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


def remove_quotes(df, column_list=None):
    """ Remove quotes from the entries of the specified columns in a dataframe or from all columns if no list provided.

    Args:
        df (Dataframe):             Dataframe to process by removing specified quotes
        column_list (list) :        Optional list of column names for which to remove
    """

    col_types = df.dtypes
    for index, col in enumerate(df.columns):
        if col_types.iloc[index] in ['string', 'object']:
            df.iloc[:, index] = df.iloc[:, index].str.replace('"', '')
            df.iloc[:, index] = df.iloc[:, index].str.replace("'", "")


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


def update_dict_counts(count_dicts, col_name, col_values):
    values = col_values.value_counts(ascending=True)
    if col_name not in count_dicts:
        count_dicts[col_name] = {}

    total_values = count_dicts[col_name]
    for name, value in values.items():
        total_values[name] = total_values.get(name, 0) + value
