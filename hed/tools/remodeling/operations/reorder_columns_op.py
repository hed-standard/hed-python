""" Reorder columns in a tabular file. """
from hed.tools.remodeling.operations.base_op import BaseOp


class ReorderColumnsOp(BaseOp):
    """ Reorder columns in a tabular file.

    Required parameters:
        column_order (*list*): The names of the columns to be reordered.
        ignore_missing (*bool*): If false and a column in column_order is not in df, skip the column
        keep_others (*bool*): If true, columns not in column_order are placed at end.

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
        """ Constructor for reorder columns operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        Raises:
            KeyError   
                - If a required parameter is missing.   
                - If an unexpected parameter is provided.   

            TypeError  
                If a parameter has the wrong type.  

        """
        super().__init__(self.PARAMS, parameters)
        self.column_order = parameters['column_order']
        self.ignore_missing = parameters['ignore_missing']
        self.keep_others = parameters['keep_others']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Reorder columns as specified in event dictionary.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame):  The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):   Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:
            ValueError   
                - When ignore_missing is false and column_order has columns not in the data.   

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
