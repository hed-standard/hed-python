"""Utility functions for saving as an ontology or dataframe."""
import os

import pandas as pd

from hed.schema.schema_io import schema_util
from hed.errors.exceptions import HedFileError
from hed.schema import hed_schema_df_constants as constants
from hed.schema.hed_schema_constants import HedKey
from hed.schema.schema_io.text_util import parse_attribute_string

library_index_ranges = {
    "": (10000, 40000),
    "score": (40000, 60000),
    "lang": (60000, 80000)
}
UNKNOWN_LIBRARY_VALUE = 9910000

object_type_id_offset = {
    constants.OBJECT_KEY: (100, 300),
    constants.DATA_KEY: (300, 500),
    constants.ANNOTATION_KEY: (500, 700),
    constants.ATTRIBUTE_PROPERTY_KEY: (700, 900),
    constants.VALUE_CLASS_KEY: (1300, 1400),
    constants.UNIT_MODIFIER_KEY: (1400, 1500),
    constants.UNIT_CLASS_KEY: (1500, 1600),
    constants.UNIT_KEY: (1600, 1700),
    constants.TAG_KEY: (2000, -1),  # -1 = go to end of range
}


def get_library_name_and_id(schema):
    """ Get the library("Standard" for the standard schema) and first id for a schema range

    Parameters:
        schema(HedSchema): The schema to check

    Returns:
        library_name(str): The capitalized library name
        first_id(int): the first id for a given library
    """
    name = schema.library

    starting_id, _ = library_index_ranges.get(name, (UNKNOWN_LIBRARY_VALUE, 0))

    if not name:
        name = "standard"
    return name.capitalize(), starting_id


def _get_hedid_range(schema_name, df_key):
    """ Get the set of HedId's for this object type/schema name.

    Parameters:
        schema_name(str): The known schema name with an assigned id range
        df_key(str): The dataframe range type we're interested in.  a key from constants.DF_SUFFIXES

    Returns:
        number_set(set): A set of all id's in the requested range
    """
    if df_key == constants.STRUCT_KEY:
        raise NotImplementedError("Cannot assign hed_ids struct section")

    starting_id, ending_id = library_index_ranges[schema_name]

    start_object_range, end_object_range = object_type_id_offset[df_key]
    if df_key == constants.TAG_KEY:
        initial_tag_adj = 1  # We always skip 1 for tags
    else:
        initial_tag_adj = 0
    final_start = starting_id + start_object_range + initial_tag_adj
    final_end = starting_id + end_object_range
    if end_object_range == -1:
        final_end = ending_id
    return set(range(final_start, final_end))


# todo: Replace this once we no longer support < python 3.9
def remove_prefix(text, prefix):
    if text and text.startswith(prefix):
        return text[len(prefix):]
    return text


def get_all_ids(df):
    """Returns a set of all unique hedIds in the dataframe

    Parameters:
        df(pd.DataFrame): The dataframe

    Returns:
        numbers(Set or None): None if this has no hed column, otherwise all unique numbers as a set.
    """
    if constants.hed_id in df.columns:
        modified_df = df[constants.hed_id].apply(lambda x: remove_prefix(x, "HED_"))
        modified_df = pd.to_numeric(modified_df, errors="coerce").dropna().astype(int)
        return set(modified_df.unique())
    return None


def update_dataframes_from_schema(dataframes, schema, schema_name="", get_as_ids=False,
                                  assign_missing_ids=False):
    """ Write out schema as a dataframe, then merge in extra columns from dataframes.

    Parameters:
        dataframes(dict of str:pd.DataFrames): A full set of schema spreadsheet formatted dataframes
        schema(HedSchema): The schema to write into the dataframes:
        schema_name(str): The name to use to find the schema id range.
        get_as_ids(bool): If True, replace all known references with HedIds
        assign_missing_ids(bool): If True, replacing any blank(new) HedIds with valid ones

    Returns:
        dataframes(dict of str:pd.DataFrames): The updated dataframes
                                               These dataframes can potentially have extra columns
    """
    hedid_errors = []
    # 1. Verify existing hed ids don't conflict between schema/dataframes
    for df_key, df in dataframes.items():
        section_key = constants.section_mapping.get(df_key)
        if not section_key:
            continue
        section = schema[section_key]

        unused_tag_ids = _get_hedid_range(schema_name, df_key)
        hedid_errors += _verify_hedid_matches(section, df, unused_tag_ids)

    if hedid_errors:
        raise HedFileError(hedid_errors[0]['code'],
                           f"{len(hedid_errors)} issues found with hedId mismatches.  See the .issues "
                           f"parameter on this exception for more details.", schema.name,
                           issues=hedid_errors)

    # 2. Get the new schema as DFs
    from hed.schema.schema_io.schema2df import Schema2DF  # Late import as this is recursive
    output_dfs = Schema2DF(get_as_ids=get_as_ids).process_schema(schema, save_merged=False)

    if assign_missing_ids:
        # 3: Add any hed ID's as needed to these generated dfs
        for df_key, df in output_dfs.items():
            if df_key == constants.STRUCT_KEY:
                continue
            unused_tag_ids = _get_hedid_range(schema_name, df_key)

            # If no errors, assign new hed ID's
            assign_hed_ids_section(df, unused_tag_ids)

    # 4: Merge the dataframes
    for df_key in output_dfs.keys():
        out_df = output_dfs[df_key]
        df = dataframes[df_key]
        merge_dfs(out_df, df)

    return output_dfs


