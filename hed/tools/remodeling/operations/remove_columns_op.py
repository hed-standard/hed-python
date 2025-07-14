""" Remove columns from a columnar file. """
from __future__ import annotations
from hed.tools.remodeling.operations.base_op import BaseOp


class RemoveColumnsOp(BaseOp):
    """ Remove columns from a columnar file.

    Required remodeling parameters:
        - **column_names** (*list*): The names of the columns to be removed.
        - **ignore_missing** (*boolean*): If True, names in column_names that are not columns in df should be ignored.

    """
    NAME = "remove_columns"

    PARAMS = {
        "type": "object",
        "properties": {
            "column_names": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "ignore_missing": {
                "type": "boolean"
            }
        },
        "required": [
            "column_names",
            "ignore_missing"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for remove columns operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.column_names = parameters['column_names']
        ignore_missing = parameters['ignore_missing']
        if ignore_missing:
            self.error_handling = 'ignore'
        else:
            self.error_handling = 'raise'

    def do_op(self, dispatcher, df, name, sidecar=None) -> 'pd.DataFrame':
        """ Remove indicated columns from a dataframe.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Not needed for this operation.

        Returns:
            pd.DataFrame: A new dataframe after processing.

        :raises KeyError:
            - If ignore_missing is False and a column not in the data is to be removed.

        """
        df_new = df.copy()
        try:
            return df_new.drop(self.column_names, axis=1, errors=self.error_handling)
        except KeyError:
            raise KeyError("MissingColumnCannotBeRemoved",
                           f"{name}: Ignore missing is False but a column in {str(self.column_names)} is "
                           f"not in the data columns [{str(df_new.columns)}]")

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
