from enum import Enum
from hed.models.hed_string import HedString
from hed.errors.error_types import SidecarErrors, ValidationErrors
from hed.errors.error_reporter import ErrorHandler


class ColumnType(Enum):
    """ The overall column_type of a column in column mapper, eg treat it as HED tags.

        Mostly internal to column mapper related code
    """
    Unknown = None
    # Do not return this column at all
    Ignore = "ignore"
    # This column is a category with a list of possible values to replace with hed strings.
    Categorical = "categorical"
    # This column has a value(eg filename) that is added to a hed tag in place of a # sign.
    Value = "value"
    # Return this column exactly as given, it is HED tags.
    HEDTags = "hed_tags"


class ColumnMetadata:
    """ Column in a ColumnMapper. """

    def __init__(self, column_type=None, name=None, hed_dict=None, column_prefix=None):
        """ A single column entry in the column mapper.

        Parameters:
            column_type (ColumnType or None): How to treat this column when reading data.
            name (str, int, or None): The column_name or column number identifying this column.
                If name is a string, you'll need to use a column map to set the number later.
            hed_dict (dict or str or None): The loaded data (usually from json) for the given def
                                     For category columns, this is a dict.
                                     For value columns, it's a string.
            column_prefix (str or None): If present, prepend the given column_prefix to all hed tags in the columns.
                Only works on ColumnType HedTags.

        Notes:
            - Each column from which data is retrieved must have a ColumnMetadata representing its contents.
            - The column_prefix dictionaries are used when the column is processed.
        """
        if hed_dict is None:
            hed_dict = {}

        self.column_type = column_type
        self.column_name = name
        self.column_prefix = column_prefix
        self._hed_dict = hed_dict

    @property
    def hed_dict(self):
        """ The hed strings for any given entry.

        Returns:
            dict or str: A string or dict of strings for this column

        """
        return self._hed_dict

    def _get_category_hed_string(self, category):
        """ Fetch the hed string for a category key.

        Parameters:
            category (str): The category key to retrieve the string from.

        Returns:
            str: The hed string for a given category entry in a category column.

        """
        if self.column_type != ColumnType.Categorical:
            return None

        return self._hed_dict.get(category, None)

    def _get_value_hed_string(self):
        """ Fetch the hed string in a value column.

        Returns:
            str: The hed string for a given value column.

        """
        if self.column_type != ColumnType.Value:
            return None

        return self._hed_dict

    def expand(self, input_text):
        """ Expand text using the rules for this column.

        Parameters:
            input_text (str): Text to expand (generally from a single cell in a spreadsheet).

        Returns:
            str or None: The expanded column as a hed_string.
            str or dict: If this is a string, contains the name of this column
                as an attribute. If the first return value is None, this is an error message dictionary.

        Notes:
            - Examples are adding name_prefix, inserting a column hed_string from a category key, etc.

        """
        column_type = self.column_type

        if column_type == ColumnType.Categorical:
            final_text = self._get_category_hed_string(input_text)
            if final_text:
                return HedString(final_text), False
            else:
                return None, ErrorHandler.format_error(ValidationErrors.HED_SIDECAR_KEY_MISSING, invalid_key=input_text,
                                                       category_keys=list(self._hed_dict.keys()))
        elif column_type == ColumnType.Value:
            prelim_text = self._get_value_hed_string()
            final_text = prelim_text.replace("#", input_text)
            return HedString(final_text), False
        elif column_type == ColumnType.HEDTags:
            hed_string_obj = HedString(input_text)
            self._prepend_required_prefix(hed_string_obj, self.column_prefix)
            return hed_string_obj, False
        elif column_type == ColumnType.Ignore:
            return None, False

        return None, {"error_type": "INTERNAL_ERROR"}

    @staticmethod
    def _prepend_required_prefix(required_tag_column_tags, required_tag_prefix):
        """ Prepend the tag paths to the required tag column tags that need them.

        Parameters:
            required_tag_column_tags (HedString): A string containing HED tags associated with a
                required tag column that may need a tag name_prefix prepended to its tags.
            required_tag_prefix (str): A string that will be added if missing to any given tag.
        """
        if not required_tag_prefix:
            return required_tag_column_tags

        for tag in required_tag_column_tags.get_all_tags():
            tag.add_prefix_if_needed(required_tag_prefix)

        return required_tag_column_tags

    def remove_prefix(self, original_tag, current_tag_text):
        """ Remove column_prefix if present from tag.

        Parameters:
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
    def expected_pound_sign_count(column_type):
        """ Return how many pound signs a column string should have.

        Parameters:
            column_type(ColumnType): The type of the column

        Returns:
            tuple:
                expected_count(int): The expected count.  0 or 1
                error_type(str): The type of the error we should issue
        """
        if column_type == ColumnType.Value:
            expected_count = 1
            error_type = SidecarErrors.INVALID_POUND_SIGNS_VALUE
        elif column_type == ColumnType.HEDTags or column_type == ColumnType.Categorical:
            expected_count = 0
            error_type = SidecarErrors.INVALID_POUND_SIGNS_CATEGORY
        else:
            return 0, None
        return expected_count, error_type
