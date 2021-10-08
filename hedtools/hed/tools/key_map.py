import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.map_utils import get_new_dataframe, get_row_hash, remove_quotes, separate_columns


class KeyMap:
    """A class to handle extraction of unique column values and to remap columns."""

    def __init__(self, key_cols, target_cols=None, name=''):
        """ Class stores base data for doing event remapping.

        Args:
            key_cols (list):       List of columns to be replaced (assumed in the DataFrame)
            target_cols(list):     List of replacement columns (assumed to not be in the DataFrame)
            name (str):            Name associated with this remap (usually a pathname of the events file).

        """

        if not key_cols:
            raise HedFileError("KeyColumnsEmpty", "KeyMap key columns must exist", "")
        self.key_cols = key_cols.copy()
        if target_cols and set(key_cols).intersection(target_cols):
            raise HedFileError("KeyTargetNotDisjoint",
                               f"Key cols {str(key_cols)} and target cols {str(target_cols)} must be disjoint", "")
        elif target_cols:
            self.target_cols = target_cols.copy()
        else:
            self.target_cols = []
        self.name = name
        self.columns = self.key_cols + self.target_cols
        self.col_map = pd.DataFrame(columns=self.columns)
        self.map_dict = {}

    def lookup_row(self, row):
        """ Extracts the column key from row and returns the position.

        Args:
            row (Series):          A Pandas Series corresponding to one row of a DataFrame representing events

        Returns:
            tuple has

        """
        key = row[self.key_cols]
        key_hash = hash(tuple(key))
        if key_hash in self.map_dict:
            key_value = self.map_dict[key_hash]
        else:
            key_value = None
        return key_hash, key_value

    def remap(self, data):
        """ Takes a dataframe or filename and remaps the columns

        Args:
            data (DataFrame, str) :        Data whose columns are to be remapped

        Returns:
            DataFrame                      New dataframe with columns remapped
            list                           List of row numbers that had no correspondence in the mapping
        """

        df_new = get_new_dataframe(data)
        remove_quotes(df_new)
        present_keys, missing_keys = separate_columns(df_new.columns.values.tolist(), self.key_cols)
        if missing_keys:
            raise HedFileError("MissingKeys", f"File must have key columns {str(self.key_cols)}", "")
        df_new[self.target_cols] = 'n/a'
        missing_indices = self._remap(df_new)
        return df_new, missing_indices

    def _remap(self, df):
        """ Utility method that iterates through df to do the replacements

        Args:
            df (DataFrame):         DataFrame in which to perform the mapping

        Returns:
            list                           List of row numbers that had no correspondence in the mapping
        """

        missing_indices = []
        for index, row in df.iterrows():
            key = get_row_hash(row, self.key_cols)
            key_value = self.map_dict.get(key, None)
            if key_value:
                result = self.col_map.iloc[key_value]
                row[self.target_cols] = result[self.target_cols].values
                df.iloc[index] = row
            else:
                missing_indices.append(index)
        return missing_indices

    def update(self, data):
        """ Updates the existing map with information from data.

        Args:
            data (DataFrame or str):     DataFrame or filename of an events file or event map

        Returns:
            list                   Indices of duplicates
        """
        df = get_new_dataframe(data)
        remove_quotes(df)
        col_list = df.columns.values.tolist()
        keys_present, keys_missing = separate_columns(col_list, self.key_cols)
        if keys_missing:
            raise HedFileError("MissingKeyColumn",
                               f"make_template data does not have key columns {str(keys_missing)}", "")
        base_df = pd.DataFrame(columns=self.columns)
        base_df[self.key_cols] = df[self.key_cols].values
        targets_present, targets_missing = separate_columns(col_list, self.target_cols)
        if targets_present:
            base_df[targets_present] = df[targets_present].values
        if targets_missing:
            base_df[targets_missing] = 'n/a'
        return self._update(base_df)

    def _update(self, base_df):
        """ Takes DataFrame objects containing keys and DataFrame containing targets and overwrites existing keys

        Args:
            base_df (DataFrame):       DataFrame of consisting of the columns in the KeyMap

        Returns:
            duplicate_indices (list):         List of key positions that were duplicated
        """

        duplicate_indices = []
        for index, row in base_df.iterrows():
            key = get_row_hash(row, self.key_cols)
            if key not in self.map_dict:
                self.map_dict[key] = len(self.col_map)
                self.col_map = self.col_map.append(row, ignore_index=True)
            else:
                duplicate_indices.append(index)
        return duplicate_indices
