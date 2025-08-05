""" Append to columnar file the factors computed from type variables. """

import pandas as pd
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_type_manager import HedTypeManager
from hed.tools.util.data_util import replace_na


class FactorHedTypeOp(BaseOp):
    """ Append to columnar file the factors computed from type variables.

    Required remodeling parameters:
        - **type_tag** (*str*): HED tag used to find the factors (most commonly `condition-variable`).

    Optional remodeling parameters:
        - **type_values** (*list*): If provided, specifies which factor values to include.

    """
    NAME = "factor_hed_type"

    PARAMS = {
        "type": "object",
        "properties": {
            "type_tag": {
                "type": "string",
                "description": "Type tag to use for computing factor vectors (e.g., Condition-variable or Task)."
            },
            "type_values": {
                "type": "array",
                "description": "If provided, only compute one-hot factors for these values of the type tag.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            }
        },
        "required": [
            "type_tag"
        ],
        "additionalProperties": False
    }

    def __init__(self, parameters):
        """ Constructor for the factor HED type operation.

        Parameters:
            parameters (dict):  Actual values of the parameters for the operation.

        """
        super().__init__(parameters)
        self.type_tag = parameters["type_tag"]
        self.type_values = parameters.get("type_values", None)

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
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

        input_data = TabularInput(df.copy().fillna('n/a'), sidecar=sidecar, name=name)
        df_list = [input_data.dataframe]
        var_manager = HedTypeManager(EventManager(input_data, dispatcher.hed_schema))
        var_manager.add_type(self.type_tag.casefold())

        df_factors = var_manager.get_factor_vectors(
            self.type_tag, self.type_values, factor_encoding="one-hot")
        if len(df_factors.columns) > 0:
            df_list.append(df_factors)
        df_new = pd.concat(df_list, axis=1)
        replace_na(df_new)
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []
