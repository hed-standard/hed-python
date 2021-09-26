import os
import pandas as pd
from hed.errors.exceptions import HedFileError


def extract_dataframe(data):
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
        raise HedFileError("BadDataFrame", "extract_dataframe could not extract DataFrame from data", "")
    return df


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


def get_file_list(path, types=None, suffix=None):
    """ Traverses a directory tree and returns a list of paths to files ending with a particular suffix.

    Args:
        path (str):       The full path of the directory tree to be traversed (no ending slash)
        types (list):     A list of extensions to be selected
        suffix (str):     The suffix of the paths to be extracted

    Returns: 
        list:             A list of full paths
    """
    file_list = []
    for r, d, f in os.walk(path):
        for r_file in f:
            file_split = os.path.splitext(r_file)
            if (types and file_split[1] not in types) or (suffix and not file_split[0].endswith(suffix)):
                continue
            file_list.append(os.path.join(r, r_file))
    return file_list


def get_event_counts(root_dir, skip_cols=None):
    file_list = get_file_list(root_dir, types=[".tsv"], suffix = "_events")
    count_dicts = {}
    for file in file_list:
        dataframe = extract_dataframe(file)
        for col_name, col_values in dataframe.iteritems():
            if col_name in skip_cols:
                continue
            update_dict_counts(count_dicts, col_name, col_values)


def reorder_columns(data, col_order, skip_missing=True):
    """ Takes a dataframe or filename representing event file and reorders columns to desired order

    Args:
        data (DataFrame, str) :        Represents mapping
        col_order (list):              List of column names for desired order
        skip_missing (bool):           If true, col_order columns missing from data are skipped, otherwise error

    Returns:
        DataFrame                      A new reordered dataframe
    """
    df = extract_dataframe(data)
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


def update_dict_counts(count_dicts, col_name, col_values):
    values = col_values.value_counts(ascending=True)
    if col_name not in count_dicts:
        count_dicts[col_name] = values
    else:
        total_values = count_dicts[col_name]
        for name, value in values.items():
            total_values[name] = total_values.get(name, 0) + value
