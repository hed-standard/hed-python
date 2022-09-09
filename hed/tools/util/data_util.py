""" Data handling utilities involving dataframes. """

import pandas as pd
import numpy as np
from hed.errors.exceptions import HedFileError


def add_columns(df, column_list, value='n/a'):
    """ Add specified columns to df if not there.

    Args:
        df (DataFrame):      Pandas dataframe.
        column_list (list):  List of columns to append to the dataframe.
        value (str):         Default fill value for the column.

    """

    add_cols = list(set(column_list) - set(list(df)))
    for col in add_cols:
        df[col] = value


def check_match(ds1, ds2, numeric=False):
    """ Check two Pandas data series have the same values.

    Args:
        ds1 (DataSeries):      Pandas data series to check.
        ds2 (DataSeries):      Pandas data series to check.
        numeric (bool):        If true, treat as numeric and do close-to comparison.

    Returns:
        list: Error messages indicating the mismatch or empty if the series match.

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
        if sum(unequal) > 0:
            return f"Series differ at positions {list(ds1.loc[unequal].index)}"
    return []


def delete_columns(df, column_list):
    """ Delete the specified columns from a dataframe.

    Args:
        df (DataFrame):      Pandas dataframe from which to delete columns.
        column_list (list):  List of candidate column names for deletion.

    Notes:
        - The deletion of columns is done in place.
        - This does not raise an error if df does not have a column in the list.

    """

    delete_cols = list(set(column_list).intersection(set(list(df))))
    df.drop(columns=delete_cols, axis=1, inplace=True)


def delete_rows_by_column(df, value, column_list=None):
    """ Delete rows where columns have this value.

    Args:
        df (DataFrame):      Pandas dataframe from which to delete rows.
        value (str):         Specified value to indicate row should be deleted.
        column_list (list):  List of columns to search for value.

    Notes:
        - All values are converted to string before testing.
        - Deletion is done in place.

    """
    if column_list:
        cols = list(set(column_list).intersection(set(list(df))))
    else:
        cols = list(df)

    for col in cols:
        map_col = df[col].map(str) == str(value)
        df.drop(df[map_col].index, axis=0, inplace=True)


def get_key_hash(key_tuple):
    """ Calculate a hash key for tuple of values.

    Args:
        key_tuple (tuple, list):  The key values in the correct order for lookup.

    Returns:
        int:  A hash key for the tuple.

    """

    return hash(tuple(key_tuple))


def get_new_dataframe(data):
    """ Get a new dataframe representing a tsv file.

    Args:
        data (DataFrame or str):  DataFrame or filename representing a tsv file.

    Returns:
        DataFrame:  A dataframe containing the contents of the tsv file or if data was
             a DataFrame to start with, a new copy of the DataFrame.

    Raises:
        HedFileError: If a filename is given and it cannot be read into a Dataframe.

    """

    if isinstance(data, str):
        df = pd.read_csv(data, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise HedFileError("BadDataFrame", "get_new_dataframe could not extract DataFrame from data", "")
    return df


def get_row_hash(row, key_list):
    """ Get a hash key from key column values for row.

    Args:
        row (DataSeries)   A Pandas data series corresponding to a row in a spreadsheet.
        key_list (list)    List of column names to create the hash value from.

    Returns:
        str: Hash key constructed from the entries of row in the columns specified by key_list.

    Raises:
        HedFileError: If row doesn't have all of the columns in key_list HedFileError is raised.

    """
    columns_present, columns_missing = separate_columns(list(row.index.values), key_list)
    if columns_missing:
        raise HedFileError("lookup_row", f"row must have all keys, missing{str(columns_missing)}", "")
    return get_key_hash(row[key_list])


def get_value_dict(tsv_path, key_col='file_basename', value_col='sampling_rate'):
    """ Get a dictionary of two columns of a dataframe.

    Args:
        tsv_path (str)   Path to a tsv file with a header row to be read into a DataFrame.
        key_col (str)    Name of the column which should be the key.
        value_col (str)  Name of the column which should be the value.

    Returns:
        dict:  Dictionary with key_col values as the keys and the corresponding
               value_col values as the values.

    Raises:
        HedFileError: When tsv_path does not correspond to a file that can be read into a DataFrame.
    """

    value_dict = {}
    df = get_new_dataframe(tsv_path)
    for index, row in df.iterrows():
        if row[key_col] in value_dict:
            raise HedFileError("DuplicateKeyInValueDict", "The key column must have unique values", "")
        value_dict[row[key_col]] = row[value_col]
    return value_dict


def make_info_dataframe(col_info, selected_col):
    """ Get a dataframe from selected columns.

    Args:
        col_info (dict):      Dictionary of dictionaries of column values and counts.
        selected_col (str):   Name of the column used as top level key for col_info.

    Returns:
        dataframe:  A two-column dataframe with first column containing values from the
                    dictionary whose key is selected_col and whose second column are the corresponding counts.
                    The returned value is None if selected_col is not a top-level key in col_info.

    """
    col_dict = col_info.get(selected_col, None)
    if not col_dict:
        return None
    col_values = col_dict.keys()
    df = pd.DataFrame(sorted(list(col_values)), columns=[selected_col])
    return df


def replace_values(df, values=None, replace_value='n/a', column_list=None):
    """ Replace string values in specified columns.

    Args:
        df (DataFrame):            Dataframe whose values will replaced.
        values (list, None):       List of strings to replace. If None, only empty strings are replaced.
        replace_value (str):       String replacement value.
        column_list (list, None):  List of columns in which to do replacement. If None all columns are processed.

    Returns:
        int: number of values replaced.
    """

    num_replaced = 0
    if column_list:
        cols = list(set(column_list).intersection(set(list(df))))
    else:
        cols = list(df)
    if not values:
        values = ['']
    for col in cols:
        for value in values:
            value_mask = df[col].map(str) == str(value)
            num_replaced += sum(value_mask)
            index = df[value_mask].index
            df.loc[index, col] = replace_value
    return num_replaced


def remove_quotes(df):
    """ Remove quotes from all columns.

    Args:
        df (Dataframe):   Dataframe to process by removing quotes.

    Notes:
        - Replacement is done in place.

    """

    col_types = df.dtypes
    for index, col in enumerate(df.columns):
        if col_types.iloc[index] in ['string', 'object']:
            df.iloc[:, index] = df.iloc[:, index].str.replace('"', '')
            df.iloc[:, index] = df.iloc[:, index].str.replace("'", "")


def reorder_columns(data, col_order, skip_missing=True):
    """ Create a new dataframe with columns reordered.
    Args:
        data (DataFrame, str) :        Dataframe or filename of dataframe whose columns are to be reordered.
        col_order (list):              List of column names in desired order.
        skip_missing (bool):           If true, col_order columns missing from data are skipped, otherwise error.

    Returns:
        DataFrame                      A new reordered dataframe.

    Raises:
        HedFileError:  If col_order contains columns not in data and skip_missing is False or if
            data corresponds to a filename from which a dataframe cannot be created.
    """
    df = get_new_dataframe(data)
    present_cols, missing_cols = separate_columns(df.columns.values.tolist(), col_order)
    if missing_cols and not skip_missing:
        raise HedFileError("MissingKeys", f"Events file must have columns {str(missing_cols)}", "")
    df = df[present_cols]
    return df


def separate_columns(base_cols, target_cols):
    """ Get target columns from the base list.

    Args:
        base_cols (list) :        List of columns to be tested.
        target_cols (list):       List of desired column names.

     Returns:
        tuples:
            list:  Target columns present in base_cols.
            list:  Target columns missing from base_cols.

     Notes:
         - The function computes the set difference of target_cols and base_cols and returns a list
         of columns of target_cols that are in base_cols and a list of those missing.

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
