""" Column type for a column in a ColumnMapper. """
from enum import Enum
from typing import Union

from hed.errors.error_types import SidecarErrors
import pandas as pd
import copy


class ColumnType(Enum):
    """ The overall column_type of a column in column mapper, e.g. treat it as HED tags.

        Mostly internal to column mapper related code
    """
    Unknown = None
    # Do not return this column at all
    Ignore = "ignore"
    # This column is a category with a list of possible values to replace with HED strings.
    Categorical = "categorical"
    # This column has a value(e.g. filename) that is added to a HED tag in place of a # sign.
    Value = "value"
    # Return this column exactly as given, it is HED tags.
    HEDTags = "hed_tags"


class ColumnMetadata:
    """ Column in a ColumnMapper. """

    def __init__(self, column_type=None, name=None, source=None):
        """ A single column entry in the column mapper.

        Parameters:
            column_type (ColumnType or None): How to treat this column when reading data.
            name (str, int, or None): The column_name or column number identifying this column.
                If name is a string, you'll need to use a column map to set the number later.
            source (dict or str or None): Either the entire loaded json sidecar or a single HED string.
        """
        self.column_name = name
        self._source = source
        if column_type is None:
            column_type = self._detect_column_type(self.source_dict)
        self.column_type = column_type

    @property
    def hed_dict(self) -> Union[dict, str]:
        """ The HED strings for any given entry.

        Returns:
            Union[dict, str]: A string or dict of strings for this column.

        """
        if self._source is None or isinstance(self._source, str):
            return self._source
        return self._source[self.column_name].get("HED", {})

    @property
    def source_dict(self) -> Union[dict, str]:
        """ The raw dict for this entry(if it exists).

        Returns:
            Union[dict, str]: A string or dict of strings for this column.
        """
        if self._source is None or isinstance(self._source, str):
            return {"HED": self._source}
        return self._source[self.column_name]

    def get_hed_strings(self) -> pd.Series:
        """ Return the HED strings for this entry as a series.

        Returns:
            pd.Series: The HED strings for this series.(potentially empty).
        """
        if not self.column_type:
            return pd.Series(dtype=str)

        series = pd.Series(self.hed_dict, dtype=str)

        return series

    def set_hed_strings(self, new_strings) -> bool:
        """ Set the HED strings for this entry.

        Parameters:
            new_strings (pd.Series, dict, or str): The HED strings to set.
                This should generally be the return value from get_hed_strings.

        Returns:
            bool: True if the strings were successfully set, False otherwise.
        """
        if new_strings is None:
            return False

        if not self.column_type:
            return False

        if isinstance(new_strings, pd.Series):
            if self.column_type == ColumnType.Categorical:
                new_strings = new_strings.to_dict()
            elif new_strings.empty:
                return False
            else:
                new_strings = new_strings.iloc[0]

        self._source[self.column_name]["HED"] = new_strings

        return True

    @staticmethod
    def _detect_column_type(dict_for_entry, basic_validation=True):
        """ Determine the ColumnType of a given json entry.

        Parameters:
            dict_for_entry (dict): The loaded json entry a specific column.
                Generally has a "HED" entry among other optional ones.
            basic_validation (bool): If False, does not verify past "HED" exists and the type
                                     This is used to issue more precise errors that are normally just silently ignored,
                                     but also not crash.
        Returns:
            ColumnType: The determined type of given column.  Returns None if unknown.

        """
        if not dict_for_entry or not isinstance(dict_for_entry, dict):
            return ColumnType.Ignore

        minimum_required_keys = ("HED",)
        if not set(minimum_required_keys).issubset(dict_for_entry.keys()):
            return ColumnType.Ignore

        hed_entry = dict_for_entry["HED"]
        if isinstance(hed_entry, dict):
            if basic_validation and not all(isinstance(entry, str) for entry in hed_entry.values()):
                return None
            return ColumnType.Categorical

        if not isinstance(hed_entry, str):
            return None

        if basic_validation and "#" not in dict_for_entry["HED"]:
            return None

        return ColumnType.Value

    @staticmethod
    def expected_pound_sign_count(column_type)-> tuple[int, int]:
        """ Return how many pound signs a column string should have.

        Parameters:
            column_type (ColumnType): The type of the column.

        Returns:
            tuple[int, int]:
                - The expected count:  0 or 1.
                - The type of the error we should issue.
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

    def _get_unvalidated_data(self):
        """Returns a copy with less preliminary validation done(such as verifying all data types)"""
        return_copy = copy.deepcopy(self)
        return_copy.column_type = ColumnMetadata._detect_column_type(dict_for_entry=return_copy.source_dict,
                                                                     basic_validation=False)
        return return_copy
