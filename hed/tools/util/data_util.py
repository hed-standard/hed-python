""" Data handling utilities involving dataframes. """

import pandas as pd
import numpy as np
from hed.errors.exceptions import HedFileError


def add_columns(df, column_list, value='n/a'):
    """ Add specified columns to df if not there.

    Parameters:
        df (DataFrame):      Pandas dataframe.
        column_list (list):  List of columns to append to the dataframe.
        value (str):         Default fill value for the column.

    """

    add_cols = list(set(column_list) - set(list(df)))
    for col in add_cols:
        df[col] = value


def check_match(ds1, ds2, numeric=False):
    """ Check two Pandas data series have the same values.

    Parameters:
        ds1 (DataSeries):      Pandas data series to check.
        ds2 (DataSeries):      Pandas data series to check.
        numeric (bool):        If True, treat as numeric and do close-to comparison.

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

    Parameters:
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

    Parameters:
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


def get_eligible_values(values, values_included):
    """ Return a list of the items from values that are in values_included or None if no values_included.

    Parameters:
        values (list): List of strings against which to test.
        values_included (list): List of items to be selected from values if they are present.

    Returns:
        list:  list of selected values or None if values_included is empty or None.


    """

    if values_included:
        eligible_columns = [x for x in values_included if x in frozenset(values)]
    else:
        eligible_columns = None
    return eligible_columns


def get_key_hash(key_tuple):
    """ Calculate a hash key for tuple of values.

    Parameters:
        key_tuple (tuple, list):  The key values in the correct order for lookup.

    Returns:
        int:  A hash key for the tuple.

    """

    return hash(tuple((str(n) for n in key_tuple)))


def get_new_dataframe(data):
    """ Get a new dataframe representing a tsv file.

    Parameters:
        data (DataFrame or str):  DataFrame or filename representing a tsv file.

    Returns:
        DataFrame:  A dataframe containing the contents of the tsv file or if data was
             a DataFrame to start with, a new copy of the DataFrame.

    :raises HedFileError:
        - A filename is given, and it cannot be read into a Dataframe.

    """

    if isinstance(data, str):
        df = pd.read_csv(data, delimiter='\t', header=0, keep_default_na=True, na_values=[",", "null"])
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise HedFileError("BadDataFrame", "get_new_dataframe could not extract DataFrame from data", "")
    return df


def get_row_hash(row, key_list):
    """ Get a hash key from key column values for row.

    Parameters:
        row (DataSeries)   A Pandas data series corresponding to a row in a spreadsheet.
        key_list (list)    List of column names to create the hash value from.

    Returns:
        str: Hash key constructed from the entries of row in the columns specified by key_list.

    :raises HedFileError:
        - If row doesn't have all the columns in key_list HedFileError is raised.

    """
    columns_present, columns_missing = separate_values(list(row.index.values), key_list)
    if columns_missing:
        raise HedFileError("lookup_row", f"row must have all keys, missing{str(columns_missing)}", "")
    new_row = row[key_list].fillna('n/a').astype(str)
    return get_key_hash(new_row)


def get_value_dict(tsv_path, key_col='file_basename', value_col='sampling_rate'):
    """ Get a dictionary of two columns of a dataframe.

    Parameters:
        tsv_path (str):   Path to a tsv file with a header row to be read into a DataFrame.
        key_col (str):    Name of the column which should be the key.
        value_col (str):  Name of the column which should be the value.

    Returns:
        dict:  Dictionary with key_col values as the keys and the corresponding value_col values as the values.

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

    Parameters:
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


def replace_na(df):
    """ Replace (in place) the n/a with np.nan taking care of categorical columns.  """
    for column in df.columns:
        if df[column].dtype.name != 'category':
            df[column] = df[column].replace('n/a', np.nan)
        elif 'n/a' in df[column].cat.categories:
            df[column] = df[column].astype('object')
            df[column] = df[column].replace('n/a', np.nan)
            df[column] = pd.Categorical(df[column])


def replace_values(df, values=None, replace_value='n/a', column_list=None):
    """ Replace string values in specified columns.

    Parameters:
        df (DataFrame):            Dataframe whose values will be replaced.
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


def reorder_columns(data, col_order, skip_missing=True):
    """ Create a new dataframe with columns reordered.

    Parameters:
        data (DataFrame, str):      Dataframe or filename of dataframe whose columns are to be reordered.
        col_order (list):           List of column names in desired order.
        skip_missing (bool):        If true, col_order columns missing from data are skipped, otherwise error.

    Returns:
        DataFrame: A new reordered dataframe.

    Raises:
        HedFileError: If col_order contains columns not in data and skip_missing is False.
        If data corresponds to a filename from which a dataframe cannot be created.

    """
    df = get_new_dataframe(data)
    present_cols, missing_cols = separate_values(df.columns.values.tolist(), col_order)
    if missing_cols and not skip_missing:
        raise HedFileError("MissingKeys", f"Events file must have columns {str(missing_cols)}", "")
    df = df[present_cols]
    return df


def separate_values(values, target_values):
    """ Get target values from the target_values list.

    Parameters:
        values (list):          List of values to be tested.
        target_values (list):   List of desired values.

     Returns:
        tuple[list, list]: A tuple containing two lists:
        - Target values present in values.
        - Target values missing from values.

     Notes:
         - The function computes the set difference of target_cols and base_cols and returns a list
           of columns of target_cols that are in base_cols and a list of those missing.

     """

    if not target_values:
        return [], []
    elif not values:
        return [], target_values
    present_values = [x for x in target_values if x in frozenset(values)]
    missing_values = list(set(target_values).difference(set(values)))
    return present_values, missing_values
