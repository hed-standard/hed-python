"""
This module is used to create a HedSchema object from a set of .tsv files.
"""
import io
import os

from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.errors.exceptions import HedFileError, HedExceptions
from .base2schema import SchemaLoader
import pandas as pd
from hed.schema.schema_io.schema2df import Schema2DF
from hed.schema.hed_schema_df_constants import *
import copy
from hed.errors import error_reporter


class SchemaLoaderDF(SchemaLoader):
    """ Load dataframe schemas from filenames

        Expected usage is SchemaLoaderDF.load(filenames)

        Note: due to supporting multiple files, this one differs from the other schema loaders
    """

    def __init__(self, filenames, schema_as_strings, name=""):
        from hed.schema.hed_schema_io import load_schema_version

        self.filenames = self.convert_filenames_to_dict(filenames)
        self.schema_as_strings = schema_as_strings
        if self.filenames:
            reported_filename = self.filenames.get(STRUCT_KEY)
        else:
            reported_filename = "from_strings"
        super().__init__(reported_filename, None, None, None, name)
        # Grab the header attributes we already loaded
        save_header = self._schema.header_attributes
        # BFK - just load 8.3.0 for the non tag sections
        version = save_header.get("withStandard", "8.3.0")
        schema = copy.deepcopy(load_schema_version(version))

        self._schema = schema
        self._schema.header_attributes = save_header

        # Blow away tags section if needed.  This will eventually be removed once we load all from spreadsheets.
        if self._schema.merged or not self._schema.with_standard:
            # todo: reset this once we load more from the spreadsheets
            clear_sections(schema, [HedSectionKey.Tags])
            # clear_sections(schema, [HedSectionKey.Tags, HedSectionKey.UnitClasses, HedSectionKey.Units,
            #                         HedSectionKey.ValueClasses, HedSectionKey.UnitModifiers, HedSectionKey.Properties,
            #                         HedSectionKey.Attributes])

        self._schema.source_format = "spreadsheet"

    @classmethod
    def load_spreadsheet(cls, filenames=None, schema_as_strings=None, name=""):
        """ Loads and returns the schema, including partnered schema if applicable.

        Parameters:
            filenames(str or None or dict of str): A valid set of schema spreadsheet filenames
                                                   If a single filename string, assumes the standard filename suffixes.
            schema_as_strings(None or dict of str): A valid set of schema spreadsheet files(tsv as strings)
            name (str): what to identify this schema as
        Returns:
            schema(HedSchema): The new schema
        """
        loader = cls(filenames, schema_as_strings=schema_as_strings, name=name)
        return loader._load()

    @staticmethod
    def convert_filenames_to_dict(filenames):
        """Infers filename meaning based on suffix, e.g. _Tag for the tags sheet

        Parameters:
            filenames(None or list or dict): The list to convert to a dict

        Returns:
            filename_dict(str: str): The required suffix to filename mapping"""
        needed_suffixes = {TAG_KEY, STRUCT_KEY}
        result_filenames = {}
        if isinstance(filenames, str):
            base, base_ext = os.path.splitext(filenames)
            for suffix in needed_suffixes:
                filename = f"{base}_{suffix}.tsv"
                result_filenames[suffix] = filename
            filenames = result_filenames
        elif isinstance(filenames, list):
            for filename in filenames:
                remainder, suffix = filename.replace("_", "-").rsplit("-")
                for needed_suffix in needed_suffixes:
                    if needed_suffix in suffix:
                        result_filenames[needed_suffix] = filename
            filenames = result_filenames

        return filenames

    def _open_file(self):
        if self.filenames:
            dataframes = load_dataframes(self.filenames)
        else:
            dataframes = load_dataframes_from_strings(self.schema_as_strings)

        return dataframes

    def _get_header_attributes(self, file_data):
        header_attributes = {}
        for row_number, row in file_data[STRUCT_KEY].iterrows():
            cls = row["omn:SubClassOf"]
            attributes = row["Attributes"]
            if cls == "HedHeader" and attributes:
                header_attributes, _ = self._parse_attributes_line(attributes)
                continue

        return header_attributes

    def _parse_data(self):
        self._schema.prologue, self._schema.epilogue = self._get_prologue_epilogue(self.input_data)
        self._read_schema(self.input_data)
        if self.fatal_errors:
            self.fatal_errors = error_reporter.sort_issues(self.fatal_errors)
            raise HedFileError(self.fatal_errors[0]['code'],
                               f"{len(self.fatal_errors)} issues found when parsing schema.  See the .issues "
                               f"parameter on this exception for more details.", self.name,
                               issues=self.fatal_errors)

    def _get_prologue_epilogue(self, file_data):
        prologue, epilogue = "", ""
        for row_number, row in file_data[STRUCT_KEY].iterrows():
            cls = row["omn:SubClassOf"]
            description = row["dc:description"]
            if cls == "HedPrologue" and description:
                prologue = description.replace("\\n", "\n")
                continue
            elif cls == "HedEpilogue" and description:
                epilogue = description.replace("\\n", "\n")

        return prologue, epilogue

    def _read_schema(self, dataframe):
        """Add the main schema section

        Parameters:
            dataframe (pd.DataFrame): The dataframe for the main tags section
        """
        # note: this assumes loading is in order line by line.
        # If tags are NOT sorted this won't work.(same as mediawiki)
        known_tag_levels = {"HedTag": -1}
        parent_tags = []
        level_adj = 0
        self._schema._initialize_attributes(HedSectionKey.Tags)
        for row_number, row in dataframe[TAG_KEY].iterrows():
            # skip blank rows, though there shouldn't be any
            if not any(row):
                continue
            parent_tag = row["omn:SubClassOf"]
            # Return -1 by default for top level rooted tag support(they might not be in the dict)
            raw_level = known_tag_levels.get(parent_tag, -1) + 1
            if raw_level == 0:
                parent_tags = []
                level_adj = 0
            else:
                level = raw_level + level_adj
                if level < len(parent_tags):
                    parent_tags = parent_tags[:level]
                elif level > len(parent_tags):
                    self._add_fatal_error(row_number, row,
                                          "Invalid level reported from Level column",
                                          HedExceptions.GENERIC_ERROR)
                    continue
            # Create the entry
            tag_entry = self._add_tag_line(parent_tags, row_number, row)

            if not tag_entry:
                # This will have already raised an error
                continue

            known_tag_levels[tag_entry.short_tag_name] = raw_level

            try:
                rooted_entry = self.find_rooted_entry(tag_entry, self._schema, self._loading_merged)
                if rooted_entry:
                    parent_tags = rooted_entry.long_tag_name.split("/")
                    level_adj = len(parent_tags)
                    # Create the entry again for rooted tags, to get the full name.
                    tag_entry = self._add_tag_line(parent_tags, row_number, row)
            except HedFileError as e:
                self._add_fatal_error(row_number, row, e.message, e.code)
                continue

            tag_entry = self._add_to_dict(row_number, row, tag_entry, HedSectionKey.Tags)

            parent_tags.append(tag_entry.short_tag_name)

    def _add_tag_line(self, parent_tags, line_number, row):
        """ Add a tag to the dictionaries.

        Parameters:
            parent_tags (list): A list of parent tags in order.
            line_number (int): The line number to report errors as
            row (pd.Series): the pandas row
        Returns:
            HedSchemaEntry: The entry for the added tag.

        Notes:
            Includes attributes and description.
        """
        tag_name = self._get_tag_name_from_row(row)
        if tag_name:
            if parent_tags:
                long_tag_name = "/".join(parent_tags) + "/" + tag_name
            else:
                long_tag_name = tag_name
            long_tag_name = long_tag_name
            return self._create_entry(line_number, row, HedSectionKey.Tags, long_tag_name)

        self._add_fatal_error(line_number, row, f"No tag name found in row.",
                              error_code=HedExceptions.GENERIC_ERROR)

    def _get_tag_name_from_row(self, row):
        try:
            base_tag_name = row["rdfs:label"]
            if base_tag_name.endswith("-#"):
                return "#"
            return base_tag_name
        except KeyError:
            return None

    def _get_hedid_from_row(self, row):
        try:
            return row[hed_id_column]
        except KeyError:
            return None

    def _create_entry(self, line_number, row, key_class, full_tag_name=None):
        element_name = self._get_tag_name_from_row(row)
        if full_tag_name:
            element_name = full_tag_name

        hedID = self._get_hedid_from_row(row)

        node_attributes = self._get_tag_attributes(line_number, row)

        if hedID:
            node_attributes[HedKey.HedID] = hedID

        description = row["dc:description"]
        tag_entry = self._schema._create_tag_entry(element_name, key_class)

        if description:
            tag_entry.description = description.strip()

        for attribute_name, attribute_value in node_attributes.items():
            tag_entry._set_attribute_value(attribute_name, attribute_value)

        return tag_entry

    def _get_tag_attributes(self, row_number, row):
        """ Get the tag attributes from a line.

        Parameters:
            row_number (int): The line number to report errors as.
            row (pd.Series): A tag line.
        Returns:
            dict: Dictionary of attributes.
        """
        attr_string = row["Attributes"]
        return self._parse_attribute_string(row_number, attr_string)

    def _add_to_dict(self, line_number, line, entry, key_class):
        if entry.has_attribute(HedKey.InLibrary) and not self._loading_merged and not self.appending_to_schema:
            self._add_fatal_error(line_number, line,
                                  "Library tag in unmerged schema has InLibrary attribute",
                                  HedExceptions.IN_LIBRARY_IN_UNMERGED)

        return self._add_to_dict_base(entry, key_class)




def load_dataframes(filenames):
    dict_filenames = SchemaLoaderDF.convert_filenames_to_dict(filenames)
    return {key: pd.read_csv(filename, sep="\t", dtype=str, na_filter=False) for (key, filename) in dict_filenames.items()}


def load_dataframes_from_strings(data_contents):
    # Assume data_contents is a list of tuples (key, tsv_string)
    return {key: pd.read_csv(io.StringIO(tsv_string), sep="\t", dtype=str, na_filter=False)
            for key, tsv_string in data_contents.items()}


def get_all_ids(df):
    if hed_id_column in df.columns:
        modified_df = df[hed_id_column].str.replace("HED_", "")
        modified_df = pd.to_numeric(modified_df, errors="coerce").dropna().astype(int)
        return set(modified_df.unique())
    return None


tag_index_ranges = {
    "": (10000, 40000),
    "score": (40000, 60000),
    "lang": (60000, 80000)
}

def _get_hedid_range(schema_name, section_key):
    if section_key != HedSectionKey.Tags:
        raise NotImplementedError("Cannot assign hedID's to non tag sections yet")

    starting_id, ending_id = tag_index_ranges[schema_name]

    tag_section_adj = 2000
    initial_tag_adj = 1
    starting_id += tag_section_adj + initial_tag_adj
    return set(range(starting_id, ending_id))


