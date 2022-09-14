import pandas as pd
from hed import HedFileError


class HedTypeFactors:
    """ Holds index of positions for a variable type for one tabular file. """

    ALLOWED_ENCODINGS = ("categorical", "one-hot")

    def __init__(self, variable_value, number_elements, variable_type="condition-variable"):
        """ Constructor for HedTypeFactors.

        Args:
            variable_value (str): The value of the type summarized by this class.
            number_elements (int): Number of elements in the data column
            variable_type (str):  Lowercase string corresponding to a HED tag which has a takes value child.

        """

        self.variable_value = variable_value
        self.number_elements = number_elements
        self.variable_type = variable_type.lower()
        self.levels = {}
        self.direct_indices = {}

    def __str__(self):
        return f"{self.variable_value}[{self.variable_type}]: {self.number_elements} elements " + \
               f"{str(self.levels)} levels {len(self.direct_indices)} references"

    def get_factors(self, factor_encoding="one-hot"):
        df = pd.DataFrame(0, index=range(self.number_elements), columns=[self.variable_value])
        df.loc[list(self.direct_indices.keys()), [self.variable_value]] = 1
        if not self.levels:
            return df

        levels = list(self.levels.keys())
        levels_list = [f"{self.variable_value}.{level}" for level in levels]
        df_levels = pd.DataFrame(0, index=range(self.number_elements), columns=levels_list)
        for index, level in enumerate(levels):
            index_keys = list(self.levels[level].keys())
            df_levels.loc[index_keys, [levels_list[index]]] = 1
        factors = pd.concat([df, df_levels], axis=1)
        if factor_encoding == "one-hot":
            return factors
        sum_factors = factors.sum(axis=1)
        if sum_factors.max() > 1:
            raise HedFileError("MultipleFactorSameEvent",
                               f"{self.variable_value} has multiple occurrences at index{sum_factors.idxmax()}", "")
        if factor_encoding == "categorical":
            return self.factors_to_vector(factors, levels)
        else:
            raise ValueError("BadFactorEncoding",
                             f"{factor_encoding} is not in the allowed encodings: {str(self.ALLOWED_ENCODINGS)}")

    def factors_to_vector(self, factors, levels):
        df = pd.DataFrame('n/a', index=range(len(factors.index)), columns=[self.variable_value])
        for index, row in factors.iterrows():
            if row[self.variable_value]:
                df.at[index, self.variable_value] = self.variable_value
                continue
            for level in levels:
                if row[f"{self.variable_value}.{level}"]:
                    df.at[index, self.variable_value] = level
                    break
        return df

    def get_summary(self, full=True):
        count_list = [0] * self.number_elements
        for index in list(self.direct_indices.keys()):
            count_list[index] = count_list[index] + 1
        for level, cond in self.levels.items():
            for index, item in cond.items():
                count_list[index] = count_list[index] + 1
        number_events, number_multiple, max_multiple = self.count_events(count_list)
        summary = {'name': self.variable_value, 'variable_type': self.variable_type, 'levels': len(self.levels.keys()),
                   'direct_references': len(self.direct_indices.keys()),
                   'total_events': self.number_elements, 'events': number_events,
                   'multiple_events': number_multiple, 'multiple_event_maximum': max_multiple}
        if full:
            summary['level_counts'] = self._get_level_counts()
        return summary

    def _get_level_counts(self):
        count_dict = {}
        for level, cond in self.levels.items():
            count_dict[level] = len(cond.values())
        return count_dict

    @staticmethod
    def count_events(count_list):
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
