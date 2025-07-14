""" Utilities to facilitate annotation of events in BIDS. """

import io
import re
from typing import Union

import pandas as pd
from pandas import DataFrame, Series
from hed.models.sidecar import Sidecar
from hed.models.hed_string import HedString
from hed.models.tabular_input import TabularInput

from hed.errors.exceptions import HedFileError
from hed.models import df_util


def check_df_columns(df, required_cols=('column_name', 'column_value', 'description', 'HED')) -> list[str]:
    """ Return a list of the specified columns that are missing from a dataframe.

    Parameters:
        df (DataFrame):  Spreadsheet to check the columns of.
        required_cols (tuple):  List of column names that must be present.

    Returns:
        list[str]:   List of column names that are missing.

    """
    missing_cols = []
    column_list = list(df.columns.values)
    for col in required_cols:
        if col not in column_list:
            missing_cols.append(col)
    return missing_cols


def df_to_hed(dataframe, description_tag=True) -> dict:
    """ Create sidecar-like dictionary from a 4-column dataframe.

    Parameters:
        dataframe (DataFrame):   A four-column Pandas DataFrame with specific columns.
        description_tag (bool):  If True description tag is included.

    Returns:
        dict:  A dictionary compatible with BIDS JSON tabular file that includes HED.

    Notes:
        - The DataFrame must have the columns with names: column_name, column_value, description, and HED.

    """
    df = dataframe.fillna('n/a')
    missing_cols = check_df_columns(df)
    if missing_cols:
        raise HedFileError("RequiredColumnsMissing", f"Columns {str(missing_cols)} are missing from dataframe", "")
    hed_dict = {}
    for index, row in df.iterrows():
        if row['HED'] == 'n/a' and row['description'] == 'n/a':
            continue
        if row['column_value'] == 'n/a':
            hed_dict[row['column_name']] = _get_value_entry(row['HED'], row['description'],
                                                            description_tag=description_tag)
            continue
        cat_dict = hed_dict.get(row['column_name'], {})
        _update_cat_dict(cat_dict, row['column_value'], row['HED'], row['description'],
                         description_tag=description_tag)
        hed_dict[row['column_name']] = cat_dict
    return hed_dict


def extract_tags(hed_string, search_tag) -> tuple[str, list[str]]:
    """ Extract all instances of specified tag from a tag_string.

        Parameters:
           hed_string (str):   Tag string from which to extract tag.
           search_tag (str):   HED tag to extract.

        Returns:
            tuple[str, list[str]
                - Tag string without the tags.
                - A list of the tags that were extracted, for example descriptions.

    """
    possible_descriptions = hed_string.replace(")", "").replace("(", "").split(",")
    extracted = [tag.strip() for tag in possible_descriptions if search_tag in tag]
    remainder = hed_string
    for tag in extracted:
        remainder = df_util.replace_ref(remainder, tag)

    return remainder, extracted


def generate_sidecar_entry(column_name, column_values=None) -> dict:
    """ Create a sidecar column dictionary for column.

    Parameters:
        column_name (str):       Name of the column.
        column_values (list):    List of column values.

     Returns:
         dict:   A dictionary representing a template for a sidecar entry.

    """

    name_label = re.sub(r'[^A-Za-z0-9-]+', '_', column_name)
    sidecar_entry = {"Description": f"Description for {column_name}", "HED": ""}
    if not column_values:
        sidecar_entry["HED"] = f"(Label/{name_label}, ID/#)"
    else:
        levels = {}
        hed = {}
        for column_value in column_values:
            if column_value == "n/a":
                continue
            value_label = re.sub(r'[^A-Za-z0-9-]+', '_', column_value)
            levels[column_value] = f"Here describe column value {column_value} of column {column_name}"
            hed[column_value] = f"(Label/{name_label}, ID/{value_label})"
        sidecar_entry["Levels"] = levels
        sidecar_entry["HED"] = hed
    return sidecar_entry