def update_dataframes_from_schema(dataframes, schema, schema_name=""):
    # We're going to potentially alter the schema, so make a copy
    schema = copy.deepcopy(schema)

    section_mapping = {
        STRUCT_KEY: None,
        TAG_KEY: HedSectionKey.Tags
    }

    # todo: this needs to handle other sections eventually
    for key, df in dataframes.items():
        section_key = section_mapping.get(key)
        if not section_key:
            continue
        section = schema[section_key]

        hedid_errors = _verify_hedid_matches(section, df)
        if hedid_errors:
            raise HedFileError(hedid_errors[0]['code'],
                               f"{len(hedid_errors)} issues found with hedId mismatches.  See the .issues "
                               f"parameter on this exception for more details.", schema.name,
                               issues=hedid_errors)
        unused_tag_ids = _get_hedid_range(schema_name, section_key)

        # If no errors, assign new hed ID's
        assign_hed_ids_section(section, unused_tag_ids, df)

    output_dfs = Schema2DF.process_schema(schema, save_merged=False)

    merge_dfs(output_dfs[TAG_KEY], dataframes[TAG_KEY])
    # Struct is special, just directly merge for now.
    output_dfs[STRUCT_KEY] = pd.concat([dataframes[STRUCT_KEY], output_dfs[STRUCT_KEY]]).drop_duplicates('rdfs:label', keep='last').reset_index(drop=True)

    return output_dfs


