""" Manager for type factors and type definitions. """

import pandas as pd
import json
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.tools.analysis.hed_context_manager import HedContextManager


class HedTypeManager:

    def __init__(self, hed_strings, hed_schema, definitions):
        """ Create a variable manager for one tabular file for all type variables.

        Parameters:
            hed_strings (list): A list of HED strings.
            hed_schema (HedSchema or HedSchemaGroup): The HED schema to use for processing.
            definitions (dict): A dictionary of DefinitionEntry objects.

        Raises:
            HedFileError:  On errors such as unmatched onsets or missing definitions.
        """

        self.definitions = definitions
        self.context_manager = HedContextManager(hed_strings, hed_schema)
        self._type_tag_map = {}   # a map of type tag into HedTypeValues objects

    @property
    def type_variables(self):
        return list(self._type_tag_map.keys())

    def add_type_variable(self, type_name):
        if type_name.lower() in self._type_tag_map:
            return
        self._type_tag_map[type_name.lower()] = \
            HedTypeValues(self.context_manager, self.definitions, 'run-01', type_tag=type_name)

    def get_factor_vectors(self, type_tag, type_values=None, factor_encoding="one-hot"):
        """ Return a DataFrame of factor vectors for the indicated HED tag and values

        Parameters:
            type_tag (str):    HED tag to retrieve factors for.
            type_values (list or None):  The values of the tag to create factors for or None if all unique values.
            factor_encoding (str):   Specifies type of factor encoding (one-hot or categorical).

        Returns:
            DataFrame:   DataFrame containing the factor vectors as the columns.

        """
        this_var = self.get_type_variable(type_tag)
        if this_var is None:
            return None
        variables = this_var.get_type_value_names()
        if variables is None:
            variables = type_values
        df_list = [0]*len(variables)
        for index, variable in enumerate(variables):
            var_sum = this_var._type_value_map[variable]
            df_list[index] = var_sum.get_factors(factor_encoding=factor_encoding)
        return pd.concat(df_list, axis=1)

    def get_type_variable(self, type_tag):
        """

        Parameters:
            type_tag (str): Hed tag to retrieve the type for

        Returns:
            HedTypeValues or None: the values associated with this type tag

        """
        return self._type_tag_map.get(type_tag.lower(), None)

    def get_type_tag_factor(self, type_tag, type_value):
        """ Return the HedTypeFactors a specified value and extension.

        Parameters:
            type_tag (str or None):    HED tag for the type
            type_value (str or None):  Value of this tag to return the factors for.

        """
        this_map = self._type_tag_map.get(type_tag.lower(), None)
        if this_map:
            return this_map._type_value_map.get(type_value.lower(), None)
        return None

    def get_type_tag_def_names(self, type_var):
        this_map = self._type_tag_map.get(type_var, None)
        if not this_map:
            return []
        return this_map.get_type_def_names()

    def summarize_all(self, as_json=False):
        summary = {}
        for type_tag, type_tag_var in self._type_tag_map.items():
            summary[type_tag] = type_tag_var.get_summary()
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary

    def __str__(self):
        return f"Type_variables: {str(list(self._type_tag_map.keys()))}"


# if __name__ == '__main__':
#     import os
#     from hed import Sidecar, TabularInput
#     from hed.tools.analysis.analysis_util import get_assembled_strings
#     schema = load_schema_version(xml_version="8.1.0")
#
#     bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#                                                    '../../../tests/data/bids_tests/eeg_ds003645s_hed'))
#     events_path = os.path.realpath(os.path.join(bids_root_path,
#                                                 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
#     sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
#     sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
#     input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
#     assembled_strings = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
#     definitions = input_data.get_definitions()
#     var_manager = HedTypeManager(assembled_strings, schema, definitions)
#     var_manager.add_type_variable("condition-variable")
#     var_cond = var_manager.get_type_variable("condition-variable")
#     var_summary = var_cond.get_summary()
#     summary_total = var_manager.summarize_all()
