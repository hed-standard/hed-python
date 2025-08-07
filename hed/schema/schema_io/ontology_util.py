"""Utility functions for saving as an ontology or dataframe."""

import pandas as pd

from hed.schema.schema_io import schema_util, df_constants as constants
from hed.errors.exceptions import HedFileError
from hed.schema.hed_schema_constants import HedKey
from hed.schema.schema_io.df_util import remove_prefix, calculate_attribute_type, get_attributes_from_row
from hed.schema.hed_cache import get_library_data

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


def _get_hedid_range(schema_name, df_key):
    """ Get the set of HedId's for this object type/schema name.

    Parameters:
        schema_name(str): The known schema name with an assigned id range.
        df_key(str): The dataframe range type we're interested in.  a key from constants.DF_SUFFIXES.

    Returns:
        set: A set of all id's in the requested range.
    """
    if df_key == constants.STRUCT_KEY:
        raise NotImplementedError("Cannot assign hed_ids struct section")

    library_data = get_library_data(schema_name)
    if not library_data:
        return set()
    starting_id, ending_id = library_data["id_range"]

    start_object_range, end_object_range = object_type_id_offset[df_key]
    if df_key == constants.TAG_KEY:
        initial_tag_adj = 1  # We always skip 1 for tags
    else:
        initial_tag_adj = 0
    final_start = starting_id + start_object_range + initial_tag_adj
    final_end = starting_id + end_object_range
    if end_object_range == -1:
        # Add one since the versions on hed-schemas are set to max_value - 1
        final_end = ending_id + 1
    return set(range(final_start, final_end))


def get_all_ids(df):
    """Returns a set of all unique hedIds in the dataframe

    Parameters:
        df(pd.DataFrame): The dataframe

    Returns:
        Union[Set, None]: None if this has no HED column, otherwise all unique numbers as a set.
    """
    if constants.hed_id in df.columns:
        modified_df = df[constants.hed_id].apply(lambda x: remove_prefix(x, "HED_"))
        modified_df = pd.to_numeric(modified_df, errors="coerce").dropna().astype(int)
        return set(modified_df.unique())
    return None


def update_dataframes_from_schema(dataframes, schema, schema_name="", get_as_ids=False, assign_missing_ids=False):
    """ Write out schema as a dataframe, then merge in extra columns from dataframes.

    Parameters:
        dataframes(dict): A full set of schema spreadsheet formatted dataframes
        schema(HedSchema): The schema to write into the dataframes:
        schema_name(str): The name to use to find the schema id range.
        get_as_ids(bool): If True, replace all known references with HedIds
        assign_missing_ids(bool): If True, replacing any blank(new) HedIds with valid ones

    Returns:
        dict[str:pd.DataFrames]: The updated dataframes. These dataframes can potentially have extra columns.

    """
    hedid_errors = []
    if not schema_name:
        schema_name = schema.library
    # 1. Verify existing HED ids don't conflict between schema/dataframes
    for df_key, df in dataframes.items():
        if df_key in constants.DF_SUFFIXES:
            continue
        section_key = constants.section_mapping_hed_id.get(df_key)
        if not section_key:
            continue
        section = schema[section_key]

        unused_tag_ids = _get_hedid_range(schema_name, df_key)
        hedid_errors += _verify_hedid_matches(section, df, unused_tag_ids)

    if hedid_errors:
        raise HedFileError(hedid_errors[0]['code'],
                           f"{len(hedid_errors)} issues found with hedId mismatches.  See the .issues "
                           f"parameter on this exception for more details.", schema.name, issues=hedid_errors)

    # 2. Get the new schema as DFs
    from hed.schema.schema_io.schema2df import Schema2DF  # Late import as this is recursive
    output_dfs = Schema2DF(get_as_ids=get_as_ids).process_schema(schema, save_merged=False)

    if assign_missing_ids:
        # 3: Add any HED ID's as needed to these generated dfs
        for df_key, df in output_dfs.items():
            if df_key == constants.STRUCT_KEY or df_key in constants.DF_EXTRAS:
                continue
            unused_tag_ids = _get_hedid_range(schema_name, df_key)

            # If no errors, assign new HED ID's
            assign_hed_ids_section(df, unused_tag_ids)

    # 4: Merge the dataframes
    for df_key in output_dfs.keys():
        if df_key in constants.DF_EXTRAS:
            continue
        out_df = output_dfs[df_key]
        df = dataframes[df_key]
        merge_dfs(out_df, df)

    return output_dfs


