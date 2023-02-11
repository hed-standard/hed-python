from hed.models.column_metadata import ColumnMetadata, ColumnType
from hed.models.sidecar import Sidecar
from hed.models.hed_string import HedString
from hed.models import model_constants
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors

import copy


PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "


class ColumnMapper:
    """ Mapping of a base input file columns into HED tags.

    Notes:
        - Functions and type_variables column and row indexing starts at 0.
    """
    def __init__(self, sidecar=None, tag_columns=None, column_prefix_dictionary=None,
                 optional_tag_columns=None, requested_columns=None, warn_on_missing_column=False):
        """ Constructor for ColumnMapper.

        Parameters:
            sidecar (Sidecar): A sidecar to gather column data from.
            tag_columns: (list):  A list of ints or strings containing the columns that contain the HED tags.
                Sidecar column definitions will take precedent if there is a conflict with tag_columns.
            column_prefix_dictionary (dict): Dictionary with keys that are column numbers and values are HED tag
                prefixes to prepend to the tags in that column before processing.
            optional_tag_columns (list): A list of ints or strings containing the columns that contain
                the HED tags. If the column is otherwise unspecified, convert this column type to HEDTags.
            requested_columns (list or None): A list of columns you wish to retrieve.
                If None, retrieve all columns.
            warn_on_missing_column (bool): If True, issue mapping warnings on column names that are missing from
                                            the sidecar.

        Notes:
            - All column numbers are 0 based.

        Examples:
            column_prefix_dictionary = {3: 'Description/', 4: 'Label/'}

            The third column contains tags that need Description/ tag prepended, while the fourth column
            contains tag that needs Label/ prepended.
        """
        # This points to column_type entries based on column names or indexes if columns have no column_name.
        self.column_data = {}
        # Maps column number to column_entry.  This is what's actually used by most code.
        self._final_column_map = {}
        self._no_mapping_info = True

        self._column_map = {}
        self._reverse_column_map = {}
        self._requested_columns = []
        self._warn_on_missing_column = warn_on_missing_column
        self._tag_columns = []
        self._optional_tag_columns = []
        self._column_prefix_dictionary = {}

        self._na_patterns = ["n/a", "nan"]
        self._finalize_mapping_issues = []
        self._sidecar = None
        self._set_sidecar(sidecar)

        self.set_requested_columns(requested_columns, False)
        self.set_tag_columns(tag_columns, optional_tag_columns, False)
        self.set_column_prefix_dict(column_prefix_dictionary, False)

        # finalize the column map based on initial settings with no header
        self._finalize_mapping()

    @staticmethod
    def validate_column_map(column_map, allow_blank_names):
        """ Validate there are no issues with column names.

        Parameters:
            column_map(iterable): A list of column names
            allow_blank_names(bool): Only find issues if this is true

        Returns:
            issues(list): A list of dicts, one per issue.
        """
        # We don't have any checks right now if blank/duplicate is allowed
        if allow_blank_names:
            return []
        issues = []
        used_names = set()
        for column_number, name in enumerate(column_map):
            if name is None or name.startswith(PANDAS_COLUMN_PREFIX_TO_IGNORE):
                issues += ErrorHandler.format_error(ValidationErrors.HED_BLANK_COLUMN, column_number)
                continue
            if name in used_names:
                # todo: Add this check once it's more fleshed out
                # issues += ErrorHandler.format_error(ValidationErrors.HED_DUPLICATE_COLUMN, name)
                continue
            used_names.add(name)

        return issues

    def _set_sidecar(self, sidecar):
        """ Set the sidecar this column mapper uses

        Parameters:
            sidecar (Sidecar or None): the sidecar to use

        Returns:

        """
        if self._sidecar:
            raise ValueError("Trying to set a second sidecar on a column mapper.")
        if not sidecar:
            return None
        for column_data in sidecar.column_data:
            self._add_column_data(column_data)

        self._sidecar = sidecar

    def get_tag_columns(self):
        """ Returns the column numbers that are mapped to be HedTags

            Note: This is NOT the tag_columns or optional_tag_columns parameter, though they set it.

        Returns:
            column_numbers(list): A list of column numbers that are ColumnType.HedTags
        """
        return [number for number, column_entry in self._final_column_map.items()
                if column_entry.column_type == ColumnType.HEDTags]

    def set_column_prefix_dict(self, column_prefix_dictionary, finalize_mapping=True):
        """ Replace the column prefix dictionary

        Parameters:
            column_prefix_dictionary (dict):  Dictionary with keys that are column numbers and values are HED tag
                prefixes to prepend to the tags in that column before processing.
            finalize_mapping (bool): Re-generate the internal mapping if True, otherwise no effect until finalize.

        Returns:
            list:  List of issues that occurred during this process. Each issue is a dictionary.

        """
        if column_prefix_dictionary:
            self._column_prefix_dictionary = column_prefix_dictionary
        if finalize_mapping:
            return self._finalize_mapping()
        return []

    def set_tag_columns(self, tag_columns=None, optional_tag_columns=None, finalize_mapping=True):
        """ Set tag columns and optional tag columns

        Parameters:
            tag_columns (list): A list of ints or strings containing the columns that contain the HED tags.
                                If None, clears existing tag_columns
            optional_tag_columns (list): A list of ints or strings containing the columns that contain the HED tags,
                                         but not an error if missing.
                                         If None, clears existing tag_columns
            finalize_mapping (bool): Re-generate the internal mapping if True, otherwise no effect until finalize.

        Returns:
            list: List of issues that occurred during this process. Each issue is a dictionary.

        """
        if tag_columns is None:
            tag_columns = []
        if optional_tag_columns is None:
            optional_tag_columns = []
        self._tag_columns = tag_columns
        self._optional_tag_columns = optional_tag_columns
        if finalize_mapping:
            issues = self._finalize_mapping()
            return issues
        return []

    def set_requested_columns(self, requested_columns, finalize_mapping=True):
        """ Set to return only the columns listed in requested_columns

        Parameters:
            requested_columns(list or None): If this is not None, return ONLY these columns.  Names or numbers allowed.
            finalize_mapping(bool): Finalize the mapping right now if True

        Returns:
        issues(list): An empty list of mapping issues
        """
        self._requested_columns = requested_columns
        if finalize_mapping:
            return self._finalize_mapping()
        return []

    def set_column_map(self, new_column_map=None):
        """ Set the column number to name mapping.

        Parameters:
            new_column_map (list or dict):  Either an ordered list of the column names or column_number:column name
                dictionary. In both cases, column numbers start at 0

        Returns:
            list: List of issues. Each issue is a dictionary.

        """
        if new_column_map is None:
            new_column_map = {}
        if isinstance(new_column_map, dict):
            column_map = new_column_map
        # List like
        else:
            column_map = {column_number: column_name for column_number, column_name in enumerate(new_column_map)}
        self._column_map = column_map
        self._reverse_column_map = {column_name: column_number for column_number, column_name in column_map.items()}
        return self._finalize_mapping()

    def add_columns(self, column_names_or_numbers, column_type=ColumnType.HEDTags):
        """ Add blank columns in the given column category.

        Parameters:
            column_names_or_numbers (list): A list of column names or numbers to add as the specified type.
            column_type (ColumnType property): The category of column these should be.

        """
        if column_names_or_numbers:
            if not isinstance(column_names_or_numbers, list):
                column_names_or_numbers = [column_names_or_numbers]
            for column_name in column_names_or_numbers:
                new_def = ColumnMetadata(column_type, column_name)
                self._add_column_data(new_def)

    def _expand_column(self, column_number, input_text):
        """ Expand the specified text based on the rules for expanding the specified column.

        Parameters:
            column_number (int): The column number this text should be treated as from.
            input_text (str): The text to expand, generally from a single cell of a spreadsheet.

        Returns:
            str or None: The text after expansion or None if this column is undefined or the given text is null.
            False or str: Depends on the value of first return value. If None, this is an error message.
                If string, this is an attribute name that should be stored separately.

        """

        # Default 1-1 mapping if we don't have specific behavior.
        if self._no_mapping_info:
            return HedString(input_text), False

        # If no entry, ignore this column.
        if column_number not in self._final_column_map:
            return None, False

        if not input_text or input_text in self._na_patterns:
            return None, False

        column_entry = self._final_column_map[column_number]
        return column_entry.expand(input_text)

    def expand_row_tags(self, row_text):
        """ Expand all mapped columns for row.

        Parameters:
            row_text (list): The text for the given row, one list entry per column number.

        Returns:
            dict: A dictionary containing the keys COLUMN_TO_HED_TAGS, COLUMN_ISSUES.

        Notes:
            - The "column_to_hed_tags" is each expanded column given separately as a list of HedStrings.
            - Attributes are any column identified as an attribute.
              They will appear in the return value as {attribute_name: value_of_column}

        """
        result_dict = {}
        column_to_hed_tags_dictionary = {}
        column_issues_dict = {}
        for column_number, cell_text in enumerate(row_text):
            translated_column, translation_errors = self._expand_column(column_number, str(cell_text))
            if translated_column is None:
                if translation_errors:
                    if column_number not in column_issues_dict:
                        column_issues_dict[column_number] = []
                    column_issues_dict[column_number] += translation_errors
                    column_to_hed_tags_dictionary[column_number] = translated_column
                continue

            column_to_hed_tags_dictionary[column_number] = translated_column

        result_dict[model_constants.COLUMN_TO_HED_TAGS] = column_to_hed_tags_dictionary
        if column_issues_dict:
            result_dict[model_constants.COLUMN_ISSUES] = column_issues_dict

        return result_dict

    def get_prefix_remove_func(self, column_number):
        """ Return a function to removes name prefixes for column

        Parameters:
            column_number (int): Column number to look up in the prefix dictionary.

        Returns:
            func: A function taking a tag and string, returning a string.

        """
        if column_number not in self._final_column_map:
            return None

        entry = self._final_column_map[column_number]
        if not entry.column_prefix:
            return None

        return entry.remove_prefix

    def _add_column_data(self, new_column_entry):
        """ Add the metadata of a column to this column mapper.

        Parameters:
            new_column_entry (ColumnMetadata): The column definition to add.

        Notes:
            If an entry with the same name exists, the new entry will replace it.

        """
        column_name = new_column_entry.column_name
        self.column_data[column_name] = copy.deepcopy(new_column_entry)

    @staticmethod
    def _set_column_prefix(final_map, column_number, new_required_prefix):
        """ Internal function to add this as a required name_prefix to a column

        Parameters:
            final_map (dict): {column_number:prefix} Dict of column numbers with prefixes
            column_number (int): The column number with this name_prefix.
            new_required_prefix (str): The name_prefix to add to the column when loading from a spreadsheet.

        Raises:
            TypeError if column number is passed as a str rather an int.

        Notes:
            If the column is not known to the mapper, it will be added as a HEDTags column.

        """
        if isinstance(column_number, str):
            raise TypeError("Must pass in a column number not column_name to _set_column_prefix")
        if column_number not in final_map:
            column_entry = ColumnMetadata(ColumnType.HEDTags)
            final_map[column_number] = column_entry
        else:
            column_entry = final_map[column_number]

        column_entry.column_prefix = new_required_prefix
        if column_entry.column_type is None or column_entry.column_type == ColumnType.Ignore:
            column_entry.column_type = ColumnType.HEDTags

    @staticmethod
    def _get_basic_final_map(column_map, column_data):
        basic_final_map = {}
        unhandled_names = {}
        if column_map:
            for column_number, column_name in column_map.items():
                if column_name is None:
                    continue
                if column_name in column_data:
                    column_entry = copy.deepcopy(column_data[column_name])
                    column_entry.column_name = column_name
                    basic_final_map[column_number] = column_entry
                    continue
                elif column_name.startswith(PANDAS_COLUMN_PREFIX_TO_IGNORE):
                    continue
                unhandled_names[column_name] = column_number
        for column_number in column_data:
            if isinstance(column_number, int):
                column_entry = copy.deepcopy(column_data[column_number])
                column_entry.column_name = column_number
                basic_final_map[column_number] = column_entry

        return basic_final_map, unhandled_names

    @staticmethod
    def _convert_to_indexes(name_to_column_map, column_list):
        converted_indexes = []
        unknown_names = []
        for name in column_list:
            if isinstance(name, str):
                if name in name_to_column_map:
                    converted_indexes.append(name_to_column_map[name])
                    continue
                else:
                    unknown_names.append(name)
            else:
                # Name is in int here
                converted_indexes.append(name)
        return converted_indexes, unknown_names

    @staticmethod
    def _add_tag_columns(final_map, unhandled_names, all_tag_columns, required_tag_columns, warn_on_missing_columns):
        issues = []

        # Add numbered tag columns
        for column_name, column_number in unhandled_names.items():
            if column_number in all_tag_columns:
                final_map[column_number] = ColumnMetadata(ColumnType.HEDTags, column_name)
            else:
                if warn_on_missing_columns and column_number not in required_tag_columns:
                    issues += ErrorHandler.format_error(ValidationErrors.HED_UNKNOWN_COLUMN,
                                                        column_name=column_name)

        # Add numbered tag columns
        for column_name_or_number in all_tag_columns:
            if isinstance(column_name_or_number, int):
                if column_name_or_number not in final_map:
                    final_map[column_name_or_number] = ColumnMetadata(ColumnType.HEDTags,
                                                                      column_name_or_number)

        # Switch any tag/requested columns to be HedTags if they were being ignored
        for column_number, entry in final_map.items():
            if column_number in all_tag_columns and entry.column_type == ColumnType.Ignore:
                entry.column_type = ColumnType.HEDTags

        return issues

    @staticmethod
    def _filter_by_requested(final_map, requested_columns):
        if requested_columns is not None:
            return {key: value for key, value in final_map.items()
                    if key in requested_columns or value.column_name in requested_columns}
        return final_map

    @staticmethod
    def _convert_tag_columns(tag_columns, optional_tag_columns, requested_columns, reverse_column_map):
        all_tag_columns = tag_columns + optional_tag_columns
        required_tag_columns = tag_columns.copy()
        if requested_columns:
            all_tag_columns += requested_columns
            required_tag_columns += requested_columns

        all_tag_columns, _ = ColumnMapper._convert_to_indexes(reverse_column_map, all_tag_columns)
        required_tag_columns, missing_tag_column_names = ColumnMapper._convert_to_indexes(reverse_column_map,
                                                                                          required_tag_columns)

        issues = []
        for column_name in missing_tag_column_names:
            issues += ErrorHandler.format_error(ValidationErrors.HED_MISSING_REQUIRED_COLUMN,
                                                column_name=column_name)

        return all_tag_columns, required_tag_columns, issues

    def _finalize_mapping(self):
        # 1. All named and numbered columns are located from sidecars and put in final mapping
        # 2. Add any tag columns and note issues about missing columns
        # 3. Add any numbered columns that have required prefixes
        # 4. Filter to just requested columns, if any
        final_map, unhandled_names = self._get_basic_final_map(self._column_map, self.column_data)

        # convert all tag lists to indexes -> Issuing warnings at this time potentially for unknown ones
        all_tag_columns, required_tag_columns, issues = self._convert_tag_columns(self._tag_columns,
                                                                                  self._optional_tag_columns,
                                                                                  self._requested_columns,
                                                                                  self._reverse_column_map)

        # Notes any missing required columns
        issues += self._add_tag_columns(final_map, unhandled_names, all_tag_columns, required_tag_columns,
                                        self._warn_on_missing_column)

        # Add prefixes
        for column_number, prefix in self._column_prefix_dictionary.items():
            self._set_column_prefix(final_map, column_number, prefix)

        issues += ColumnMapper.validate_column_map(self._column_map.values(), allow_blank_names=False)

        self._final_column_map = self._filter_by_requested(final_map, self._requested_columns)

        self._no_mapping_info = not self._check_if_mapping_info()
        self._finalize_mapping_issues = issues
        return issues

    def _check_if_mapping_info(self):
        # If any of these have any data, don't do default behavior.
        return bool(self.column_data or self._final_column_map
                    or self._requested_columns is not None or self._tag_columns
                    or self._optional_tag_columns or self._column_prefix_dictionary)

    def _column_name_requested(self, column_name):
        if self._requested_columns is None:
            return True
        return column_name in self._requested_columns

    def get_def_dicts(self):
        """ Return def dicts from every column description.

        Returns:
           list:   A list of DefinitionDict objects corresponding to each column entry.

        """
        if self._sidecar:
            return self._sidecar.get_def_dicts()
        return []

    def get_column_mapping_issues(self):
        """ Get all the issues with finalizing column mapping.  Primarily a missing required column.

        Returns:
            list: A list dictionaries of all issues found from mapping column names to numbers.

        """
        return self._finalize_mapping_issues
