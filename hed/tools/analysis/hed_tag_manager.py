""" Manager for the HED tags in a tabular file. """

import pandas as pd
import json
from hed.tools.analysis.hed_type import HedType
from hed.models import HedString
from hed.models.string_util import split_base_tags, split_def_tags
from hed.tools.analysis.hed_type_defs import HedTypeDefs


class HedTagManager:

    def __init__(self, event_manager, remove_types=None, include_context=False):
        """ Create a tag manager for one tabular file.

        Parameters:
            event_manager (EventManager): an event manager for the tabular file.
            remove_types (list or None): List of type tags (such as condition-variable) to remove.
            include_context (bool):  If True, include the context.

        """

        self.event_manager = event_manager
        self.remove_types = remove_types
        [self.hed_strings, self.base_strings, self.context_strings] = self.event_manager.unfold_context()
        self.type_def_names = self.event_manager.find_type_defs(remove_types)

    def get_hed_objs(self, include_context=True):
        hed_objs = [None for _ in range(len(self.event_manager.onsets))]
        for index in range(len(hed_objs)):
            hed_list = self.hed_strings[index] + self.base_strings[index]
            if hed_list:
                hed = ",".join(hed_list)
            else:
                hed = ""
            if include_context and self.context_strings[index]:
                hed = hed + ',(Event-context, (' + ",".join(self.context_strings[index]) + "))"

            hed_objs[index] = HedString(hed,self.event_manager.hed_schema,  def_dict=self.event_manager.def_dict)
        return hed_objs

    def filter_types(self, hed_strings, types, groups=False):
        hed_objs = [None for _ in range(len(hed_strings))]
        for hed in hed_strings:
            if not hed:
                continue
    def get_hed_string_obj(self, hed_str, filter_types=False):
        hed_obj = HedString(hed_str, self.event_manager.hed_schema, def_dict=self.event_manager.def_dict)
        # if filter_types:
        #     hed_obj = hed_obj
        for def_tag in hed_obj.find_def_tags(recursive=True, include_groups=0):
            hed_obj.replace(def_tag, def_tag.expandable.get_first_group())
        return hed_obj
    # def _initialize(self):
    #     for index in range(len(hed)):
    #         keep_hed = hed[index].copy()
    #         for type_name in self.remove_types:
    #             keep_hed, lose_hed =  split_base_tags(keep_hed, type_name)
    #             print(f"Keep {keep_hed}")
    #             print(f"Lose {lose_hed}")
    #     

    # def _extract_definition_variables(self, item, index):
    #     """ Extract the definition uses from a HedTag, HedGroup, or HedString.
    # 
    #     Parameters:
    #         item (HedTag, HedGroup, or HedString): The item to extract variable information from.
    #         index (int):  Position of this item in the object's hed_strings.
    # 
    #     Notes:
    #         This updates the HedTypeFactors information.
    # 
    #     """
    # 
    #     if isinstance(item, HedTag):
    #         tags = [item]
    #     else:
    #         tags = item.get_all_tags()
    #     for tag in tags:
    #         if tag.short_base_tag.lower() != "def":
    #             continue
    #         hed_vars = self.type_defs.get_type_values(tag)
    #         if not hed_vars:
    #             continue
    #         self._update_definition_variables(tag, hed_vars, index)
    # 
    # def _update_definition_variables(self, tag, hed_vars, index):
    #     """Update the HedTypeFactors map with information from Def tag.
    # 
    #     Parameters:
    #         tag (HedTag): A HedTag that is a Def tag.
    #         hed_vars (list): A list of names of the hed type_variables
    #         index (ind):  The event number associated with this.
    # 
    #     Notes:
    #         This modifies the HedTypeFactors map.
    # 
    #     """
    #     level = tag.extension.lower()
    #     for var_name in hed_vars:
    #         hed_var = self._type_map.get(var_name, None)
    #         if hed_var is None:
    #             hed_var = HedTypeFactors(self.type_tag, var_name, self.total_events)
    #             self._type_map[var_name] = hed_var
    #         var_levels = hed_var.levels.get(level, {index: 0})
    #         var_levels[index] = 0
    #         hed_var.levels[level] = var_levels
    # 
    # def _extract_variables(self):
    #     """ Extract all type_variables from hed_strings and event_contexts. """
    # 
    #     hed, context = self.event_manager.unfold_context()
    #     for index in range(len(hed)):
    #         this_list = hed[index] + context[index]  # list of strings
    #         if not this_list:    # empty lists don't contribute
    #             continue
    #         this_hed = HedString(",".join(this_list), self.event_manager.hed_schema)
    #         self._extract_direct_variables(this_hed, index)
    #         self._extract_definition_variables(this_hed, index)
    # 
    # def _extract_direct_variables(self, item, index):
    #     """ Extract the condition type_variables from a HedTag, HedGroup, or HedString.
    # 
    #     Parameters:
    #         item (HedTag or HedGroup): The item from which to extract condition type_variables.
    #         index (int):  Position in the array.
    # 
    #     """
    #     if isinstance(item, HedTag) and item.short_base_tag.lower() == self.type_tag:
    #         tag_list = [item]
    #     elif isinstance(item, HedGroup) and item.children:
    #         tag_list = item.find_tags_with_term(self.type_tag, recursive=True, include_groups=0)
    #     else:
    #         tag_list = []
    #     self._update_variables(tag_list, index)