def _verify_hedid_matches(section, df, unused_tag_ids):
    """ Verify ID's in both have the same label, and verify all entries in the dataframe are already in the schema

    Parameters:
        section(HedSchemaSection): The loaded schema section to compare ID's with
        df(pd.DataFrame): The loaded spreadsheet dataframe to compare with
        unused_tag_ids(set): The valid range of ID's for this df

    Returns:
        error_list(list of str): A list of errors found matching id's
    """
    hedid_errors = []
    for row_number, row in df.iterrows():
        if not any(row):
            continue
        label = row[constants.name]
        if label.endswith("-#"):
            label = label.replace("-#", "/#")
        df_id = row[constants.hed_id]
        entry = section.get(label)
        if not entry:
            hedid_errors += schema_util.format_error(row_number, row,
                                                     f"'{label}' does not exist in the schema file provided, only the spreadsheet.")
            continue
        entry_id = entry.attributes.get(HedKey.HedID)
        if df_id:
            if not (df_id.startswith("HED_") and len(df_id) == len("HED_0000000")):
                hedid_errors += schema_util.format_error(row_number, row,
                                                         f"'{label}' has an improperly formatted hedID in the dataframe.")
                continue
            id_value = remove_prefix(df_id, "HED_")
            try:
                id_int = int(id_value)
                if id_int not in unused_tag_ids:
                    hedid_errors += schema_util.format_error(row_number, row,
                                                             f"'{label}' has id {id_int} which is outside of the valid range for this type.  Valid range is: {min(unused_tag_ids)} to {max(unused_tag_ids)}")
                    continue
            except ValueError:
                hedid_errors += schema_util.format_error(row_number, row,
                                                         f"'{label}' has a non-numeric hedID in the dataframe.")
                continue

        if entry_id and entry_id != df_id:
            hedid_errors += schema_util.format_error(row_number, row,
                                                     f"'{label}' has hedID '{df_id}' in dataframe, but '{entry_id}' in schema.")
            continue

    return hedid_errors


def assign_hed_ids_section(df, unused_tag_ids):
    """ Adds missing HedIds to dataframe.

    Parameters:
        df(pd.DataFrame): The dataframe to add id's to.
        unused_tag_ids(set of int): The possible hed id's to assign from
    """
    # Remove already used ids
    unused_tag_ids -= get_all_ids(df)
    sorted_unused_ids = sorted(unused_tag_ids, reverse=True)

    for row_number, row in df.iterrows():
        hed_id = row[constants.hed_id]
        # we already verified existing ones
        if hed_id:
            continue
        hed_id = f"HED_{sorted_unused_ids.pop():07d}"
        row[constants.hed_id] = hed_id


def merge_dfs(dest_df, source_df):
    """ Merges extra columns from source_df into dest_df, adding the extra columns from the ontology to the schema df.

    Args:
        dest_df: The dataframe to add extra columns to
        source_df: The dataframe to get extra columns from
    """
    # todo: vectorize this at some point
    save_df1_columns = dest_df.columns.copy()
    for index, row in source_df.iterrows():
        # Find matching index in df1 based on 'rdfs:label'
        match_index = dest_df[dest_df['rdfs:label'] == row['rdfs:label']].index
        if not match_index.empty:
            for col in source_df.columns:
                if col not in save_df1_columns:
                    dest_df.at[match_index[0], col] = row[col]


def _get_annotation_prop_ids(dataframes):
    annotation_props = {key: value for key, value in zip(dataframes[constants.ANNOTATION_KEY][constants.name],
                                                         dataframes[constants.ANNOTATION_KEY][constants.hed_id])}
    # Also add schema properties
    annotation_props.update(
        {key: value for key, value in zip(dataframes[constants.ATTRIBUTE_PROPERTY_KEY][constants.name],
                                          dataframes[constants.ATTRIBUTE_PROPERTY_KEY][constants.hed_id])})

    return annotation_props


