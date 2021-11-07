from pandas import DataFrame
import re
from hed.errors.exceptions import HedFileError


class SidecarMap:
    """A class to parse bids style spreadsheets into a more general format."""

    def __init__(self, header_char="*"):
        """ Takes representing an event file and creates a template for remapping.

        Args:
            header_char (str):     The character used to construct and recognize headers


        """
        self.header_char = header_char

    def flatten(self, sidecar, col_names=None):
        """ Takes a sidecar dictionary and returns a two-column flattened tsv version of the HED portions

        This form of flatten produces a result that is slightly different from the version produced
        by flatten_hed in that it has a header separator after each dictionary is flattened
        because it supports arbitrary levels of nesting rather than the maximum of two levels
        for HED entries.

        Args:
            sidecar (dict):     A dictionary conforming to BIDS JSON events sidecar format.
            col_names (list):   A list of the cols to include in the flattened side car.

        Returns:
            dataframe containing two columns corresponding to a flattened tsv.

        """

        if not isinstance(sidecar, dict):
            raise HedFileError("BadSidecar", f"flatten sidecar must have a sidecar dictionary not [{str(sidecar)}]", "")
        sidecar_keys = sidecar.keys()
        if not col_names:
            col_names = sidecar_keys
        keys = []
        values = []

        for col_key, col_dict in sidecar.items():
            if col_key not in col_names:
                continue
            elif isinstance(col_dict, str):
                keys.append(col_key)
                values.append(col_dict)
                continue
            col_keys, col_values = self.flatten_col(col_key, col_dict)
            keys = keys + col_keys
            values = values + col_values

        data = {"column": keys, "HED": values}
        dataframe = DataFrame(data)
        return dataframe

    def flatten_col(self, col_key, col_dict, append_header=True):
        header = self.get_marked_key(col_key, 1)
        [next_keys, next_values] = self.flatten_col_dict(col_dict)
        col_keys = [header] + next_keys
        col_values = ['n/a'] + next_values
        if append_header:
            col_keys = col_keys + [header]
            col_values = col_values + ['n/a']
        return col_keys, col_values

    def flatten_col_dict(self, column_dict, marker_level=2):
        if not isinstance(column_dict, dict):
            raise HedFileError("UnsupportedJSONValue",
                               f"[{str(column_dict)}] format not in supported by flatten", "")
        keys = []
        values = []
        for key, value in column_dict.items():
            if isinstance(value, str):
                keys.append(key)
                values.append(value)
            elif isinstance(value, dict):
                header = self.get_marked_key(key, marker_level)
                [next_keys, next_values] = self.flatten_col_dict(value, marker_level=marker_level + 1)
                keys = keys + [header] + next_keys + [header]
                values = values + ['n/a'] + next_values + ['n/a']
            else:
                raise HedFileError("UnsupportedJSONValue", f"[{str(value)}] should be a string or dictionary", "")
        return keys, values

    def flatten_hed(self, sidecar, col_names=None):
        """ Takes a sidecar dictionary and returns a two-column flattened tsv version of the HED portions

        Args:
            sidecar (dict):     A dictionary conforming to BIDS JSON events sidecar format.
            col_names (list):   A list of the cols to include in the flattened side car.

        Returns:
            dataframe containing two columns corresponding to a flattened tsv.

        """

        if not isinstance(sidecar, dict):
            raise HedFileError("BadSidecar", f"flatten sidecar must have a sidecar dictionary not [{str(sidecar)}]", "")
        sidecar_keys = sidecar.keys()
        if not col_names:
            col_names = sidecar_keys
        keys = []
        values = []

        for col_key, col_dict in sidecar.items():
            if col_key not in col_names or 'HED' not in col_dict:
                continue
            next_keys, next_values = self.flatten_hed_value(col_key, col_dict['HED'])
            keys = keys + next_keys
            values = values + next_values
        data = {"column": keys, "HED": values}
        dataframe = DataFrame(data)
        return dataframe

    def flatten_hed_value(self, col_key, hed_target):
        header = self.get_marked_key(col_key, 1)
        if isinstance(hed_target, str):
            keys = [header]
            values = [hed_target]
        else:
            keys, values = self.flatten_col(col_key, hed_target, False)
        return keys, values

    def get_marked_key(self, key, marker_level):
        if marker_level == 0:
            marker = ""
        else:
            marker = f"{('_' * marker_level)}{self.header_char}{('_' * marker_level)}"
        return marker + key + marker

    def get_unmarked_key(self, key):
        reg = f"[_]+[{self.header_char}]"
        matched = re.search(reg, key)
        if not matched:
            return key
        match_tag = matched.group()
        match_tag = match_tag[:-1] + self.header_char + match_tag[:-1]
        if key.startswith(match_tag) and key.endswith(match_tag) and len(key) > 2*len(match_tag):
            return key[len(match_tag):-len(match_tag)]
        else:
            return None

    def unflatten(self, dataframe):
        """ Takes a sidecar dictionary and returns a two-column flattened tsv version of the HED portions

        Args:
            dataframe (DataFrame): A Pandas DataFrame containing flattened sidecar.

        Returns:
            dict compatible with BIDS JSON events.

        """

        dict_list = [{}]
        key_list = []

        for index, row in dataframe.iterrows():
            key = row['column']
            value = row["HED"]
            unmarked_key = self.get_unmarked_key(key)
            if not unmarked_key:
                raise HedFileError("unflatten", f"Empty or invalid flattened sidecar key {str(key)}", "")
            elif unmarked_key == key:
                dict_list[-1][key] = value
            elif len(key_list) > 0 and key_list[-1] == key:  # End of dictionary
                key_list = key_list[:-1]
                current_dict = dict_list[-1]
                dict_list = dict_list[:-1]
                dict_list[-1][unmarked_key] = current_dict
            else:  # New key corresponding to new dictionary
                key_list.append(key)
                dict_list.append({})
        return dict_list[0]

    def unflatten_hed(self, dataframe):
        """ Takes a sidecar dictionary and returns a two-column flattened tsv version of the HED portions

        Args:
            dataframe (DataFrame): A Pandas DataFrame containing flattened sidecar.

        Returns:
            dict compatible with BIDS JSON events.

        """

        master_dict = {}
        current_dict = {}
        for index, row in dataframe.iterrows():
            key = row['column']
            value = row["HED"]
            unmarked_key = self.get_unmarked_key(key)
            if not unmarked_key:
                raise HedFileError("unflatten", f"Empty or invalid flattened sidecar key {str(key)}", "")
            if unmarked_key == key:
                current_dict[key] = value
            elif value != 'n/a':
                master_dict[unmarked_key] = {"HED": value}
                current_dict = {}
            else:
                current_dict = {}
                master_dict[unmarked_key] = {"HED": current_dict}

        return master_dict

    @staticmethod
    def get_key_value(key, column_values, categorical=True):
        """  Creates the sidecar value dictionary for a given column name in an events.tsv file

        Args:
            key (str):   Name of the column in the events file
            column_values (list):    List of column values in the event file if categorical
            categorical (bool):      If true the value_columns is a value.

         Returns:
             dict   A dictionary representing the extracted values for a given column name.
        """

        key_value = {"Description":  f"Description for {key}", "HED": ''}
        if not column_values:
            return key_value
        elif categorical:
            levels = {}
            hed = {}
            for val_key in column_values:
                levels[val_key] = f"Level for {val_key}"
                hed[val_key] = f"Description/Tags for {val_key}"
            key_value["Levels"] = levels
        else:
            hed = "Label/#"
        key_value["HED"] = hed
        return key_value

    @staticmethod
    def get_sidecar_dict(columns_info, selected_columns=None):
        """  Extracts a sidecar dictionary suitable for direct conversion to JSON sidecar.

        Args:
            columns_info (dict): Dictionary with column names of an events file as keys and values that are dictionaries
                                 of unique column entries.

            selected_columns (list): A list of column names that should be included


        Returns:
            dict suitable:return: A dictionary suitable for conversion to JSON sidecar.
            :rtype: dict
            :return: A list of issues if errors, otherwise empty.
            :rtype: list
        """

        hed_dict = {}
        issues = []
        if not selected_columns:
            return hed_dict, [{'code': 'HED_EMPTY_COLUMN_SELECTION', 'severity': 1,
                               'message': "Must select at least one column"}]
        elif not columns_info:
            return hed_dict, [{'code': 'HED_NO_COLUMNS', 'severity': 1,
                               'message': "Must have columns to do extraction"}]
        for key in selected_columns:
            if key not in columns_info:
                issues += [{'code': 'HED_INVALID_COLUMN_NAME', 'severity': 1,
                            'message': f"{key} is not a valid column name to select"}]
            else:
                hed_dict[key] = SidecarMap.get_key_value(key, columns_info[key], selected_columns[key])
        return hed_dict, issues
