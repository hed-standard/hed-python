import numpy as np
import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp

PARAMS = {
    "command": "split_events",
    "required_parameters": {
        "anchor_column": str,
        "new_events": dict,
        "remove_parent_event": bool
    },
    "optional_parameters": {}
}


class SplitEventOp(BaseOp):

    def __init__(self, parameters):
        super().__init__(PARAMS["command"], PARAMS["required_parameters"], PARAMS["optional_parameters"])
        self.check_parameters(parameters)
        self.anchor_column = parameters['anchor_column']
        self.new_events = parameters['new_events']
        self.remove_parent_event = parameters['remove_parent_event']

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Split a row representing a particular event into multiple rows.

        Args:
            dispatcher (Dispatcher) - dispatcher object for context
            df (DataFrame) - The DataFrame to be remodeled.
            name (str) - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like)   Only needed for HED operations.

        Returns:
            Dataframe - a new dataframe after processing.

        Raises:
            TypeError - if bad onset or duration.

        """

        df_new = df.copy()

        if self.anchor_column not in df_new.columns:
            df_new[self.anchor_column] = np.nan
        # new_df = pd.DataFrame('n/a', index=range(len(df.index)), columns=df.columns)
        if self.remove_parent_event:
            df_list = []
        else:
            df_list = [df_new]
        for event, event_parms in self.new_events.items():
            add_events = pd.DataFrame([], columns=df.columns)
            onsets = pd.to_numeric(df['onset'], errors='coerce')

            for onset in event_parms['onset_source']:
                if isinstance(onset, float) or isinstance(onset, int):
                    onsets = onsets + onset
                elif isinstance(onset, str) and onset in list(df.columns):
                    onsets = onsets.add(pd.to_numeric(df[onset], errors='coerce'))
                else:
                    raise TypeError("BadOnsetInModel",
                                    f"Remodeling onset {str(onset)} must either be numeric or a column name", "")
            add_events['onset'] = onsets
            add_events[self.anchor_column] = event
            # remove events if there is no onset (=no response)
            add_events['duration'] = 0
            for duration in event_parms['duration']:
                if isinstance(duration, float) or isinstance(duration, int):
                    add_events['duration'] = add_events['duration'].add(duration)
                elif isinstance(duration, str) and duration in list(df.columns):
                    add_events['duration'] = add_events['duration'].add(pd.to_numeric(df[duration], errors='coerce'))
                else:
                    raise TypeError("BadDurationInModel",
                                    f"Remodeling duration {str(duration)} must either be numeric or a column name", "")

            if len(event_parms['copy_columns']) > 0:
                for column in event_parms['copy_columns']:
                    add_events[column] = df_new[column]

            # add_events['event_type'] = event
            add_events = add_events.dropna(axis='rows', subset=['onset'])
            df_list.append(add_events)

        df_new = pd.concat(df_list, axis=0, ignore_index=True)
        df_new = df_new.sort_values('onset').reset_index(drop=True)
        return df_new
