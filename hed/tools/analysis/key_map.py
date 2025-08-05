""" A map of column value keys into new column values. """

import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.util import data_util


class KeyMap:
    """ A map of unique column values for remapping columns.

    Attributes:
        key_cols (list):  A list of column names that will be hashed into the keys for the map.
        target_cols (list or None):  Optional list of column names that will be inserted into data and later remapped.
        name (str):       An optional name of this remap for identification purposes.

    Notes: This mapping converts all columns in the mapping to strings.
    The remapping does not support other types of columns.

    """

    def __init__(self, key_cols, target_cols=None, name=''):
        """ Information for remapping columns of tabular files.

        Parameters:
            key_cols (list): List of columns to be replaced (assumed in the DataFrame).
            target_cols(list): List of replacement columns (assumed to not be in the DataFrame).
            name (str): Name associated with this remap (usually a pathname of the events file).

        """

        if not key_cols:
            raise ValueError("KEY_COLUMNS_EMPTY", "KeyMap key columns must exist", "")
        self.key_cols = key_cols.copy()
        if target_cols:
            self.target_cols = target_cols.copy()
        else:
            self.target_cols = []
        if set(self.key_cols).intersection(set(self.target_cols)):
            raise ValueError("KEY_AND_TARGET_COLUMNS_NOT_DISJOINT",
                             f"Key cols {str(key_cols)} and target cols {str(target_cols)} must be disjoint", "")
        self.name = name
        self.col_map = pd.DataFrame(columns=self.key_cols + self.target_cols)
        self.map_dict = {}  # Index of key to position in the col_map DataFrame
        self.count_dict = {}  # Keeps a running count of the number of times a key appears in the data

    @property
    def columns(self):
        """ Return the column names of the columns managed by this map.

        Returns:
            list:  Column names of the columns managed by this map.
        """
        return self.key_cols + self.target_cols

    def __str__(self):
        temp_list = [f"{self.name} counts for key [{str(self.key_cols)}]:"]
        for index, row in self.col_map.iterrows():
            key_hash = data_util.get_row_hash(row, self.columns)
            temp_list.append(f"{str(list(row.values))}:\t{self.count_dict[key_hash]}")
        return "\n".join(temp_list)

    def make_template(self, additional_cols=None, show_counts=True):
        """ Return a dataframe template.

        Parameters:
            additional_cols (list or None): Optional list of additional columns to append to the returned dataframe.
            show_counts (bool): If True, number of times each key combination appears is in first column and
                                values are sorted in descending order by.

        Returns:
            DataFrame:  A dataframe containing the template.

        Raises:
            HedFileError: If additional columns are not disjoint from the key columns.

        Notes:
            -  The template consists of the unique key columns in this map plus additional columns.

        """
        if additional_cols and set(self.key_cols).intersection(additional_cols):
            raise HedFileError("AdditionalColumnsNotDisjoint",
                               f"Additional columns {str(additional_cols)} must be disjoint from \
                                {str(self.columns)} must be disjoint", "")
        df = self.col_map[self.key_cols].copy()
        if additional_cols:
            df[additional_cols] = 'n/a'
        if show_counts:
            df.insert(0, 'key_counts', self._get_counts())
            df.sort_values(by=['key_counts'], inplace=True, ignore_index=True, ascending=False)
        return df

    def _get_counts(self):
        """ Return counts for the key column combinations.

        Returns:
            list:  List which is the same length as the col_map containing the counts of the combinations.

        """
        counts = [0 for _ in range(len(self.col_map))]
        for index, row in self.col_map.iterrows():
            key_hash = data_util.get_row_hash(row, self.key_cols)
            counts[index] = self.count_dict[key_hash]
        return counts

    def remap(self, data):
        """ Remap the columns of a dataframe or columnar file.

        Parameters:
            data (DataFrame, str):  Columnar data (either DataFrame or filename) whose columns are to be remapped.

        Returns:
            tuple [DataFrame, list]:
            - New dataframe with columns remapped.
            - List of row numbers that had no correspondence in the mapping.

        Raises:
            HedFileError: If data is missing some of the key columns.

        """

        df_new = data_util.get_new_dataframe(data)
        present_keys, missing_keys = data_util.separate_values(df_new.columns.values.tolist(), self.key_cols)
        if missing_keys:
            raise HedFileError("MissingKeys", f"File must have key columns {str(self.key_cols)}", "")
        self.remove_quotes(df_new, columns=present_keys)
        df_new[self.target_cols] = 'n/a'
        missing_indices = self._remap(df_new)
        return df_new, missing_indices

    def _remap(self, df):
        """ Utility method that does the remapping

        Parameters:
            df (DataFrame):    DataFrame in which to perform the mapping.

        Returns:
            list:  The row numbers that had no correspondence in the mapping.
        """
        key_series = df.apply(lambda row: data_util.get_row_hash(row, self.key_cols), axis=1)
        # Key series now contains row_number: hash for each row in the dataframe

        # Add a column containing the mapped index for each row
        map_series = pd.Series(self.map_dict)  # map_series is hash:row_index for each entry in the map_dict index
        key_values = key_series.map(map_series)  # key_values is df_row_number:map_dict_index
        # e.g. a key_value entry of 0:79 means row 0 maps to row 79 in the map_dict

        # This adds the map_dict_index column, to merged_df as a new column "key_value"
        merged_df = df.assign(key_value=key_values.values)

        # Copy all the map_dict data into merged_df as new columns, merging on the map_dict_index number of both
        remapped_df = pd.merge(merged_df, self.col_map, left_on='key_value', right_index=True,
                               suffixes=('', '_new'), how='left').fillna("n/a")

        # Override the original columns with our newly calculated ones
        for col in self.target_cols:
            df[col] = remapped_df[col + '_new']

        # Finally calculate missing indices
        missing_indices = key_series.index[key_values.isna()].tolist()

        return missing_indices

    def resort(self):
        """ Sort the col_map in place by the key columns. """
        self.col_map.sort_values(by=self.key_cols, inplace=True, ignore_index=True)
        for index, row in self.col_map.iterrows():
            key_hash = data_util.get_row_hash(row, self.key_cols)
            self.map_dict[key_hash] = index

    def update(self, data, allow_missing=True):
        """ Update the existing map with information from data.

        Parameters:
            data (DataFrame or str):     DataFrame or filename of an events file or event map.
            allow_missing (bool):        If True allow missing keys and add as n/a columns.

        Raises:
            HedFileError: If there are missing keys and allow_missing is False.

        """
        df = data_util.get_new_dataframe(data)
        col_list = df.columns.values.tolist()
        keys_present, keys_missing = data_util.separate_values(col_list, self.key_cols)
        if keys_missing and not allow_missing:
            raise HedFileError("MissingKeyColumn",
                               f"make_template data does not have key columns {str(keys_missing)}", "")

        base_df = df[keys_present].copy()
        self.remove_quotes(base_df)
        if keys_missing:
            base_df[keys_missing] = 'n/a'
        if self.target_cols:
            base_df[self.target_cols] = 'n/a'
            targets_present, targets_missing = data_util.separate_values(col_list, self.target_cols)
            if targets_present:
                base_df[targets_present] = df[targets_present].values
        self._update(base_df)

    def _update(self, base_df):
        """ Update the dictionary of key values based on information in the dataframe.

        Parameters:
            base_df (DataFrame):       DataFrame of consisting of the columns in the KeyMap

        """

        row_list = []
        next_pos = len(self.col_map)
        for index, row in base_df.iterrows():
            key, pos_update = self._handle_update(row, row_list, next_pos)
            next_pos += pos_update
        if row_list:
            df = pd.DataFrame(row_list)
            # Ignore empty col_map to suppress warning
            col_map = self.col_map if not self.col_map.empty else None
            self.col_map = pd.concat([col_map, df], axis=0, ignore_index=True)

    def _handle_update(self, row, row_list, next_pos):
        """ Update the dictionary and counts of the number of times this combination of key columns appears.

        Parameters:
            row (DataSeries):  Data the values in a row.
            row_list (list):   A list of rows to be appended to hold the unique rows.
            next_pos (int):    Index into the row_list of this row

        Returns:
            tuple[int, int]:
            - the row hash.
            - 1 if new row or 0 otherwise.

        """
        key = data_util.get_row_hash(row, self.key_cols)
        pos_update = 0
        if key not in self.map_dict:
            self.map_dict[key] = next_pos
            row_list.append(row)
            pos_update = 1
            self.count_dict[key] = 0
        self.count_dict[key] = self.count_dict[key] + 1
        return key, pos_update

    @staticmethod
    def remove_quotes(df, columns=None):
        """ Remove quotes from the specified columns and convert to string.

        Parameters:
            df (Dataframe):   Dataframe to process by removing quotes.
            columns (list):  List of column names. If None, all columns are used.

        Notes:
            - Replacement is done in place.
        """

        col_types = df.dtypes
        if not columns:
            columns = df.columns.values.tolist()
        for index, col in enumerate(df.columns):
            if col in columns and col_types.iloc[index] in ['string', 'object']:
                df[col] = df[col].astype(str)
                df.iloc[:, index] = df.iloc[:, index].str.replace('"', '')
                df.iloc[:, index] = df.iloc[:, index].str.replace("'", "")