def _verify_hedid_matches(section, df):
    """ Verify ID's in both have the same label, and verify all entries in the dataframe are already in the schema

    Parameters:
        section(HedSchemaSection): The loaded schema section to compare ID's with
        df(pd.DataFrame): The loaded spreadsheet dataframe to compare with

    Returns:
        error_list(list of str): A list of errors found matching id's
    """
    hedid_errors = []
    for row_number, row in df.iterrows():
        if not any(row):
            continue
        label = row["rdfs:label"]
        if label.endswith("-#"):
            label = label.replace("-#", "/#")
        df_id = row[hed_id_column]
        entry = section.get(label)
        if not entry:
            hedid_errors += SchemaLoaderDF._format_error(row_number, row,
                                          f"'{label}' does not exist in the schema file provided, only the spreadsheet.")
            continue
        entry_id = entry.attributes.get(HedKey.HedID)
        if entry_id and entry_id != df_id:
            hedid_errors += SchemaLoaderDF._format_error(row_number, row,
                                          f"'{label}' has hedID '{df_id}' in dataframe, but '{entry_id}' in schema.")
            continue

    return hedid_errors


def assign_hed_ids_schema(schema):
    """Note: only assigns values to TAGS section for now."""
    for section_key in HedSectionKey:
        section = schema[section_key]
        # Still need to add hed ranges for non tag sections
        if section_key != HedSectionKey.Tags:
            continue
        unused_tag_ids = _get_hedid_range(schema.library, section_key)
        assign_hed_ids_section(section, unused_tag_ids, None)


def assign_hed_ids_section(section, unused_tag_ids, df=None):
    spreadsheet_label_to_hedid = {}
    if df is not None:
        # Remove hedIds already used in the dataframe
        unused_tag_ids -= get_all_ids(df)
        spreadsheet_label_to_hedid = df.set_index('rdfs:label')['hedId'].to_dict()

    # Remove hedId's already used in the schema
    section_used_ids = set(
        int(entry.attributes.get(HedKey.HedID, "0").replace("HED_", "")) for entry in section.all_entries)
    unused_tag_ids -= section_used_ids

    sorted_unused_ids = sorted(unused_tag_ids, reverse=True)

    # Next assign hed ID to this if needed
    for entry in section.all_entries:
        if section.section_key == HedSectionKey.Tags:
            name = entry.short_tag_name
        else:
            name = entry.name
        current_tag_id = spreadsheet_label_to_hedid.get(name)
        if not current_tag_id:
            current_tag_id = f"HED_{sorted_unused_ids.pop():07d}"
        entry._set_attribute_value(HedKey.HedID, current_tag_id)


def merge_dfs(df1, df2):
    """Merges df2 into df1, adding the extra columns from the ontology to the schema df."""
    # todo: vectorize this at some point
    save_df1_columns = df1.columns.copy()
    for index, row in df2.iterrows():
        # Find matching index in df1 based on 'rdfs:label'
        match_index = df1[df1['rdfs:label'] == row['rdfs:label']].index
        if not match_index.empty:
            for col in df2.columns:
                if col not in save_df1_columns:
                    df1.at[match_index[0], col] = row[col]

    return df1


def clear_sections(schema, sections_to_clear):
    # Temporary function until these spreadsheet writers are finished
    # Also clear prologue and epilogue
    schema.prologue = ""
    schema.epilogue = ""
    empty_sections = schema._create_empty_sections()
    for section_key in sections_to_clear:
        schema._sections[section_key] = empty_sections[section_key]
