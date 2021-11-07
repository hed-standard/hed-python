import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.map_utils import get_new_dataframe, get_key_hash, get_row_hash, remove_quotes, separate_columns


class KeyTemplate:
    """A class to handle keeping track of unique keys (which could be tuples."""

    def __init__(self, columns, name=''):
        """ Class stores base data for doing event remapping.

        Args:
            columns (list):       List of columns (assumed to be from a DataFrame or tsv file)
            name (str):           Name associated with this dictionary.

        """

        if not columns:
            raise HedFileError("ColumnsEmpty", "KeyTemplate key columns must exist", "")
        self.columns = columns.copy()
        self.name = name
        self.col_map = pd.DataFrame(columns=self.columns)
        self.map_dict = {}
        self.count_dict = {}

    def make_template(self, additional_cols=[]):
        if additional_cols and set(self.columns).intersection(additional_cols):
            raise HedFileError("AdditionalColumnsNotDisjoint",
                               f"Additional columns {str(additional_cols)} must be disjoint from \
                                {str(self.columns)} must be disjoint", "")
        df = pd.DataFrame(columns=self.columns+additional_cols)
        df[self.columns] = self.col_map[self.columns].values
        if additional_cols:
            df[additional_cols] = 'n/a'
        return df

    def update_by_tuple(self, key_tuple):
        key_hash = get_key_hash(key_tuple)
        if key_hash not in self.map_dict:
            self.map_dict[key_hash] = len(self.col_map)
            new_row = pd.Series(list(key_tuple), index=self.columns)
            self.col_map = self.col_map.append(new_row, ignore_index=True)
            self.count_dict[key_hash] = 0
        self.count_dict[key_hash] += 1

    def update(self, data):
        """ Takes a dataframe containing an key map and updates the existing map

        Args:
            data (str or DataFrame):        File name or DataFrame containing event-type data.

        """

        df = get_new_dataframe(data)
        remove_quotes(df)
        col_list = df.columns.values.tolist()
        cols_present, cols_missing = separate_columns(col_list, self.columns)
        base_df = pd.DataFrame(columns=self.columns)
        base_df[cols_present] = df[cols_present].values
        base_df[cols_missing] = 'n/a'
        self._update(base_df)

    def _update(self, base_df):
        """ Takes DataFrame objects containing keys

        Args:
            base_df (DataFrame):       DataFrame of consisting of the columns in the KeyMap
        """

        for index, row in base_df.iterrows():
            key = get_row_hash(row, self.columns)
            if key not in self.map_dict:
                self.map_dict[key] = len(self.col_map)
                self.col_map = self.col_map.append(row[self.columns], ignore_index=True)
                self.count_dict[key] = 0
            self.count_dict[key] += 1

    def resort(self):
        self.col_map.sort_values(by=self.columns, inplace=True, ignore_index=True)
        for index, row in self.col_map.iterrows():
            key_hash = get_row_hash(row, self.columns)
            self.map_dict[key_hash] = index

    def print(self):
        print(f"Counts for key [{str(self.columns)}]:")
        for index, row in self.col_map.iterrows():
            key_hash = get_row_hash(row, self.columns)
            print(f"{str(list(row.values))}\t{self.count_dict[key_hash]}")
