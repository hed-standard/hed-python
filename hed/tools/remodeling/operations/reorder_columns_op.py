from hed.tools.remodeling.operations.base_op import BaseOp


class ReorderColumnsOp(BaseOp):
    """ Reorder columns in a dataframe.

    Notes: The required parameters are:
        - column_order (list)   The names of the columns to be reordered.
        - ignore_missing (bool) If false and a column in column_order is not in df, skip the column
        - keep_others (bool)    If true, columns not in column_order are placed at end.

    Raises:
        KeyError if ignore_missing is false and a column name in column_order is not in the dataframe.

    """

    PARAMS = {
        "operation": "reorder_columns",
        "required_parameters": {
            "column_order": list,
            "ignore_missing": bool,
            "keep_others": bool
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        super().__init__(self.PARAMS, parameters)
        self.column_order = parameters['column_order']
        self.ignore_missing = parameters['ignore_missing']
        self.keep_others = parameters['keep_others']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Reorder columns as specified in event dictionary.

        Parameters:
            dispatcher (Dispatcher): The dispatcher object for context.
            df (DataFrame):  The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):   Only needed for HED operations.

        Returns:
            Dataframe: a new dataframe after processing.

        Raises:
            ValueError:  when ignore_missing is false and column_order has columns not in df.

        """

        current_columns = list(df.columns)
        missing_columns = set(self.column_order).difference(set(df.columns))
        ordered = self.column_order
        if missing_columns and not self.ignore_missing:
            raise ValueError("MissingReorderedColumns",
                             f"{str(missing_columns)} are not in dataframe columns "
                             f" [{str(df.columns)}] and not ignored.")
        elif missing_columns:
            ordered = [elem for elem in self.column_order if elem not in list(missing_columns)]
        if self.keep_others:
            ordered += [elem for elem in current_columns if elem not in ordered]
        df = df.loc[:, ordered]
        return df