def _verify_hedid_matches(section, df, unused_tag_ids):
    """ Verify ID's in both have the same label, and verify all entries in the dataframe are already in the schema

    Parameters:
        section(HedSchemaSection): The loaded schema section to compare ID's with
        df(pd.DataFrame): The loaded spreadsheet dataframe to compare with
        unused_tag_ids(set): The valid range of IDs for this df.

    Returns:
        list[str]: A list of errors found matching IDs.
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
            # Neither side has a hedID, so nothing to do.
            if not df_id:
                continue
            hedid_errors += schema_util.format_error(row_number, row,
                                                     f"'{label}' does not exist in schema file only the spreadsheet.")
            continue
        entry_id = entry.attributes.get(HedKey.HedID)
        if df_id:
            if not (df_id.startswith("HED_") and len(df_id) == len("HED_0000000")):
                hedid_errors += schema_util.format_error(row_number, row,
                                                         f"'{label}' has an improperly formatted hedID in dataframe.")
                continue
            id_value = remove_prefix(df_id, "HED_")
            try:
                id_int = int(id_value)
                if id_int not in unused_tag_ids:
                    hedid_errors += schema_util.format_error(
                        row_number, row, f"'{label}' has id {id_int} which is outside " +
                        "of the valid range for this type.  Valid range is: " +
                        f"{min(unused_tag_ids)} to {max(unused_tag_ids)}")
                    continue
            except ValueError:
                hedid_errors += schema_util.format_error(
                    row_number, row, f"'{label}' has a non-numeric hedID in the dataframe.")
                continue

        if entry_id and entry_id != df_id:
            hedid_errors += schema_util.format_error(
                row_number, row, f"'{label}' has hedID '{df_id}' in dataframe, but '{entry_id}' in schema.")
            continue

    return hedid_errors


def assign_hed_ids_section(df, unused_tag_ids):
    """ Adds missing HedIds to dataframe.

    Parameters:
        df(pd.DataFrame): The dataframe to add id's to.
        unused_tag_ids(set of int): The possible HED id's to assign from
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

    Parameters:
        dest_df (DataFrame): The dataframe to add extra columns to
        source_df (DataFrame): The dataframe to get extra columns from
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


def _get_annotation_prop_ids(schema):
    annotation_props = dict()
    for entry in schema.attributes.values():
        attribute_type = calculate_attribute_type(entry)

        if attribute_type == "annotation":
            annotation_props[entry.name] = entry.attributes[HedKey.HedID]

    for entry in schema.properties.values():
        annotation_props[entry.name] = entry.attributes[HedKey.HedID]

    return annotation_props


def get_prefixes(dataframes):
    """ Get the prefixes and external annotation terms from the dataframes for ontology conversion."""
    prefixes = dataframes.get(constants.PREFIXES_KEY)
    extensions = dataframes.get(constants.EXTERNAL_ANNOTATION_KEY)
    sources = dataframes.get(constants.SOURCES_KEY)
    if prefixes is None or extensions is None:
        return {}
    prefixes.columns = prefixes.columns.str.lower()
    all_prefixes = {prefix.prefix: prefix[2] for prefix in prefixes.itertuples()}
    extensions.columns = extensions.columns.str.lower()
    sources.columns = sources.columns.str.lower()
    annotation_terms = {}
    for row in extensions.itertuples():
        annotation_terms[row.prefix + row.id] = all_prefixes[row.prefix]
    source_dict = {}
    for row in sources.itertuples():
        source_dict[row.source] = row.link
    return annotation_terms, source_dict


def convert_df_to_omn(dataframes):
    """ Convert the dataframe format schema to omn format.

    Parameters:
        dataframes(dict): A set of dataframes representing a schema, potentially including extra columns

    Returns:
        tuple[str, dict]:
        - A combined string representing (most of) a schema omn file.
        - A of DF_SUFFIXES:str, representing each .tsv file in omn format.
    """
    from hed.schema.hed_schema_io import from_dataframes
    from hed.schema.schema_io.schema2df import Schema2DF  # Late import as this is recursive
    annotation_terms, source_dict = get_prefixes(dataframes)

    # Load the schema, so we can save it out with ID's
    schema = from_dataframes(dataframes)
    schema2df = Schema2DF(get_as_ids=True)
    output1 = schema2df.process_schema(schema, save_merged=False)
    if hasattr(schema, 'extras') and schema.extras:
        output1.update(schema.extras)
    # Convert dataframes to hedId format, and add any missing hedId's(generally, they should be replaced before here)
    dataframes_u = update_dataframes_from_schema(dataframes, schema, get_as_ids=True)

    # Copy over remaining non schema dataframes.
    for suffix in constants.DF_EXTRAS:
        if suffix in dataframes:
            dataframes_u[suffix] = dataframes[suffix]

    # Write out the new dataframes in omn format
    annotation_props = _get_annotation_prop_ids(schema)
    full_text = ""
    omn_data = {}
    for suffix, dataframe in dataframes_u.items():
        if suffix in constants.DF_EXTRAS:
            output_text = _convert_extra_df_to_omn(dataframes_u[suffix], suffix)
        else:
            output_text = _convert_df_to_omn(dataframes_u[suffix], annotation_properties=annotation_props,
                                             annotation_terms=annotation_terms)
        omn_data[suffix] = output_text
        full_text += output_text + "\n"

    return full_text, omn_data


