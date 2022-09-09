import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp

PARAMS = {
    "command": "merge_consecutive",
    "required_parameters": {
        "column_name": str,
        "event_code": [str, int, float],
        "match_columns": list,
        "set_durations": bool,
        "ignore_missing": bool
    },
    "optional_parameters": {}
}


class MergeConsecutiveOp(BaseOp):

    def __init__(self, parameters):
        super().__init__(PARAMS["command"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.column_name = parameters["column_name"]
        self.event_code = parameters["event_code"]
        self.match_columns = parameters["match_columns"]
        if self.column_name in self.match_columns:
            raise ValueError("MergeColumnCannotBeMatched",
                             f"column{self.column_name} cannot be one of the match columns: {str(self.match_columns)}")
        self.set_durations = parameters["set_durations"]
        self.ignore_missing = parameters["ignore_missing"]

    def do_op(self, dispatcher, df, name, sidecar=None, verbose=False):
        """ Merge consecutive events of the same type

        Args:
            dispatcher (Dispatcher) - dispatcher object for context
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.
            verbose (bool) If True output informative messages during operation.

        Returns:
            Dataframe - a new dataframe after processing.

        """

        if not self.ignore_missing and self.column_name not in df.columns:
            raise ValueError("ColumnMissing",
                             f"{self.column_name} is not in data and missing columns are not ignored")
        if self.set_durations and "onset" not in df.columns:
            raise ValueError("MissingOnsetColumn",
                             f"Data must have an onset column in order to set_durations")
        if self.set_durations and "duration" not in df.columns:
            raise ValueError("MissingDurationColumn",
                             f"Data must have a duration column in order to set_durations")
        missing = set(self.match_columns).difference(set(df.columns))
        if self.match_columns and not self.ignore_missing and missing:
            raise ValueError("ColumnMissing", f"{str(missing)} columns are unmatched and not ignored")
        match_columns = list(set(self.match_columns).intersection(set(df.columns)))

        df_new = df.copy()
        code_mask = df_new[self.column_name] == self.event_code
        if sum(code_mask.astype(int)) == 0:
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

        Args:
            match_df (DataFrame): DataFrame containing columns to be matched must contain at least the base column.
            code_mask (list):  List of the same length as match_df with the names of the

        Returns:
            list with group numbers set (starting at 1).

        # TODO: Handle roundoff in rows for comparison.
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
        remove_df = pd.DataFrame(remove_groups, columns=["remove"])
        max_groups = max(remove_groups)
        for index in range(max_groups):
            df_group = df_new.loc[remove_df["remove"] == index + 1, ["onset", "duration"]]
            max_group = df_group.sum(axis=1, skipna=True).max()
            anchor = df_group.index[0] - 1
            max_anchor = df_new.loc[anchor, ["onset", "duration"]].sum(skipna=True).max()
            df_new.loc[anchor, "duration"] = max(max_group, max_anchor) - df_new.loc[anchor, "onset"]

        # in_group = False
        # start_group = -1
        # end_group = -1
        # for index in range(len(remove_groups)):
        #     if in_group and remove_groups[index] > 0:
        #         end_group = index
        #     elif in_group and remove_groups[index] == 0:
        #         in_group = False
        #         df_new.loc[start_group, "duration"] = df_new.loc[end_group, "onset"] - \
        #                                               df_new.loc[start_group, "onset"] + \
        #                                               df_new.loc[end_group, "duration"]
        # return
