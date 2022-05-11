from enum import Enum
from hed.models.hed_string import HedString
from hed.models.definition_dict import DefinitionDict
from hed.errors.error_types import SidecarErrors, ErrorContext, ValidationErrors
from hed.errors import error_reporter
from hed.errors.error_reporter import ErrorHandler
from hed.models.hed_ops import translate_ops
import copy


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


class ColumnMetadata:
    """ Class representing a single column in a ColumnMapper or top-level dict in Sidecar. """

    def __init__(self, column_type=None, name=None, hed_dict=None, column_prefix=None, error_handler=None):
        """ A single column entry in the column mapper.

        Args:
            column_type (ColumnType or None): How to treat this column when reading data.
            name (str, int, or None): The column_name or column number identifying this column.
                If name is a string, you'll need to use a column map to set the number later.
            hed_dict (dict or None): The loaded data (usually from json) for the given def
                At a minimum, this needs "HED" in the dict for several ColumnType
            column_prefix (str or None): If present, prepend the given column_prefix to all hed tags in the columns.
                Only works on ColumnType HedTags.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default if None.

        Notes:
            Each column from which data is retrieved must have a ColumnMetadata representing its contents.
            The column_prefix dictionaries are used when the column is processed.
        """
        if column_type is None or column_type == ColumnType.Unknown:
            column_type = ColumnMetadata._detect_column_type(hed_dict)

        if hed_dict is None:
            hed_dict = {}

        self.column_type = column_type
        self.column_name = name
        self.column_prefix = column_prefix
        self._hed_dict = hed_dict
        self._def_removed_hed_dict = {}
        self._def_dict = self.extract_definitions(error_handler=error_handler)

    @property
    def def_dict(self):
        """ Return the definition dictionary for this column.

        Returns:
            DefinitionDict: Contains all the definitions located in the column.

        """
        return self._def_dict

    @property
    def hed_dict(self):
        """ The loaded dict for any given entry.

        Returns:
            dict: A dict which generally contains a "HED" entry and optional others like description.

        """
        return self._hed_dict

    def hed_string_iter(self, hed_ops=None, error_handler=None, **kwargs):
        """ Iterator that yields all hed strings in this column metadata.

        Args:
            hed_ops (func, HedOps, or list of these): The HedOps or funcs to apply to the hed strings before returning.
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if none.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options

        Yields:
            HedString: The hed string at a given column and key position.
            str: Indication of the where hed string was loaded from so it can be later set by the user.
            list: List of issues found applying hed_ops. Each issue is a dictionary.

        """
        if error_handler is None:
            error_handler = ErrorHandler()

        if not isinstance(self._hed_dict, dict):
            return

        tag_funcs = []
        if hed_ops:
            tag_funcs = translate_ops(hed_ops, error_handler=error_handler, **kwargs)

        for hed_string_obj, key_name in self._hed_iter():
            new_col_issues = []
            error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
            if not hed_string_obj:
                new_col_issues += ErrorHandler.format_error(SidecarErrors.BLANK_HED_STRING)
                error_handler.add_context_to_issues(new_col_issues)
                yield hed_string_obj, key_name, new_col_issues
            else:
                error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj,
                                                 increment_depth_after=False)
                if tag_funcs:
                    new_col_issues += hed_string_obj.apply_funcs(tag_funcs)

                error_handler.add_context_to_issues(new_col_issues)
                yield hed_string_obj, key_name, new_col_issues
                error_handler.pop_error_context()
            error_handler.pop_error_context()

    def _hed_iter(self, also_return_bad_types=False):
        """ Iterate over all the hed string entries, returning HedString objects.

        Args:
            also_return_bad_types (bool): If true, this can yield types other than HedString, otherwise skips these.

        Yields:
            HedString: Individual hed strings for different entries.
            str: The position to pass back to set this string.

        """
        hed_strings = self._hed_dict.get("HED", None)
        if isinstance(hed_strings, dict):
            for key, hed_string in hed_strings.items():
                if isinstance(hed_string, str):
                    hed_string = HedString(hed_string)
                elif not also_return_bad_types:
                    continue

                yield hed_string, key
        elif isinstance(hed_strings, str):
            hed_string = HedString(hed_strings)
            yield hed_string, None

    def set_hed_string(self, new_hed_string, position=None, set_def_removed=False):
        """ Set a hed string in a provided category key/etc.

        Args:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            position (str, optional): This should only be a value returned from hed_string_iter.
            set_def_removed (bool): If True, set the version with definitions removed, rather than the normal version.

        """
        hed_strings = self._hed_dict.get("HED", None)
        if isinstance(hed_strings, dict):
            if position is None:
                raise TypeError("Error: Trying to set a category HED string with no category")
            if position not in self._hed_dict["HED"]:
                raise TypeError("Error: Not allowed to add new categories to a column")
            if set_def_removed:
                self._def_removed_hed_dict[position] = str(new_hed_string)
            else:
                self._hed_dict["HED"][position] = str(new_hed_string)
        elif isinstance(hed_strings, (str, HedString)):
            if position is not None:
                raise TypeError("Error: Trying to set a value HED string with a category")
            if set_def_removed:
                self._def_removed_hed_dict = str(new_hed_string)
            else:
                self._hed_dict["HED"] = str(new_hed_string)
        else:
            raise TypeError("Error: Trying to set a HED string on a column_type that doesn't support it.")

    def _get_category_hed_string(self, category):
        """ Fetch the hed string from a given category key.

        Args:
            category (str): The category key to retrieve the string from.

        Returns:
            str: The hed string for a given category entry in a category column.

        """
        if self.column_type != ColumnType.Categorical:
            return None

        return self._def_removed_hed_dict.get(category, None)

    def _get_value_hed_string(self):
        """ Fetch the hed string from a given value column.

        Returns:
            str: The hed string for a given value column.

        """
        if self.column_type != ColumnType.Value:
            return None

        return self._def_removed_hed_dict

    def expand(self, input_text):
        """ Expand the input_text based on the rules for this column.

        Args:
            input_text (str): Text to expand (generally from a single cell in a spreadsheet).

        Returns:
            str: The expanded column as a hed_string.
            attribute_name_or_error_message (str or dict): If this is a string, contains the name of this column
                as an attribute. If the first return value is None, this is an error message dictionary.

        Notes:
            An example is adding name_prefix, inserting a column hed_string from key, etc.

        """
        column_type = self.column_type

        if column_type == ColumnType.Categorical:
            final_text = self._get_category_hed_string(input_text)
            if final_text:
                return HedString(final_text), False
            else:
                return None, ErrorHandler.format_error(ValidationErrors.HED_SIDECAR_KEY_MISSING, invalid_key=input_text,
                                                       category_keys=list(self._hed_dict["HED"].keys()))
        elif column_type == ColumnType.Value:
            prelim_text = self._get_value_hed_string()
            final_text = prelim_text.replace("#", input_text)
            return HedString(final_text), False
        elif column_type == ColumnType.HEDTags:
            hed_string_obj = HedString(input_text)
            final_text = self._prepend_prefix_to_required_tag_column_if_needed(hed_string_obj, self.column_prefix)
            return final_text, False
        elif column_type == ColumnType.Ignore:
            return None, False
        elif column_type == ColumnType.Attribute:
            return input_text, self.column_name

        return None, {"error_type": "INTERNAL_ERROR"}

    @staticmethod
    def _prepend_prefix_to_required_tag_column_if_needed(required_tag_column_tags, required_tag_prefix):
        """ Prepend the tag paths to the required tag column tags that need them.

        Args:
            required_tag_column_tags (HedString): A string containing HED tags associated with a
                required tag column that may need a tag
            name_prefix prepended to its tags.
            required_tag_prefix (str): A string that will be added if missing to any given tag.

        Returns:
            HedString: A comma separated string that contains the required HED tags with the tag name_prefix prepended to them if
            needed.

        """
        if not required_tag_prefix:
            return required_tag_column_tags

        for tag in required_tag_column_tags.get_all_tags():
            tag.add_prefix_if_not_present(required_tag_prefix)

        return required_tag_column_tags

    def remove_prefix_if_needed(self, original_tag, current_tag_text):
        """ Remove column_prefix if present from the given tag text.

        Args:
            original_tag (HedTag): The original hed tag being written.
            current_tag_text (str): A single tag as a string, in any form.

        Returns:
            str: current_tag_text with required prefixes removed
        """
        prefix_to_remove = self.column_prefix
        if not prefix_to_remove:
            return current_tag_text

        if current_tag_text.lower().startswith(prefix_to_remove.lower()):
            current_tag_text = current_tag_text[len(prefix_to_remove):]
        return current_tag_text

    @staticmethod
    def _detect_column_type(dict_for_entry):
        """ Determine the ColumnType of a given json entry.

        Args:
            dict_for_entry (dict): The loaded json entry a specific column.
                Generally has a "HED" entry among other optional ones.

        Returns:
            ColumnType: The determined type of given column.  Returns None if unknown.

        """
        if not dict_for_entry or not isinstance(dict_for_entry, dict):
            return ColumnType.Attribute

        minimum_required_keys = ("HED",)
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

    def get_definition_issues(self):
        """ Return the issues found from extracting definitions from this column.

        Returns:
            list: A list of issues found when parsing definitions. Indiviudal issues are dictionaries.

        """
        return self._def_dict.get_definition_issues()

    def validate_column(self, hed_ops, error_handler, **kwargs):
        """ Run the given hed_ops on this column.

        Args:
            hed_ops (list or func or HedOps) A list of HedOps of funcs or a HedOps or func to apply
                to the hed strings in the columns.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Returns:
            list: Issues found by the given hed_ops. Each issue is a dictionary.

        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()

        if not isinstance(hed_ops, list):
            hed_ops = [hed_ops]
        hed_ops = hed_ops.copy()
        hed_ops.append(self._validate_pound_sign_count)
        error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, self.column_name)

        col_validation_issues = self._run_ops(hed_ops, allow_placeholders=True,
                                              error_handler=error_handler, **kwargs)
        col_validation_issues += self._validate_column_structure(error_handler)
        col_validation_issues += self.get_definition_issues()
        error_handler.pop_error_context()
        return col_validation_issues

    def _validate_column_structure(self, error_handler):
        """ Checks primarily for type errors such as expecting a string and getting a list in a json sidecar.

        Args:
            error_handler (ErrorHandler)  Sets the context for the error reporting. Cannot be None.

        Returns:
            list:  Issues in performing the operations. Each issue is a dictionary.

        """
        val_issues = []
        if self.column_type is None:
            val_issues += ErrorHandler.format_error(SidecarErrors.UNKNOWN_COLUMN_TYPE,
                                                    column_name=self.column_name)
        elif self.column_type == ColumnType.Categorical:
            raw_hed_dict = self._hed_dict["HED"]
            if not raw_hed_dict:
                val_issues += ErrorHandler.format_error(SidecarErrors.BLANK_HED_STRING)

        error_handler.add_context_to_issues(val_issues)

        for hed_string_obj, key_name in self._hed_iter(also_return_bad_types=True):
            new_col_issues = []
            error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
            if not isinstance(hed_string_obj, HedString):
                new_col_issues += ErrorHandler.format_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                            given_type=type(hed_string_obj),
                                                            expected_type="str")
                error_handler.add_context_to_issues(new_col_issues)
            val_issues += new_col_issues

        return val_issues

    def _run_ops(self, hed_ops, error_handler, **kwargs):
        col_validation_issues = []
        for _, _, col_issues in self.hed_string_iter(hed_ops, error_handler=error_handler, **kwargs):
            col_validation_issues += col_issues

        return col_validation_issues

    def _validate_pound_sign_count(self, hed_string):
        """ Check if a given hed string in the column has the correct number of pound signs.

        Args:
            hed_string (str or HedString): HED string to be checked.

        Returns:
            list: Issues due to pound sign errors. Each issue is a dictionary.

        Notes:
            Normally the number of # should be either 0 or 1, but sometimes will be higher due to the
            presence of definition tags.

        """
        if self.column_type == ColumnType.Value or self.column_type == ColumnType.Attribute:
            expected_pound_sign_count = 1
            error_type = SidecarErrors.INVALID_POUND_SIGNS_VALUE
        elif self.column_type == ColumnType.HEDTags or self.column_type == ColumnType.Categorical:
            expected_pound_sign_count = 0
            error_type = SidecarErrors.INVALID_POUND_SIGNS_CATEGORY
        else:
            return []

        # Make a copy without definitions to check placeholder count.
        hed_string_copy = copy.copy(hed_string)
        hed_string_copy.remove_definitions()

        if hed_string_copy.lower().count("#") != expected_pound_sign_count:
            return ErrorHandler.format_error(error_type, pound_sign_count=str(hed_string_copy).count("#"))

        return []

    def extract_definitions(self, error_handler=None):
        """ Gather and validate all definitions found in this column.

        Args:
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if None.

        Returns:
            DefinitionDict: Contains all the definitions located in the column.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        new_def_dict = DefinitionDict()
        hed_ops = []
        hed_ops.append(new_def_dict)
        hed_ops.append(HedString.remove_definitions)

        all_issues = []
        for hed_string, key_name, issues in self.hed_string_iter(hed_ops=hed_ops, allow_placeholders=True,
                                                                 error_handler=error_handler):
            self.set_hed_string(hed_string, key_name, set_def_removed=True)
            all_issues += issues

        return new_def_dict
