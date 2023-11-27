""" Base class for remodeling operations. """

from abc import ABC, abstractmethod

class BaseOp(ABC):
    """ Base class for operations. All remodeling operations should extend this class."""

    def __init__(self, parameters):
        """"""
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
