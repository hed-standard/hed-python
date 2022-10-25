from hed.tools.remodeling.operations.base_op import BaseOp


class RenameColumnsOp (BaseOp):
    """ Rename columns in a dataframe.

    Notes: The required parameters are:
        - column_mapping (dict) The names of the columns to be removed.
        - ignore_missing (bool) If true, the names in remove_names that are not columns in df should be ignored.

    Raises:
        KeyError if ignore_missing is false and a column name in column_mapping is not in the dataframe.

    """

    PARAMS = {
        "operation": "rename_columns",
        "required_parameters": {
            "column_mapping": dict,
            "ignore_missing": bool
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        super().__init__(self.PARAMS["operation"], self.PARAMS["required_parameters"],
                         self.PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.column_mapping = parameters['column_mapping']
        if parameters['ignore_missing']:
            self.error_handling = 'ignore'
        else:
            self.error_handling = 'raise'

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Rename columns as specified in column_mapping dictionary.

        Parameters:
            dispatcher (Dispatcher) - dispatcher object for context
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.

        Returns:
            Dataframe - a new dataframe after processing.

        Raises:
            KeyError - when ignore_missing is false and column_mapping has columns not in df.

        """

        return df.rename(columns=self.column_mapping, errors=self.error_handling)
