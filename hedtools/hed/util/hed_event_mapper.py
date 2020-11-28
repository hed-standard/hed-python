from enum import Enum
import json

from hed.util.error_types import SidecarErrors
from hed.util.hed_string_util import split_hed_string, split_hed_string_return_strings
from hed.validator.tag_validator import TagValidator
from hed.util.error_reporter import format_sidecar_error

class ColumnType(Enum):
    """The overall type of a column in event mapper, eg treat it as HED tags.

    Mostly internal."""
    # Do not return this column at all
    Ignore = 0
    # This column is a category with a list of possible values to replace with hed strings.
    Categorical = 1
    # This column has a value(eg filename) that is added to a hed tag in place of a # sign.
    Value = 2
    # Return this column exactly as given, it is HED tags.
    HEDTags = 3
    # Return this as a separate property in the dictionary, rather than as part of the hed string.
    Attribute = 4


class ColumnSettings:
    def __init__(self, event_type=None, name=None, hed_dict=None, column_prefix=None):
        """
        A single column entry in the event mapper.  Each column you want to retrieve data from will have one.
            Mostly internal

        Parameters
        ----------
        event_type : ColumnType
            How to treat this column when reading data
        name : str or int
            The name or column number of this column.  If name is a string, you'll need to use a column map
            to set the number later.
        hed_dict : dict
            The loaded data (usually from json) for the given Event.
            At a minimum, this needs "HED" in the dict for several event_types
        column_prefix : str
            If present, prepend the given prefix to all hed tags in the columns.  Only works on ColumnType HedTags
        """
        self.type = event_type
        self.name = name
        self.column_prefix = column_prefix
        self._hed_dict = hed_dict
        if "HED" in self._hed_dict:
            self.hed_strings = hed_dict["HED"]
        else:
            self.hed_strings = None


