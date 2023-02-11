""" Remove columns from a tabular file. """
from hed.tools.remodeling.operations.base_op import BaseOp


class RemoveColumnsOp(BaseOp):
    """ Remove columns from a tabular file.

    Required remodeling parameters:
        - **remove_names** (*list*): The names of the columns to be removed.  
        - **ignore_missing** (*boolean*): If true, names in remove_names that are not columns in df should be ignored.  

    """

    PARAMS = {
        "operation": "remove_columns",
        "required_parameters": {
            "column_names": list,
            "ignore_missing": bool
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        """ Constructor for remove columns operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters

        Raises:
            KeyError
                - If a required parameter is missing.    
                - If an unexpected parameter is provided.   

            TypeError   
                - If a parameter has the wrong type.   

        """
        super().__init__(self.PARAMS, parameters)
        self.column_names = parameters['column_names']
        ignore_missing = parameters['ignore_missing']
        if ignore_missing:
            self.error_handling = 'ignore'
        else:
            self.error_handling = 'raise'

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Remove indicated columns from a dataframe.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:
            KeyError   
                - If ignore_missing is False and a column not in the data is to be removed.   

        """

        try:
            return df.drop(self.column_names, axis=1, errors=self.error_handling)
        except KeyError:
            raise KeyError("MissingColumnCannotBeRemoved",
                           f"{name}: Ignore missing is False but a column in {str(self.column_names)} is "
                           f"not in the data columns [{str(df.columns)}]")
