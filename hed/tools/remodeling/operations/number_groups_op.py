""" Implementation in progress. """
import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.util.data_util import get_indices, tuple_to_range
import itertools

#TODO: This class is under development


class NumberGroupsOp(BaseOp):
    """ Implementation in progress. """

    PARAMS = {
        "operation": "number_groups",
        "required_parameters": {
            "number_column_name": str,
            "source_column": str,
            "start": dict,
            "stop": dict
        },
        "optional_parameters": {"overwrite": bool}
    }

    def __init__(self, parameters):
        super().__init__(self.PARAMS, parameters)
        self.number_column_name = parameters['number_column_name']
        self.source_column = parameters['source_column']
        self.start = parameters['start']
        self.stop = parameters['stop']
        self.start_stop_test = {"values": list, "inclusion": str}
        self.inclusion_test = ["include", "exclude"]

        required = set(self.start_stop_test.keys())
        for param_to_test in [self.start, self.stop]:
            required_missing = required.difference(set(param_to_test.keys()))
            if required_missing:
                raise KeyError("MissingRequiredParameters",
                               f"Specified {param_to_test} for number_rows requires parameters {list(required_missing)}")
            for param_name, param_value in param_to_test.items():
                param_type = str
                if param_name in required:
                    param_type = self.start_stop_test[param_name]
                else:
                    raise KeyError("BadParameter",
                                   f"{param_name} not a required or optional parameter for {self.operation}")
                # TODO: This has a syntax error
                # if not isinstance(param_value, param_type):
                #     raise TypeError("BadType" f"{param_value} has type {type(param_value)} not {param_type}")
                if (param_name == 'inclusion') & (param_value not in self.inclusion_test):
                    raise ValueError("BadValue" f" {param_name} must be one of {self.inclusion_test} not {param_value}")

        self.overwrite = parameters.get('overwrite', False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Add numbers to groups of events in dataframe.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame):  The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            Dataframe - a new dataframe after processing.

        """
        # check if number_column_name exists and if so, check overwrite setting
        if self.number_column_name in df.columns:
            if self.overwrite is False:
                raise ValueError("ExistingNumberColumn",
                                 f"Column {self.number_column_name} already exists in event file.", "")

        # check if source_column exists
        if self.source_column not in df.columns:
            raise ValueError("MissingSourceColumn",
                             f"Column {self.source_column} does not exist in event file {name}.", "")

        # check if all elements in value lists start and stop exist in the source_column
        missing = []
        for element in self.start['values']:
            if element not in df[self.source_column].tolist():
                missing.append(element)
        if len(missing) > 0:
            raise ValueError("MissingValue",
                             f"Start value(s) {missing} does not exist in {self.source_column} of event file {name}")

        missing = []
        for element in self.stop['values']:
            if element not in df[self.source_column].tolist():
                missing.append(element)
        if len(missing) > 0:
            raise ValueError("MissingValue",
                             f"Start value(s) {missing} does not exist in {self.source_column} of event file {name}")

        df_new = df.copy()
        # create number column
        df_new[self.number_column_name] = np.nan

        # find group indices
        indices = tuple_to_range(
            get_indices(df, self.source_column, self.start['values'], self.stop['values']),
            [self.start['inclusion'], self.stop['inclusion']])
        for i, group in enumerate(indices):
            df_new.loc[group, self.number_column_name] = i + 1

        return df_new
