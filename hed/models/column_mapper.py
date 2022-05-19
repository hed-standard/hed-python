from hed.models.column_metadata import ColumnMetadata, ColumnType
from hed.models.sidecar import Sidecar
from hed.models.hed_string import HedString
from hed.models import model_constants
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors

import copy


PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "


class ColumnMapper:
    """ Container class for mapping columns in event files into HED tags.

    Notes:
        Functions and variables column and row indexing starts at 0.

    """

    def __init__(self, sidecars=None, tag_columns=None, column_prefix_dictionary=None,
                 attribute_columns=None, optional_tag_columns=None):
        """ Constructor for ColumnMapper.

        Args:
            sidecars (Sidecar, string, or list of these): A list of Sidecars or
                 filenames to gather ColumnDefinitions from.
            tag_columns: (list):  A list of ints or strings containing the columns that contain the HED tags.
                Sidecar column definitions will take precedent if there is a conflict with tag_columns.
            column_prefix_dictionary (dict): Dictionary with keys that are column numbers and values are HED tag
                prefixes to prepend to the tags in that column before processing.
            attribute_columns (str, int or list): A column name, column number or a list of column names
                or numbers to treat as attributes.
            optional_tag_columns (list): A list of ints or strings containing the columns that contain
                the HED tags. If the column is otherwise unspecified, convert this column type to HEDTags.

        Notes:
            Sidecars later in the list override those earlier in the list.
            All column numbers are 0 based.

        Examples:
            column_prefix_dictionary = {3: 'Description/', 4: 'Label/'}

            The third column contains tags that need Description/ tag prepended, while the fourth column
            contains tag that needs Label/ prepended.

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
        """ Gather column definitions from a list of sidecars and add them to the column mapper.

        Args:
            sidecars (list): A list of filenames or loaded sidecar files in any mix.

        """
        self._has_sidecars = True
        sidecars = Sidecar.load_multiple_sidecars(sidecars)
        for sidecar in sidecars:
            for column_data in sidecar:
                self._add_column_data(column_data)

    def set_column_prefix_dict(self, column_prefix_dictionary, finalize_mapping=True):
        """ Add the columns specified by the column_prefix_dictionary as HED tag columns with required prefix.

        Args:
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
        """ Set the current tag columns, clearing the current ones if None.

        Args:
            tag_columns (list): A list of ints or strings containing the columns that contain the HED tags.
            optional_tag_columns (list): A list of ints or strings containing the columns that contain the HED tags,
                but not an error if missing.
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

    def set_column_map(self, new_column_map=None):
        """ Set the column number to column_name mapping.

        Args:
            new_column_map (list or dict):  Either an ordered list of the column names or column_number:column name
                dictionary. In both cases column numbers start at 0

        Returns:
            list: List of issues. Each issue is a dictionary.

        """
        if isinstance(new_column_map, dict):
            column_map = new_column_map
        # List like
        else:
            column_map = {column_number: column_name for column_number, column_name in enumerate(new_column_map)}
        self._column_map = column_map
        return self._finalize_mapping()

    def add_columns(self, column_names_or_numbers, column_type=ColumnType.Attribute):
        """ Add a list of blank columns in the given column category.

        Args:
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

        Args:
            column_number (int): The column number this text should be treated as from.
            input_text (str): The text to expand, generally from a single cell of a spreadsheet.

        Returns:
            str or None: The text after expansion or None if this column is undefined or the given text is null.
            False or str: Depends on the value of first return value. If None, this is an error message.
                If string, this is an attribute name that should be stored separately.

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
        """ Expand all mapped columns from a given row.

        Args:
            row_text (list): The text for the given row, one list entry per column number.

        Returns:
            dict: A dictionary containing the keys HED, column_to_hed_tags, and attribute.

        Notes:
            The value of the "HED" entry is the entire expanded row.
            The "column_to_hed_tags" is each expanded column given separately as a list of strings.
            The attribute is the value from the spreadsheet column only present when a given column is an attribute.

        """
        result_dict = {}
        column_to_hed_tags_dictionary = {}
        column_issues_dict = {}
        for column_number, cell_text in enumerate(row_text):
            # if column_number == 0:
            #     continue
            translated_column, attribute_name_or_error = self._expand_column(column_number, str(cell_text))
            if translated_column is None:
                if attribute_name_or_error:
                    if column_number not in column_issues_dict:
                        column_issues_dict[column_number] = []
                    column_issues_dict[column_number] += attribute_name_or_error
                    column_to_hed_tags_dictionary[column_number] = translated_column
                continue
            if attribute_name_or_error:
                result_dict[attribute_name_or_error] = translated_column
                continue

            column_to_hed_tags_dictionary[column_number] = translated_column

        result_dict[model_constants.COLUMN_TO_HED_TAGS] = column_to_hed_tags_dictionary
        if column_issues_dict:
            result_dict[model_constants.COLUMN_ISSUES] = column_issues_dict

        return result_dict

    def get_prefix_remove_func(self, column_number):
        """ Return a function that removes the name_prefix for the given column.

        Args:
            column_number (int): Column number to look up in the prefix dictionary.

        Returns:
            func: A function taking a tag and string, returning a string.

        """
        if column_number not in self._final_column_map:
            return None

        entry = self._final_column_map[column_number]
        if not entry.column_prefix:
            return None

        return entry.remove_prefix_if_needed

    def _add_column_data(self, new_column_entry):
        """ Add the metadata of a column to this column mapper.

        Args:
            new_column_entry (ColumnMetadata): The column definition to add.

        Notes:
            If an entry with the same name exists, the new entry will replace it.

        """
        column_name = new_column_entry.column_name
        self.column_data[column_name] = copy.deepcopy(new_column_entry)

    def _set_column_prefix(self, column_number, new_required_prefix):
        """ Internal function to add this as a required name_prefix to a column

        Args:
            column_number (int): The column number with this name_prefix.
            new_required_prefix (str): The name_prefix to add to the column when loading from a spreadsheet.

        Raises:
            TypeError if column number is passed as a str rather an int.

        Notes:
            If the column is not known to the mapper, it will be added as a HEDTags column.

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
        """ Set the final column mapping information.

        Internal function that gathers all the various sources of column rules and puts them
        in a list mapping from column number to definition.

        Returns:
            list: A list of issues that occurred when creating the mapping. Each issue is a dictionary.

        Notes:
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
                column_number = column_name
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

        return self._finalize_mapping_issues

    def get_def_dicts(self):
        """ Return a list of all def dicts from every column description.

        Returns:
           list:   A list of DefinitionDict objects corresponding to each column entry.

        """
        def_dicts = [entry.def_dict for entry in self.column_data.values()]
        return def_dicts

    def get_column_mapping_issues(self):
        """ Get all the issues with finalizing column mapping.  Primarily a missing required column.

        Returns:
            list: A list dictionaries of all issues found from mapping column names to numbers.

        """
        return self._finalize_mapping_issues

    def validate_column_data(self, hed_ops, error_handler=None, **kwargs):
        """ Validate all column definitions that are being used and column definition hed strings

        Args:
            hed_ops (list, func, or HedOps): A func, a HedOps or a list of these to apply to the
                hed strings in the sidecars.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Returns:
            list: A list of syntax and semantic issues found in the definitions. Each issue is a dictionary.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        all_validation_issues = []
        for column_data in self.column_data.values():
            all_validation_issues += column_data.validate_column(hed_ops,
                                                                 error_handler=error_handler,
                                                                 **kwargs)

        return all_validation_issues
