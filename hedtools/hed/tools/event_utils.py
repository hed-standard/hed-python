from pandas import DataFrame, to_numeric
import numpy as np


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
        close_test = np.isclose(to_numeric(ds1, errors='coerce'), to_numeric(ds2, errors='coerce'), equal_nan=True)
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


# def get_mask(df, column_name, value_list):
#     df[column_name].map(str) == str(value)
#     x2 = to_numeric(ds2, errors='coerce')
#     close_test = np.isclose(to_numeric(ds1, errors='coerce'), to_numeric(ds2, errors='coerce'), equal_nan=True):
