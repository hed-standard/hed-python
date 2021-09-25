from pandas import DataFrame
import re
from hed.errors.exceptions import HedFileError


class SidecarRemap:
    """A class to parse bids style spreadsheets into a more general format."""

    def __init__(self, header_char="*"):
        """ Takes representing an event file and creates a template for remapping.

        Args:
            header_char (str):     The character used to construct and recognize headers


        """
        self.header_char = header_char

    def flatten(self, sidecar, col_names=None):
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
            if col_key not in col_names:
                continue
            elif isinstance(col_dict, str):
                keys.append(col_key)
                values.append(col_dict)
                continue
            col_keys, col_values = self.flatten_col(col_key, col_dict)
            keys = keys + col_keys
            values = values + col_values

        data = {"keys": keys, "values": values}
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
            hed_target = col_dict['HED']
            header = self.get_marked_key(col_key, 1)

            if isinstance(hed_target, str):
                keys.append(header)
                values.append(hed_target)
            else:
                col_keys, col_values = self.flatten_col(col_key, hed_target, False)
                keys = keys + col_keys
                values = values +  col_values

        data = {"keys": keys, "values": values}
        dataframe = DataFrame(data)
        return dataframe

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
            key = row['keys']
            value = row["values"]
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
    def get_sidecar_dict(columns_info, columns_selected):
        """  Extracts a sidecar dictionary suitable for direct conversion to JSON sidecar.
            :param columns_info: A dict with column names of an events file as keys and values that are dictionaries
                of unique column entries.
            :type columns_info: dict
            :param columns_selected: A dict with keys that are names of columns that should be documented
                in the JSON sidecar.
            :type columns_selected: list
            :return: A dictionary suitable for conversion to JSON sidecar.
            :rtype: dict
            :return: A list of issues if errors, otherwise empty.
            :rtype: list
        """

        hed_dict = {}
        issues = []
        if not columns_selected:
            return hed_dict, [{'code': 'HED_EMPTY_COLUMN_SELECTION', 'severity': 1,
                               'message': "Must select at least one column"}]
        elif not columns_info:
            return hed_dict, [{'code': 'HED_NO_COLUMNS', 'severity': 1,
                               'message': "Must have columns to do extraction"}]
        for key in columns_selected:
            if key not in columns_info:
                issues += [{'code': 'HED_INVALID_COLUMN_NAME', 'severity': 1,
                            'message': f"{key} is not a valid column name to select"}]
            else:
                hed_dict[key] = SidecarRemap.get_key_value(key, columns_info[key], columns_selected[key])
        return hed_dict, issues
