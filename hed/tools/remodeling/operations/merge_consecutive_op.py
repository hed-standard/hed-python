""" Merge consecutive rows with same column value. """

import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class MergeConsecutiveOp(BaseOp):
    """ Merge consecutive rows with same column value.

    Required remodeling parameters:
        - **column_name** (*str*): the name of the column whose consecutive values are to be compared (the merge column).  
        - **event_code** (*str* or *int* or *float*): the particular value in the match column to be merged.  
        - **match_columns** (*list*):  A list of columns whose values have to be matched for two events to be the same.  
        - **set_durations** (*bool*): If true, set the duration of the merged event to the extent of the merged events.  
        - **ignore_missing** (*bool*):  If true, missing match_columns are ignored.  

    """
    PARAMS = {
        "operation": "merge_consecutive",
        "required_parameters": {
            "column_name": str,
            "event_code": [str, int, float],
            "match_columns": list,
            "set_durations": bool,
            "ignore_missing": bool
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        """ Constructor for the merge consecutive operation.

        Parameters:
            op_spec (dict): Specification for required and optional parameters.
            parameters (dict): Actual values of the parameters for the operation.

        Raises:

            KeyError   
            - If a required parameter is missing.   
            - If an unexpected parameter is provided.   
 
            TypeError   
            - If a parameter has the wrong type.   

            ValueError   
            - If the specification is missing a valid operation.   
            - If one of the match column is the merge column.   

        """
        super().__init__(self.PARAMS, parameters)
        self.column_name = parameters["column_name"]
        self.event_code = parameters["event_code"]
        self.match_columns = parameters["match_columns"]
        if self.column_name in self.match_columns:
            raise ValueError("MergeColumnCannotBeMatchColumn",
                             f"Column {self.column_name} cannot be one of the match columns: {str(self.match_columns)}")
        self.set_durations = parameters["set_durations"]
        self.ignore_missing = parameters["ignore_missing"]

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Merge consecutive rows with the same column value.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:

            ValueError   
                - If dataframe does not have the anchor column and ignore_missing is False.   
                - If a match column is missing and ignore_missing is false.   
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

        Parameters:
            match_df (DataFrame): DataFrame containing columns to be matched.
            code_mask (DataSeries):  Same length as match_df with the names.

        Returns:
            list:  Group numbers set (starting at 1).

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
