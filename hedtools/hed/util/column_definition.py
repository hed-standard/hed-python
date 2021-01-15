from enum import Enum
from hed.util.hed_string_util import split_hed_string, split_hed_string_return_strings
from hed.util.error_types import SidecarErrors
from hed.util.error_reporter import format_sidecar_error
from hed.validator.tag_validator import TagValidator


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
    def __init__(self, column_type=None, name=None, hed_dict=None, column_prefix=None):
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
        """
        if column_type is None or column_type == ColumnType.Unknown:
            column_type = ColumnDef._detect_column_def_type(hed_dict)

        if hed_dict is None:
            hed_dict = {}

        self.column_type = column_type
        self.column_name = name
        self.column_prefix = column_prefix
        self._hed_dict = hed_dict

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

    def hed_string_iter(self, include_position=False):
        """
        Return iterator to loop over all hed strings in this column definition

        Parameters
        ----------
        include_position : bool
            If true, this returns a tuple including a position element you can pass back in to set_hed_string

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
        new_hed_string : str
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
            self._hed_dict["HED"][position] = new_hed_string
        elif isinstance(hed_strings, str):
            if position is not None:
                raise TypeError("Error: Trying to set a value HED string with a category")
            self._hed_dict["HED"] = new_hed_string
        else:
            raise TypeError("Error: Trying to set a HED string on a column_type that doesn't support it.")

    def get_category_hed_string(self, category):
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

    def get_value_hed_string(self):
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
        attribute_name: str
            If not None, contains the name of this column as an attribute.

        """
        column_type = self.column_type

        if column_type == ColumnType.Categorical:
            final_text = self.get_category_hed_string(input_text)
            if final_text:
                return final_text, False
            else:
                # todo: Issue a warning here that the category key is missing.
                pass
        elif column_type == ColumnType.Value:
            prelim_text = self.get_value_hed_string()
            final_text = prelim_text.replace("#", input_text)
            return final_text, False
        elif column_type == ColumnType.HEDTags:
            new_text = self._prepend_prefix_to_required_tag_column_if_needed(input_text, self.column_prefix)
            return new_text, False
        elif column_type == ColumnType.Ignore:
            return None, False
        elif column_type == ColumnType.Attribute:
            return input_text, self.column_name

        return "BUG NO ENTRY FOUND", False

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

    def remove_prefix_if_needed(self, original_text):
        """
        Remove prefix from all tags in given hed string if this column has a required prefix

        Parameters
        ----------
        original_text : str
            Input text, generally from a single cell of a spreadsheet

        Returns
        -------
        prefix_removed_text: str
            original_text with required prefixes removed from all hed tags
        """
        prefix_to_remove = self.column_prefix
        if not prefix_to_remove:
            return original_text

        hed_tags = split_hed_string(original_text)
        final_string = ""
        for is_hed_tag, (startpos, endpos) in hed_tags:
            tag = original_text[startpos:endpos]
            if is_hed_tag:
                if tag and tag.lower().startswith(prefix_to_remove.lower()):
                    tag = tag[len(prefix_to_remove):]
            final_string += tag
        return final_string

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

        if "#" not in dict_for_entry["HED"]:
            return None

        return ColumnType.Value

    def validate_column_entry(self, hed_dictionary=None):
        """
        Finds all validation issues in this column.

        Parameters
        ----------
        hed_dictionary : HedDictionary, optional
            The dictionary to use to validate hed_strings.  If absent, will only validate column syntax.

        Returns
        -------
        column_issues: [{}]
        """
        col_validation_issues = []
        # Hed string validation can only be done with a hed_dictionary
        if hed_dictionary and self.hed_string_iter():
            tag_validator = TagValidator(hed_dictionary, check_for_warnings=True, run_semantic_validation=True,
                                         allow_numbers_to_be_pound_sign=True)
            for hed_string, position in self.hed_string_iter(include_position=True):
                new_col_validation_issues = tag_validator.run_hed_string_validators(hed_string)
                for hed_tag in split_hed_string_return_strings(hed_string):
                    hed_tag_lower = hed_tag.lower()
                    tag_issues = tag_validator.run_individual_tag_validators(hed_tag, hed_tag_lower)
                    if tag_issues:
                        new_col_validation_issues += tag_issues
                if new_col_validation_issues:
                    new_col_validation_issues = format_sidecar_error(SidecarErrors.SIDECAR_HED_STRING,
                                                                     hed_string=hed_string,
                                                                     position=position) + new_col_validation_issues
                    col_validation_issues += new_col_validation_issues

        if self.column_type is None:
            col_validation_issues += format_sidecar_error(SidecarErrors.UNKNOWN_COLUMN_TYPE,
                                                          column_name=self.column_name)
        elif self.column_type == ColumnType.Value:
            raw_hed_dict = self._hed_dict["HED"]
            if not raw_hed_dict:
                col_validation_issues += format_sidecar_error(SidecarErrors.BLANK_HED_STRING)
            elif not isinstance(raw_hed_dict, str):
                col_validation_issues += format_sidecar_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                              given_type=type(raw_hed_dict),
                                                              expected_type="str")
            elif raw_hed_dict.count("#") != 1:
                col_validation_issues += format_sidecar_error(SidecarErrors.INVALID_NUMBER_POUND_SIGNS,
                                                              pound_sign_count=raw_hed_dict.count("#"))

        elif self.column_type == ColumnType.Categorical:
            raw_hed_dict = self._hed_dict["HED"]
            if not raw_hed_dict:
                col_validation_issues += format_sidecar_error(SidecarErrors.BLANK_HED_STRING)
            elif not isinstance(raw_hed_dict, dict):
                col_validation_issues += format_sidecar_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                              given_type=type(raw_hed_dict),
                                                              expected_type="dict")
            else:
                if len(raw_hed_dict) < 2:
                    # Make this a warning
                    col_validation_issues += format_sidecar_error(SidecarErrors.TOO_FEW_CATEGORIES,
                                                                  category_count=len(raw_hed_dict))

                for key, value in raw_hed_dict.items():
                    if value.count("#") != 0:
                        col_validation_issues += format_sidecar_error(SidecarErrors.TOO_MANY_POUND_SIGNS,
                                                                      pound_sign_count=value.count("#"))
        if col_validation_issues:
            col_validation_issues = format_sidecar_error(SidecarErrors.SIDECAR_COLUMN_NAME,
                                                         column_name=self.column_name) \
                                    + col_validation_issues
        return col_validation_issues
