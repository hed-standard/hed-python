from hed.tools.remodeling.operations.base_op import BaseOp

PARAMS = {
    "operation": "remove_rows",
    "required_parameters": {
        "column_name": str,
        "remove_values": list
    },
    "optional_parameters": {}
}


class RemoveRowsOp(BaseOp):
    """ Remove dataframe rows that take one of the specified values in the specified column.

         Notes: The required parameters are
             - column_name (str)     The name of column to be tested.
             - remove_values (list)  The values to test for row removal.

     """

    def __init__(self, parameters):
        super().__init__(PARAMS["operation"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.column_name = parameters["column_name"]
        self.remove_values = parameters["remove_values"]

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Remove rows with the values indicated in the column.

        Parameters:
            dispatcher (Dispatcher) - dispatcher object for context
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.

        Returns:
            Dataframe - a new dataframe after processing.

        """

        if self.column_name not in df.columns:
            return df
        for value in self.remove_values:
            df = df.loc[df[self.column_name] != value, :]
        return df
