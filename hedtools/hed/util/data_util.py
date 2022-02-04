"""Data handling utilities involving dataframes."""

import pandas as pd
import numpy as np
from hed.errors.exceptions import HedFileError


def add_columns(df, column_list, value='n/a'):
    """ Add specified columns to df if df they are not already there

    Args:
        df (DataFrame):      Pandas dataframe
        column_list (list):  List of columns
        value (str):         Default value to place in string

    """

    add_cols = list(set(column_list) - set(list(df)))
    for col in add_cols:
        df[col] = value


def check_match(ds1, ds2, numeric=False):
    """ Check that the two series match

    Args:
        ds1 (DataSeries):      Pandas data series
        ds2 (DataSeries):      Pandas data series
        numeric (bool):        If true, treat as numeric and do close-to comparison

    Returns:
        list                   List of error messages or empty if match

    """

    if len(ds1.index) != len(ds2.index):
        return f"First series has length {len(ds1.index)} and {len(ds2.index)} events"
    if numeric:
        close_test = np.isclose(pd.to_numeric(ds1, errors='coerce'), pd.to_numeric(ds2, errors='coerce'),
                                equal_nan=True)
        if sum(np.logical_not(close_test)):
            return f"Series differ at positions {list(ds1.loc[np.logical_not(close_test)].index)}"
    else:
        unequal = ds1.map(str) != ds2.map(str)
        if sum(unequal):
            return f"Series differ at positions {list(ds1.loc[unequal].index)}"
    return []


def delete_columns(df, column_list):
    """ Delete specified columns from df if df has

    Args:
        df (DataFrame):      Pandas dataframe
        column_list (list):  List of columns

    """

    delete_cols = list(set(column_list).intersection(set(list(df))))
    df.drop(columns=delete_cols, axis=1, inplace=True)


def delete_rows_by_column(df, value, column_list=None):
    """ Delete rows in which the specified column of df has particular values

    Args:
        df (DataFrame):      Pandas dataframe
        value (str):         Specified value
        column_list (list):  List of columns to search for value

    Note: all values are convert to string before test.
    """
    if column_list:
        cols = list(set(column_list).intersection(set(list(df))))
    else:
        cols = list(df)

    # Remove boundary type events
    for col in cols:
        map_col = df[col].map(str) == str(value)
        df.drop(df[map_col].index, axis=0, inplace=True)


def get_key_hash(key_tuple):
    """ Calculates the key_hash for key_tuple. If the key_hash in map_dict, also return the key value.

    Args:
        key_tuple (tuple):       A tuple with the key values in the correct order for lookup

    Returns:
        key_hash (int)              Hash key for the tuple

    """

    return hash(tuple(key_tuple))


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


def get_row_hash(row, key_list):
    columns_present, columns_missing = separate_columns(list(row.index.values), key_list)
    if columns_missing:
        raise HedFileError("lookup_row", f"row must have all keys, missing{str(columns_missing)}", "")
    return get_key_hash(row[key_list])


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


def replace_values(df, values=[''], replace_value='n/a', column_list=None):
    """ Replace specified string values in specified columns of df with replace_value

    Args:
        df (DataFrame):      Pandas dataframe
        values (list):       List of strings to replace
        replace_value (str): String replacement value
        column_list (list):  List of columns in which to do replacement

    """
    if column_list:
        cols = list(set(column_list).intersection(set(list(df))))
    else:
        cols = list(df)
    for col in cols:
        for value in values:
            value_mask = df[col].map(str) == str(value)
            index = df[value_mask].index
            df.loc[index, col] = 'n/a'


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
