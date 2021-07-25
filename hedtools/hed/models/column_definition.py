from enum import Enum
from hed.models.hed_string import HedString
from hed.models.def_dict import DefDict
from hed.errors.error_types import SidecarErrors, ErrorContext, ValidationErrors
from hed.errors import error_reporter

import re


class ColumnType(Enum):
    """The overall column_type of a column in column mapper, eg treat it as HED tags.

    Mostly internal to column mapper related code"""
    Unknown = None
    # Do not return this column at all
    Ignore = "ignore"
    # This column is a category with a list of possible values to replace with hed strings.
    Categorical = "categorical"
    # This column has a value(eg filename) that is added to a hed tag in place of a # sign.
    Value = "value"
    # Return this column exactly as given, it is HED tags.
    HEDTags = "hed_tags"
    # Return this as a separate property in the dictionary, rather than as part of the hed string.
    Attribute = "attribute"


class ColumnDef:
    """A single column in either the ColumnMapper or ColumnDefGroup"""
    def __init__(self, column_type=None, name=None, hed_dict=None, column_prefix=None,
                 error_handler=None):
        """
        A single column entry in the column mapper.  Each column you want to retrieve data from will have one.

        Parameters
        ----------
        column_type : ColumnType
            How to treat this column when reading data
        name : str or int
            The column_name or column number of this column.  If name is a string, you'll need to use a column map
            to set the number later.
        hed_dict : dict
            The loaded data (usually from json) for the given def
            At a minimum, this needs "HED" in the dict for several ColumnType
        column_prefix : str
            If present, prepend the given prefix to all hed tags in the columns.  Only works on ColumnType HedTags
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        """
        if column_type is None or column_type == ColumnType.Unknown:
            column_type = ColumnDef._detect_column_def_type(hed_dict)

        if hed_dict is None:
            hed_dict = {}

        self.column_type = column_type
        self.column_name = name
        self.column_prefix = column_prefix
        self._hed_dict = hed_dict
        self._def_dict = self.extract_defs(error_handler=error_handler)

    @property
    def def_dict(self):
        return self._def_dict

    @property
    def hed_dict(self):
        """
            The loaded dict for any given entry.

        Returns
        -------
        dict_for_entry: dict
            A dict which generally contains a "HED" entry and optional others like description.
        """
        return self._hed_dict

    def hed_string_iter(self, include_position=False, also_return_bad_types=False):
        """
        Return iterator to loop over all hed strings in this column definition

        Parameters
        ----------
        include_position : bool
            If true, this returns a tuple including a position element you can pass back in to set_hed_string
        also_return_bad_types: bool
            If true, will return invalid entries, such as lists, rather than silently skipping them.
        Yields
        -------
        hed_string : str
            hed_string at a given column and key position
        position: str, optional
            Indicates where hed_string was loaded from so it can be later set by the user
        """
        if not isinstance(self._hed_dict, dict):
            return
        hed_strings = self._hed_dict.get("HED", None)
        if isinstance(hed_strings, dict):
            for key, value in hed_strings.items():
                if not also_return_bad_types and not isinstance(value, str):
                    continue
                if include_position:
                    yield value, key
                else:
                    yield value
        elif isinstance(hed_strings, str):
            if include_position:
                yield hed_strings, None
            else:
                yield hed_strings

    def set_hed_string(self, new_hed_string, position=None):
        """
            Set a hed string in a provided category key/etc

        Parameters
        ----------
        new_hed_string : str or HedString
            The new hed_string to replace the value at position.
        position : str, optional
            This should only be a value returned from hed_string_iter
        """
        hed_strings = self._hed_dict.get("HED", None)
        if isinstance(hed_strings, dict):
            if position is None:
                raise TypeError("Error: Trying to set a category HED string with no category")
            if position not in self._hed_dict["HED"]:
                raise TypeError("Error: Not allowed to add new categories to a column")
            self._hed_dict["HED"][position] = str(new_hed_string)
        elif isinstance(hed_strings, (str, HedString)):
            if position is not None:
                raise TypeError("Error: Trying to set a value HED string with a category")
            self._hed_dict["HED"] = str(new_hed_string)
        else:
            raise TypeError("Error: Trying to set a HED string on a column_type that doesn't support it.")

    def _get_category_hed_string(self, category):
        """Fetches the hed string from a given category key.

        Parameters
        ----------
        category : str
            The category key to retrieve the string from

        Returns
        -------
        hed_string: str
            The hed string for a given category entry in a category column
        """
        if self.column_type != ColumnType.Categorical:
            return None

        return self._hed_dict["HED"].get(category, None)

    def _get_value_hed_string(self):
        """Fetches the hed_string from a given value column

        Returns
        -------
        hed_string: str
            The hed string for a given value column
        """
        if self.column_type != ColumnType.Value:
            return None

        return self._hed_dict["HED"]

    def expand(self, input_text):
        """
            Expands the input_text based on the rules for this column.
            Eg adding prefix, inserting a column hed_string from key, etc.

        Parameters
        ----------
        input_text : str
            Text to expand(generally from a single cell in a spreadsheet)

        Returns
        -------
        hed_string: str
            The expanded column as a hed_string
        attribute_name_or_error_message: str or {}
            If this is a string, contains the name of this column as an attribute.
            If the first return value is None, this is an error message dict.
        """
        column_type = self.column_type

        if column_type == ColumnType.Categorical:
            final_text = self._get_category_hed_string(input_text)
            if final_text:
                return HedString(final_text), False
            else:
                return None, [{"error_type": ValidationErrors.HED_SIDECAR_KEY_MISSING,
                               "tag": input_text,
                               "category_keys": list(self._hed_dict["HED"].keys())}]
        elif column_type == ColumnType.Value:
            prelim_text = self._get_value_hed_string()
            final_text = prelim_text.replace("#", input_text)
            return HedString(final_text), False
        elif column_type == ColumnType.HEDTags:
            hed_string_obj = HedString(input_text)
            new_text = self._prepend_prefix_to_required_tag_column_if_needed(hed_string_obj, self.column_prefix)
            return new_text, False
        elif column_type == ColumnType.Ignore:
            return None, False
        elif column_type == ColumnType.Attribute:
            return input_text, self.column_name

        return None, {"error_type": "INTERNAL_ERROR"}

    @staticmethod
    def _prepend_prefix_to_required_tag_column_if_needed(required_tag_column_tags, required_tag_prefix):
        """Prepends the tag paths to the required tag column tags that need them.
        Parameters
        ----------
        required_tag_column_tags: HedString
            A string containing HED tags associated with a required tag column that may need a tag prefix prepended to
            its tags.
        required_tag_prefix: str
            A string that will be added if missing to any given tag.
        Returns
        -------
        HedString
            A comma separated string that contains the required HED tags with the tag prefix prepended to them if
            needed.

        """
        if not required_tag_prefix:
            return required_tag_column_tags

        for tag in required_tag_column_tags.get_all_tags():
            tag.add_prefix_if_not_present(required_tag_prefix)

        return required_tag_column_tags

    def remove_prefix_if_needed(self, original_tag, current_tag_text):
        """
        Remove prefix from all tags in given hed string if this column has a required prefix

        Parameters
        ----------
        original_tag: HedTag
            The original hed tag being written.
        current_tag_text : str
            A single tag as a string, in any form.

        Returns
        -------
        prefix_removed_text: str
            original_text with required prefixes removed from all hed tags
        """
        prefix_to_remove = self.column_prefix
        if not prefix_to_remove:
            return current_tag_text

        if current_tag_text.lower().startswith(prefix_to_remove.lower()):
            current_tag_text = current_tag_text[len(prefix_to_remove):]
        return current_tag_text

    @staticmethod
    def _detect_column_def_type(dict_for_entry):
        """
        Determines the ColumnType of a given json entry.

        Parameters
        ----------
        dict_for_entry : dict
            The loaded json entry a specific column.  Generally has a "HED" entry among other optional ones.

        Returns
        -------
        column_type: ColumnType
            The determined type of a given column.  Returns None if unknown.
        """
        if not dict_for_entry or not isinstance(dict_for_entry, dict):
            return ColumnType.Attribute

        minimum_required_keys = ("HED", )
        if not set(minimum_required_keys).issubset(dict_for_entry.keys()):
            return ColumnType.Attribute

        hed_entry = dict_for_entry["HED"]
        if isinstance(hed_entry, dict):
            return ColumnType.Categorical

        if not isinstance(hed_entry, str):
            return None

        if "#" not in dict_for_entry["HED"]:
            return None

        return ColumnType.Value

    def get_def_issues(self):
        """
        Returns the issues found extracting definitions from this column.
        Returns
        -------

        """
        return self._def_dict.get_def_issues()

    def validate_column_entry(self, hed_schema=None, def_mapper=None, error_handler=None):
        """
        Finds all validation issues in this column.

        Parameters
        ----------
        hed_schema : HedSchema, optional
            The dictionary to use to validate hed_strings.  If absent, will only validate column syntax.
        def_mapper: DefMapper
            The definition mapper to validate def tags with.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        column_issues: [{}]
        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()

        error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, self.column_name)
        col_validation_issues = []
        if self.hed_string_iter():
            event_validator = None
            # Full Hed string validation can only be done with a hed_schema
            if hed_schema is not None:
                from hed.validator.event_validator import EventValidator
                event_validator = EventValidator(check_for_warnings=True, run_semantic_validation=True,
                                                 hed_schema=hed_schema, error_handler=error_handler,
                                                 allow_numbers_to_be_pound_sign=True)
            for hed_string, position in self.hed_string_iter(include_position=True, also_return_bad_types=True):
                error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, position)
                if not hed_string:
                    col_validation_issues += error_handler.format_error(SidecarErrors.BLANK_HED_STRING)
                if not isinstance(hed_string, str):
                    col_validation_issues += error_handler.format_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                                        given_type=type(hed_string),
                                                                        expected_type="str")
                else:
                    hed_string_obj = HedString(hed_string)
                    error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj,
                                                     increment_depth_after=False)
                    if def_mapper:
                        col_validation_issues += def_mapper.replace_and_remove_tags(hed_string_obj, expand_defs=False)
                    if event_validator:
                        col_validation_issues += event_validator.validate_input(hed_string_obj)
                    col_validation_issues += self._validate_pound_sign_count(hed_string_obj, error_handler)
                    error_handler.pop_error_context()
                error_handler.pop_error_context()

        if self.column_type is None:
            col_validation_issues += error_handler.format_error(SidecarErrors.UNKNOWN_COLUMN_TYPE,
                                                                column_name=self.column_name)
        elif self.column_type == ColumnType.Categorical:
            raw_hed_dict = self._hed_dict["HED"]
            if not raw_hed_dict:
                col_validation_issues += error_handler.format_error(SidecarErrors.BLANK_HED_STRING)

        col_validation_issues += self.get_def_issues()
        error_handler.pop_error_context()
        return col_validation_issues

    def _validate_pound_sign_count(self, hed_string, error_handler):
        """Checks if a a given hed string in the column has the correct number of pound signs

        This normally should be either 0 or 1, but sometimes will be higher due to the presence of definition tags.

        Parameters
        ----------
        hed_string : str or HedString
        error_handler : ErrorHandler

        Returns
        -------
        issues_list: [{}]
            A list of the pound sign errors(always 0 or 1 item in the list)
        """
        if self.column_type == ColumnType.Value or self.column_type == ColumnType.Attribute:
            base_pound_sign_count = 1
            error_type = SidecarErrors.INVALID_POUND_SIGNS_VALUE
        elif self.column_type == ColumnType.HEDTags or self.column_type == ColumnType.Categorical:
            base_pound_sign_count = 0
            error_type = SidecarErrors.INVALID_POUND_SIGNS_CATEGORY
        else:
            return []

        definition_and_exp_pattern = "definition\/.*?\/#"
        pattern = re.compile(definition_and_exp_pattern)
        expected_pound_sign_count = len(pattern.findall(hed_string.lower())) * 2 + base_pound_sign_count

        if str(hed_string).count("#") != expected_pound_sign_count:
            return error_handler.format_error(error_type, pound_sign_count=str(hed_string).count("#"))

        return []

    def extract_defs(self, error_handler=None):
        """
            Finds all definitions in the hed strings of this column def group.

        Parameters
        ----------
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        def_dicts: DefDict
            A DefDict containing all the definitions found.
        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        def_dict = DefDict()
        for hed_string, key_name in self.hed_string_iter(include_position=True):
            hed_string_obj = HedString(hed_string)
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, self.column_name)
            error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj, False)
            def_dict.check_for_definitions(hed_string_obj, error_handler=error_handler)
            error_handler.pop_error_context()
            error_handler.pop_error_context()
            error_handler.pop_error_context()

        return def_dict