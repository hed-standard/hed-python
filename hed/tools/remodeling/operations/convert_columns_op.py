""" Convert the type of the specified columns of a tabular file. """
#TODO finish implementation
#TODO Specify when requirements for decimal_places parameter

from hed.tools.remodeling.operations.base_op import BaseOp


class ConvertColumnsOp(BaseOp):
    """ Convert data type in column

    Required remodeling parameters:   
        - **column_names** (*list*):   The list of columns to convert.   
        - **convert_to** (*str*):  Name of type to convert to. (One of 'str', 'int', 'float', 'fixed'.)   
    
    Optional remodeling parameters:
        - **decimal_places** (*int*):   Number decimal places to keep (for fixed only).   

    Notes:
        - Decimal places requirements not implemented    
    """
    NAME = "convert_columns"
    
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
            "convert_to": {
                "type": "string",
                "enum": ['str', 'int', 'float', 'fixed'],
            },
            "decimal_places": {
                "type": "integer"
            }
        },
        "required": [
            "column_names",
            "convert_to"
        ],
        "additionalProperties": False,
        "if": {
            "properties": {
                "convert_to": {"const": "fixed"}
            }
        },
        "then": {
            "required": ["decimal_places"]
        }
    }

    def __init__(self, parameters):
        """ Constructor for the convert columns operation.

        Parameters:
            parameters (dict): Parameter values for required and optional parameters.

        """
        super().__init__(self.PARAMS, parameters)
        self.column_names = parameters['column_names']
        self.convert_to = parameters['convert_to']
        self.decimal_places = parameters.get('decimal_places', None)

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
