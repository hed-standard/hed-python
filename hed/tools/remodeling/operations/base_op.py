""" Base class for remodeling operations. """

from abc import ABC, abstractmethod


class BaseOp(ABC):
    """ Base class for operations. All remodeling operations should extend this class."""

    def __init__(self, parameters):
        """ Constructor for the BaseOp class. Should be extended by operations.

        Parameters:
            parameters (dict): A dictionary specifying the appropriate parameters for the operation.
        """
        self.parameters = parameters

    @property
    @abstractmethod
    def NAME(self):
        pass

    @property
    @abstractmethod
    def PARAMS(self):
        pass

    @abstractmethod
    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Base class method to be overridden by each operation.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The tabular file to be remodeled.
            name (str): Unique identifier for the data -- often the original file path.
            sidecar (Sidecar or file-like):  A JSON sidecar needed for HED operations.

        """

        return df.copy()

    @staticmethod
    @abstractmethod
    def validate_input_data(parameters):
        """ Validates whether operation parameters meet op-specific criteria beyond that captured in json schema.

        Example: A check to see whether two input arrays are the same length.

        Notes: The minimum implementation should return an empty list to indicate no errors were found.
               If additional validation is necessary, method should perform the validation and
               return a list with user-friendly error strings.
        """
        return []
