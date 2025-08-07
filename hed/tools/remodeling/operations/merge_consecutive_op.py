""" Merge consecutive rows of a columnar file with same column value. """

import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class MergeConsecutiveOp(BaseOp):
    """ Merge consecutive rows of a columnar file with same column value.

    Required remodeling parameters:
        - **column_name** (*str*): name of column whose consecutive values are to be compared (the merge column).
        - **event_code** (*str* or *int* or *float*): the particular value in the match column to be merged.
        - **set_durations** (*bool*): If true, set the duration of the merged event to the extent of the merged events.
        - **ignore_missing** (*bool*):  If true, missing match_columns are ignored.

    Optional remodeling parameters:
        - **match_columns** (*list*):  A list of columns whose values have to be matched for two events to be the same.

    Notes:
          This operation is meant for time-based tabular files that have an onset column.

    """
    NAME = "merge_consecutive"

    PARAMS = {
        "type": "object",
        "properties": {
            "column_name": {
                "type": "string",
                "description": "The name of the column to check for repeated consecutive codes."
            },
            "event_code": {
                "type": [
                    "string",
                    "number"
                ],
                "description": "The event code to match for duplicates."
            },
            "match_columns": {
                "type": "array",
                "description": "List of columns whose values must also match to be considered a repeat.",
                "items": {
                    "type": "string"
                }
            },
            "set_durations": {
                "type": "boolean",
                "description": "If true, then the duration should be computed based on start of first to end of last."
            },
            "ignore_missing": {
                "type": "boolean",
                "description": "If true, missing match columns are ignored."
            }
        },
        "required": [
            "column_name",
            "event_code",
            "set_durations",
            "ignore_missing"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for the merge consecutive operation.

        Parameters:
            parameters (dict): Actual values of the parameters for the operation.

        """
        super().__init__(parameters)
        self.column_name = parameters["column_name"]
        self.event_code = parameters["event_code"]
        self.set_durations = parameters["set_durations"]
        self.ignore_missing = parameters["ignore_missing"]
        self.match_columns = parameters.get("match_columns", None)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Merge consecutive rows with the same column value.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        :raises ValueError:
            - If dataframe does not have the anchor column and ignore_missing is False.
            - If a match column is missing and ignore_missing is False.
            - If the durations were to be set and the dataframe did not have an onset column.
            - If the durations were to be set and the dataframe did not have a duration column.

        """

        if not self.ignore_missing and self.column_name not in df.columns:
            raise ValueError("ColumnMissing",
                             f"{name}: {self.column_name} is not in data columns [{str(df.columns)}] "
                             f"and missing columns are not ignored")
        if self.set_durations and "onset" not in df.columns:
            raise ValueError("MissingOnsetColumn",
                             f"{name}: Data must have an onset column in order to set durations")
        if self.set_durations and "duration" not in df.columns:
            raise ValueError("MissingDurationColumn",
                             f"{name}: Data must have a duration column in order to set durations")
        missing = set(self.match_columns).difference(set(df.columns))
        if self.match_columns and not self.ignore_missing and missing:
            raise ValueError("MissingMatchColumns",
                             f"{name}: {str(missing)} columns are unmatched by data columns"
                             f"[{str(df.columns)}] and not ignored")
        match_columns = list(
            set(self.match_columns).intersection(set(df.columns)))

        df_new = df.copy()
        code_mask = df_new[self.column_name] == self.event_code
        if not code_mask.any():
            return df_new
        match_columns.append(self.column_name)
        match_df = df_new.loc[:, match_columns]
        remove_groups = self._get_remove_groups(match_df, code_mask)
        if self.set_durations and max(remove_groups) > 0:
            self._update_durations(df_new, remove_groups)
        keep_mask = [remove_group == 0 for remove_group in remove_groups]
        df_new = df_new.loc[keep_mask, :].reset_index(drop=True)
        return df_new

    @staticmethod
    def _get_remove_groups(match_df, code_mask):
        """ Return a list of same length as match_df with group numbers of consecutive items.

        Parameters:
            match_df (DataFrame): DataFrame containing columns to be matched.
            code_mask (DataSeries):  Same length as match_df with the names.

        Returns:
            list:  Group numbers set (starting at 1).

        # TODO: Handle round off in rows for comparison.
        """
        in_group = False
        remove_groups = [0] * len(match_df)
        group_count = 0
        for index, row in match_df.iterrows():
            if not code_mask.iloc[index]:
                in_group = False
                continue
            elif not in_group:
                in_group = True
                group_count += 1
                continue
            if in_group and row.equals(match_df.loc[index - 1, :]):
                remove_groups[index] = group_count
            else:
                group_count += 1
        return remove_groups

    @staticmethod
    def _update_durations(df_new, remove_groups):
        """ Update the durations for the columns based on merged columns.

        Parameters:
            df_new (DataFrame): Tabular data to merge.
            remove_groups (list): List of names of columns to remove.

        """
        remove_df = pd.DataFrame(remove_groups, columns=["remove"])
        max_groups = max(remove_groups)
        for index in range(max_groups):
            df_group = df_new.loc[remove_df["remove"]
                                  == index + 1, ["onset", "duration"]]
            max_group = df_group.sum(axis=1, skipna=True).max()
            anchor = df_group.index[0] - 1
            max_anchor = df_new.loc[anchor, [
                "onset", "duration"]].sum(skipna=True).max()
            df_new.loc[anchor, "duration"] = max(
                max_group, max_anchor) - df_new.loc[anchor, "onset"]

    @staticmethod
    def validate_input_data(parameters):
        """ Verify that the column name is not in match columns.

        Parameters:
            parameters (dict): Dictionary of parameters of actual implementation.

        """
        match_columns = parameters.get("match_columns", None)
        name = parameters.get("column_name", None)
        if match_columns and name in match_columns:
            return [f"column_name `{name}` cannot not be a match_column."]
        return []
