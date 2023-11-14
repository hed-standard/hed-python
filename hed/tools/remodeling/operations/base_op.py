""" Base class for remodeling operations. """


class BaseOp:
    """ Base class for operations. All remodeling operations should extend this class.

    The base class holds the parameters and does basic parameter checking against the operation's specification.

    """

    def __init__(self, name, parameters):
        """ Base class constructor for operations.

        Parameters:
            op_spec (dict): Specification for required and optional parameters.
            parameters (dict):  Actual values of the parameters for the operation.

        :raises KeyError:
            - If a required parameter is missing.
            - If an unexpected parameter is provided.

        :raises TypeError:
            - If a parameter has the wrong type.

        :raises ValueError:
            - If the specification is missing a valid operation.

        """
        self.name = name
        self.parameters = parameters

    
    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Base class method to be overridden by each operation.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The tabular file to be remodeled.
            name (str): Unique identifier for the data -- often the original file path.
            sidecar (Sidecar or file-like):  A JSON sidecar needed for HED operations.

        """

        return df.copy()
