"""
Mapping of a base input file columns into HED tags.
"""
from hed.models.column_metadata import ColumnMetadata, ColumnType
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors
from hed.models.definition_dict import DefinitionDict

import copy
from collections import Counter

PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "
NO_WARN_COLUMNS = ['onset', 'duration']


class ColumnMapper:
    """ Mapping of a base input file columns into HED tags.

    Notes:
        - All column numbers are 0 based.
    """

    def __init__(self, sidecar=None, tag_columns=None, column_prefix_dictionary=None,
                 optional_tag_columns=None, warn_on_missing_column=False):
        """ Constructor for ColumnMapper.

        Parameters:
            sidecar (Sidecar): A sidecar to gather column data from.
            tag_columns: (list):  A list of ints or strings containing the columns that contain the HED tags.
                Sidecar column definitions will take precedent if there is a conflict with tag_columns.
            column_prefix_dictionary (dict): Dictionary with keys that are column numbers/names and values are HED tag
                prefixes to prepend to the tags in that column before processing.
            optional_tag_columns (list): A list of ints or strings containing the columns that contain
                the HED tags. If the column is otherwise unspecified, convert this column type to HEDTags.
            warn_on_missing_column (bool): If True, issue mapping warnings on column names that are missing from
                                            the sidecar.

        Notes:
            - All column numbers are 0 based.
            - The column_prefix_dictionary may be deprecated/renamed in the future.
                - These are no longer prefixes, but rather converted to value columns:
                  {"key": "Description", 1: "Label/"} will turn into value columns as
                  {"key": "Description/#", 1: "Label/#"}
                  It will be a validation issue if column 1 is called "key" in the above example.
                  This means it no longer accepts anything but the value portion only in the columns.

        """

        # Maps column number to column_entry.  This is what's actually used by most code.
        self._final_column_map = {}
        self._no_mapping_info = True
        self._column_map = {}
        self._reverse_column_map = {}
        self._warn_on_missing_column = warn_on_missing_column
        if tag_columns is None:
            tag_columns = []
        self._tag_columns = tag_columns
        if optional_tag_columns is None:
            optional_tag_columns = []
        self._optional_tag_columns = optional_tag_columns
        if column_prefix_dictionary is None:
            column_prefix_dictionary = {}
        self._column_prefix_dictionary = column_prefix_dictionary

        self._na_patterns = ["n/a", "nan"]
        self._sidecar = None
        self._set_sidecar(sidecar)

        # finalize the column map based on initial settings with no header
        self._finalize_mapping()

    @property
    def tag_columns(self):
        """ Return the known tag and optional tag columns with numbers as names when possible.

            Returns:
                tag_columns(list of str or int): A list of all tag and optional tag columns as labels.
        """
        joined_list = self._tag_columns + self._optional_tag_columns
        return list(set(self._convert_to_names(self._column_map, joined_list)))

    @property
    def column_prefix_dictionary(self):
        """ Return the column_prefix_dictionary with numbers turned into names where possible.

            Returns:
                column_prefix_dictionary(list of str or int): A column_prefix_dictionary with column labels as keys.
        """
        return self._convert_to_names_dict(self._column_map, self._column_prefix_dictionary)

    def get_transformers(self):
        """ Return the transformers to use on a dataframe.

            Returns:
                tuple(dict, list):
                    dict({str or int: func}): The functions to use to transform each column.
                    need_categorical(list of int): A list of columns to treat as categorical.
        """
        final_transformers = {}
        need_categorical = []
        for column in self._final_column_map.values():
            assign_to_column = column.column_name
            if isinstance(assign_to_column, int):
                if self._column_map:
                    assign_to_column = self._column_map[assign_to_column]
                else:
                    assign_to_column = assign_to_column
            if column.column_type == ColumnType.Ignore:
                continue
            elif column.column_type == ColumnType.Value:
                value_str = column.hed_dict
                from functools import partial
                final_transformers[assign_to_column] = partial(self._value_handler, value_str)
            elif column.column_type == ColumnType.Categorical:
                need_categorical.append(column.column_name)
                category_values = column.hed_dict
                from functools import partial
                final_transformers[assign_to_column] = partial(self._category_handler, category_values)
            else:
                final_transformers[assign_to_column] = lambda x: x

        return final_transformers, need_categorical

    @staticmethod
    def check_for_blank_names(column_map, allow_blank_names) -> list[dict]:
        """ Validate there are no blank column names.

        Parameters:
            column_map (iterable): A list of column names.
            allow_blank_names (bool): Only find issues if True.

        Returns:
            list[dict]: A list of dicts, one per issue.
        """
        # We don't have any checks right now if blank/duplicate is allowed
        if allow_blank_names:
            return []

        issues = []

        for column_number, name in enumerate(column_map):
            if name is None or not name or name.startswith(PANDAS_COLUMN_PREFIX_TO_IGNORE):
                issues += ErrorHandler.format_error(ValidationErrors.HED_BLANK_COLUMN, column_number)
                continue

        return issues

    def _set_sidecar(self, sidecar):
        """ Set the sidecar this column mapper uses.

        Parameters:
            sidecar (Sidecar or None): The sidecar to use.

        Raises:
             ValueError: A sidecar was previously set.

        """
        if self._sidecar:
            raise ValueError("Trying to set a second sidecar on a column mapper.")
        if not sidecar:
            return

        self._sidecar = sidecar

    @property
    def sidecar_column_data(self):
        """ Pass through to get the sidecar ColumnMetadata.

        Returns:
            dict({str:ColumnMetadata}): The column metadata defined by this sidecar.
        """
        if self._sidecar:
            return self._sidecar.column_data

        return {}

    def get_tag_columns(self):
        """ Return the column numbers or names that are mapped to be HedTags.

            Note: This is NOT the tag_columns or optional_tag_columns parameter, though they set it.

        Returns:
            column_identifiers(list): A list of column numbers or names that are ColumnType.HedTags.
                0-based if integer-based, otherwise column name.
        """
        return [column_entry.column_name for number, column_entry in self._final_column_map.items()
                if column_entry.column_type == ColumnType.HEDTags]

    def set_tag_columns(self, tag_columns=None, optional_tag_columns=None, finalize_mapping=True):
        """ Set tag columns and optional tag columns.

        Parameters:
            tag_columns (list): A list of ints or strings containing the columns that contain the HED tags.
                                If None, clears existing tag_columns
            optional_tag_columns (list): A list of ints or strings containing the columns that contain the HED tags,
                                         but not an error if missing.
                                         If None, clears existing tag_columns
            finalize_mapping (bool): Re-generate the internal mapping if True, otherwise no effect until finalize.
        """
        if tag_columns is None:
            tag_columns = []
        if optional_tag_columns is None:
            optional_tag_columns = []
        self._tag_columns = tag_columns
        self._optional_tag_columns = optional_tag_columns
        if finalize_mapping:
            self._finalize_mapping()

    def set_column_map(self, new_column_map=None) -> list[dict]:
        """ Set the column number to name mapping.

        Parameters:
            new_column_map (list or dict):  Either an ordered list of the column names or column_number:column name.
                dictionary. In both cases, column numbers start at 0.

        Returns:
            list[dict]: List of issues. Each issue is a dictionary.

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
        self._finalize_mapping()

    def set_column_prefix_dictionary(self, column_prefix_dictionary, finalize_mapping=True):
        """Set the column prefix dictionary. """
        self._column_prefix_dictionary = column_prefix_dictionary
        if finalize_mapping:
            self._finalize_mapping()

    @staticmethod
    def _get_sidecar_basic_map(column_map, column_data):
        basic_final_map = {}
        unhandled_cols = []
        if column_map:
            for column_number, column_name in column_map.items():
                if column_name is None:
                    continue
                if column_name in column_data:
                    column_entry = copy.deepcopy(column_data[column_name])
                    column_entry.column_name = column_name
                    basic_final_map[column_name] = column_entry
                    continue
                elif isinstance(column_name, str) and column_name.startswith(PANDAS_COLUMN_PREFIX_TO_IGNORE):
                    continue
                unhandled_cols.append(column_name)

        return basic_final_map, unhandled_cols

    @staticmethod
    def _convert_to_names(column_to_name_map, column_list):
        converted_names = []
        for index in column_list:
            if isinstance(index, int):
                if not column_to_name_map:
                    converted_names.append(index)
                elif index in column_to_name_map:
                    converted_names.append(column_to_name_map[index])
            else:
                if index in column_to_name_map.values():
                    converted_names.append(index)
        return converted_names

    @staticmethod
    def _convert_to_names_dict(column_to_name_map, column_dict):
        converted_dict = {}
        for index, column_data in column_dict.items():
            if isinstance(index, int):
                if not column_to_name_map:
                    converted_dict[index] = column_data
                elif index in column_to_name_map:
                    converted_dict[column_to_name_map[index]] = column_data
            else:
                if index in column_to_name_map.values():
                    converted_dict[index] = column_data
        return converted_dict

    @staticmethod
    def _add_value_columns(final_map, column_prefix_dictionary):
        for col, prefix in column_prefix_dictionary.items():
            if prefix.endswith("/"):
                prefix = prefix + "#"
            else:
                prefix = prefix + "/#"
            new_def = ColumnMetadata(ColumnType.Value, col, source=prefix)
            final_map[col] = new_def

    @staticmethod
    def _add_tag_columns(final_map, tag_columns):
        for col in tag_columns:
            new_def = ColumnMetadata(ColumnType.HEDTags, col)
            final_map[col] = new_def

    def _get_column_lists(self):
        column_lists = self._tag_columns, self._optional_tag_columns, self._column_prefix_dictionary
        list_names = ["tag_columns", "optional_tag_columns", "column_prefix_dictionary"]

        if not any(column for column in column_lists):
            return column_lists, list_names
        # Filter out empty lists from the above
        column_lists, list_names = zip(*[(col_list, list_name) for col_list, list_name in zip(column_lists, list_names)
                                         if col_list])

        return column_lists, list_names

    def _check_for_duplicates_and_required(self, list_names, column_lists) -> list[dict]:
        """ Check for duplicates and required columns in the given lists.
        """
        issues = []
        for list_name, col_list in zip(list_names, column_lists):
            # Convert all known strings to ints, then check for duplicates
            converted_list = [item if isinstance(item, int) else self._reverse_column_map.get(item, item)
                              for item in col_list]

            if col_list != self._optional_tag_columns:
                for test_col in converted_list:
                    if isinstance(test_col, str) and test_col not in self._reverse_column_map:
                        issues += ErrorHandler.format_error(ValidationErrors.HED_MISSING_REQUIRED_COLUMN,
                                                            test_col, list_name)

            issues += self._check_for_duplicates_between_lists(converted_list, list_name,
                                                               ValidationErrors.DUPLICATE_COLUMN_IN_LIST)

        return issues

    def _check_for_duplicates_between_lists(self, checking_list, list_names, error_type):
        issues = []
        duplicates = [item for item, count in Counter(checking_list).items() if count > 1]
        for duplicate in duplicates:
            issues += ErrorHandler.format_error(error_type, duplicate,
                                                self._column_map.get(duplicate), list_names)
        return issues

    def check_for_mapping_issues(self, allow_blank_names=False) ->list[dict]:
        """ Find all issues given the current column_map, tag_columns, etc.

        Parameters:
            allow_blank_names (bool): Only flag blank names if False.

        Returns:
            list[dict]: All issues found as a list of dicts.
        """
        # 1. Get the lists with entries
        column_lists, list_names = self._get_column_lists()
        # 2. Verify column_prefix columns and tag columns are present, and check for duplicates
        issues = self._check_for_duplicates_and_required(list_names, column_lists)

        combined_list = self.tag_columns + list(self.column_prefix_dictionary)
        # 3. Verify prefix and tag columns do not conflict.
        issues += self._check_for_duplicates_between_lists(combined_list, list_names,
                                                           ValidationErrors.DUPLICATE_COLUMN_BETWEEN_SOURCES)

        # 4. Verify we didn't get both a sidecar and a tag column list
        if self._sidecar and combined_list and combined_list != ["HED"]:
            issues += ErrorHandler.format_error(ValidationErrors.SIDECAR_AND_OTHER_COLUMNS, column_names=combined_list)

        # 5. Verify we handled all columns
        if self._warn_on_missing_column:
            fully_combined_list = list(self.sidecar_column_data) + combined_list + NO_WARN_COLUMNS
            for column in self._column_map.values():
                if column not in fully_combined_list:
                    issues += ErrorHandler.format_error(ValidationErrors.HED_UNKNOWN_COLUMN, column)

        issues += self.check_for_blank_names(self._column_map.values(), allow_blank_names=allow_blank_names)
        return issues

    def _finalize_mapping(self):
        final_map, unhandled_cols = self._get_sidecar_basic_map(self._column_map, self.sidecar_column_data)

        self._add_tag_columns(final_map, self.tag_columns)
        self._remove_from_list(unhandled_cols, self.tag_columns)

        self._add_value_columns(final_map, self.column_prefix_dictionary)
        self._remove_from_list(unhandled_cols, self.column_prefix_dictionary)

        self._final_column_map = dict(sorted(final_map.items()))

    @staticmethod
    def _remove_from_list(list_to_alter, to_remove) -> list:
        return [item for item in list_to_alter if item not in to_remove]

    def get_def_dict(self, hed_schema, extra_def_dicts=None) -> DefinitionDict:
        """ Return def dicts from every column description.

        Parameters:
            hed_schema (Schema): A HED schema object to use for extracting definitions.
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
           DefinitionDict:   A single definition dict representing all the data(and extra def dicts).
        """
        if self._sidecar:
            return self._sidecar.get_def_dict(hed_schema=hed_schema, extra_def_dicts=extra_def_dicts)

        return DefinitionDict(extra_def_dicts, hed_schema=hed_schema)

    def get_column_mapping_issues(self) -> list[dict]:
        """ Get all the issues with finalizing column mapping(duplicate columns, missing required, etc.).

        Notes:
            - This is deprecated and now a wrapper for "check_for_mapping_issues()".

        Returns:
            list[dict]: A list dictionaries of all issues found from mapping column names to numbers.

        """
        return self.check_for_mapping_issues()

    @staticmethod
    def _category_handler(category_values, x):
        return category_values.get(x, "")

    @staticmethod
    def _value_handler(value_str, x):
        if x == "n/a":
            return "n/a"

        return value_str.replace("#", str(x))
