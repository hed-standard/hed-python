""" Split rows in a columnar file with  onset and duration columns into multiple rows based on a specified column. """

import numpy as np
import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class SplitRowsOp(BaseOp):
    """ Split rows in a columnar file with  onset and duration columns into multiple rows based on a specified column.

    Required remodeling parameters:
        - **anchor_column** (*str*): The column in which the names of new items are stored.
        - **new_events** (*dict*):  Mapping of new values based on values in the original row.
        - **remove_parent_row** (*bool*):  If true, the original row that was split is removed.

    Notes:
        - In specifying onset and duration for the new row, you can give values or the names of columns as strings.

    """
    NAME = "split_rows"

    PARAMS = {
        "type": "object",
        "properties": {
            "anchor_column": {
                "type": "string",
                "description": "The column containing the keys for the new rows. (Original rows will have own keys.)"
            },
            "new_events": {
                "type": "object",
                "description": "A map describing how the rows for the new codes will be created.",
                "patternProperties": {
                    ".*": {
                        "type": "object",
                        "properties": {
                            "onset_source": {
                                "type": "array",
                                "description": "List of items to add to compute the onset time of the new row.",
                                "items": {
                                    "type": [
                                        "string",
                                        "number"
                                    ]
                                },
                                "minItems": 1
                            },
                            "duration": {
                                "type": "array",
                                "description": "List of items to add to compute the duration of the new row.",
                                "items": {
                                    "type": [
                                        "string",
                                        "number"
                                    ]
                                },
                                "minItems": 1
                            },
                            "copy_columns": {
                                "type": "array",
                                "description": "List of columns whose values to copy for the new row.",
                                "items": {
                                    "type": "string"
                                },
                                "minItems": 1,
                                "uniqueItems": True
                            }
                        },
                        "required": [
                            "onset_source",
                            "duration"
                        ],
                        "additionalProperties": False
                    }
                },
                "minProperties": 1
            },
            "remove_parent_row": {
                "type": "boolean",
                "description": "If true, the row from which these rows were split is removed, otherwise it stays."
            }
        },
        "required": [
            "anchor_column",
            "new_events",
            "remove_parent_row"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for the split rows operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.anchor_column = parameters['anchor_column']
        self.new_events = parameters['new_events']
        self.remove_parent_row = parameters['remove_parent_row']

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Split a row representing a particular event into multiple rows.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:
            TypeError: If bad onset or duration.

        """
        if 'onset' not in df.columns:
            raise ValueError("MissingOnsetColumn",
                             f"{name}: Data must have an onset column for split_rows_op")
        elif 'duration' not in df.columns:
            raise ValueError("MissingDurationColumn",
                             f"{name}: Data must have an duration column for split_rows_op")
        df_new = df.copy()

        if self.anchor_column not in df_new.columns:
            df_new[self.anchor_column] = np.nan
        if self.remove_parent_row:
            df_list = []
        else:
            df_list = [df_new]
        self._split_rows(df, df_list)
        df_ret = pd.concat(df_list, axis=0, ignore_index=True)
        df_ret["onset"] = df_ret["onset"].apply(pd.to_numeric)
        df_ret = df_ret.sort_values('onset').reset_index(drop=True)
        return df_ret

    def _split_rows(self, df, df_list):
        """ Split the rows based on an anchor and different columns.

        Parameters:
            df (DataFrame):  The DataFrame to be split.
            df_list (list):  The list of split events and possibly the

        """
        for event, event_params in self.new_events.items():
            add_events = pd.DataFrame([], columns=df.columns)
            add_events['onset'] = self._create_onsets(
                df, event_params['onset_source'])
            add_events[self.anchor_column] = event
            self._add_durations(df, add_events, event_params['duration'])
            if len(event_params['copy_columns']) > 0:
                for column in event_params['copy_columns']:
                    add_events[column] = df[column]

            # add_events['event_type'] = event
            add_events = add_events.dropna(axis='rows', subset=['onset'])
            df_list.append(add_events)

    @staticmethod
    def _add_durations(df, add_events, duration_sources):
        add_events['duration'] = 0
        for duration in duration_sources:
            if isinstance(duration, float) or isinstance(duration, int):
                add_events['duration'] = add_events['duration'].add(duration)
            elif isinstance(duration, str) and duration in list(df.columns):
                add_events['duration'] = add_events['duration'].add(
                    pd.to_numeric(df[duration], errors='coerce'))
            else:
                raise TypeError("BadDurationInModel",
                                f"Remodeling duration {str(duration)} must either be numeric or a column name", "")

    @staticmethod
    def _create_onsets(df, onset_source):
        """ Create a vector of onsets for the new events.

        Parameters:
            df (DataFrame):  The dataframe to process.
            onset_source (list):  List of onsets of process.

        Returns:
            list:  list of same length as df with the onsets.

        :raises HedFileError:
            - If one of the onset specifiers is invalid.

        """

        onsets = pd.to_numeric(df['onset'], errors='coerce')
        for onset in onset_source:
            if isinstance(onset, float) or isinstance(onset, int):
                onsets = onsets + onset
            elif isinstance(onset, str) and onset in list(df.columns):
                onsets = onsets.add(pd.to_numeric(df[onset], errors='coerce'))
            else:
                raise TypeError("BadOnsetInModel",
                                f"Remodeling onset {str(onset)} must either be numeric or a column name.", "")
        return onsets

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
