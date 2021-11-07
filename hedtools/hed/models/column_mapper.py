from hed.models.column_metadata import ColumnMetadata, ColumnType
from hed.models.sidecar import Sidecar
from hed.models.hed_string import HedString
from hed.models import model_constants
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors

import copy


PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "


class ColumnMapper:
    """Handles mapping columns of hed tags from a file to a usable format.

        Private Functions and variables column and row indexing starts at 0.
        Public functions and variables indexing starts at 1(or 2 if has column names)"""

    def __init__(self, sidecars=None, tag_columns=None, column_prefix_dictionary=None,
                 attribute_columns=None, optional_tag_columns=None):
        """Constructor for ColumnMapper

        Parameters
        ----------
        sidecars : Sidecar or string or list
            A list of ColumnDefinitionGroups or filenames to gather ColumnDefinitions from.
        tag_columns: [int or str]
             A list of ints or strings containing the columns that contain the HED tags.
             If the column is otherwise unspecified, it will convert this column type to HEDTags
        column_prefix_dictionary: dict
            A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
            prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
            4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/
            prepended to them, the fourth column contains tags that need Event/Label/ prepended to them,
            and the fifth column contains tags that needs Event/Category/ prepended to them.
        attribute_columns: str or int or [str] or [int]
             A list of column names or numbers to treat as attributes.
        optional_tag_columns: [int or str]
             A list of ints or strings containing the columns that contain the HED tags.
             If the column is otherwise unspecified, it will convert this column type to HEDTags
        """
        # This points to column_type entries based on column names or indexes if columns have no column_name.
        self.column_data = {}
        # Maps column number to column_entry.  This is what's actually used by most code.
        self._final_column_map = {}

        self._column_map = None
        self._tag_columns = []
        self._optional_tag_columns = []
        self._column_prefix_dictionary = {}

        self._na_patterns = ["n/a", "nan"]
        self._finalize_mapping_issues = []
        self._has_sidecars = False
        if sidecars:
            self.add_sidecars(sidecars)
        self.add_columns(attribute_columns)

        self.set_tag_columns(tag_columns, optional_tag_columns, False)
        self.set_column_prefix_dict(column_prefix_dictionary, False)

        # finalize the column map based on initial settings with no header
        self._finalize_mapping()

    def add_sidecars(self, sidecars):
        """
        Gathers column definitions from a list of files and adds them to the column mapper.

        Parameters
        ----------
        sidecars : [str or Sidecar]
            A list of filenames or loaded files in any mix
        """
        self._has_sidecars = True
        sidecars = Sidecar.load_multiple_sidecars(sidecars)
        for sidecar in sidecars:
            for column_data in sidecar:
                self._add_column_data(column_data)

    def set_column_prefix_dict(self, column_prefix_dictionary, finalize_mapping=True):
        """Adds the given columns as hed tag columns with the required prefix if it does not already exist.

        Parameters
        ----------
        column_prefix_dictionary: dict
            A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
            prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
            4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/
            prepended to them, the fourth column contains tags that need Event/Label/ prepended to them,
            and the fifth column contains tags that needs Event/Category/ prepended to them.
        finalize_mapping : bool
            If True, will re-generate the internal mapping. If False, this function has no effect until you do finalize.
        """
        if column_prefix_dictionary:
            self._column_prefix_dictionary = self._subtract_1_from_dictionary_keys(column_prefix_dictionary)
        if finalize_mapping:
            return self._finalize_mapping()
        return []

    def set_tag_columns(self, tag_columns=None, optional_tag_columns=None, finalize_mapping=True):
        """Sets the current tag columns to the passed in values, clearing the current ones if None.

        Parameters
        ----------
        tag_columns : [str or int]
            A list of ints or strings containing the columns that contain the HED tags.
        optional_tag_columns : [str or int]
            A list of ints or strings containing the columns that contain the HED tags, but not an error if missing.
        finalize_mapping :
            If True, will re-generate the internal mapping. If False, this function has no effect until you do finalize.
        """
        self._tag_columns = []
        self._optional_tag_columns = []
        if tag_columns:
            self._tag_columns = self._subtract_1_from_list_elements(tag_columns)
        if optional_tag_columns:
            self._optional_tag_columns = self._subtract_1_from_list_elements(optional_tag_columns)
        if finalize_mapping:
            issues = self._finalize_mapping()
            return issues
        return []

    def set_column_map(self, new_column_map=None):
        """Pass in the column number to column_name mapping to finalize

        Parameters
        ----------
        new_column_map : list or dict
            If list, should be each column name with column numbers assumed to start at 1.
            If dict, should be column_number : column name.  Column number should start at 1.
        """
        if isinstance(new_column_map, dict):
            column_map = self._subtract_1_from_dictionary_keys(new_column_map)
        # List like
        else:
            column_map = {column_number: column_name for column_number, column_name in enumerate(new_column_map)}
        self._column_map = column_map
        return self._finalize_mapping()

    def add_columns(self, column_names_or_numbers, column_type=ColumnType.Attribute):
        """
        Add a list of blank columns of the given type.

        Parameters
        ----------
        column_names_or_numbers : [int or str]
            A list of column names or numbers to add as the specified type.
        column_type : ColumnType, default Attribute
            The type of this column.  Generally will be Attribute
        """
        if column_names_or_numbers:
            if not isinstance(column_names_or_numbers, list):
                column_names_or_numbers = [column_names_or_numbers]
            for column_name in column_names_or_numbers:
                new_def = ColumnMetadata(column_type, column_name)
                self._add_column_data(new_def)

    def _expand_column(self, column_number, input_text):
        """
        Expand the given text based on the rules for expanding this column

        Parameters
        ----------
        column_number : int
            The column number this text should be treated as from
        input_text : str
            The text to expand, generally a single cell of a spreadsheet.

        Returns
        -------
        expanded_text : str or None
            The text after expansion.  Returns None if this column is undefined or the given text is null.
        attribute_name_or_error_message: False or str
            Depends on the value of first return value.
            If None, this is an error message.
            If string, this is an attribute name, that should be stored separately..
        """
        # Default 1-1 mapping if we don't have specific behavior.
        if not self._final_column_map:
            return HedString(input_text), False

        # If no entry, ignore this column.
        if column_number not in self._final_column_map:
            return None, False

        if not input_text or input_text in self._na_patterns:
            return None, False

        column_entry = self._final_column_map[column_number]
        return column_entry.expand(input_text)

    def expand_row_tags(self, row_text):
        """
        Expands all mapped columns from a given row

        Parameters
        ----------
        row_text : [str]
            The text for the given row, one entry per column number.
        Returns
        -------
        expanded_dict: {str: }
            A dictionary containing:
                "HED": The entire expanded row
                "column_to_hed_tags": Each expanded column separately as a list of strings.
                (attribute name): The attribute value from the spreadsheet column,
                                    only present when a given column is an attribute
        """
        result_dict = {}
        column_to_hed_tags_dictionary = {}
        column_issues_dict = {}
        for column_number, cell_text in enumerate(row_text):
            translated_column, attribute_name_or_error = self._expand_column(column_number, str(cell_text))
            if translated_column is None:
                if attribute_name_or_error:
                    if column_number + 1 not in column_issues_dict:
                        column_issues_dict[column_number + 1] = []
                    column_issues_dict[column_number + 1] += attribute_name_or_error
                    column_to_hed_tags_dictionary[column_number + 1] = translated_column
                continue
            if attribute_name_or_error:
                result_dict[attribute_name_or_error] = translated_column
                continue

            column_to_hed_tags_dictionary[column_number + 1] = translated_column

        result_dict[model_constants.COLUMN_TO_HED_TAGS] = column_to_hed_tags_dictionary
        if column_issues_dict:
            result_dict[model_constants.COLUMN_ISSUES] = column_issues_dict

        return result_dict

    def get_prefix_remove_func(self, column_number):
        """
        Returns a function that will remove the prefix for the given column.

        Parameters
        ----------
        column_number : int
            numbered column to use prefix check from.
        Returns
        -------
            A function taking a tag and string, returning a string.
        """
        column_number -= 1
        if column_number not in self._final_column_map:
            return None

        entry = self._final_column_map[column_number]
        if not entry.column_prefix:
            return None

        return entry.remove_prefix_if_needed

    def _add_column_data(self, new_column_entry):
        """
        Add a column definition to this column mapper.

        Note if an entry with the same name exists, the new entry will replace it.

        Parameters
        ----------
        new_column_entry : ColumnMetadata
            The column definition to add
        """
        column_name = new_column_entry.column_name
        self.column_data[column_name] = copy.deepcopy(new_column_entry)

    def _set_column_prefix(self, column_number, new_required_prefix):
        """
        Internal function to add this as a required prefix to a column

        If the column is not known to the mapper, it will be added as a HEDTags column.

        Parameters
        ----------
        column_number : int
            The column number with this prefix
        new_required_prefix : str
            The prefix to add to the column when loading from a spreadsheet.
        """
        if isinstance(column_number, str):
            raise TypeError("Must pass in a column number not column_name to _set_column_prefix")
        if column_number not in self._final_column_map:
            column_entry = ColumnMetadata(ColumnType.HEDTags)
            self._final_column_map[column_number] = column_entry
        else:
            column_entry = self._final_column_map[column_number]

        column_entry.column_prefix = new_required_prefix
        if column_entry.column_type is None or column_entry.column_type == ColumnType.Ignore:
            column_entry.column_type = ColumnType.HEDTags

    def _finalize_mapping(self):
        """
        Internal function that gathers up all the various sources of column rules and puts them
        in a list mapping from column number to definition.

        This needs to be called after all definitions and columns are added.
        """
        self._final_column_map = {}
        found_named_tag_columns = {}
        all_tag_columns = self._tag_columns + self._optional_tag_columns
        self._finalize_mapping_issues = []
        if self._column_map is not None:
            for column_number, column_name in self._column_map.items():
                if column_name in self.column_data:
                    column_entry = self.column_data[column_name]
                    column_entry.column_name = column_name
                    self._final_column_map[column_number] = column_entry
                elif column_name in all_tag_columns:
                    found_named_tag_columns[column_name] = column_number
                elif column_name.startswith(PANDAS_COLUMN_PREFIX_TO_IGNORE):
                    continue
                elif self._has_sidecars:
                    if column_number not in all_tag_columns:
                        self._finalize_mapping_issues += ErrorHandler.format_error(ValidationErrors.HED_UNKNOWN_COLUMN,
                                                                                   extra_column_name=column_name)

        # Add any numbered columns
        for column_name, column_entry in self.column_data.items():
            if isinstance(column_name, int):
                # Convert to internal numbering format
                column_number = column_name - 1
                self._final_column_map[column_number] = column_entry

        # Add any tag columns
        for column_number in all_tag_columns:
            if isinstance(column_number, int):
                if column_number not in self._final_column_map:
                    self._final_column_map[column_number] = ColumnMetadata(ColumnType.HEDTags, column_number)
            elif column_number in found_named_tag_columns:
                column_name = column_number
                column_number = found_named_tag_columns[column_name]
                self._final_column_map[column_number] = ColumnMetadata(ColumnType.HEDTags, column_number)
            elif column_number in self._tag_columns:
                self._finalize_mapping_issues += ErrorHandler.format_error(ValidationErrors.HED_MISSING_COLUMN,
                                                                           missing_column_name=column_number)

        # Add prefixes
        for column_number, prefix in self._column_prefix_dictionary.items():
            self._set_column_prefix(column_number, prefix)

        # Finally check if any numbered columns don't have an entry in final columns and issue a warning.
        return self._finalize_mapping_issues

    def get_def_dicts(self):
        """
            Return a list of all def dicts from every column description

        Returns
        -------
        def_dicts: [DefDict]
            A list of def dicts, corresponding to each column entry.
        """
        def_dicts = [entry.def_dict for entry in self.column_data.values()]
        return def_dicts

    def get_column_mapping_issues(self):
        """
            Gets all the issues with finalizing column mapping.  Primarily a missing required column.
        Returns
        -------
        col_mapping_issues: [{}]
            A list of all issues found from mapping column names to numbers.
        """
        return self._finalize_mapping_issues

    def validate_column_data(self, validators, error_handler=None, **kwargs):
        """
        Validates all column definitions that are being used and column definition hed strings

        Parameters
        ----------
        validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings in the sidecars.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        kwargs:
            See util.translate_ops or the specific validators for additional options
        Returns
        -------
        validation_issues : [{}]
            A list of syntax and semantic issues found in the definitions.
        """
        if error_handler is None:
            error_handler = ErrorHandler()
        all_validation_issues = []
        for column_data in self.column_data.values():
            all_validation_issues += column_data.validate_column(validators, also_validate=True,
                                                                 error_handler=error_handler,
                                                                 **kwargs)

        return all_validation_issues

    @staticmethod
    def _subtract_1_from_dictionary_keys(int_key_dictionary):
        """Subtracts 1 from each dictionary key.

        Parameters
        ----------
        int_key_dictionary: {}
            A dictionary with int keys.
        Returns
        -------
        adjusted_dict: {}
            A dictionary with the keys subtracted by 1.

        """
        return {key - 1: value for key, value in int_key_dictionary.items()}

    @staticmethod
    def _subtract_1_from_list_elements(int_list):
        """Subtracts 1 from each int in a list.

        Parameters
        ----------
        int_list: [int]
            A list of ints.
        Returns
        -------
        adjusted_list: [int]
            A list of containing each element subtracted by 1.

        """
        return [x if isinstance(x, str) else x - 1 for x in int_list]
