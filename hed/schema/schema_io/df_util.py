import csv
import os

import pandas as pd

from hed.errors import HedFileError, HedExceptions
from hed.schema.schema_io import df_constants as constants
from hed.schema.hed_schema_constants import HedKey
from hed.schema.hed_cache import get_library_data
from hed.schema.schema_io.text_util import parse_attribute_string, _parse_header_attributes_line

UNKNOWN_LIBRARY_VALUE = 0

def merge_dataframes(df1, df2, key) :
    """ Create a new dataframe where df2 is merged into df1 and duplicates are eliminated.

    Parameters:
        df1(df.DataFrame): dataframe to use as destination merge.
        df2(df.DataFrame): dataframe to use as a merge element.
        key(str): name of the column that is treated as the key when dataframes are merged

    Returns:
        df.DataFrame: The merged dataframe.

    """
    if df2 is None or df2.empty:
        return df1
    if set(df1.columns) != set(df2.columns):
        raise HedFileError(HedExceptions.BAD_COLUMN_NAMES,
                           f"Both dataframes corresponding to {key} to be merged must have the same columns.  "
                           f"df1 columns: {list(df1.columns)} df2 columns: {list(df2.columns)}", "")
    combined = pd.concat([df1, df2], ignore_index=True)
    combined = combined.sort_values(by=list(combined.columns))
    combined = combined.drop_duplicates()
    return combined

def merge_dataframe_dicts(df_dict1, df_dict2, key_column=constants.KEY_COLUMN_NAME):
    """ Create a new dictionary of DataFrames where dict2 is merged into dict1.

    Does not validate contents or suffixes.

    Parameters:
        df_dict1(dict of str: df.DataFrame): dataframes to use as destination merge.
        df_dict2(dict of str: df.DataFrame): dataframes to use as a merge element.
        key_column(str): name of the column that is treated as the key when dataframes are merged
    """

    result_dict = {}
    all_keys = set(df_dict1.keys()).union(set(df_dict2.keys()))

    for key in all_keys:
        if key in df_dict1 and key in df_dict2:
            result_dict[key] = _merge_dataframes(df_dict1[key], df_dict2[key], key_column)
        elif key in df_dict1:
            result_dict[key] = df_dict1[key]
        else:
            result_dict[key] = df_dict2[key]

    return result_dict


def _merge_dataframes(df1, df2, key_column):
    # Add columns from df2 that are not in df1, only for rows that are in df1

    if df1.empty or df2.empty or key_column not in df1.columns or key_column not in df2.columns:
        raise HedFileError(HedExceptions.BAD_COLUMN_NAMES,
                           f"Both dataframes to be merged must be non-empty had nave a '{key_column}' column", "")
    df1 = df1.copy()
    for col in df2.columns:
        if col not in df1.columns and col != key_column:
            df1 = df1.merge(df2[[key_column, col]], on=key_column, how='left')

    # Fill missing values with '' for object columns, 0 for numeric columns
    for col in df1.columns:
        if df1[col].dtype == 'object':
            df1[col] = df1[col].fillna('')
        else:
            df1[col] = df1[col].fillna(0)

    return df1

def save_dataframes(base_filename, dataframe_dict):
    """ Writes out the dataframes using the provided suffixes.

    Does not validate contents or suffixes.

    If base_filename has a .tsv suffix, save directly to the indicated location.
    If base_filename is a directory(does NOT have a .tsv suffix), save the contents into a directory named that.
    The subfiles are named the same.  e.g. HED8.3.0/HED8.3.0_Tag.tsv

    Parameters:
        base_filename(str): The base filename to use.  Output is {base_filename}_{suffix}.tsv
                            See DF_SUFFIXES for all expected names.
        dataframe_dict(dict of str: df.DataFrame): The list of files to save out.  No validation is done.
    """
    if base_filename.lower().endswith(".tsv"):
        base, base_ext = os.path.splitext(base_filename)
        base_dir, base_name = os.path.split(base)
    else:
        # Assumed as a directory name
        base_dir = base_filename
        base_filename = os.path.split(base_dir)[1]
        base = os.path.join(base_dir, base_filename)
    os.makedirs(base_dir, exist_ok=True)
    for suffix, dataframe in dataframe_dict.items():
        filename = f"{base}_{suffix}.tsv"
        with open(filename, mode='w', encoding='utf-8') as opened_file:
            dataframe.to_csv(opened_file, sep='\t', index=False, header=True, quoting=csv.QUOTE_NONE,
                             lineterminator="\n")


def convert_filenames_to_dict(filenames):
    """Infers filename meaning based on suffix, e.g. _Tag for the tags sheet

    Parameters:
        filenames(str or None or list or dict): The list to convert to a dict
            If a string with a .tsv suffix: Save to that location, adding the suffix to each .tsv file
            If a string with no .tsv suffix: Save to that folder, with the contents being the separate .tsv files.

    Returns:
        dict[str: str]: The required suffix to filename mapping.

    """
    result_filenames = {}
    dataframe_names = constants.DF_SUFFIXES
    if isinstance(filenames, str):
        if filenames.endswith(".tsv"):
            base, base_ext = os.path.splitext(filenames)
        else:
            # Load as foldername/foldername_suffix.tsv
            base_dir = filenames
            base_filename = os.path.split(base_dir)[1]
            base = os.path.join(base_dir, base_filename)
        for suffix in dataframe_names:
            filename = f"{base}_{suffix}.tsv"
            result_filenames[suffix] = filename
        filenames = result_filenames
    elif isinstance(filenames, list):
        for filename in filenames:
            remainder, suffix = filename.replace("_", "-").rsplit("-")
            for needed_suffix in dataframe_names:
                if needed_suffix in suffix:
                    result_filenames[needed_suffix] = filename
        filenames = result_filenames

    return filenames


