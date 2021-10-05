import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.map_utils import get_new_dataframe, separate_columns
from hed.tools import KeyDict


class KeyMap1:
    """A class to handle extraction of unique column values and to remap columns.

    Internally, the
    """

    def __init__(self, data, key_cols, target_cols, name=''):
        """ Class stores base data for doing event remapping.

        Args:
            data (str or DataFrame):
            key_cols (list):          List of columns to be replaced (assumed in the DataFrame)
            target_cols(list):        List of replacement columns (assumed to not be in the DataFrame)
            name (str):               Name associated with this remap (usually a pathname of the events file).

        """

        self.key_dict = KeyDict(key_cols)
        self.target_dict = KeyDict(target_cols)
        if set(key_cols).intersection(target_cols):
            raise HedFileError("KeyTargetNotDisjoint",
                               f"Key cols {str(key_cols)} and target cols {str(target_cols)} must be disjoint", "")
        self.name = name
        self.mapping = {}
        self.create_mapping(data)

    def remap_keys(self, data):
        """ Takes a dataframe or filename and remaps the columns

        Args:
            data (DataFrame, str) :        Data whose columns are to be remapped

        Returns:
            DataFrame                      New dataframe with columns remapped
            list                           List of row numbers that had no correspondence in the mapping
        """

        df_new = get_new_dataframe(data)
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
            key, key_value = self.key_dict.lookup_cols(row)
            if key_value:
                result = self.col_map.iloc[key_value]
                row[self.target_cols] = result[self.target_cols].values
                df.iloc[index] = row
            else:
                missing_indices.append(index)
        return missing_indices

    def create_maping(self, data):
        """ Takes a dataframe containing a key map

        Args:
            df (DataFrame):        Represents mapping

        Returns:
            list                   Indices of duplicates
        """
        df_new = get_new_dataframe(data)
        col_list = df_new.columns.values.tolist()
        keys_present, keys_missing = separate_columns(col_list, self.key_dict.columns)
        if keys_missing:
            raise HedFileError("MissingKeyColumn",
                               f"make_template data does not have key columns {str(keys_missing)}", "")
        base_df = pd.DataFrame(columns=self.columns)
        base_df[self.key_cols] = df_new[self.key_cols].values
        targets_present, targets_missing = separate_columns(col_list, self.target_cols)
        if targets_present:
            base_df[targets_present] = df_new[targets_present].values
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
            key = self.key_dict.lookup_key(tuple(row))
            key, key_value = self._lookup_cols(row)
            if key not in self.map_dict:
                self.map_dict[key] = len(self.col_map)
                self.col_map = self.col_map.append(row, ignore_index=True)
            else:
                duplicate_indices.append(index)
        return duplicate_indices

        key_df = pd.DataFrame(columns=self.self.key_dict.columns)
        self.key_dict.update(key_df)

        target_df = pd.DataFrame(columns=self.self.target_dict.columns)
        targets_present, targets_missing = separate_columns(col_list, self.target_dict.columns)
        if targets_present:
            target_df[targets_present] = df[targets_present].values
        if targets_missing:
            target_df[targets_missing] = 'n/a'
        self.target_dict.update(target_df)

    def update_map(self, key_df, target_df):
        for index, row in key_df.iterrows():
            key = self.key_dict.lookup_key(tuple(row))
            target = self.target_dict.lookup_key()
