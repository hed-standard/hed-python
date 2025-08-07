""" Manager for factor information for a columnar file. """

import pandas as pd
from hed.errors.exceptions import HedFileError


class HedTypeFactors:
    """ Holds index of positions for a variable type for A columnar file. """

    ALLOWED_ENCODINGS = ("categorical", "one-hot")

    def __init__(self, type_tag, type_value, number_elements):
        """ Constructor for HedTypeFactors.

        Parameters:
            type_tag (str):  Lowercase string corresponding to a HED tag which has a takes value child.
            type_value (str): The value of the type summarized by this class.
            number_elements (int): Number of elements in the data column

        """

        self.type_value = type_value
        self.number_elements = number_elements
        self.type_tag = type_tag.casefold()
        self.levels = {}
        self.direct_indices = {}

    def __str__(self):
        return f"[{self.type_value},{self.type_tag}]: {self.number_elements} elements " + \
            f"{str(self.levels)} levels {len(self.direct_indices)} references"

    def get_factors(self, factor_encoding="one-hot"):
        """ Return a DataFrame of factor vectors for this type factor.

        Parameters:
            factor_encoding (str):   Specifies type of factor encoding (one-hot or categorical).

        Returns:
            pd.DataFrame:   DataFrame containing the factor vectors as the columns.

        """

        if not self.levels:
            df = pd.DataFrame(0, index=range(self.number_elements), columns=[self.type_value])
            df.loc[list(self.direct_indices.keys()), [self.type_value]] = 1
            return df

        levels = list(self.levels.keys())
        levels_list = [f"{self.type_value}.{level}" for level in levels]
        factors = pd.DataFrame(0, index=range(self.number_elements), columns=levels_list)
        for index, level in enumerate(levels):
            index_keys = list(self.levels[level].keys())
            factors.loc[index_keys, [levels_list[index]]] = 1
        if factor_encoding == "one-hot":
            return factors
        sum_factors = factors.sum(axis=1)
        if factor_encoding == "categorical" and sum_factors.max() > 1:
            raise HedFileError("MultipleFactorSameEvent",
                               f"{self.type_value} has multiple occurrences at index {sum_factors.idxmax()}", "")
        elif factor_encoding == "categorical":
            return self._one_hot_to_categorical(factors, levels)
        else:
            raise ValueError("BadFactorEncoding",
                             f"{factor_encoding} is not in the allowed encodings: {str(self.ALLOWED_ENCODINGS)}")

    def _one_hot_to_categorical(self, factors, levels):
        """ Convert factors to one-hot representation.

        Parameters:
            factors (DataFrame):  Dataframe containing categorical values.
            levels (list):  List of categorical columns to convert.

        Return:
            pd.ataFrame:  Contains one-hot representation of requested levels.

        """
        df = pd.DataFrame('n/a', index=range(len(factors.index)), columns=[self.type_value])
        for index, row in factors.iterrows():
            if self.type_value in row.index and row[self.type_value]:
                df.at[index, self.type_value] = self.type_value
                continue
            for level in levels:
                level_str = f"{self.type_value}.{level.casefold()}"
                if level_str in row.index and row[level_str]:
                    df.at[index, self.type_value] = level.casefold()
                    break
        return df

    def get_summary(self):
        """ Return the summary of the type tag value as a dictionary.

        Returns:
            dict:  Contains the summary.

        """
        count_list = [0] * self.number_elements
        for index in list(self.direct_indices.keys()):
            count_list[index] = count_list[index] + 1
        for level, cond in self.levels.items():
            for index, item in cond.items():
                count_list[index] = count_list[index] + 1
        number_events, number_multiple, max_multiple = self._count_level_events(count_list)
        summary = {'type_value': self.type_value, 'type_tag': self.type_tag,
                   'levels': len(self.levels.keys()), 'direct_references': len(self.direct_indices.keys()),
                   'total_events': self.number_elements, 'events': number_events,
                   'events_with_multiple_refs': number_multiple, 'max_refs_per_event': max_multiple,
                   'level_counts': self._get_level_counts()}
        return summary

    def _get_level_counts(self):
        """ Return the level counts as a dictionary.

        Returns:
            dict:  Dictionary with counts of level values.

        """
        count_dict = {}
        for level, cond in self.levels.items():
            count_dict[level] = len(cond.values())
        return count_dict

    @staticmethod
    def _count_level_events(count_list):
        """ Count the number of events and multiples in a list.

        Parameters:
            count_list (list): list of integers of the number of times a level occurs in an event.

        Returns:
            int:   Number of events this level
        """
        if not len(count_list):
            return 0, 0, None
        number_events = 0
        number_multiple = 0
        max_multiple = count_list[0]
        for index, count in enumerate(count_list):
            if count_list[index] > 0:
                number_events = number_events + 1
            if count_list[index] > 1:
                number_multiple = number_multiple + 1
            if count_list[index] > max_multiple:
                max_multiple = count_list[index]
        return number_events, number_multiple, max_multiple