def hed_to_df(sidecar_dict, col_names=None) -> DataFrame:
    """ Return a 4-column dataframe of HED portions of sidecar.

    Parameters:
        sidecar_dict (dict):      A dictionary conforming to BIDS JSON events sidecar format.
        col_names (list, None):   A list of the cols to include in the flattened sidecar.

    Returns:
        DataFrame:  Four-column spreadsheet representing HED portion of sidecar.

    Notes:
        - The returned DataFrame has columns: column_name, column_value, description, and HED.

    """

    if not col_names:
        col_names = sidecar_dict.keys()
    column_name = []
    column_value = []
    column_description = []
    hed_tags = []

    for col_key, col_dict in sidecar_dict.items():
        if col_key not in col_names or not isinstance(col_dict, dict) or 'HED' not in col_dict:
            continue
        elif 'Levels' in col_dict or isinstance(col_dict['HED'], dict):
            keys, values, descriptions, tags = _flatten_cat_col(col_key, col_dict)
        else:
            keys, values, descriptions, tags = _flatten_val_col(col_key, col_dict)
        column_name = column_name + keys
        column_value = column_value + values
        column_description = column_description + descriptions
        hed_tags = hed_tags + tags

    data = {"column_name": column_name, "column_value": column_value,
            "description": column_description, "HED": hed_tags}
    dataframe = pd.DataFrame(data).astype(str)
    return dataframe


def merge_hed_dict(sidecar_dict, hed_dict):
    """ Update a JSON sidecar based on the hed_dict values.

    Parameters:
        sidecar_dict (dict):  Dictionary representation of a BIDS JSON sidecar.
        hed_dict (dict):       Dictionary derived from a dataframe representation of HED in sidecar.

    """

    for key, value_dict in hed_dict.items():
        if key not in sidecar_dict:
            sidecar_dict[key] = value_dict
            continue
        sidecar_dict[key]['HED'] = value_dict['HED']
        if isinstance(value_dict['HED'], str) and value_dict.get('Description', "n/a") != "n/a":
            sidecar_dict[key]['Description'] = value_dict['Description']
            continue
        if isinstance(value_dict['HED'], dict) and 'Levels' in value_dict:
            sidecar_dict[key]['Levels'] = value_dict['Levels']


def series_to_factor(series) -> list[int]:
    """Convert a series to an integer factor list.

    Parameters:
        series (pd.Series): Series to be converted to a list.

    Returns:
        list[int] - contains 0's and 1's, empty, 'n/a' and np.nan are converted to 0.
    """
    replaced = series.replace('n/a', False)
    filled = replaced.fillna(False)
    bool_list = filled.astype(bool).tolist()
    return [int(value) for value in bool_list]


def str_to_tabular(tsv_str, sidecar=None) -> TabularInput:
    """ Return a TabularInput a tsv string.

    Parameters:
        tsv_str (str):  A string representing a tabular input.
        sidecar (Sidecar, str, File or File-like): An optional Sidecar object.

     Returns:
         TabularInput:  Represents a tabular input object.
     """

    return TabularInput(file=io.StringIO(tsv_str), sidecar=sidecar)


def strs_to_hed_objs(hed_strings, hed_schema) -> Union[list[HedString], None]:
    """ Returns a list of HedString objects from a list of strings.

     Parameters:
         hed_strings (string or list):  String or strings representing HED annotations.
         hed_schema (HedSchema or HedSchemaGroup): Schema version for the strings.

     Returns:
         Union[list[HedString], None]:  A list of HedString objects or None.

     """
    if not hed_strings:
        return None
    if not isinstance(hed_strings, list):
        hed_strings = [hed_strings]
    if hed_strings:
        return [HedString(hed, hed_schema=hed_schema) for hed in hed_strings]
    else:
        return None


def strs_to_sidecar(sidecar_strings) -> Union[Sidecar, None]:
    """ Return a Sidecar from a sidecar as string or as a list of sidecars as strings.

     Parameters:
         sidecar_strings (string or list):  String or strings representing sidecars.

     Returns:
         Union[Sidecar, None]:  the merged sidecar from the list.
     """

    if not sidecar_strings:
        return None
    if not isinstance(sidecar_strings, list):
        sidecar_strings = [sidecar_strings]
    if sidecar_strings:
        file_list = []
        for s_string in sidecar_strings:
            file_list.append(io.StringIO(s_string))
        return Sidecar(files=file_list, name="Merged_Sidecar")
    else:
        return None


