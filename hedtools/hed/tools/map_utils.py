from hed.errors.exceptions import HedFileError
from hed.tools.col_dict import ColumnDict
from hed.tools.io_utils import get_file_list, get_new_dataframe, separate_columns


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
    file_list = get_file_list(root_dir, suffix="_events", extensions=[".tsv"])
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


def make_combined_dicts(file_dict, skip_cols=None):
    """ Return a combined dictionary of column information as we

    Args:
        file_dict (dict):  Dictionary of file name keys and full path
        skip_cols (list):  Name of the column

    Returns:
        dict:  A combined dictionary
    """

    dicts_all = ColumnDict(skip_cols=skip_cols)
    dicts = {}
    for key, file in file_dict.items():
        orig_dict = ColumnDict(skip_cols=skip_cols)
        df = get_new_dataframe(file)
        orig_dict.update(df)
        dicts[key] = orig_dict
        dicts_all.update_dict(orig_dict)
    return dicts_all, dicts


def print_columns_info(columns_info, skip_cols=None):

    for col_name, col_counts in columns_info.items():
        if skip_cols and col_name in skip_cols:
            continue
        print(f"\n{col_name}:")
        sorted_counts = sorted(col_counts.items())

        for key, value in sorted_counts:
            print(f"\t{key}: {value}")


def update_dict_counts(count_dicts, col_name, col_values):
    values = col_values.value_counts(ascending=True)
    if col_name not in count_dicts:
        count_dicts[col_name] = {}

    total_values = count_dicts[col_name]
    for name, value in values.items():
        total_values[name] = total_values.get(name, 0) + value
