""" Utilities for extracting counts of items in columns. """
from hed.tools.annotation.event_value_summary import EventValueSummary
from hed.util.io_util import get_file_list
from hed.util.data_util import get_new_dataframe


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


def get_key_counts(root_dir, skip_cols=None):
    file_list = get_file_list(root_dir, name_suffix="_events", extensions=[".tsv"])
    count_dicts = {}
    for file in file_list:
        dataframe = get_new_dataframe(file)
        for col_name, col_values in dataframe.iteritems():
            if skip_cols and col_name in skip_cols:
                continue
            update_dict_counts(count_dicts, col_name, col_values)
    return count_dicts


# def print_columns_info(columns_info, skip_cols=None):
#
#     for col_name, col_counts in columns_info.items():
#         if skip_cols and col_name in skip_cols:
#             continue
#         print(f"\n{col_name}:")
#         sorted_counts = sorted(col_counts.items())
#
#         for key, value in sorted_counts:
#             print(f"\t{key}: {value}")


def update_dict_counts(count_dicts, col_name, col_values):
    """ Update the counts in a dictionary based on the column values in a dictionary.

    """
    values = col_values.value_counts(ascending=True)
    if col_name not in count_dicts:
        count_dicts[col_name] = {}

    total_values = count_dicts[col_name]
    for name, value in values.items():
        total_values[name] = total_values.get(name, 0) + value