def to_factor(data, column=None) -> list[int]:
    """Convert data to an integer factor list.

    Parameters:
        data (Series or DataFrame): Series or DataFrame to be converted to a list.
        column (str, optional): Column name if DataFrame, otherwise column 0 is used.

    Returns:
        list[int]: A list containing 0's and 1's. Empty, 'n/a', and np.nan values are converted to 0.

    """
    if isinstance(data, Series):
        series = data
    elif isinstance(data, DataFrame) and column:
        series = data[column]
    elif isinstance(data, DataFrame):
        series = data.iloc[:, 0]
    else:
        raise HedFileError("CannotConvertToFactor",
                           f"Expecting Series or DataFrame but got {type(data)}", "")

    replaced = series.replace('n/a', False)
    filled = replaced.fillna(False)
    bool_list = filled.astype(bool).tolist()
    return [int(value) for value in bool_list]


def to_strlist(obj_list) -> list[str]:
    """Convert objects in a list to strings, preserving None values.

    Parameters:
        obj_list (list): A list of objects that are None or have a str method.

    Returns:
        list[str]: A list with the objects converted to strings. None values are preserved as empty strings.

    """
    # Using list comprehension to convert non-None items to strings
    return [str(item) if item is not None else '' for item in obj_list]


def _flatten_cat_col(col_key, col_dict):
    """Flatten a sidecar entry corresponding to a categorical column.

    Parameters:
        col_key (str): Name of the column.
        col_dict (dict): Dictionary corresponding to the categorical column (must include a 'HED' key).

    Returns:
        tuple[list[str], list[str], list[str], list[str]]:
            - A list of keys (column names).
            - A list of values (unique categorical values).
            - A list of descriptions (associated descriptions for each value).
            - A list of HED tag strings (associated HED tags for each value).

    Notes:
        - The `col_dict` must include a 'HED' key containing HED tag strings for each value.
        - The function extracts descriptions from HED tags and associates them with values.
        - If no description is found, the function uses the `Levels` dictionary in `col_dict`.

    """
    keys = []
    values = []
    descriptions = []
    tags = []
    hed_dict = col_dict['HED']
    level_dict = col_dict.get('Levels', {})
    for col_value, entry_value in hed_dict.items():
        keys.append(col_key)
        values.append(col_value)
        remainder, extracted = extract_tags(entry_value, 'Description/')
        if remainder:
            tags.append(remainder)
        else:
            tags.append('n/a')

        if extracted:
            descriptions.append(_tag_list_to_str(extracted, "Description/"))
        else:
            descriptions.append(level_dict.get(col_value, 'n/a'))

    return keys, values, descriptions, tags


def _flatten_val_col(col_key, col_dict) -> tuple[list[str], list[str], list[str], list[str]]:
    """Flatten a sidecar entry corresponding to a value column.

    Parameters:
        col_key (str): Name of the column.
        col_dict (dict): Dictionary corresponding to the value column (must include a 'HED' key).

    Returns:
        tuple[list[str], list[str], list[str], list[str]]:
            - A one-element list containing the name of the column.
            - A one-element list containing the value 'n/a'.
            - A one-element list containing the description.
            - A one-element list containing the HED string.

    Notes:
        - The `col_dict` must include a 'HED' key containing the HED tag string for the column.
        - The function extracts descriptions from HED tags and associates them with the column.
        - If no description is found, the function uses the `Description` key in `col_dict`.

    """
    tags, extracted = extract_tags(col_dict['HED'], 'Description/')
    if extracted:
        description = _tag_list_to_str(extracted, removed_tag="Description/")
    else:
        description = col_dict.get('Description', 'n/a')
    return [col_key], ['n/a'], [description], [tags]


