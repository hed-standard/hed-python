""" Base class for remodeling operations. """


class BaseOp:
    """ Base class for operations. All remodeling operations should extend this class.

    The base class holds the parameters and does basic parameter checking against the operations specification.

    """

    def __init__(self, op_spec, parameters):
        """ Base class constructor for operations.

        Parameters:
            op_spec (dict): Specification for required and optional parameters.
            parameters (dict):  Actual values of the parameters for the operation.

        Raises:
            KeyError   
                - If a required parameter is missing.   
                - If an unexpected parameter is provided.   

            TypeError   
                - If a parameter has the wrong type.   

            ValueError   
                - If the specification is missing a valid operation.   

        """
        self.operation = op_spec.get("operation", "")
        if not self.operation:
            raise ValueError("OpMustHaveOperation", "Op must have operation is empty")
        self.required_params = op_spec.get("required_parameters", {})
        self.optional_params = op_spec.get("optional_parameters", {})
        self.check_parameters(parameters)

    def check_parameters(self, parameters):
        """ Verify that the parameters meet the operation specification.

        Parameters:
            parameters (dict): Dictionary of parameters for this operation.

        Raises:

            KeyError   
                - If a required parameter is missing.   
                - If an unexpected parameter is provided.    

            TypeError   
                - If a parameter has the wrong type.   

        """

        required = set(self.required_params.keys())
        required_missing = required.difference(set(parameters.keys()))
        if required_missing:
            raise KeyError("MissingRequiredParameters",
                           f"{self.operation} requires parameters {list(required_missing)}")
        for param_name, param_value in parameters.items():
            if param_name in self.required_params:
                param_type = self.required_params[param_name]
            elif param_name in self.optional_params:
                param_type = self.optional_params[param_name]
            else:
                raise KeyError("BadParameter",
                               f"{param_name} not a required or optional parameter for {self.operation}")
            if isinstance(param_type, list):
                self._check_list_type(param_value, param_type)
            elif not isinstance(param_value, param_type):
                raise TypeError("BadType", f"{param_value} has type {type(param_value)} not {param_type}")

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Base class method to be overridden with by each operation.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The tabular file to be remodeled.
            name (str): Unique identifier for the data -- often the original file path.
            sidecar (Sidecar or file-like):  A JSON sidecar needed for HED operations.

        """

        return df

    @staticmethod
    def _check_list_type(param_value, param_type):
        """ Check a parameter value against its specified type.

        Parameters:
            param_value (any):   The value to be checked.
            param_type (any):    Class to check the param_value against.

        Raises:
            TypeError: If param_value is not an instance of param_type.

        """

        for this_type in param_type:
            if isinstance(param_value, this_type):
                return
        raise TypeError("BadType", f"{param_value} has type {type(param_value)} which is not in {str(param_type)}")
