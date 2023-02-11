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
        **integer_sources** (*list*): Sour columns that should be treated as integers rather than strings.   

    Notes:
        Each list element list is of length m + n with the key columns followed by mapped columns. 
         
    TODO: Allow wildcards

    """

    PARAMS = {
        "operation": "remap_columns",
        "required_parameters": {
            "source_columns": list,
            "destination_columns": list,
            "map_list": list,
            "ignore_missing": bool
        },
        "optional_parameters": {
            "integer_sources": list
        }
    }

    def __init__(self, parameters):
        """ Constructor for the remap columns operation.

            Parameters:
                parameters (dict): Parameter values for required and optional parameters.

            Raises:
                KeyError   
                    - If a required parameter is missing.    
                    - If an unexpected parameter is provided.    
 
                TypeError   
                    - If a parameter has the wrong type.   

                ValueError   
                    - If an integer column is not a key column.    
                    - If a column designated as an integer source does not have valid integers.    
                    - If no source columns are specified.    
                    - If no destination columns are specified.    
                    - If a map_list entry has the wrong number of items (source columns + destination columns).    

          """
        super().__init__(self.PARAMS, parameters)
        self.source_columns = parameters['source_columns']
        self.integer_sources = []
        self.string_sources = self.source_columns
        if "integer_sources" in parameters:
            self.integer_sources = parameters['integer_sources']
            if not set(self.integer_sources).issubset(set(self.source_columns)):
                raise ValueError("IntegerSourceColumnsInvalid",
                                 f"Integer courses {str(self.integer_sources)} must be in {str(self.source_columns)}")
            self.string_sources = list(set(self.source_columns).difference(set(self.integer_sources)))
        self.destination_columns = parameters['destination_columns']
        self.map_list = parameters['map_list']
        self.ignore_missing = parameters['ignore_missing']
        if len(self.source_columns) < 1:
            raise ValueError("EmptySourceColumns",
                             f"The source column list {str(self.source_columns)} must be non-empty")

        if len(self.destination_columns) < 1:
            raise ValueError("EmptyDestinationColumns",
                             f"The destination column list {str(self.destination_columns)} must be non-empty")
        entry_len = len(self.source_columns) + len(self.destination_columns)
        for index, item in enumerate(self.map_list):
            if len(item) != entry_len:
                raise ValueError("BadColumnMapEntry",
                                 f"Map list entry {index} has {len(item)} elements, but must have {entry_len} elements")

        self.key_map = self._make_key_map()

    def _make_key_map(self):
        key_df = pd.DataFrame(self.map_list, columns=self.source_columns+self.destination_columns)
        key_map = KeyMap(self.source_columns, target_cols=self.destination_columns, name="remap")
        key_map.update(key_df)
        return key_map

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Remap new columns from combinations of others.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            Dataframe: A new dataframe after processing.

        Raises:
            ValueError   
                - If ignore_missing is false and source values from the data are not in the map.   

        """
        df[self.source_columns] = df[self.source_columns].replace(np.NaN, 'n/a')
        for column in self.integer_sources:
            int_mask = df[column] != 'n/a'
            df.loc[int_mask, column] = df.loc[int_mask, column].astype(int)
        df[self.source_columns] = df[self.source_columns].astype(str)
        df_new, missing = self.key_map.remap(df)
        if missing and not self.ignore_missing:
            raise ValueError("MapSourceValueMissing",
                             f"{name}: Ignore missing is false, but source values [{missing}] are in data but not map")
        return df_new
