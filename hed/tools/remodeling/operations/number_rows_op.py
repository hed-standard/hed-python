""" Implementation in progress. """

from hed.tools.remodeling.operations.base_op import BaseOp

# TODO: This class is under development


class NumberRowsOp(BaseOp):
    """ Implementation in progress. """
    NAME = "number_rows"

    PARAMS = {
        "type": "object",
        "properties": {
            "number_column_name": {
                "type": "string"
            },
            "overwrite": {
                "type": "boolean"
            },
            "match_value": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string"
                    },
                    "value": {
                        "type": [
                            "string",
                            "number"
                        ]
                    }
                },
                "required": [
                    "column",
                    "value"
                ],
                "additionalProperties": False
            }
        },
        "required": [
            "number_column_name"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        super().__init__(parameters)
        self.number_column_name = parameters['number_column_name']
        self.overwrite = parameters.get('overwrite', False)
        self.match_value = parameters.get('match_value', False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Add numbers events dataframe.

        Parameters:
            dispatcher (Dispatcher): Manages operation I/O.
            df (DataFrame): - The DataFrame to be remodeled.
            name (str): - Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):   Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        """
        if self.number_column_name in df.columns:
            if self.overwrite is False:
                raise ValueError("ExistingNumberColumn",
                                 f"Column {self.number_column_name} already exists in event file.", "")

        if self.match_value:
            if self.match_value['column'] not in df.columns:
                raise ValueError("MissingMatchColumn",
                                 f"Column {self.match_value['column']} does not exist in event file.", "")
            if self.match_value['value'] not in df[self.match_value['column']].tolist():
                raise ValueError("MissingMatchValue",
                                 f"Value {self.match_value['value']} does not exist in event file column"
                                 f"{self.match_value['column']}.", "")

        df_new = df.copy()
        # df_new[self.number_column_name] = np.nan
        # if self.match_value:
        #     filter = df[self.match_value['column']] == self.match_value['value']
        #     numbers = [*range(1, sum(filter)+1)]
        #     df_new.loc[filter, self.number_column_name] = numbers
        # else:
        #     df_new[self.number_column_name] = df_new.index + 1

        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