def _convert_df_to_omn(df, annotation_properties=("",), annotation_terms=None):
    """Takes a single df format schema and converts it to omn.

        This is one section, e.g. tags, units, etc.

        Note: This mostly assumes a fully valid df.  A df missing a required column will raise an error.

    Parameters:
        df(pd.DataFrame): the dataframe to turn into omn
        annotation_properties(dict): Known annotation properties, with the values being their hedId.
        annotation_terms(dict): The list of valid external omn tags, such as "dc:source".

    Returns:
        str: The omn formatted text for this section.

    """
    output_text = ""
    for index, row in df.iterrows():
        prop_type = _get_property_type(row)
        hed_id = row[constants.hed_id]
        output_text += f"{prop_type}: hed:{hed_id}\n"
        output_text += _add_annotation_lines(row, annotation_properties, annotation_terms)

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
            if equivalent_to:
                output_text += "\tEquivalentTo:\n"
                output_text += f"\t\t{equivalent_to}"
            else:
                output_text += "\tSubClassOf:\n"
                output_text += f"\t\t{subclass_of}"
            output_text += "\n"

        output_text += "\n"
    return output_text


def _convert_extra_df_to_omn(df, suffix):
    """Takes a single df format schema and converts it to omn.

        This is one section, e.g. tags, units, etc.

        Note: This mostly assumes a fully valid df.  A df missing a required column will raise an error.

    Parameters:
        df(pd.DataFrame): the dataframe to turn into omn
        suffix(dict): Known annotation properties, with the values being their hedId.

    Returns:
        str: the omn formatted text for this section.

    """
    output_text = ""
    for index, row in df.iterrows():
        renamed_row = row.rename(index=constants.EXTRAS_CONVERSIONS)
        if suffix == constants.PREFIXES_KEY:
            output_text += f"Prefix: {renamed_row[constants.Prefix]} <{renamed_row[constants.namespace]}>"
        elif suffix == constants.EXTERNAL_ANNOTATION_KEY:
            output_text += f"AnnotationProperty: {renamed_row[constants.Prefix]}{renamed_row[constants.ID]}"
        elif suffix == constants.SOURCES_KEY:
            output_text += f"Source: {renamed_row[constants.source]}"
            if renamed_row[constants.link]:
                output_text += f" <{renamed_row[constants.link]}>"
            if renamed_row[constants.description]:
                output_text += f" \"{renamed_row[constants.description]}\""
        else:
            raise ValueError(f"Unknown tsv suffix attempting to be converted {suffix}")

        output_text += "\n"
    return output_text


def _split_on_unquoted_commas(input_string):
    """ Splits the given string into comma separated portions, ignoring commas inside double quotes.

    Parameters:
        input_string: The string to split

    Returns:
        list: The split apart string.
    """
    # Note: does not handle escaped double quotes.
    parts = []
    current = []
    in_quotes = False

    for char in input_string:
        if char == '"':
            in_quotes = not in_quotes
        if char == ',' and not in_quotes:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(char)

    if current:  # Add the last part if there is any.
        parts.append(''.join(current).strip())

    return parts


def _split_annotation_values(parts):
    annotations = dict()
    for part in parts:
        key, value = part.split(" ", 1)
        annotations[key] = value

    return annotations


def _add_annotation_lines(row, annotation_properties, annotation_terms):
    annotation_lines = []
    description = row[constants.dcdescription]
    if description:
        annotation_lines.append(f"\t\t{constants.dcdescription} \"{description}\"")
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

    # if constants.annotations in row.index:
    #     portions = _split_on_unquoted_commas(row[constants.annotations])
    #     annotations = _split_annotation_values(portions)
    #
    #     for key, value in annotations.items():
    #         if key not in annotation_terms:
    #             raise ValueError(f"Problem.  Found {key} which is not in the prefix/annotation list.")
    #         annotation_lines.append(f"\t\t{key} {value}")

    output_text = ""
    if annotation_lines:
        output_text += "\tAnnotations:\n"
        output_text += ",\n".join(annotation_lines)
    output_text += "\n"

    return output_text


def _get_property_type(row):
    """Gets the property type from the row."""
    return row[constants.property_type] if constants.property_type in row.index else "Class"
