""" Remove rows from a columnar file based on column values. """

import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class RemoveRowsOp(BaseOp):
    """ Remove rows from a columnar file based on the values in a specified row.

    Required remodeling parameters:
        - **column_name** (*str*): The name of column to be tested.
        - **remove_values** (*list*): The values to test for row removal.

    """
    NAME = "remove_rows"

    PARAMS = {
        "type": "object",
        "properties": {
            "column_name": {
                "type": "string",
                "description": "Name of the key column to determine which rows to remove."
            },
            "remove_values": {
                "type": "array",
                "description": "List of key values for rows to remove.",
                "items": {
                    "type": [
                        "string",
                        "number"
                    ]
                },
                "minItems": 1,
                "uniqueItems": True
            }
        },
        "required": [
            "column_name",
            "remove_values"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for remove rows operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.column_name = parameters["column_name"]
        self.remove_values = parameters["remove_values"]

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Remove rows with the values indicated in the column.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        """
        df_new = df.copy()
        if self.column_name not in df_new.columns:
            return df_new
        for value in self.remove_values:
            df_new = df_new.loc[df_new[self.column_name] != value, :]
        df_new = df_new.reset_index(drop=True)
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
