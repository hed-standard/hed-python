""" Reorder columns in a columnar file. """

import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class ReorderColumnsOp(BaseOp):
    """ Reorder columns in a columnar file.

    Required parameters:
        - column_order (*list*): The names of the columns to be reordered.
        - ignore_missing (*bool*): If False and a column in column_order is not in df, skip the column.
        - keep_others (*bool*): If True, columns not in column_order are placed at end.

    """
    NAME = "reorder_columns"

    PARAMS = {
        "type": "object",
        "properties": {
            "column_order": {
                "type": "array",
                "description": "A list of column names in the order you wish them to be.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "ignore_missing": {
                "type": "boolean",
                "description": "If true, ignore column_order columns that aren't in file, otherwise error."
            },
            "keep_others": {
                "type": "boolean",
                "description": "If true columns not in column_order are placed at end, otherwise ignored."
            }
        },
        "required": [
            "column_order",
            "ignore_missing",
            "keep_others"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for reorder columns operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.column_order = parameters['column_order']
        self.ignore_missing = parameters['ignore_missing']
        self.keep_others = parameters['keep_others']

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Reorder columns as specified in event dictionary.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame):  The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:
            ValueError: When ignore_missing is false and column_order has columns not in the data.

        """
        df_new = df.copy()
        current_columns = list(df_new.columns)
        missing_columns = set(self.column_order).difference(
            set(df_new.columns))
        ordered = self.column_order
        if missing_columns and not self.ignore_missing:
            raise ValueError("MissingReorderedColumns",
                             f"{str(missing_columns)} are not in dataframe columns "
                             f" [{str(df_new.columns)}] and not ignored.")
        elif missing_columns:
            ordered = [
                elem for elem in self.column_order if elem not in list(missing_columns)]
        if self.keep_others:
            ordered += [elem for elem in current_columns if elem not in ordered]
        df_new = df_new.loc[:, ordered]
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
