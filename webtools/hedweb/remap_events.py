import pandas as pd
from hed.errors.exceptions import HedFileError
from hedweb.remap_utils import extract_dataframe, separate_columns


class RemapEvents:
    """A class to handle extraction of event file column values and remap event file columns."""

    def __init__(self, key_cols, target_cols):
        """ Class stores base data for doing event remapping.

        Args:
            key_cols (list):       List of columns to be replaced (assumed in the DataFrame)
            target_cols(list):     List of replacement columns (assumed to not be in the DataFrame)

        """

        if not key_cols or not target_cols:
            raise HedFileError("KeysOrTargetsEmpty", "EventMap key and target columns must be non empty", "")
        if set(key_cols).intersection(target_cols):
            raise HedFileError("KeyTargetNotDisjoint",
                               f"Key cols {str(key_cols)} and target cols {str(target_cols)} must be disjoint", "")

        self.key_cols = key_cols
        self.target_cols = target_cols
        self.col_map = pd.DataFrame(columns=key_cols+target_cols)
        self.map_dict = {}

    def _lookup_cols(self, row):
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

    def make_template(self, data, keys_unique=False, use_targets=False):
        """ Takes a dataframe representing an event file or template and creates a template for remapping.

        Args:
            data (DataFrame or str):      DataFrame or filename representing an events file
            keys_unique (bool):           If True and the keys in data are not unique, raise an exception
            use_targets (bool):           If True th

        Returns:
            DataFrame containing with a template

        """

        df = extract_dataframe(data)
        if not use_targets:
            df[self.target_cols] = 'n/a'
        new_map = RemapEvents(self.key_cols, self.target_cols)
        new_map.update_map(df, keys_unique)

        df_template = pd.DataFrame(new_map.col_map)
        df_template.sort_values(by=self.key_cols, inplace=True, ignore_index=True)
        return df_template

    def remap_events(self, data):
        """ Takes a dataframe or filename representing event file and remaps the columns

        Args:
            data (DataFrame, str) :        Represents mapping


        Returns:
            DataFrame
        """
        df_new = extract_dataframe(data)
        present_keys, missing_keys = separate_columns(df_new.columns.values.tolist(), self.key_cols)
        if missing_keys:
            raise HedFileError("MissingKeys", f"Events file must have key columns {str(self.key_cols)}", "")

        present_targets, missing_targets = separate_columns(df_new.columns.values.tolist(), self.target_cols)
        if missing_targets:
            df_new[missing_targets] = 'n/a'
        missing_indices = []
        for index, row in df_new.iterrows():
            key, key_value = self._lookup_cols(row)
            if key_value:
                result = self.col_map.iloc[key_value]
                row[self.target_cols] = result[self.target_cols]
                df_new.iloc[index] = row
            else:
                missing_indices.append(index)

        return df_new, missing_indices

    def update_map(self, df, keys_unique=False):
        """ Takes a dataframe containing an event map and updates the existing map

        Args:
            df (DataFrame):        Represents mapping
            keys_unique (bool):    If True, raises an exception if it encounters a key already in dictionary

        """
        keys_present, keys_missing = separate_columns(df.columns.values.tolist(), self.key_cols)
        if keys_missing:
            raise HedFileError("MissingKeyColumn",
                               f"make_template data does not have key columns {str(keys_missing)}", "")
        key_df = df[self.key_cols]
        targets_present, targets_missing = separate_columns(df.columns.values.tolist(), self.target_cols)

        target_df = df[targets_present]
        if targets_missing:
            target_df[targets_missing] = 'n/a'
        target_df = target_df[self.target_cols]
        self._update(key_df, target_df, keys_unique)

    def _update(self, key_df, target_df, keys_unique):
        """ Takes DataFrame objects containing keys and DataFrame containing targets and overwrites existing keys

        Args:
            key_df (DataFrame):       DataFrame of keys
            target_df (DataFrame):    DataFrame of
            keys_unique (bool):       If True raises and exception if a duplicate key is encountered

        """
        base_df = key_df.join(target_df)
        for index, row in base_df.iterrows():
            key, key_value = self._lookup_cols(row)
            if key not in self.map_dict:
                self.map_dict[key] = len(self.col_map)
                self.col_map = self.col_map.append(row, ignore_index=True)
            elif not keys_unique:
                self.col_map.iloc[key_value] = row
            else:
                raise HedFileError("DuplicateKeyNotAllowed",
                                   f"Key {str(key_df.iloc[index])} already in dictionary", "")