# def _get_row_tags(row, description_tag=True):
#     """ Return the HED string associated with row, possibly without the description.
#
#     Parameters:
#         row (DataSeries):        Pandas data frame containing a row of a tagging spreadsheet.
#         description_tag (bool):  If True, include any Description tags in the returned string.
#
#     Returns:
#         str:  A HED string extracted from the row.
#         str:  A string representing the description (without the Description tag).
#
#     Notes:
#         If description_tag is True the entire tag string is included with description.
#         If there was a description extracted, it is appended to any existing description.
#
#     """
#     remainder, extracted = extract_tags(row['HED'], 'Description/')
#     if description_tag:
#         tags = row["HED"]
#     else:
#         tags = remainder
#
#     if row["description"] != 'n/a':
#         description = row["description"]
#     else:
#         description = ""
#     if extracted:
#         description = " ".join([description, extracted])
#     return tags, description


def _get_value_entry(hed_entry, description_entry, description_tag=True):
    """ Return a HED dictionary representing a value entry in a HED tagging spreadsheet.

    Parameters:
        hed_entry (str):   The string found in the HED column of the row.
        description_entry (str):  The string found in the description column of the row.
        description_tag (bool):  If True, include the description column as part of the HED entry.

    Returns:
        dict:  A dictionary with containing only HED and Description keys (as in for a value column of a JSON sidecar.)

    """
    value_dict = {}
    tags = ""
    if hed_entry and hed_entry != 'n/a':
        tags = hed_entry
    if description_entry and description_entry != 'n/a':
        value_dict['Description'] = description_entry
        if description_tag and tags:
            tags = tags + ", Description/" + description_entry
        elif description_tag and not tags:
            tags = "Description/" + description_entry
    if tags:
        value_dict["HED"] = tags
    return value_dict


def _tag_list_to_str(extracted, removed_tag=None):
    """ Return a concatenation of the strings in extracted, with removed_tag prefix deleted.

    Parameters:
        extracted (list):          List of tag strings to be concatenated.
        removed_tag (str, None):   A HED tag prefix to be removed before concatenation.

    Returns: (str)
        concatenated string

    Note: This function is designed to concatenate strings containing Description tags into a single description.

    """
    if not removed_tag:
        return " ".join(extracted)
    str_list = []
    for ind, item in enumerate(extracted):
        ind = item.casefold().find(removed_tag.casefold())
        if ind >= 0:
            str_list.append(item[ind+len(removed_tag):])
        else:
            str_list.append(item)
    return " ".join(str_list)


def _update_cat_dict(cat_dict, value_entry, hed_entry, description_entry, description_tag=True):
    """ Update a category entry in the sidecar dictionary based on a row of the spreadsheet.

    Parameters:
        cat_dict (dict):         A dictionary representing a category column in a JSON sidecar.
        value_entry (str):       The value of the key in the category dictionary.
        hed_entry (str):         HED tag string corresponding to the key.
        description_entry (str): The description column for the Level entry and possible as a Description tag.
        description_tag (bool):  If True then the description entry is used for Level and as Description tag.

    Returns:
        dict: An updated dictionary representing a category column.

    """
    value_dict = _get_value_entry(hed_entry, description_entry, description_tag)
    if 'Description' in value_dict:
        level_part = cat_dict.get('Levels', {})
        level_part[value_entry] = value_dict['Description']
        cat_dict['Levels'] = level_part
    if 'HED' in value_dict:
        hed_part = cat_dict.get('HED', {})
        hed_part[value_entry] = value_dict['HED']
        cat_dict['HED'] = hed_part


# def _update_remainder(remainder, update_piece):
#     """ Update remainder with update piece.
#
#     Parameters:
#         remainder (str):      A tag string without trailing comma.
#         update_piece (str):   A tag string to be appended.
#
#     Returns:
#         str: A concatenation of remainder and update_piece, paying attention to separating commas.
#
#     """
#     if not update_piece:
#         return remainder
#     elif not remainder:
#         return update_piece
#     elif remainder.endswith(')') or update_piece.startswith('('):
#         return remainder + update_piece
#     else:
#         return remainder + ", " + update_piece
