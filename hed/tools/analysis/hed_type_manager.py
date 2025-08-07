""" Manager for type factors and type definitions. """

import pandas as pd
import json
from hed.tools.analysis.hed_type import HedType
from hed.tools.analysis.event_manager import EventManager


class HedTypeManager:
    """ Manager for type factors and type definitions. """

    def __init__(self, event_manager):
        """ Create a variable manager for one tabular file for all type variables.

        Parameters:
            event_manager (EventManager): An event manager for the tabular file.

        Raises:
            HedFileError: On errors such as unmatched onsets or missing definitions.

        """

        self.event_manager = event_manager
        self._type_map = {}   # a map of type tag into HedType objects

    @property
    def types(self):
        """ Return a list of types managed by this manager.

        Returns:
            list:  Type tags names.
        """

        return list(self._type_map.keys())

    def add_type(self, type_name):
        """ Add a type variable to be managed by this manager.

        Parameters:
            type_name (str):  Type tag name of the type to be added.

        """
        if type_name.casefold() in self._type_map:
            return
        self._type_map[type_name.casefold()] = \
            HedType(self.event_manager, 'run-01', type_tag=type_name)

    def get_factor_vectors(self, type_tag, type_values=None, factor_encoding="one-hot"):
        """ Return a DataFrame of factor vectors for the indicated HED tag and values.

        Parameters:
            type_tag (str):    HED tag to retrieve factors for.
            type_values (list or None):  The values of the tag to create factors for or None if all unique values.
            factor_encoding (str):   Specifies type of factor encoding (one-hot or categorical).

        Returns:
            Union[pd.DataFrame, None]:   DataFrame containing the factor vectors as the columns.

        """
        this_var = self.get_type(type_tag.casefold())
        if this_var is None:
            return None
        variables = this_var.get_type_value_names()
        if not type_values:
            type_values = variables
        df_list = [0]*len(type_values)
        for index, variable in enumerate(type_values):
            var_sum = this_var._type_map[variable]
            df_list[index] = var_sum.get_factors(factor_encoding=factor_encoding)
        if not df_list:
            return None
        return pd.concat(df_list, axis=1)

    def get_type(self, type_tag):
        """ Returns the HedType variable associated with the type tag.

        Parameters:
            type_tag (str): HED tag to retrieve the type for.

        Returns:
            Union[HedType, None]: the values associated with this type tag.

        """
        return self._type_map.get(type_tag.casefold(), None)

    def get_type_tag_factor(self, type_tag, type_value):
        """ Return the HedTypeFactors a specified value and extension.

        Parameters:
            type_tag (str or None):    HED tag for the type.
            type_value (str or None):  Value of this tag to return the factors for.

        """
        this_map = self._type_map.get(type_tag.casefold(), None)
        if this_map:
            return this_map._type_map.get(type_value.casefold(), None)
        return None

    def get_type_def_names(self, type_var):
        """ Return the definitions associated with a particular type tag.

        Parameters:
            type_var (str): The name of a type tag such as Condition-variable.

        Returns:
            list: Names of definitions that use this type.

        """
        this_map = self._type_map.get(type_var, None)
        if not this_map:
            return []
        return this_map.get_type_def_names()

    def summarize_all(self, as_json=False):
        """ Return a dictionary containing the summaries for the types managed by this manager.

        Parameters:
             as_json (bool): If False (the default), return as an object otherwise return as a JSON string.

        Returns:
            Union[dict, str]:  Dictionary with the summary.

        """
        summary = {}
        for type_tag, type_tag_var in self._type_map.items():
            summary[type_tag] = type_tag_var.get_summary()
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary

    def __str__(self):
        return f"Type_variables: {str(list(self._type_map.keys()))}"
