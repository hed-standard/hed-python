""" Append to tabular file columns of factors based on column values. """

import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class FactorColumnOp(BaseOp):
    """ Append to tabular file columns of factors based on column values.

    Required remodeling parameters:
        - **column_name** (*str*):  The name of a column in the DataFrame to compute factors from.

    Optional remodeling parameters
        - **factor_names** (*list*):   Names to use as the factor columns.
        - **factor_values** (*list*):  Values in the column column_name to create factors for.

    Notes:
        - If no factor_values are provided, factors are computed for each of the unique values in column_name column.
        - If factor_names are provided, then factor_values must also be provided and the two lists be the same size.

    """
    NAME = "factor_column"

    PARAMS = {
        "type": "object",
        "properties": {
            "column_name": {
                "type": "string",
                "description": "Name of the column for which to create one-hot factors for unique values."
            },
            "factor_names": {
                "type": "array",
                "description": "Names of the resulting factor columns. If given must be same length as factor_values",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "factor_values": {
                "type": "array",
                "description": "Specific unique column values to compute factors for (otherwise all unique values).",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            }
        },
        "required": [
            "column_name"
        ],
        "dependentRequired": {
            "factor_names": ["factor_values"]
        },
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for the factor column operation.

        Parameters:
            parameters (dict): Parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.column_name = parameters['column_name']
        self.factor_values = parameters.get('factor_values', None)
        self.factor_names = parameters.get('factor_names', None)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Create factor columns based on values in a specified column.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        """

        factor_values = self.factor_values
        factor_names = self.factor_names
        if len(factor_values) == 0:
            factor_values = df[self.column_name].unique()
            factor_names = [self.column_name + '.' +
                            str(column_value) for column_value in factor_values]

        df_new = df.copy()
        for index, factor_value in enumerate(factor_values):
            factor_index = df_new[self.column_name].map(
                str).isin([str(factor_value)])
            column = factor_names[index]
            df_new[column] = factor_index.astype(int)
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Check that factor_names and factor_values have same length if given. """
        names = parameters.get("factor_names", None)
        values = parameters.get("factor_values", None)
        if names and not values:
            return ["factor_names cannot be given without factor_values"]
        elif names and values and len(names) != len(values):
            return ["factor_names must be same length as factor_values"]
        else:
            return []
