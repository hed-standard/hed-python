""" Manager a type variable and its associated context. """
import pandas as pd
from hed.models.hed_group import HedGroup
from hed.models.hed_tag import HedTag
from hed.models.model_constants import DefTagNames
from hed.tools.analysis.hed_type_defs import HedTypeDefs
from hed.tools.analysis.hed_type_factors import HedTypeFactors


class HedType:
    """ Manager of a type variable and its associated context. """

    def __init__(self, event_manager, name, type_tag="condition-variable"):
        """ Create a variable manager for one type-variable for one tabular file.

        Parameters:
            event_manager (EventManager): Event manager instance
            name (str): Name of the tabular file as a unique identifier.
            type_tag (str): Lowercase short form of the tag to be managed.

        Raises:
            HedFileError: On errors such as unmatched onsets or missing definitions.

        """
        self.name = name
        self.type_tag = type_tag.casefold()
        self.event_manager = event_manager
        self.type_defs = HedTypeDefs(self.event_manager.def_dict, type_tag=type_tag)
        self._type_map = {}  # Dictionary of type tags versus dictionary with keys being definition names.
        self._extract_variables()

    @property
    def total_events(self):
        return len(self.event_manager.event_list)

    def get_type_value_factors(self, type_value):
        """ Return the HedTypeFactors associated with type_name or None.

        Parameters:
            type_value (str): The tag corresponding to the type's value (such as the name of the condition variable).

        Returns:
            Union[HedTypeFactors, None]

        """
        return self._type_map.get(type_value.casefold(), None)

    def get_type_value_level_info(self, type_value):
        """ Return type variable corresponding to type_value.

        Parameters:
            type_value (str) - name of the type variable

        Returns:


        """
        return self._type_map.get(type_value, None)

    @property
    def type_variables(self):
        return set(self._type_map.keys())

    def get_type_def_names(self):
        """ Return the type defs names """
        tag_list = []
        for variable, factor in self._type_map.items():
            tag_list = tag_list + [key for key in factor.levels.keys()]
        return list(set(tag_list))

    def get_type_value_names(self):
        return list(self._type_map.keys())

    def get_summary(self):
        var_summary = self._type_map.copy()
        summary = {}
        for var_name, var_sum in var_summary.items():
            summary[var_name] = var_sum.get_summary()
        return summary

    def get_type_factors(self, type_values=None, factor_encoding="one-hot"):
        """ Create a dataframe with the indicated type tag values as factors.

        Parameters:
            type_values (list or None): A list of values of type tags for which to generate factors.
            factor_encoding (str):      Type of factor encoding (one-hot or categorical).

        Returns:
            pd.DataFrame:  Contains the specified factors associated with this type tag.


        """
        if type_values is None:
            type_values = self.get_type_value_names()
        df_list = []
        for index, type_value in enumerate(type_values):
            var_sum = self._type_map.get(type_value, None)
            if not var_sum:
                continue
            df_list.append(var_sum.get_factors(factor_encoding=factor_encoding))
        if not df_list:
            return None
        else:
            return pd.concat(df_list, axis=1)

    def __str__(self):
        return f"{self.type_tag} type_variables: {str(list(self._type_map.keys()))}"

    def _extract_definition_variables(self, item, index):
        """ Extract the definition uses from a HedTag, HedGroup, or HedString.

        Parameters:
            item (HedTag, HedGroup, or HedString): The item to extract variable information from.
            index (int):  Position of this item in the object's hed_strings.

        Notes:
            This updates the HedTypeFactors information.

        """

        if isinstance(item, HedTag):
            tags = [item]
        else:
            tags = item.get_all_tags()
        for tag in tags:
            if tag.short_base_tag != DefTagNames.DEF_KEY:
                continue
            hed_vars = self.type_defs.get_type_values(tag)
            if not hed_vars:
                continue
            self._update_definition_variables(tag, hed_vars, index)

    def _update_definition_variables(self, tag, hed_vars, index):
        """Update the HedTypeFactors map with information from Def tag.

        Parameters:
            tag (HedTag): A HedTag that is a Def tag.
            hed_vars (list): A list of names of the HED type_variables
            index (ind):  The event number associated with this.

        Notes:
            This modifies the HedTypeFactors map.

        """
        level = tag.extension.casefold()
        for var_name in hed_vars:
            hed_var = self._type_map.get(var_name, None)
            if hed_var is None:
                hed_var = HedTypeFactors(self.type_tag, var_name, self.total_events)
                self._type_map[var_name] = hed_var
            var_levels = hed_var.levels.get(level, {index: 0})
            var_levels[index] = 0
            hed_var.levels[level] = var_levels

    def _extract_variables(self):
        """ Extract all type_variables from hed_strings and event_contexts. """

        hed, base, context = self.event_manager.unfold_context()
        for index in range(len(hed)):
            this_hed = self.event_manager.str_list_to_hed([hed[index], base[index], context[index]])
            if this_hed:
                tag_list = self.get_type_list(self.type_tag, this_hed)
                self._update_variables(tag_list, index)
                self._extract_definition_variables(this_hed, index)

    @staticmethod
    def get_type_list(type_tag, item):
        """ Find a list of the given type tag from a HedTag, HedGroup, or HedString.

        Parameters:
            type_tag (str): a tag whose direct items you wish to remove
            item (HedTag or HedGroup): The item from which to extract condition type_variables.

        Returns:
            list:  List of the items with this type_tag

        """
        if isinstance(item, HedTag) and item.short_base_tag.casefold() == type_tag:
            tag_list = [item]
        elif isinstance(item, HedGroup) and item.children:
            tag_list = item.find_tags_with_term(type_tag, recursive=True, include_groups=0)
        else:
            tag_list = []
        return tag_list

    def _update_variables(self, tag_list, index):
        """ Update the HedTypeFactors based on tags in the list.

        Parameters:
            tag_list (list): A list of Condition-variable HedTags.
            index (int):  An integer representing the position in an array

        """
        for tag in tag_list:
            tag_value = tag.extension.casefold()
            if not tag_value:
                tag_value = self.type_tag
            hed_var = self._type_map.get(tag_value, None)
            if hed_var is None:
                hed_var = HedTypeFactors(self.type_tag, tag_value, self.total_events)
            self._type_map[tag_value] = hed_var
            hed_var.direct_indices[index] = ''
