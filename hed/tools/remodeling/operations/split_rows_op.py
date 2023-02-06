""" Split rows in a tabular file into multiple rows based on a column. """

import numpy as np
import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp


class SplitRowsOp(BaseOp):
    """ Split rows in a tabular file into multiple rows based on a column.

    Required remodeling parameters:   
        - **anchor_column** (*str*): The column in which new items are generated.   
        - **new_events** (*dict*):  Mapping of new values based on values in the anchor_column.   
        - **remove_parent_row** (*bool*):  If true, columns not in column_order are placed at end.   

    """

    PARAMS = {
        "operation": "split_rows",
        "required_parameters": {
            "anchor_column": str,
            "new_events": dict,
            "remove_parent_row": bool
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        """ Constructor for the split rows operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        Raises:
            KeyError   
                - If a required parameter is missing.   
                - If an unexpected parameter is provided.   

            TypeError   
                - If a parameter has the wrong type.   

        """
        super().__init__(self.PARAMS, parameters)
        self.anchor_column = parameters['anchor_column']
        self.new_events = parameters['new_events']
        self.remove_parent_row = parameters['remove_parent_row']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Split a row representing a particular event into multiple rows.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str):  Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:
            TypeError   
                -If bad onset or duration.   

        """

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
        for event, event_parms in self.new_events.items():
            add_events = pd.DataFrame([], columns=df.columns)
            add_events['onset'] = self._create_onsets(df, event_parms['onset_source'])
            add_events[self.anchor_column] = event
            self._add_durations(df, add_events, event_parms['duration'])
            if len(event_parms['copy_columns']) > 0:
                for column in event_parms['copy_columns']:
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
                add_events['duration'] = add_events['duration'].add(pd.to_numeric(df[duration], errors='coerce'))
            else:
                raise TypeError("BadDurationInModel",
                                f"Remodeling duration {str(duration)} must either be numeric or a column name", "")

    @staticmethod
    def _create_onsets(df, onset_source):
        """ Create a vector of onsets for the the new events.

        Parameters:
            df (DataFrame):  The dataframe to process.
            onset_source (list):  List of onsets of process.

        Returns:
            list:  list of same length as df with the onsets.

        Raises:
            HedFileError: raised if one of the onset specifiers is invalid.

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
