""" Map values in m columns into a new combinations in n columns. """

import pandas as pd
import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.analysis.key_map import KeyMap


class RemapColumnsOp(BaseOp):
    """ Map values in m columns into a new combinations in n columns.

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
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "destination_columns": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            },
            "map_list": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": [
                            "string",
                            "number"
                        ]
                    },
                    "minItems" : 1
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "ignore_missing": {
                "type": "boolean"
            },
            "integer_sources": {
                "type": "array",
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
        super().__init__(self.PARAMS, parameters)
        self.source_columns = parameters['source_columns']
        self.integer_sources = []
        self.string_sources = self.source_columns
        if "integer_sources" in parameters:
            self.string_sources = list(
                set(self.source_columns).difference(set(self.integer_sources)))
        self.destination_columns = parameters['destination_columns']
        self.map_list = parameters['map_list']
        self.ignore_missing = parameters['ignore_missing']

        self.key_map = self._make_key_map()

    def _make_key_map(self):
        """

        :raises ValueError:
        - If a column designated as an integer source does not have valid integers.

        """
                            
        key_df = pd.DataFrame(
            self.map_list, columns=self.source_columns+self.destination_columns)
        key_map = KeyMap(self.source_columns,
                         target_cols=self.destination_columns, name="remap")
        key_map.update(key_df)
        return key_map

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Remap new columns from combinations of others.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Not needed for this operation.

        Returns:
            Dataframe: A new dataframe after processing.

        :raises ValueError:
            - If ignore_missing is false and source values from the data are not in the map.

        """
        df1 = df.copy()
        df1[self.source_columns] = df1[self.source_columns].replace(
            np.NaN, 'n/a')
        for column in self.integer_sources:
            int_mask = df1[column] != 'n/a'
            df1.loc[int_mask, column] = df1.loc[int_mask, column].astype(int)
        df1[self.source_columns] = df1[self.source_columns].astype(str)
        df_new, missing = self.key_map.remap(df1)
        if missing and not self.ignore_missing:
            raise ValueError("MapSourceValueMissing",
                             f"{name}: Ignore missing is false, but source values [{missing}] are in data but not map")
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        errors = []
        if len(set([len(x) for x in parameters.get("map_list")])) != 1:
            errors.append("The lists specified in the map_list parameter in the remap_columns operation should all have the same length.")
        else:
            if (len(parameters.get('source_columns')) + len(parameters.get("destination_columns"))) != len(parameters.get("map_list")[0]):
                errors.append("The lists specified in the map_list parameter in the remap_columns operation should have a length equal to the number of source columns + the number of destination columns.")
        if parameters.get("integer_sources", False):
            if not all([(x in parameters.get("source_columns")) for x in parameters.get("integer_sources")]):
                errors.append("All integer_sources in the remap_columns operation should be source_columns.")       
        return errors
