""" Manager for the HED tags in a tabular file. """

from hed.models import HedString
from hed.models.string_util import split_base_tags


class HedTagManager:

    def __init__(self, event_manager, remove_types=[]):
        """ Create a tag manager for one tabular file.

        Parameters:
            event_manager (EventManager): an event manager for the tabular file.
            remove_types (list or None): List of type tags (such as condition-variable) to remove.

        """

        self.event_manager = event_manager
        self.remove_types = remove_types
        self.hed_strings, self.base_strings, self.context_strings = (
            self.event_manager.unfold_context(remove_types=remove_types))
        self.type_def_names = self.event_manager.get_type_defs(remove_types)

    # def get_hed_objs1(self, include_context=True):
    #     hed_objs = [None for _ in range(len(self.event_manager.onsets))]
    #     for index in range(len(hed_objs)):
    #         hed_list = [self.hed_strings[index], self.base_strings[index]]
    #         if include_context and self.context_strings[index]:
    #             hed_list.append('(Event-context, (' + self.context_strings[index] + "))")
    #         hed_objs[index] = self.event_manager.str_list_to_hed(hed_list)
    #     return hed_objs

    def get_hed_objs(self, include_context=True, replace_defs=False):
        hed_objs = [None for _ in range(len(self.event_manager.onsets))]
        for index in range(len(hed_objs)):
            hed_list = [self.hed_strings[index], self.base_strings[index]]
            if include_context and self.context_strings[index]:
                hed_list.append("(Event-context, (" + self.context_strings[index] + "))")
            hed_objs[index] = self.event_manager.str_list_to_hed(hed_list)
            if replace_defs and hed_objs[index]:
                for def_tag in hed_objs[index].find_def_tags(recursive=True, include_groups=0):
                    hed_objs[index].replace(def_tag, def_tag.expandable.get_first_group())
        return hed_objs

    def get_hed_obj(self, hed_str, remove_types=False, remove_group=False):
        if not hed_str:
            return None
        hed_obj = HedString(hed_str, self.event_manager.hed_schema, def_dict=self.event_manager.def_dict)
        if remove_types:
            hed_obj, temp = split_base_tags(hed_obj, self.remove_types, remove_group=remove_group)
        return hed_obj

    # def get_hed_string_obj(self, hed_str, filter_types=False):
    #     hed_obj = HedString(hed_str, self.event_manager.hed_schema, def_dict=self.event_manager.def_dict)
    #     # if filter_types:
    #     #     hed_obj = hed_obj
    #     return hed_obj
