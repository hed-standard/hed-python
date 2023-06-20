""" Convert the type of the specified columns of a tabular file. """

from hed.tools.remodeling.operations.base_op import BaseOp


class ConvertColumnsOp(BaseOp):
    """ Convert.

    Required remodeling parameters:   
        - **column_names** (*list*):   The list of columns to convert.   
        - **convert_to_** (*str*):  Name of type to convert to. (One of 'str', 'int', 'float', 'fixed'.)   
        - **decimal_places** (*int*):   Number decimal places to keep (for fixed only).   


    """

    PARAMS = {
        "operation": "convert_columns",
        "required_parameters": {
            "column_names": list,
            "convert_to": str
        },
        "optional_parameters": {
            "decimal_places": int
        }
    }

    def __init__(self, parameters):
        """ Constructor for the convert columns operation.

        Parameters:
            parameters (dict): Parameter values for required and optional parameters.

        :raises KeyError:
            - If a required parameter is missing.
            - If an unexpected parameter is provided.

        :raises TypeError:
            - If a parameter has the wrong type.

        :raises ValueError:
            - If convert_to is not one of the allowed values.

        """
        super().__init__(self.PARAMS, parameters)
        self.column_names = parameters['column_names']
        self.convert_to = parameters['convert_to']
        self.decimal_places = parameters.get('decimal_places', None)
        self.allowed_types = ['str', 'int', 'float', 'fixed']
        if self.convert_to not in self.allowed_types:
            raise ValueError("CannotConvertToSpecifiedType",
                             f"The convert_to value {self.convert_to} must be one of {str(self.allowed_types)}")

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Convert the specified column to a specified type.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            DataFrame: A new DataFrame with the factor columns appended.

        """

        df_new = df.copy()
        return df_new
