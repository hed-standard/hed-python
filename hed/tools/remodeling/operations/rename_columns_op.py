""" Rename columns in a tabular file. """

from hed.tools.remodeling.operations.base_op import BaseOp


class RenameColumnsOp (BaseOp):
    """ Rename columns in a tabular file.

    Required remodeling parameters:   
        - **column_mapping** (*dict*): The names of the columns to be renamed.   
        - **ignore_missing** (*bool*): If true, the names in column_mapping that are not columns and should be ignored.

    """
    NAME = "rename_columns"
    
    PARAMS = {
        "type": "object",
        "properties": {
            "column_mapping": {
                "type": "object",
                "patternProperties": {
                    ".*": {
                        "type": "string"
                    }
                },
                "minProperties": 1
            },
            "ignore_missing": {
                "type": "boolean"
            }
        },
        "required": [
            "column_mapping",
            "ignore_missing"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for rename columns operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters

        """
        super().__init__(parameters)
        self.column_mapping = parameters['column_mapping']
        if parameters['ignore_missing']:
            self.error_handling = 'ignore'
        else:
            self.error_handling = 'raise'

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Rename columns as specified in column_mapping dictionary.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        :raises KeyError:
            - When ignore_missing is false and column_mapping has columns not in the data.

        """
        df_new = df.copy()
        try:
            return df_new.rename(columns=self.column_mapping, errors=self.error_handling)
        except KeyError:
            raise KeyError("MappedColumnsMissingFromData",
                           f"{name}: ignore_missing is False, mapping columns [{self.column_mapping}]"
                           f" but df columns are [{str(df.columns)}")

    @staticmethod
    def validate_input_data(parameters):
        return []