def convert_df_to_omn(dataframes):
    """ Convert the dataframe format schema to omn format.

    Parameters:
        dataframes(dict): A set of dataframes representing a schema, potentially including extra columns

    Returns:
        tuple:
            omn_file(str): A combined string representing (most of) a schema omn file.
            omn_data(dict): a dict of DF_SUFFIXES:str, representing each .tsv file in omn format.
    """
    from hed.schema.hed_schema_io import from_dataframes
    # Load the schema, so we can save it out with ID's
    schema = from_dataframes(dataframes)
    # Convert dataframes to hedId format, and add any missing hedId's(generally, they should be replaced before here)
    dataframes = update_dataframes_from_schema(dataframes, schema, get_as_ids=True)

    # Write out the new dataframes in omn format
    annotation_props = _get_annotation_prop_ids(dataframes)
    full_text = ""
    omn_data = {}
    for suffix, dataframe in dataframes.items():
        if suffix == constants.STRUCT_KEY:  # not handled here yet
            continue
        output_text = _convert_df_to_omn(dataframes[suffix], annotation_properties=annotation_props)
        omn_data[suffix] = output_text
        full_text += output_text + "\n"

    return full_text, omn_data


def _convert_df_to_omn(df, annotation_properties=("",)):
    """Takes a single df format schema and converts it to omn.

        This is one section, e.g. tags, units, etc.

        Note: This mostly assumes a fully valid df.  A df missing a required column will raise an error.

    Parameters:
        df(pd.DataFrame): the dataframe to turn into omn
        annotation_properties(dict of str:str): Known annotation properties, with the values being their hedId.
    Returns:
        omn_text(str): the omn formatted text for this section
    """
    output_text = ""
    for index, row in df.iterrows():
        prop_type = "Class"
        if constants.property_type in row.index:
            prop_type = row[constants.property_type]
        hed_id = row[constants.hed_id]
        output_text += f"{prop_type}: hed:{hed_id}\n"
        annotation_lines = []
        description = row[constants.description]
        if description:
            annotation_lines.append(f"\t\t{constants.description} \"{description}\"")
        name = row[constants.name]
        if name:
            annotation_lines.append(f"\t\t{constants.name} \"{name}\"")

        # Add annotation properties(other than HedId)
        attributes = get_attributes_from_row(row)
        for attribute in attributes:
            if attribute in annotation_properties and attribute != HedKey.HedID:
                annotation_id = f"hed:{annotation_properties[attribute]}"
                value = attributes[attribute]
                if value is True:
                    value = "true"
                else:
                    value = f'"{value}"'
                annotation_lines.append(f"\t\t{annotation_id} {value}")

        if annotation_lines:
            output_text += "\tAnnotations:\n"
            output_text += ",\n".join(annotation_lines)
        output_text += "\n"

        if prop_type != "AnnotationProperty":
            if constants.property_domain in row.index:
                prop_domain = row[constants.property_domain]
                output_text += "\tDomain:\n"
                output_text += f"\t\t{prop_domain}\n"
            if constants.property_range in row.index:
                prop_range = row[constants.property_range]
                output_text += "\tRange:\n"
                output_text += f"\t\t{prop_range}\n"
                output_text += "\n"

        if constants.equivalent_to in row.index:
            equivalent_to = row[constants.equivalent_to]
            equivalent_to = equivalent_to.replace(" and ", "\n\t\tand ")
            subclass_of = row[constants.subclass_of]
            if equivalent_to and equivalent_to != subclass_of:
                output_text += "\tEquivalentTo:\n"
                output_text += f"\t\t{equivalent_to}"
            else:
                output_text += "\tSubClassOf:\n"
                output_text += f"\t\t{subclass_of}"
            output_text += "\n"

        output_text += "\n"
    return output_text


def save_dataframes(base_filename, dataframe_dict):
    """ Writes out the dataframes using the provided suffixes.

    Does not validate contents or suffixes.

    Parameters:
        base_filename(str): The base filename to use.  Output is {base_filename}_{suffix}.tsv
                            See DF_SUFFIXES for all expected names.
        dataframe_dict(dict of str: df.DataFrame): The list of files to save out.  No validation is done.
    """
    base, base_ext = os.path.splitext(base_filename)
    for suffix, dataframe in dataframe_dict.items():
        filename = f"{base}_{suffix}.tsv"
        with open(filename, mode='w', encoding='utf-8') as opened_file:
            dataframe.to_csv(opened_file, sep='\t', index=False, header=True)


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
    return parse_attribute_string(attr_string)
