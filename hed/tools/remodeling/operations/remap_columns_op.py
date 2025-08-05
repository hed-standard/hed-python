""" Map values in m columns in a columnar file into a new combinations in n columns. """

import pandas as pd
import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.analysis.key_map import KeyMap


class RemapColumnsOp(BaseOp):
    """ Map values in m columns in a columnar file into a new combinations in n columns.

    Required remodeling parameters:
        - **source_columns** (*list*): The key columns to map (m key columns).
        - **destination_columns** (*list*): The destination columns to have the mapped values (n destination columns).
        - **map_list** (*list*): A list of lists with the mapping.
        - **ignore_missing** (*bool*): If True, entries whose key column values are not in map_list are ignored.

    Optional remodeling parameters:
        **integer_sources** (*list*): Source columns that should be treated as integers rather than strings.

    Notes:
        Each list element list is of length m + n with the key columns followed by mapped columns.

    TODO: Allow wildcards

    """
    NAME = "remap_columns"

    PARAMS = {
        "type": "object",
        "properties": {
            "source_columns": {
                "type": "array",
                "description": "The columns whose values are combined to provide the remap keys.",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "destination_columns": {
                "type": "array",
                "description": "The columns to insert new values based on a key lookup of the source columns.",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "map_list": {
                "type": "array",
                "description": "An array of k lists each with m+n entries corresponding to the k unique keys.",
                "items": {
                    "type": "array",
                    "items": {
                        "type": [
                            "string",
                            "number"
                        ]
                    },
                    "minItems": 1
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "ignore_missing": {
                "type": "boolean",
                "description": "If true, insert missing source columns in the result, filled with n/a, else error."
            },
            "integer_sources": {
                "type": "array",
                "description": "A list of source column names whose values are to be treated as integers.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            }
        },
        "required": [
            "source_columns",
            "destination_columns",
            "map_list",
            "ignore_missing"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for the remap columns operation.

            Parameters:
                parameters (dict): Parameter values for required and optional parameters.

          """
        super().__init__(parameters)
        self.source_columns = parameters['source_columns']
        self.destination_columns = parameters['destination_columns']
        self.map_list = parameters['map_list']
        self.ignore_missing = parameters['ignore_missing']
        self.string_sources = self.source_columns
        self.integer_sources = parameters.get('integer_sources', [])
        self.string_sources = list(set(self.source_columns).difference(set(self.integer_sources)))
        self.key_map = self._make_key_map()

    def _make_key_map(self):
        """

        Raises:
            ValueError: If a column designated as an integer source does not have valid integers.

        """

        key_df = pd.DataFrame(
            self.map_list, columns=self.source_columns+self.destination_columns)
        key_map = KeyMap(self.source_columns,
                         target_cols=self.destination_columns, name="remap")
        key_map.update(key_df)
        return key_map

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Remap new columns from combinations of others.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        :raises ValueError:
            - If ignore_missing is False and source values from the data are not in the map.

        """
        df1 = df.copy()
        df1[self.source_columns] = df1[self.source_columns].replace(
            np.nan, 'n/a')
        for column in self.integer_sources:
            int_mask = df1[column] != 'n/a'
            df1.loc[int_mask, column] = df1.loc[int_mask, column].astype(int)
        df1[self.source_columns] = df1[self.source_columns].astype(str)
        df_new, missing = self.key_map.remap(df1)
        if missing and not self.ignore_missing:
            raise ValueError("MapSourceValueMissing",
                             f"{name}: Ignore missing is False, but source values [{missing}] are in data but not map")
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        map_list = parameters["map_list"]
        required_len = len(parameters['source_columns']) + len(parameters['destination_columns'])
        for x in map_list:
            if len(x) != required_len:
                return [f"all map_list arrays must be of length {str(required_len)}."]
        missing = set(parameters.get('integer_sources', [])) - set(parameters['source_columns'])
        if missing:
            return [f"the integer_sources {str(missing)} are missing from source_columns."]
        return []
