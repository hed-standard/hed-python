""" Number groups of rows in a dataframe based on start and stop markers. """

import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp


class NumberGroupsOp(BaseOp):
    """ Number groups of rows in a dataframe based on start and stop
    markers.

    Required remodeling parameters:
        - **number_column_name** (*str*): The name of the column to add
          with the group numbers.
        - **source_column** (*str*): The column to check for start and
          stop markers.
        - **start** (*dict*): Specification for start markers.
            - **values** (*list*): List of values that mark the start of
              a group.
            - **inclusion** (*str*): Either "include" or "exclude" to
              specify whether the start marker row should be included in
              the group.
        - **stop** (*dict*): Specification for stop markers.
            - **values** (*list*): List of values that mark the end of
              a group.
            - **inclusion** (*str*): Either "include" or "exclude" to
              specify whether the stop marker row should be included in
              the group.

    Optional remodeling parameters:
        - **overwrite** (*bool*): If true, overwrite an existing column
          with the same name.

    """
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
        """ Add numbers to groups of rows in the events dataframe.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame):  The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the
                original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        """
        # check if number_column_name exists and if so, check overwrite
        # setting
        if self.number_column_name in df.columns:
            if self.overwrite is False:
                raise ValueError(
                    "ExistingNumberColumn",
                    f"Column {self.number_column_name} already exists "
                    f"in event file.", "")

        # check if source_column exists
        if self.source_column not in df.columns:
            raise ValueError(
                "MissingSourceColumn",
                f"Column {self.source_column} does not exist in event "
                f"file {name}.", "")

        # check if all elements in value lists start and stop exist in
        # the source_column
        missing = []
        for element in self.start['values']:
            if element not in df[self.source_column].tolist():
                missing.append(element)
        if len(missing) > 0:
            raise ValueError(
                "MissingValue",
                f"Start value(s) {missing} does not exist in "
                f"{self.source_column} of event file {name}")

        missing = []
        for element in self.stop['values']:
            if element not in df[self.source_column].tolist():
                missing.append(element)
        if len(missing) > 0:
            raise ValueError(
                "MissingValue",
                f"Start value(s) {missing} does not exist in "
                f"{self.source_column} of event file {name}")

        df_new = df.copy()
        df_new[self.number_column_name] = np.nan

        # Track current group number and whether we're inside a group
        current_group = 0
        in_group = False

        for idx in range(len(df_new)):
            # Use the original df to read source values in case we're
            # overwriting the source column
            value = df.iloc[idx][self.source_column]

            # Check if this is a start marker
            if value in self.start['values']:
                if not in_group:  # Start a new group only if not already
                    # in one
                    current_group += 1
                    in_group = True
                    if self.start['inclusion'] == 'include':
                        df_new.at[idx, self.number_column_name] = \
                            current_group
                # If already in a group and this is a start marker:
                # - If inclusion is 'exclude', it acts as both end and
                #   start
                elif self.start['inclusion'] == 'exclude':
                    # This marker ends the previous group and starts a
                    # new one
                    current_group += 1
                    # Don't assign the number to this row (it's excluded)
                continue

            # Check if this is a stop marker
            if value in self.stop['values']:
                if in_group:
                    if self.stop['inclusion'] == 'include':
                        df_new.at[idx, self.number_column_name] = \
                            current_group
                    in_group = False
                continue

            # Regular row - if in group, assign current group number
            if in_group:
                df_new.at[idx, self.number_column_name] = current_group

        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not
        performed by JSON schema validator. """
        return []
