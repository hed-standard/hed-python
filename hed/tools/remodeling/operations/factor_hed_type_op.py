""" Create factors for a tabular file based on type variables. """

import pandas as pd
import numpy as np
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.analysis_util import get_assembled_strings
from hed.tools.analysis.hed_type_manager import HedTypeManager

# TODO: restricted factor values are not implemented yet.


class FactorHedTypeOp(BaseOp):
    """ Create factors for a tabular file based on a specified type of tag such as `condition-variable`.

   The required parameters are
        - type_tag (str): HED tag used to find the factors (most commonly `condition-variable`).
        - type_values (list): Factor values to include. If empty all values of that type_tag are used.

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
        super().__init__(self.PARAMS, parameters)
        self.type_tag = parameters["type_tag"]
        self.type_values = parameters["type_values"]

    def do_op(self, dispatcher, df, name, sidecar=None):
        """ Factor columns based on HED type.

        Parameters:
            dispatcher (Dispatcher): The dispatcher object for context.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like): Only needed for HED operations.

        Returns:
            DataFrame: a new DataFame with that includes the factors

        If column_name is not a column in df, df is just returned.

        """

        input_data = TabularInput(df, hed_schema=dispatcher.hed_schema, sidecar=sidecar)
        df = input_data.dataframe.copy()
        df_list = [df]
        hed_strings = get_assembled_strings(input_data, hed_schema=dispatcher.hed_schema, expand_defs=False)

        definitions = input_data.get_definitions()
        var_manager = HedTypeManager(hed_strings, dispatcher.hed_schema, definitions)
        var_manager.add_type_variable(self.type_tag.lower())

        df_factors = var_manager.get_factor_vectors(self.type_tag, [], factor_encoding="one-hot")
        if len(df_factors.columns) > 0:
            df_list.append(df_factors)
        df_new = pd.concat(df_list, axis=1)
        df_new.replace('n/a', np.NaN, inplace=True)
        return df_new
