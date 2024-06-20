"""
This module is used to create a HedSchema object from a set of .tsv files.
"""
import io
import os

from hed.schema.schema_io import ontology_util
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.schema_io.text2schema import SchemaLoaderText
import pandas as pd
import hed.schema.hed_schema_df_constants as constants
from hed.errors import error_reporter
from hed.schema.schema_io import text_util


class SchemaLoaderDF(SchemaLoaderText):
    """ Load dataframe schemas from filenames

        Expected usage is SchemaLoaderDF.load(filenames)

        Note: due to supporting multiple files, this one differs from the other schema loaders
    """

    def __init__(self, filenames, schema_as_strings_or_df, name=""):
        self.filenames = self.convert_filenames_to_dict(filenames)
        self.schema_as_strings_or_df = schema_as_strings_or_df
        if self.filenames:
            reported_filename = self.filenames.get(constants.STRUCT_KEY)
        else:
            reported_filename = "from_strings"
        super().__init__(reported_filename, None, None, None, name)
        self._schema.source_format = "spreadsheet"

    @classmethod
    def load_spreadsheet(cls, filenames=None, schema_as_strings_or_df=None, name=""):
        """ Loads and returns the schema, including partnered schema if applicable.

        Parameters:
            filenames(str or None or dict of str): A valid set of schema spreadsheet filenames
                                                   If a single filename string, assumes the standard filename suffixes.
            schema_as_strings_or_df(None or dict of str): A valid set of schema spreadsheet files(tsv as strings)
            name (str): what to identify this schema as
        Returns:
            schema(HedSchema): The new schema
        """
        loader = cls(filenames, schema_as_strings_or_df=schema_as_strings_or_df, name=name)
        return loader._load()

    @staticmethod
    def convert_filenames_to_dict(filenames):
        """Infers filename meaning based on suffix, e.g. _Tag for the tags sheet

        Parameters:
            filenames(str or None or list or dict): The list to convert to a dict
                If a string with a .tsv suffix: Save to that location, adding the suffix to each .tsv file
                If a string with no .tsv suffix: Save to that folder, with the contents being the separate .tsv files.
        Returns:
            filename_dict(str: str): The required suffix to filename mapping"""
        result_filenames = {}
        if isinstance(filenames, str):
            if filenames.endswith(".tsv"):
                base, base_ext = os.path.splitext(filenames)
            else:
                # Load as foldername/foldername_suffix.tsv
                base_dir = filenames
                base_filename = os.path.split(base_dir)[1]
                base = os.path.join(base_dir, base_filename)
            for suffix in constants.DF_SUFFIXES:
                filename = f"{base}_{suffix}.tsv"
                result_filenames[suffix] = filename
            filenames = result_filenames
        elif isinstance(filenames, list):
            for filename in filenames:
                remainder, suffix = filename.replace("_", "-").rsplit("-")
                for needed_suffix in constants.DF_SUFFIXES:
                    if needed_suffix in suffix:
                        result_filenames[needed_suffix] = filename
            filenames = result_filenames

        return filenames

    def _open_file(self):
        if self.filenames:
            dataframes = load_dataframes(self.filenames)
        else:
            dataframes = load_dataframes_from_strings(self.schema_as_strings_or_df)

        return dataframes

    def _get_header_attributes(self, file_data):
        header_attributes = {}
        for row_number, row in file_data[constants.STRUCT_KEY].iterrows():
            cls = row[constants.subclass_of]
            attributes = row[constants.attributes]
            if cls == "HedHeader" and attributes:
                header_attributes, _ = text_util._parse_header_attributes_line(attributes)
                continue

        return header_attributes

    def _parse_data(self):
        self._schema.prologue, self._schema.epilogue = self._get_prologue_epilogue(self.input_data)
        self._schema._initialize_attributes(HedSectionKey.Properties)
        self._read_attribute_section(self.input_data[constants.ATTRIBUTE_PROPERTY_KEY],
                                     section_key=HedSectionKey.Properties)
        self._read_attributes()
        self._read_section(self.input_data[constants.UNIT_MODIFIER_KEY], HedSectionKey.UnitModifiers)
        self._read_section(self.input_data[constants.VALUE_CLASS_KEY], HedSectionKey.ValueClasses)
        self._read_section(self.input_data[constants.UNIT_CLASS_KEY], HedSectionKey.UnitClasses)
        self._read_units(self.input_data[constants.UNIT_KEY])
        # This one is a special case
        self._read_schema(self.input_data)
        if self.fatal_errors:
            self.fatal_errors = error_reporter.sort_issues(self.fatal_errors)
            raise HedFileError(self.fatal_errors[0]['code'],
                               f"{len(self.fatal_errors)} issues found when parsing schema.  See the .issues "
                               f"parameter on this exception for more details.", self.name,
                               issues=self.fatal_errors)

    def _get_prologue_epilogue(self, file_data):
        prologue, epilogue = "", ""
        for row_number, row in file_data[constants.STRUCT_KEY].iterrows():
            cls = row[constants.subclass_of]
            description = row[constants.description]
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
        self._schema._initialize_attributes(HedSectionKey.Tags)
        known_parent_tags =  {"HedTag": []}
        level_adj = 0
        for row_number, row in dataframe[constants.TAG_KEY].iterrows():
            # skip blank rows, though there shouldn't be any
            if not any(row):
                continue
            parent_tag = row[constants.subclass_of]
            org_parent_tags = known_parent_tags.get(parent_tag, []).copy()

            tag_entry, parent_tags, _ = self._add_tag_meta(org_parent_tags, row_number, row, level_adj)
            if tag_entry:
                known_parent_tags[tag_entry.short_tag_name] = parent_tags.copy()

    def _read_section(self, df, section_key):
        self._schema._initialize_attributes(section_key)

        for row_number, row in df.iterrows():
            new_entry = self._create_entry(row_number, row, section_key)
            self._add_to_dict(row_number, row, new_entry, section_key)

    def _read_units(self, df):
        self._schema._initialize_attributes(HedSectionKey.Units)

        for row_number, row in df.iterrows():
            new_entry = self._create_entry(row_number, row, HedSectionKey.Units)
            unit_class_name = row[constants.has_unit_class]
            unit_class_entry = self._schema.get_tag_entry(unit_class_name, HedSectionKey.UnitClasses)
            unit_class_entry.add_unit(new_entry)
            self._add_to_dict(row_number, row, new_entry, HedSectionKey.Units)

    def _read_attributes(self):
        self._schema._initialize_attributes(HedSectionKey.Attributes)
        self._read_attribute_section(self.input_data[constants.ANNOTATION_KEY], True)
        self._read_attribute_section(self.input_data[constants.OBJECT_KEY])
        self._read_attribute_section(self.input_data[constants.DATA_KEY])

    def _read_attribute_section(self, df, annotation_property=False, section_key=HedSectionKey.Attributes):
        # todo: this needs to ALSO check range/domain(and verify they match)
        for row_number, row in df.iterrows():
            new_entry = self._create_entry(row_number, row, section_key)
            if annotation_property:
                new_entry._set_attribute_value(HedKey.AnnotationProperty, True)
            self._add_to_dict(row_number, row, new_entry, section_key)

    def _get_tag_name(self, row):
        base_tag_name = row[constants.name]
        if base_tag_name.endswith("-#"):
            return "#", 0
        return base_tag_name, 0

    def _create_entry(self, row_number, row, key_class, full_tag_name=None):
        element_name, _ = self._get_tag_name(row)
        if full_tag_name:
            element_name = full_tag_name

        node_attributes = self._get_tag_attributes(row_number, row)

        hed_id = row[constants.hed_id]
        if hed_id:
            node_attributes[HedKey.HedID] = hed_id

        description = row[constants.description]
        tag_entry = self._schema._create_tag_entry(element_name, key_class)

        if description:
            tag_entry.description = description.strip()

        for attribute_name, attribute_value in node_attributes.items():
            tag_entry._set_attribute_value(attribute_name, attribute_value)

        return tag_entry

    def _get_tag_attributes(self, row_number, row):
        """ Get the tag attributes from a row.

        Parameters:
            row_number (int): The row number to report errors as.
            row (pd.Series): A tag row.
        Returns:
            dict: Dictionary of attributes.
        """
        try:
            return ontology_util.get_attributes_from_row(row)
        except ValueError as e:
            self._add_fatal_error(row_number, str(row), str(e))


def load_dataframes(filenames):
    dict_filenames = SchemaLoaderDF.convert_filenames_to_dict(filenames)
    dataframes = ontology_util.create_empty_dataframes()
    for key, filename in dict_filenames.items():
        try:
            dataframes[key] = pd.read_csv(filename, sep="\t", dtype=str, na_filter=False)
        except OSError:
            # todo: consider if we want to report this error(we probably do)
            pass  # We will use a blank one for this
    return dataframes


def load_dataframes_from_strings(schema_data):
    """ Load the given strings/dataframes as dataframes.

    Parameters:
        schema_data(dict): The dict of files(strings or pd.DataFrames) key being constants like TAG_KEY

    Returns:
        schema_data(dict): A dict with the same keys as schema_data, but values are dataframes if not before
    """
    return {key: value if isinstance(value, pd.DataFrame) else pd.read_csv(io.StringIO(value), sep="\t",
                                                                           dtype=str, na_filter=False)
            for key, value in schema_data.items()}
