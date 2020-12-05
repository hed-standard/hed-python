from hed.util.column_definition import ColumnDefinition, ColumnType
from hed.util.column_def_group import ColumnDefinitionGroup
import copy

class ColumnMapper:
    """Handles mapping columns of hed tags from a file to a usable format.

        Private Functions and variables column and row indexing starts at 0.
        Public functions and variables indexing starts at 1(or 2 if has column names)"""
    def __init__(self, json_def_files=None, tag_columns=None, column_prefix_dictionary=None,
                 hed_dictionary=None, attribute_columns=None):
        """Constructor for ColumnMapper

        Parameters
        ----------
        json_def_files : ColumnDefinitionGroup or string or list
            A list of ColumnDefinitionGroups or filenames to gather ColumnDefinitions from.
        tag_columns: list
             A list of ints containing the columns that contain the HED tags.  If the column is otherwise unspecified,
             it will convert this column type to HEDTags
        column_prefix_dictionary: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
        hed_dictionary: HedDictionary
            Used to create a TagValidator, which is then used to validate the entries in value and category entries.
        attribute_columns: str or int or [str] or [int]
             A list of column names or numbers to treat as attributes.
        """
        # This points to column_type entries based on column names or indexes if columns have no column_name.
        self.column_defs = {}
        # Maps column number to column_entry.  This is what's actually used by most code.
        self._final_column_map = {}

        self._column_map = None
        self._tag_columns = []
        self._column_prefix_dictionary = {}

        self._na_patterns = ["n/a", "nan"]
        self._hed_dictionary = hed_dictionary

        if json_def_files:
            self.add_json_file_defs(json_def_files)
        self.add_columns(attribute_columns)

        self.set_tag_columns(tag_columns, False)
        self.set_column_prefix_dict(column_prefix_dictionary, False)

        # finalize the column map based on initial settings.
        self._finalize_mapping()

    def add_json_file_defs(self, json_file_input_list):
        column_groups = ColumnDefinitionGroup.load_multiple_json_files(json_file_input_list)
        for column_group in column_groups:
            for column_def in column_group:
                self._add_column_def(column_def)

    def set_column_prefix_dict(self, column_prefix_dictionary, finalize_mapping=True):
        """Adds the given columns as hed tag columns with the required prefix if it does not already exist.

        Parameters
        ----------
        column_prefix_dictionary: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
        finalize_mapping : bool
            If True, will re-generate the internal mapping. If False, this function has no effect until you do finalize.
        """
        if column_prefix_dictionary:
            self._column_prefix_dictionary = self._subtract_1_from_dictionary_keys(column_prefix_dictionary)
        if finalize_mapping:
            self._finalize_mapping()

    def set_tag_columns(self, tag_columns, finalize_mapping=True):
        """Adds the given columns as hed tag columns if they don't exist.  If they do exist,
                it will set this column to be retrieved.

        Parameters
        ----------
        tag_columns : list
            A list of ints containing the columns that contain the HED tags. The default value is the 2nd column.
        finalize_mapping :
            If True, will re-generate the internal mapping. If False, this function has no effect until you do finalize.
        """
        if tag_columns:
            self._tag_columns = self._subtract_1_from_list_elements(tag_columns)
        if finalize_mapping:
            self._finalize_mapping()

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
        self._finalize_mapping()

    def add_columns(self, column_names_or_numbers, column_type=ColumnType.Attribute):
        if column_names_or_numbers:
            for column_name in column_names_or_numbers:
                new_def = ColumnDefinition(column_type, column_name)
                self._add_column_def(new_def)

    def _expand_column(self, column_number, input_text):
        # Default 1-1 mapping if we don't have specific behavior.
        if not self._final_column_map:
            return input_text, False

        # If no entry, ignore this column.
        if column_number not in self._final_column_map:
            return None, False

        if not input_text or input_text in self._na_patterns:
            return None, False

        column_entry = self._final_column_map[column_number]
        return column_entry.expand(input_text)

    def expand_row_tags(self, row_text):
        result_dict = {}
        column_to_hed_tags_dictionary = {}
        for column_number, cell_text in enumerate(row_text):
            translated_column, attribute_name = self._expand_column(column_number, str(cell_text))
            if translated_column is None:
                continue
            if attribute_name:
                result_dict[attribute_name] = translated_column
                continue
            column_to_hed_tags_dictionary[column_number + 1] = translated_column

        result_dict["column_to_hed_tags"] = column_to_hed_tags_dictionary
        final_hed_string = ','.join(column_to_hed_tags_dictionary.values())
        result_dict["HED"] = final_hed_string

        return result_dict

    def remove_prefix_if_needed(self, column_number, new_text):
        """This is the inverse of _prepend_prefix_to_required_tag_column_if_needed

        Used when saving back out to a file so we don't always save the added prefix"""
        column_number -= 1
        if column_number not in self._final_column_map:
            return new_text

        entry = self._final_column_map[column_number]
        if not entry.column_prefix:
            return new_text

        final_text = entry.remove_prefix(new_text)
        return final_text

    def _add_column_def(self, new_column_entry):
        column_name = new_column_entry.column_name
        self.column_defs[column_name] = copy.deepcopy(new_column_entry)

    def _set_column_prefix(self, column_number, new_required_prefix):
        if isinstance(column_number, str):
            raise TypeError("Must pass in a column number not column_name to _set_column_prefix")
        if column_number not in self._final_column_map:
            column_entry = ColumnDefinition()
            self._final_column_map[column_number] = column_entry
        else:
            column_entry = self._final_column_map[column_number]

        column_entry.column_prefix = new_required_prefix
        if column_entry.column_type is None or column_entry.column_type == ColumnType.Ignore:
            column_entry.column_type = ColumnType.HEDTags

    def _finalize_mapping(self):
        self._final_column_map = {}
        if self._column_map is not None:
            for column_number, column_name in self._column_map.items():
                if column_name in self.column_defs:
                    column_entry = self.column_defs[column_name]
                    column_entry.column_name = column_name
                    self._final_column_map[column_number] = column_entry

        # Add any numbered columns
        for column_name, column_entry in self.column_defs.items():
            if isinstance(column_name, int):
                # Convert to internal numbering format
                column_number = column_name - 1
                self._final_column_map[column_number] = column_entry

        # Add column numbers.
        for column_number in self._tag_columns:
            if column_number not in self._final_column_map:
                self._final_column_map[column_number] = ColumnDefinition(ColumnType.HEDTags, column_number)

        # Add prefixes
        for column_number, prefix in self._column_prefix_dictionary.items():
            self._set_column_prefix(column_number, prefix)

    @staticmethod
    def _subtract_1_from_dictionary_keys(int_key_dictionary):
        """Subtracts 1 from each dictionary key.

        Parameters
        ----------
        int_key_dictionary: dict
            A dictionary with int keys.
        Returns
        -------
        dictionary
            A dictionary with the keys subtracted by 1.

        """
        return {key - 1: value for key, value in int_key_dictionary.items()}

    @staticmethod
    def _subtract_1_from_list_elements(int_list):
        """Subtracts 1 from each int in a list.

        Parameters
        ----------
        int_list: list
            A list of ints.
        Returns
        -------
        list
            A list of containing each element subtracted by 1.

        """
        return [x - 1 for x in int_list]