def create_empty_dataframes():
    """Returns the default empty dataframes"""
    base_dfs = {constants.STRUCT_KEY: pd.DataFrame(columns=constants.struct_columns, dtype=str),
                constants.TAG_KEY: pd.DataFrame(columns=constants.tag_columns, dtype=str),
                constants.UNIT_KEY: pd.DataFrame(columns=constants.unit_columns, dtype=str),
                constants.UNIT_CLASS_KEY: pd.DataFrame(columns=constants.other_columns, dtype=str),
                constants.UNIT_MODIFIER_KEY: pd.DataFrame(columns=constants.other_columns, dtype=str),
                constants.VALUE_CLASS_KEY: pd.DataFrame(columns=constants.other_columns, dtype=str),
                constants.ANNOTATION_KEY: pd.DataFrame(columns=constants.attribute_columns, dtype=str),
                constants.DATA_KEY: pd.DataFrame(columns=constants.attribute_columns, dtype=str),
                constants.OBJECT_KEY: pd.DataFrame(columns=constants.attribute_columns, dtype=str),
                constants.ATTRIBUTE_PROPERTY_KEY: pd.DataFrame(columns=constants.property_columns, dtype=str),
                constants.PREFIXES_KEY: pd.DataFrame(columns=constants.prefix_columns, dtype=str),
                constants.SOURCES_KEY: pd.DataFrame(columns=constants.source_columns, dtype=str),
                constants.EXTERNAL_ANNOTATION_KEY:
                    pd.DataFrame(columns=constants.external_annotation_columns, dtype=str)
                }
    return base_dfs


def load_dataframes(filenames):
    """Load the dataframes from the source folder or series of files.

    Parameters:
        filenames(str or None or list or dict): The input filenames
            If a string with a .tsv suffix: Save to that location, adding the suffix to each .tsv file
            If a string with no .tsv suffix: Save to that folder, with the contents being the separate .tsv files.

    Returns:
        dict[str: dataframes]: The suffix:dataframe dict
    """
    dict_filenames = convert_filenames_to_dict(filenames)
    dataframes = create_empty_dataframes()
    for key, filename in dict_filenames.items():
        try:
            if key in dataframes:
                loaded_dataframe = pd.read_csv(filename, sep="\t", dtype=str, na_filter=False)
                loaded_dataframe = loaded_dataframe.rename(columns=constants.EXTRAS_CONVERSIONS)

                columns_not_in_loaded = dataframes[key].columns[~dataframes[key].columns.isin(loaded_dataframe.columns)]
                # and not dataframes[key].columns.isin(loaded_dataframe.columns).all():
                if columns_not_in_loaded.any():
                    raise HedFileError(HedExceptions.SCHEMA_LOAD_FAILED,
                                          f"Required column(s) {list(columns_not_in_loaded)} missing from {filename}.  "
                                       f"The required columns are {list(dataframes[key].columns)}", filename=filename)
                dataframes[key] = loaded_dataframe
            elif os.path.exists(filename):
                # Handle the extra files if they are present.
                dataframes[key] = pd.read_csv(filename, sep="\t", dtype=str, na_filter=False)
        except OSError:
            # todo: consider if we want to report this error(we probably do)
            pass  # We will use a blank one for this
    return dataframes


def get_library_name_and_id(schema):
    """ Get the library("Standard" for the standard schema) and first id for a schema range

    Parameters:
        schema(HedSchema): The schema to check

    Returns:
        tuple [str, int]:
        - The capitalized library name.
        - The first id for a given library.
    """

    name = schema.library

    library_data = get_library_data(name)
    starting_id, _ = library_data.get("id_range", (UNKNOWN_LIBRARY_VALUE, UNKNOWN_LIBRARY_VALUE))
    if not name:
        name = "standard"
    return name.capitalize(), starting_id


# todo: Replace this once we no longer support < python 3.9
def remove_prefix(text, prefix):
    if text and text.startswith(prefix):
        return text[len(prefix):]
    return text


def calculate_attribute_type(attribute_entry):
    """Returns the type of this attribute(annotation, object, data)

    Returns:
        str: "annotation", "object", or "data".
    """
    attributes = attribute_entry.attributes
    object_ranges = {HedKey.TagRange, HedKey.UnitRange, HedKey.UnitClassRange, HedKey.ValueClassRange}
    if HedKey.AnnotationProperty in attributes:
        return "annotation"
    elif any(attribute in object_ranges for attribute in attributes):
        return "object"
    return "data"


def get_attributes_from_row(row):
    """ Get the tag attributes from a line.

    Parameters:
        row (pd.Series): A tag line.

    Returns:
        dict: Dictionary of attributes.
    """
    if constants.properties in row.index:
        attr_string = row[constants.properties]
    elif constants.attributes in row.index:
        attr_string = row[constants.attributes]
    else:
        attr_string = ""

    if constants.subclass_of in row.index and row[constants.subclass_of] == "HedHeader":
        header_attributes, _ = _parse_header_attributes_line(attr_string)
        return header_attributes
    return parse_attribute_string(attr_string)