class EventMapper:
    """Handles mapping columns of hed tags from a file to a usable format.

        Private Functions and variables column and row indexing starts at 0.
        Public functions and variables indexing starts at 1(or 2 if has column names)"""
    def __init__(self, event_filenames=None, tag_columns=None, column_prefix_dictionary=None,
                 hed_dictionary=None):
        """Constructor for EventMapper

        Parameters
        ----------
        event_filenames : str or [str]
            A json filename or list of filenames to gather named columns from
        tag_columns: list
             A list of ints containing the columns that contain the HED tags. The default value is the 2nd column.
        column_prefix_dictionary: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
        hed_dictionary: HedDictionary object
            Used to create a TagValidator, which is then used to validate the entries in value and category entries.
        """
        self.minimum_required_keys = ("HED", )
        # This points to event_type entries based on column names or indexes if columns have no name.
        self.event_types = {}
        # Maps column number to event_entry.  This is what's actually used by most code.
        self._final_column_map = {}

        self._column_map = None
        self._tag_columns = []
        self._column_prefix_dictionary = {}

        self._hed_dictionary = hed_dictionary
        # Each will contain a list of util.error_reporter error style dicts.
        self._key_validation_issues = {}

        if event_filenames:
            self.add_json_file_events(event_filenames)

        self.set_tag_columns(tag_columns, False)
        self.set_column_prefix_dict(column_prefix_dictionary, False)

        # finalize the column map based on initial settings.
        self._finalize_mapping()

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

    def add_json_file_events(self, event_filenames):
        if isinstance(event_filenames, str):
            event_filenames = [event_filenames]
        for event_filename in event_filenames:
            try:
                with open(event_filename, "r") as fp:
                    loaded_events = json.load(fp)
                    for event, event_dict in loaded_events.items():
                        self._add_single_event_type(event, event_dict, source_filename=event_filename)
            except FileNotFoundError:
                self._key_validation_issues[event_filename] = format_sidecar_error(SidecarErrors.INVALID_FILENAME,
                                                                                   filename=event_filename)
            except json.decoder.JSONDecodeError:
                self._key_validation_issues[event_filename] = format_sidecar_error(SidecarErrors.CANNOT_PARSE_JSON,
                                                                                   filename=event_filename)

    def add_value_column(self, name, hed):
        new_entry = {
            "HED": hed
        }
        self._add_single_event_type(name, new_entry, ColumnType.Value)

    def add_categorical_column(self, name, hed_category_dict):
        new_entry = {
            "HED": hed_category_dict
        }
        self._add_single_event_type(name, new_entry, ColumnType.Categorical)

    def add_attribute_columns(self, column_names):
        self._add_multiple_events(column_names, ColumnType.Attribute)

    def add_hedtag_columns(self, column_names):
        self._add_multiple_events(column_names, ColumnType.HEDTags)

    def add_ignore_columns(self, column_names):
        self._add_multiple_events(column_names, ColumnType.Ignore)

    def set_column_map(self, new_column_map=None):
        """Pass in the column number to name mapping to finalize

        Parameters
        ----------
        new_column_map : list or dict
            If list, should be each column name with column numbers assumed to start at 1.
            If dict, should be column_number : column name.  Column number should start at 1.
        """
        column_map = {}
        if isinstance(new_column_map, dict):
            column_map = self._subtract_1_from_dictionary_keys(new_column_map)
        # List like
        else:
            column_map = {column_number: column_name for column_number, column_name in enumerate(new_column_map)}
        self._column_map = column_map
        self._finalize_mapping()

    def _expand_column(self, column_number, input_text):
        # Default 1-1 mapping if we don't have specific behavior.
        if not self._final_column_map:
            return input_text, False

        # If no entry, ignore this column.
        if column_number not in self._final_column_map:
            return None, False

        column_entry = self._final_column_map[column_number]
        event_type = column_entry.type

        if event_type == ColumnType.Categorical:
            hed_string_entries = column_entry.hed_strings
            if input_text in hed_string_entries:
                return hed_string_entries[input_text], False
        elif event_type == ColumnType.Value:
            prelim_text = column_entry.hed_strings
            final_text = prelim_text.replace("#", input_text)
            return final_text, False
        elif event_type == ColumnType.HEDTags:
            new_text = self._prepend_prefix_to_required_tag_column_if_needed(input_text, column_entry.column_prefix)
            return new_text, False
        elif event_type == ColumnType.Ignore:
            return None, False
        elif event_type == ColumnType.Attribute:
            return input_text, column_entry.name

        return "BUG NO ENTRY FOUND", False

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

        prefix_to_remove = entry.column_prefix
        hed_tags = split_hed_string(new_text)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = new_text[startpos:endpos]
            if is_hed_tag:
                if tag and tag.lower().startswith(prefix_to_remove.lower()):
                    tag = tag[len(prefix_to_remove):]
            final_string += tag
        return final_string

    def _add_multiple_events(self, column_names, event_type):
        if isinstance(column_names, str):
            column_names = [column_names]
        for column_name in column_names:
            self._add_single_event_type(column_name, None, event_type)

    def _add_single_event_type(self, column_name, dict_for_entry, event_type=None, source_filename=""):
        event_entry = self._create_event_entry(dict_for_entry, column_name, event_type)
        event_validation_issues = self._validate_event_entry(event_entry)
        if event_validation_issues and source_filename:
            event_validation_issues = format_sidecar_error(SidecarErrors.SIDECAR_FILE_NAME, filename=source_filename) \
                                      + event_validation_issues
        self._key_validation_issues[column_name] = event_validation_issues
        self.event_types[column_name] = event_entry
        return True

    def _validate_event_entry(self, event_entry):
        col_validation_issues = []
        dict_for_entry = event_entry._hed_dict
        # Hed string validation can only be done with a _hed_dictionary
        if self._hed_dictionary and dict_for_entry:
            tag_validator = TagValidator(self._hed_dictionary, check_for_warnings=True, run_semantic_validation=True,
                                         allow_numbers_to_be_pound_sign=True)
            hed_strings = dict_for_entry["HED"]
            if isinstance(hed_strings, dict):
                hed_strings = [hed_strings[key] for key in hed_strings]
            else:
                hed_strings = [hed_strings]

            for hed_string in hed_strings:
                col_validation_issues += tag_validator.run_hed_string_validators(hed_string)
                for hed_tag in split_hed_string_return_strings(hed_string):
                    hed_tag_lower = hed_tag.lower()
                    tag_issues = tag_validator.run_individual_tag_validators(hed_tag, hed_tag_lower)
                    if tag_issues:
                        col_validation_issues += tag_issues

        if event_entry.type is None:
            col_validation_issues += format_sidecar_error(SidecarErrors.UNKNOWN_EVENT_TYPE,
                                                          event_name=event_entry.name)
        elif event_entry.type == ColumnType.Value:
            if not event_entry.hed_strings:
                col_validation_issues += format_sidecar_error(SidecarErrors.BLANK_HED_STRING)
            elif not isinstance(event_entry.hed_strings, str):
                col_validation_issues += format_sidecar_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                              given_type=type(event_entry.hed_strings),
                                                              expected_type="str")
            elif event_entry.hed_strings.count("#") != 1:
                col_validation_issues += format_sidecar_error(SidecarErrors.INVALID_NUMBER_POUND_SIGNS,
                                                              pound_sign_count=event_entry.hed_strings.count("#"))

        elif event_entry.type == ColumnType.Categorical:
            if not event_entry.hed_strings:
                col_validation_issues += format_sidecar_error(SidecarErrors.BLANK_HED_STRING)
            elif not isinstance(event_entry.hed_strings, dict):
                col_validation_issues += format_sidecar_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                              given_type=type(event_entry.hed_strings),
                                                              expected_type="dict")
            else:
                if len(event_entry.hed_strings) < 2:
                    # Make this a warning
                    col_validation_issues += format_sidecar_error(SidecarErrors.TOO_FEW_CATEGORIES,
                                                                  category_count=len(event_entry.hed_strings))

                for key, value in event_entry.hed_strings.items():
                    if value.count("#") != 0:
                        col_validation_issues += format_sidecar_error(SidecarErrors.TOO_MANY_POUND_SIGNS,
                                                                      pound_sign_count=value.count("#"))
        if col_validation_issues:
            col_validation_issues = format_sidecar_error(SidecarErrors.SIDECAR_EVENT_NAME, event_name=event_entry.name) + \
                                    col_validation_issues
        return col_validation_issues

    def _create_event_entry(self, dict_for_entry=None, column_name=None, event_type=None):
        if event_type is None:
            event_type = self._detect_event_type(dict_for_entry)

        if dict_for_entry is None:
            dict_for_entry = {}

        new_entry = ColumnSettings(event_type, column_name, dict_for_entry, "")
        return new_entry

    def _detect_event_type(self, dict_for_entry):
        if not dict_for_entry or not set(self.minimum_required_keys).issubset(dict_for_entry.keys()):
            return None

        hed_entry = dict_for_entry["HED"]
        if isinstance(hed_entry, dict):
            return ColumnType.Categorical

        if "#" not in dict_for_entry["HED"]:
            return None

        return ColumnType.Value

    def _set_column_prefix(self, column_number, new_required_prefix):
        if isinstance(column_number, str):
            raise TypeError("Must pass in a column number not name to _set_column_prefix")
        if column_number not in self._final_column_map:
            event_entry = self._create_event_entry()
            self._final_column_map[column_number] = event_entry
        else:
            event_entry = self._final_column_map[column_number]

        event_entry.column_prefix = new_required_prefix
        if event_entry.type is None or event_entry.type == ColumnType.Ignore:
            event_entry.type = ColumnType.HEDTags

    def _finalize_mapping(self):
        self._final_column_map = {}
        if self._column_map is not None:
            for column_number, column_name in self._column_map.items():
                if column_name in self.event_types:
                    event_entry = self.event_types[column_name]
                    event_entry.name = column_name
                    self._final_column_map[column_number] = event_entry

        # Add any numbered event columns
        for column_name, event_entry in self.event_types.items():
            if isinstance(column_name, int):
                # Convert to internal numbering format
                column_number = column_name - 1
                self._final_column_map[column_number] = event_entry

        # Add column numbers.
        for column_number in self._tag_columns:
            if column_number not in self._final_column_map:
                self._final_column_map[column_number] = self._create_event_entry(None, column_number,
                                                                                 ColumnType.HEDTags)

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
    def _prepend_prefix_to_required_tag_column_if_needed(required_tag_column_tags, required_tag_prefix):
        """Prepends the tag paths to the required tag column tags that need them.
        Parameters
        ----------
        required_tag_column_tags: str
            A string containing HED tags associated with a required tag column that may need a tag prefix prepended to
            its tags.
        required_tag_prefix: str
            A string that will be added if missing to any given tag.
        Returns
        -------
        string
            A comma separated string that contains the required HED tags with the tag prefix prepended to them if
            needed.

        """
        if not required_tag_prefix:
            return required_tag_column_tags

        hed_tags = split_hed_string(required_tag_column_tags)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = required_tag_column_tags[startpos:endpos]
            if is_hed_tag:
                if tag and not tag.lower().startswith(required_tag_prefix.lower()):
                    tag = required_tag_prefix + tag
            final_string += tag
        return final_string

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
