from hed.errors.exceptions import HedFileError
from hed.util.data_util import get_new_dataframe
from hed.tools.bids.bids_annotation import generate_sidecar_entry


class ColumnDict:
    """Summarizes the contents of a spreadsheet. """

    def __init__(self, value_cols=None, skip_cols=None, name='', header_char='*'):
        """ .

        Args:
            value_cols (list):   List of columns to be treated as value columns
            skip_cols (list):    List of columns to be skipped
            name (str):          Name associated with the dictionary

        """

        self.name = name
        self.header_char = header_char
        self.categorical_info = {}
        self.value_info = {}
        if value_cols and skip_cols and set(value_cols).intersection(skip_cols):
            raise HedFileError("ValueSkipOverlap",
                               f"Value columns {str(value_cols)} and skip columns {str(skip_cols)} cannot overlap", "")
        if value_cols:
            for value in value_cols:
                self.value_info[value] = 0
        if skip_cols:
            self.skip_cols = skip_cols.copy()
        else:
            self.skip_cols = []
        self.total_files = 0
        self.total_events = 0

    def get_number_unique_values(self, column_names=None):
        """ Extract the number of unique values the specified columns if available ."""
        if not column_names:
            column_names = list(self.categorical_info.keys())
        counts = {}
        for column_name in column_names:
            if column_name not in self.categorical_info:
                counts[column_name] = 'n/a'
            else:
                counts[column_name] = len(self.categorical_info[column_name].keys())
        return counts

    def extract_sidecar_template(self):
        """ Extract a dictionary compatible with a BIDS JSON event sidecar."""
        side_dict = {}
        print("Extracting template.....")
        for column_name, columns in self.categorical_info.items():
            column_values = list(columns.keys())
            column_values.sort()
            side_dict[column_name] = generate_sidecar_entry(column_name, column_values)

        for column_name in self.value_info.keys():
            side_dict[column_name] = generate_sidecar_entry(column_name, [])
        return side_dict

    def print(self, title=None, indent="  "):
        if not title:
            title = f"Summary for column dictionary {self.name}:"
        print(title)
        sorted_keys = sorted(self.categorical_info.keys())
        print(f"{indent}Categorical columns ({len(sorted_keys)}):")
        for key in sorted_keys:
            value_dict = self.categorical_info[key]
            sorted_v_keys = sorted(list(value_dict))
            print(f"{indent * 2}{key} ({len(sorted_v_keys)} distinct values):")
            for v_key in sorted_v_keys:
                print(f"{indent * 3}{v_key}: {value_dict[v_key]}")

        sorted_cols = sorted(map(str, list(self.value_info)))
        print(f"{indent}Value columns ({len(sorted_cols)}):")
        for key in sorted_cols:
            print(f"{indent * 2}{key}: {self.value_info[key]}")

    # def tojson(self, max= indent=4):
    #     if not title:
    #         title = f"Summary for column dictionary {self.name}:"
    #     print(title)
    #     sorted_keys = sorted(self.categorical_info.keys())
    #     print(f"{indent}Categorical columns ({len(sorted_keys)}):")
    #     for key in sorted_keys:
    #         value_dict = self.categorical_info[key]
    #         sorted_v_keys = sorted(list(value_dict))
    #         print(f"{indent * 2}{key} ({len(sorted_v_keys)} distinct values):")
    #         for v_key in sorted_v_keys:
    #             print(f"{indent * 3}{v_key}: {value_dict[v_key]}")
    #
    #     sorted_cols = sorted(map(str, list(self.value_info)))
    #     print(f"{indent}Value columns ({len(sorted_cols)}):")
    #     for key in sorted_cols:
    #         print(f"{indent * 2}{key}: {self.value_info[key]}")

    def update(self, data):
        """ Extracts the number of times each unique value appears in each column.

        Args:
            data (DataFrame, str, or list):    DataFrame to be analyzed or the full path of a tsv file.

        Returns:
            dict:   A dictionary with keys that are column names and values that are dictionaries of unique value counts
        """

        if isinstance(data, list):
            for filename in data:
                self._update_dataframe(filename)
        else:
            self._update_dataframe(data)

    def update_dict(self, col_dict):
        """ Adds the values of another ColDict object to this object.

        The value_cols and skip_cols are updated as long as they are not contradictory. A new skip column
        cannot be in the

          Args:
              col_dict (ColDict):    A column dictionary to be combined with

          """
        self._update_dict_skip(col_dict)
        self._update_dict_value(col_dict)
        self._update_dict_categorical(col_dict)

    def _update_categorical(self, col_name, values):
        if col_name not in self.categorical_info:
            self.categorical_info[col_name] = {}

        total_values = self.categorical_info[col_name]
        for name, value in values.items():
            total_values[name] = total_values.get(name, 0) + value

    def _update_dataframe(self, data):
        df = get_new_dataframe(data)
        self.total_files = self.total_files + 1
        self.total_events = self.total_events + len(df.index)
        for col_name, col_values in df.iteritems():
            if self.skip_cols and col_name in self.skip_cols:
                continue
            if col_name in self.value_info.keys():
                self.value_info[col_name] = self.value_info[col_name] + len(col_values)
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
                self.value_info[col] = self.value_info[col] + col_dict.value_info[col]

