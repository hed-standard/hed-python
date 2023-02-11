""" Summarizes the contents of tabular files. """


import json
from hed.errors.exceptions import HedFileError
from hed.tools.util.data_util import get_new_dataframe
from hed.tools.analysis.annotation_util import generate_sidecar_entry


class TabularSummary:
    """ Summarize the contents of tabular files. """

    def __init__(self, value_cols=None, skip_cols=None, name=''):
        """ Constructor for a BIDS tabular file summary.

        Parameters:
            value_cols (list, None):  List of columns to be treated as value columns.
            skip_cols (list, None):   List of columns to be skipped.
            name (str):               Name associated with the dictionary.

        """

        self.name = name
        self.categorical_info = {}
        self.value_info = {}
        if value_cols and skip_cols and set(value_cols).intersection(skip_cols):
            raise HedFileError("ValueSkipOverlap",
                               f"Value columns {str(value_cols)} and skip columns {str(skip_cols)} cannot overlap", "")
        if value_cols:
            for value in value_cols:
                self.value_info[value] = [0, 0]
        if skip_cols:
            self.skip_cols = skip_cols.copy()
        else:
            self.skip_cols = []
        self.total_files = 0
        self.total_events = 0
        self.files = {}

    def __str__(self):
        indent = "   "
        summary_list = [f"Summary for column dictionary {self.name}:"]
        sorted_keys = sorted(self.categorical_info.keys())
        summary_list.append(f"{indent}Categorical columns ({len(sorted_keys)}):")
        for key in sorted_keys:
            value_dict = self.categorical_info[key]
            sorted_v_keys = sorted(list(value_dict))
            summary_list.append(f"{indent * 2}{key} ({len(sorted_v_keys)} distinct values):")
            for v_key in sorted_v_keys:
                summary_list.append(f"{indent * 3}{v_key}: {value_dict[v_key]}")

        sorted_cols = sorted(map(str, list(self.value_info)))
        summary_list.append(f"{indent}Value columns ({len(sorted_cols)}):")
        for key in sorted_cols:
            summary_list.append(f"{indent * 2}{key}: {self.value_info[key]}")
        return "\n".join(summary_list)

    def extract_sidecar_template(self):
        """ Extract a BIDS sidecar-compatible dictionary."""
        side_dict = {}
        for column_name, columns in self.categorical_info.items():
            column_values = list(columns.keys())
            column_values.sort()
            side_dict[column_name] = generate_sidecar_entry(column_name, column_values)

        for column_name in self.value_info.keys():
            side_dict[column_name] = generate_sidecar_entry(column_name, [])
        return side_dict

    def get_summary(self, as_json=False):
        sorted_keys = sorted(self.categorical_info.keys())
        categorical_cols = {}
        for key in sorted_keys:
            cat_dict = self.categorical_info[key]
            sorted_v_keys = sorted(list(cat_dict))
            val_dict = {}
            for v_key in sorted_v_keys:
                val_dict[v_key] = cat_dict[v_key]
            categorical_cols[key] = val_dict
        sorted_cols = sorted(map(str, list(self.value_info)))
        value_cols = {}
        for key in sorted_cols:
            value_cols[key] = self.value_info[key]
        summary = {"Summary name": self.name, "Total events": self.total_events, "Total files": self.total_files,
                   "Categorical columns": categorical_cols, "Value columns": value_cols}
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary

    def get_number_unique(self, column_names=None):
        """ Return the number of unique values in columns.

        Parameters:
            column_names (list, None):   A list of column names to analyze or all columns if None.

        Returns:
            dict: Column names are the keys and the number of unique values in the column are the values.

        """
        if not column_names:
            column_names = list(self.categorical_info.keys())
        counts = {}
        for column_name in column_names:
            if column_name not in self.categorical_info:
                counts[column_name] = 'n/a'
            else:
                counts[column_name] = len(self.categorical_info[column_name].keys())
        return counts

    def update(self, data, name=None):
        """ Update the counts based on data.

        Parameters:
            data (DataFrame, str, or list):    DataFrame containing data to update.

        """

        if isinstance(data, list):
            for filename in data:
                self._update_dataframe(filename, filename)
        elif isinstance(data, str):
            self._update_dataframe(data, data)
        else:
            self._update_dataframe(data, name)

    def update_summary(self, tab_sum):
        """ Add TabularSummary values to this object.

        Parameters:
            tab_sum (TabularSummary):   A TabularSummary to be combined.

        Notes:
            - The value_cols and skip_cols are updated as long as they are not contradictory.
            - A new skip column cannot used.

        """
        self.total_files = self.total_files + tab_sum.total_files
        self.total_events = self.total_events + tab_sum.total_events
        for file, key in tab_sum.files.items():
            self.files[file] = ''
        self._update_dict_skip(tab_sum)
        self._update_dict_value(tab_sum)
        self._update_dict_categorical(tab_sum)

    def _update_categorical(self, tab_name, values):
        if tab_name not in self.categorical_info:
            self.categorical_info[tab_name] = {}

        total_values = self.categorical_info[tab_name]
        for name, value in values.items():
            value_list = total_values.get(name, [0, 0])
            if not isinstance(value, list):
                value = [value, 1]
            total_values[name] = [value_list[0] + value[0], value_list[1] + value[1]]

    def _update_dataframe(self, data, name):
        df = get_new_dataframe(data)
        if name:
            self.files[name] = ""
        self.total_files = self.total_files + 1
        self.total_events = self.total_events + len(df.index)
        for col_name, col_values in df.items():
            if self.skip_cols and col_name in self.skip_cols:
                continue
            if col_name in self.value_info.keys():
                self.value_info[col_name][0] = self.value_info[col_name][0] + len(col_values)
                self.value_info[col_name][1] = self.value_info[col_name][1] + 1
            else:
                col_values = col_values.astype(str)
                values = col_values.value_counts(ascending=True)
                self._update_categorical(col_name,  values)

    def _update_dict_categorical(self, col_dict):
        new_cat_cols = col_dict.categorical_info.keys()
        if not new_cat_cols:
            return
        val_cols = self.value_info.keys()
        for col in new_cat_cols:
            if col in val_cols:
                raise HedFileError("CatColShouldBeValueCol",
                                   f"Categorical column [{str(col)}] is already a value column", "")
            elif col in self.skip_cols:
                continue
            else:
                self._update_categorical(col, col_dict.categorical_info[col])

    def _update_dict_skip(self, col_dict):
        if not col_dict.skip_cols:
            return
        cat_cols = self.categorical_info.keys()
        val_cols = self.value_info.keys()
        for col in col_dict.skip_cols:
            if col in cat_cols or col in val_cols:
                raise HedFileError("SkipColInvalid",
                                   f"Skip column [{str(col)}] is already a categorical or value column", "")
            elif col not in self.skip_cols:
                self.skip_cols.append(col)

    def _update_dict_value(self, col_dict):
        new_value_cols = col_dict.value_info.keys()
        if not new_value_cols:
            return
        cat_cols = self.categorical_info.keys()
        val_cols = self.value_info.keys()
        for col in new_value_cols:
            if col in cat_cols:
                raise HedFileError("ValueColIsCatCol", f"Value column [{str(col)}] is already a categorical column", "")
            elif col in self.skip_cols:
                continue
            elif col not in val_cols:
                self.value_info[col] = col_dict.value_info[col]
            else:
                self.value_info[col] = [self.value_info[col][0] + col_dict.value_info[col][0],
                                        self.value_info[col][1] + col_dict.value_info[col][1]]

    @staticmethod
    def get_columns_info(dataframe, skip_cols=None):
        """ Extract unique value counts for columns.

        Parameters:
            dataframe (DataFrame):    The DataFrame to be analyzed.
            skip_cols(list):          List of names of columns to be skipped in the extraction.

        Returns:
            dict:   A dictionary with keys that are column names and values that
                    are dictionaries of unique value counts.

        """
        col_info = dict()

        for col_name, col_values in dataframe.items():
            if skip_cols and col_name in skip_cols:
                continue
            col_info[col_name] = col_values.value_counts(ascending=True).to_dict()
        return col_info

    @staticmethod
    def make_combined_dicts(file_dictionary, skip_cols=None):
        """ Return combined and individual summaries.

        Parameters:
            file_dictionary (FileDictionary):  Dictionary of file name keys and full path.
            skip_cols (list):  Name of the column.

        Returns:
            tuple:
                - TabularSummary: Summary of the file dictionary.
                - dict: of individual TabularSummary objects.

        """

        summary_all = TabularSummary(skip_cols=skip_cols)
        summary_dict = {}
        for key, file_path in file_dictionary.items():
            orig_dict = TabularSummary(skip_cols=skip_cols)
            df = get_new_dataframe(file_path)
            orig_dict.update(df)
            summary_dict[key] = orig_dict
            summary_all.update_summary(orig_dict)
        return summary_all, summary_dict
