""" Implementation in progress. """

from hed.tools.remodeling.operations.base_op import BaseOp


# TODO: This class is under development


class NumberGroupsOp(BaseOp):
    """ Implementation in progress. """
    NAME = "number_groups"

    PARAMS = {
        "type": "object",
        "properties": {
            "number_column_name": {
                "type": "string"
            },
            "source_column": {
                "type": "string"
            },
            "start": {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array"
                    },
                    "inclusion": {
                        "type": "string",
                        "enum": [
                            "include",
                            "exclude"
                        ]
                    }
                },
                "required": [
                    "values",
                    "inclusion"
                ],
                "additionalProperties": False
            },
            "stop": {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array"
                    },
                    "inclusion": {
                        "type": "string",
                        "enum": [
                            "include",
                            "exclude"
                        ]
                    }
                },
                "required": [
                    "values",
                    "inclusion"
                ],
                "additionalProperties": False
            },
            "overwrite": {
                "type": "boolean"
            }
        },
        "required": [
            "number_column_name",
            "source_column",
            "start",
            "stop"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        super().__init__(parameters)
        self.number_column_name = parameters['number_column_name']
        self.source_column = parameters['source_column']
        self.start = parameters['start']
        self.stop = parameters['stop']
        self.start_stop_test = {"values": list, "inclusion": str}
        self.inclusion_test = ["include", "exclude"]
        self.overwrite = parameters.get('overwrite', False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Add numbers to groups of events in dataframe.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame):  The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

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
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
