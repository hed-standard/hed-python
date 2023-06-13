""" Create tabular file factors from type variables. """

import pandas as pd
import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.models.tabular_input import TabularInput
from hed.models.sidecar import Sidecar
from hed.models.df_util import get_assembled
from hed.tools.analysis.hed_type_manager import HedTypeManager

# TODO: restricted factor values are not implemented yet.


class FactorHedTypeOp(BaseOp):
    """ Create tabular file factors from type variables and append to tabular data.

    Required remodeling parameters:   
        - **type_tag** (*str*): HED tag used to find the factors (most commonly `condition-variable`).   
        - **type_values** (*list*): Factor values to include. If empty all values of that type_tag are used.   

    """

    PARAMS = {
        "operation": "factor_hed_type",
        "required_parameters": {
            "type_tag": str,
            "type_values": list
        },
        "optional_parameters": {}
    }

    def __init__(self, parameters):
        """ Constructor for the factor HED type operation.

        Parameters:
            parameters (dict):  Actual values of the parameters for the operation.

        :raises KeyError:
            - If a required parameter is missing.
            - If an unexpected parameter is provided.

        :raises TypeError:
            - If a parameter has the wrong type.

        :raises ValueError:
            - If the specification is missing a valid operation.

        """
        super().__init__(self.PARAMS, parameters)
        self.type_tag = parameters["type_tag"]
        self.type_values = parameters["type_values"]

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Factor columns based on HED type and append to tabular data.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: A new DataFame with that includes the factors.

        Notes:
            - If column_name is not a column in df, df is just returned.

        """

        if sidecar and not isinstance(sidecar, Sidecar):
            sidecar = Sidecar(sidecar)
        input_data = TabularInput(df, sidecar=sidecar, name=name)
        df_list = [input_data.dataframe.copy()]
        hed_strings, definitions = get_assembled(input_data, sidecar, dispatcher.hed_schema, 
                                                 extra_def_dicts=None, join_columns=True,
                                                 shrink_defs=True, expand_defs=False)

        var_manager = HedTypeManager(hed_strings, dispatcher.hed_schema, definitions)
        var_manager.add_type_variable(self.type_tag.lower())

        df_factors = var_manager.get_factor_vectors(self.type_tag, [], factor_encoding="one-hot")
        if len(df_factors.columns) > 0:
            df_list.append(df_factors)
        df_new = pd.concat(df_list, axis=1)
        df_new.replace('n/a', np.NaN, inplace=True)
        return df_new
