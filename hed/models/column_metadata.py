from enum import Enum
from hed.errors.error_types import SidecarErrors


class ColumnType(Enum):
    """ The overall column_type of a column in column mapper, e.g. treat it as HED tags.

        Mostly internal to column mapper related code
    """
    Unknown = None
    # Do not return this column at all
    Ignore = "ignore"
    # This column is a category with a list of possible values to replace with hed strings.
    Categorical = "categorical"
    # This column has a value(e.g. filename) that is added to a hed tag in place of a # sign.
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
