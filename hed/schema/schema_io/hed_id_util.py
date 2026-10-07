"""Utility functions for HED ID assignment and validation.

This module handles HED ID ranges, validation, and assignment for schema elements.
For ontology/OMN conversion functionality, see the hed-ontology repository.
"""

import pandas as pd

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema.hed_cache import get_library_data
from hed.schema.hed_schema_constants import HedKey
from hed.schema.schema_io import df_constants as constants, schema_util

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
    """Get the set of HedId's for this object type/schema name.

    Parameters:
        schema_name(str): The known schema name with an assigned id range.
        df_key(str): The dataframe section type. Must be a key in object_type_id_offset
            (STRUCT_KEY is not accepted and will raise NotImplementedError).

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


def _get_retired_ids(schema_name):
    """Get the set of retired HedId numbers for this schema name.

    Retired ids are recorded in hed-schemas library_data.json under "retired_ids", keyed by hedId
    (for example "HED_0011644"). A retired id is never assigned again, so callers that hand out new
    ids subtract this set from the free range. Existing spreadsheets may still carry a retired id for
    an element that has since been removed, so this set is not used when verifying existing ids.

    Parameters:
        schema_name(str): The known schema name with an assigned id range.

    Returns:
        set: The integer values of the retired ids. Empty if none are recorded for this schema.
    """
    library_data = get_library_data(schema_name)
    if not library_data:
        return set()
    retired_ids = set()
    for hed_id in library_data.get("retired_ids", {}):
        try:
            retired_ids.add(int(hed_id.removeprefix("HED_")))
        except (ValueError, AttributeError):
            continue
    return retired_ids


def get_all_ids(df):
    """Returns a set of all unique hedIds in the dataframe

    Parameters:
        df(pd.DataFrame): The dataframe

    Returns:
        Union[Set, None]: None if this has no HED column, otherwise all unique numbers as a set.
    """
    if constants.hed_id in df.columns:
        modified_df = df[constants.hed_id].apply(lambda x: x.removeprefix("HED_") if isinstance(x, str) else x)
        modified_df = pd.to_numeric(modified_df, errors="coerce").dropna().astype(int)
        return set(modified_df.unique())
    return None


def remove_retired_rows(dataframes, schema, schema_name=""):
    """Drop spreadsheet rows for elements that are gone from the schema and whose hedId is retired.

    A schema spreadsheet mirrors the schema, and hed-schemas library_data.json "retired_ids" is the
    permanent record of removed elements, so a row whose element no longer exists and whose hedId is
    listed there is removed rather than reported as a mismatch. A row is kept when its element is still
    in the schema (an older version being reprocessed) or when its hedId is not retired (that row is a
    genuine mismatch and is reported by :func:`update_dataframes_from_schema`).

    Parameters:
        dataframes (dict[str, pd.DataFrame]): Schema spreadsheet dataframes, modified in place.
        schema (HedSchema): The schema the spreadsheet is being brought in line with.
        schema_name (str): The registered schema name; the schema's library name when empty.

    Returns:
        list[dict]: One entry per removed row with keys ``section`` (the dataframe key), ``label``,
            ``hedId``, and the registry fields ``removed_in``, ``reason``, and ``replacement`` (empty
            strings when the registry does not record them).
    """
    if not schema_name:
        schema_name = schema.library
    library_data = get_library_data(schema_name) or {}
    retired = library_data.get("retired_ids", {})
    if not retired:
        return []

    removed = []
    for df_key, df in dataframes.items():
        section_key = constants.section_mapping_hed_id.get(df_key)
        if df_key in constants.DF_EXTRAS or not section_key or df is None:
            continue
        section = schema[section_key]
        drop_indexes = []
        for row_index, row in df.iterrows():
            df_id = row[constants.hed_id]
            if not isinstance(df_id, str) or df_id not in retired:
                continue
            label = row[constants.name]
            if section.get(_schema_label(label)):
                continue
            record = retired[df_id] or {}
            removed.append(
                {
                    "section": df_key,
                    "label": label,
                    "hedId": df_id,
                    "removed_in": record.get("removed_in") or "",
                    "reason": record.get("reason") or "",
                    "replacement": record.get("replacement") or "",
                }
            )
            drop_indexes.append(row_index)
        if drop_indexes:
            dataframes[df_key] = df.drop(index=drop_indexes).reset_index(drop=True)
    return removed


def _schema_label(label):
    """Return the spreadsheet label in the form the schema section is keyed by (``-#`` becomes ``/#``)."""
    if label.endswith("-#"):
        return label.replace("-#", "/#")
    return label


def update_dataframes_from_schema(dataframes, schema, schema_name="", assign_missing_ids=False):
    """Write out schema as a dataframe, then merge in extra columns from dataframes.

    Parameters:
        dataframes(dict): A full set of schema spreadsheet formatted dataframes
        schema(HedSchema): The schema to write into the dataframes:
        schema_name(str): The name to use to find the schema id range.
        assign_missing_ids(bool): If True, replacing any blank(new) HedIds with valid ones

    Returns:
        dict[str:pd.DataFrames]: The updated dataframes. These dataframes can potentially have extra columns.

    """
    hedid_errors = []
    if not schema_name:
        schema_name = schema.library
    # 1. Verify existing HED ids don't conflict between schema/dataframes
    for df_key, df in dataframes.items():
        if df_key in constants.DF_EXTRAS:
            continue
        section_key = constants.section_mapping_hed_id.get(df_key)
        if not section_key:
            continue
        section = schema[section_key]

        unused_tag_ids = _get_hedid_range(schema_name, df_key)
        hedid_errors += _verify_hedid_matches(section, df, unused_tag_ids)

    if hedid_errors:
        raise HedFileError(
            hedid_errors[0]["code"],
            f"{len(hedid_errors)} issues found with hedId mismatches. See the .issues "
            f"parameter on this exception for more details.",
            schema.name,
            issues=hedid_errors,
        )

    # 2. Get the new schema as DFs
    from hed.schema.schema_io.schema2df import Schema2DF  # Late import as this is recursive

    output_dfs = Schema2DF().process_schema(schema, save_merged=False)

    if assign_missing_ids:
        # 3: Add any HED ID's as needed to these generated dfs.
        if not get_library_data(schema_name):
            raise HedFileError(
                HedExceptions.SCHEMA_LIBRARY_INVALID,
                f"Cannot assign hedIds: '{schema_name or 'standard'}' has no id_range in hed-schemas "
                "library_data.json. Register the schema there (on hed-schemas main) before assigning ids.",
                schema.name,
            )
        # Retired ids are removed from the pool here, not in _get_hedid_range, so that step 1 still
        # accepts a spreadsheet that carries a retired id for an element removed in a later version.
        retired_ids = _get_retired_ids(schema_name)
        for df_key, df in output_dfs.items():
            if df_key == constants.STRUCT_KEY or df_key in constants.DF_EXTRAS:
                continue
            unused_tag_ids = _get_hedid_range(schema_name, df_key) - retired_ids

            # If no errors, assign new HED ID's
            assign_hed_ids_section(df, unused_tag_ids, schema_name=schema_name, df_key=df_key)

    # 4: Merge the dataframes
    for df_key in output_dfs.keys():
        if df_key in constants.DF_EXTRAS:
            continue
        out_df = output_dfs[df_key]
        df = dataframes[df_key]
        merge_dfs(out_df, df)

    return output_dfs


def _verify_hedid_matches(section, df, unused_tag_ids):
    """Verify ID's in both have the same label, and verify all entries in the dataframe are already in the schema

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
        label = _schema_label(row[constants.name])
        df_id = row[constants.hed_id]
        if not isinstance(df_id, str):
            df_id = ""
        entry = section.get(label)
        if not entry:
            # Neither side has a hedID, so nothing to do.
            if not df_id:
                continue
            hedid_errors += schema_util.format_error(
                row_number, row, f"'{label}' does not exist in schema file only the spreadsheet."
            )
            continue
        entry_id = entry.attributes.get(HedKey.HedID)
        if df_id:
            if not (df_id.startswith("HED_") and len(df_id) == len("HED_0000000")):
                hedid_errors += schema_util.format_error(
                    row_number, row, f"'{label}' has an improperly formatted hedID in dataframe."
                )
                continue
            id_value = df_id.removeprefix("HED_")
            try:
                id_int = int(id_value)
                if unused_tag_ids and id_int not in unused_tag_ids:
                    hedid_errors += schema_util.format_error(
                        row_number,
                        row,
                        f"'{label}' has id {id_int} which is outside "
                        + "of the valid range for this type. Valid range is: "
                        + f"{min(unused_tag_ids)} to {max(unused_tag_ids)}",
                    )
                    continue
            except ValueError:
                hedid_errors += schema_util.format_error(
                    row_number, row, f"'{label}' has a non-numeric hedID in the dataframe."
                )
                continue

        if entry_id and entry_id != df_id:
            hedid_errors += schema_util.format_error(
                row_number, row, f"'{label}' has hedID '{df_id}' in dataframe, but '{entry_id}' in schema."
            )
            continue

    return hedid_errors


def assign_hed_ids_section(df, unused_tag_ids, schema_name="", df_key=""):
    """Adds missing HedIds to dataframe.

    Parameters:
        df(pd.DataFrame): The dataframe to add id's to.
        unused_tag_ids(set of int): The possible HED id's to assign from
        schema_name(str): The schema name, for the error message when the range is exhausted.
        df_key(str): The dataframe section, for the same message.

    Raises:
        HedFileError: When the section needs more ids than the range has free.
    """
    # Remove already used ids
    unused_tag_ids -= get_all_ids(df)
    sorted_unused_ids = sorted(unused_tag_ids, reverse=True)

    # If the hedId column is float (all-NaN case), cast to object so strings can be assigned
    if pd.api.types.is_float_dtype(df[constants.hed_id]):
        df[constants.hed_id] = df[constants.hed_id].astype(object)

    for _row_number, row in df.iterrows():
        hed_id = row[constants.hed_id]
        # we already verified existing ones
        if isinstance(hed_id, str) and hed_id:
            continue
        if not sorted_unused_ids:
            raise HedFileError(
                HedExceptions.SCHEMA_LIBRARY_INVALID,
                f"Cannot assign hedIds: no free id left in the {df_key or 'section'} range of "
                f"'{schema_name or 'standard'}' (hed-schemas library_data.json).",
                schema_name,
            )
        df.at[_row_number, constants.hed_id] = f"HED_{sorted_unused_ids.pop():07d}"


def merge_dfs(dest_df, source_df):
    """Merges extra columns from source_df into dest_df, adding the extra columns from the ontology to the schema df.

    Parameters:
        dest_df (DataFrame): The dataframe to add extra columns to
        source_df (DataFrame): The dataframe to get extra columns from
    """
    # todo: vectorize this at some point
    save_df1_columns = dest_df.columns.copy()
    for _index, row in source_df.iterrows():
        # Find matching index in df1 based on 'rdfs:label'
        match_index = dest_df[dest_df["rdfs:label"] == row["rdfs:label"]].index
        if not match_index.empty:
            for col in source_df.columns:
                if col not in save_df1_columns:
                    dest_df.at[match_index[0], col] = row[col]
