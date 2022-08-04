from hed.models import DefMapper

class Ops:
    def __init__(self, filter_name):
        self.filter_name = filter_name

    def __get_string_funcs__(self, **kwargs):
        return []

    def __get_tag_funcs__(self, **kwargs):
        return []


class CollapseDefs(Ops):

    def __init__(self, def_mapper):
        super().__init__("collapse_defs")
        self.def_mapper = def_mapper

    def get_string_funcs(self, **kwargs):
        string_funcs = [self.collapse_defs]
        return string_funcs

    def collapse_defs(self, hed_string):
        # self.def_mapper.expand_def_tags(self, hed_string, expand_defs=False, shrink_defs=True)
        if 'def-expand' not in hed_string.lower():
            return
        #
        # # We need to check for labels to expand in ALL groups
        # for def_tag, def_expand_group, def_group in hed_string.find_def_tags(recursive=True):
        #     def_contents = self._get_definition_contents(def_tag, def_expand_group, def_issues)
        #     if def_expand_group is def_tag:
        #         if def_contents is not None and expand_defs:
        #             def_tag.short_base_tag = DefTagNames.DEF_EXPAND_ORG_KEY
        #             def_group.replace(def_tag, def_contents)
        #     else:
        #         if def_contents is not None and shrink_defs:
        #             def_tag.short_base_tag = DefTagNames.DEF_ORG_KEY
        #             def_group.replace(def_expand_group, def_tag)
        #
        # return def_issues

    def expand_defs(self, hed_string):
        self.def_mapper.expand_def_tags(self, hed_string, expand_defs=True, shrink_defs=False)


class RemoveTagsFilter(Ops):

    def __init__(self, tag_names, remove_option="both"):
        super().__init__("remove_tags")
        self.tag_names = [tag_name.lower() for tag_name in tag_names]
        self.remove_option = remove_option

    def get_string_funcs(self, **kwargs):
        string_funcs = [self.remove_tags]
        return string_funcs

    def remove_tags(self, hed_string):
        remove_tuples = hed_string.find_tags(self.tag_names, recursive=True, include_groups=2)
        if self.remove_option=="group" or self.remove_option=="all":
            remove_list = [tuple[1] for tuple in remove_tuples]
            hed_string.remove(remove_list)
        if self.remove_option=="tag" or self.remove_option=="all":
            remove_list = [tuple[0] for tuple in remove_tuples]
            hed_string.remove(remove_list)
        return True


class RemoveTypeFilter(Ops):

    def __init__(self, type_name, type_values, def_values):
        super().__init__("remove_type")
        self.type_name = type_name
        self.type_values = type_values
        self.def_values = def_values

    def get_string_funcs(self, **kwargs):
        string_funcs = [self.remove_type_values]
        return string_funcs

    def remove_type_values(self, hed_string):
        remove_tags = hed_string.find_tags(self.tag_names, recursive=True, include_groups=0)
        if remove_tags:
            hed_string.remove(remove_tags)


class HedFilters(Ops):

    def __init__(self, name, filters, **kwargs):
        super().__init__(name)
        self._filters = filters
        self._tag_funcs = self.get_tag_funcs(**kwargs)
        self._string_funcs = self.get_string_funcs(**kwargs)
        self._data_funcs = self.get_data_funcs(**kwargs)

    def get_string_funcs(self, **kwargs):
        string_funcs = []
        for filter in self._filters:
            string_funcs = string_funcs + filter.get_string_funcs(**kwargs)
        return string_funcs

    def apply_ops(self, hed_thing):
        if isinstance(hed_thing, HedString):
            for func in self._string_funcs:
                ret_val = func(hed_string)


if __name__ == '__main__':
    import os
    import json
    from hed.tools.analysis.hed_variable_manager import HedVariableManager
    from hed.schema import load_schema_version
    from hed.models import HedString, DefinitionEntry, TabularInput, Sidecar
    from hed.tools.analysis.analysis_util import get_assembled_strings
    hed_schema = load_schema_version(xml_version="8.1.0")
    hed_string = HedString('Def/Cond1, Sensory-event, (Def/Cond2, Onset), Item, (Item, Blue), (Green, (Move, Item))', hed_schema=hed_schema)

    y = hed_string.lower()
    print(f"Before: {str(hed_string)}")
    if "def" in y:
        print("to here")
    # filter1 =  RemoveFilter(['Item'], remove_option="all")
    # filters = HedFilters('test_filters', [filter1])
    # filters.__apply_ops__(hed_string)
    # print(f"After: {str(hed_string)}")
    print("to here")
    test_strings1 = [f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                     f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
                     '(Def/Cond1, Offset)',
                     'White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                     '',
                     '(Def/Cond2, Onset)',
                     '(Def/Cond3/4.3, Onset)',
                     'Arm, Leg, Condition-variable/Fast']
    def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=hed_schema)
    def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=hed_schema)
    def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
                     hed_schema=hed_schema)
    def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=hed_schema)
    def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=hed_schema)
    def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=hed_schema)
    defs = {
        'Cond1': DefinitionEntry('Cond1', def1, False, None),
        'Cond2': DefinitionEntry('Cond2', def2, False, None),
        'Cond3': DefinitionEntry('Cond3', def3, True, None),
        'Cond4': DefinitionEntry('Cond4', def4, False, None),
        'Cond5': DefinitionEntry('Cond5', def5, False, None),
        'Cond6': DefinitionEntry('Cond6', def6, True, None)
    }

    test_objs1 = [HedString(hed, hed_schema=hed_schema) for hed in test_strings1]
    var_manager = HedVariableManager(test_objs1, hed_schema, defs)
    remove_strings = var_manager.get_variable_tags()
    print(f"Remove strings {str(remove_strings)}")
    filter1 = RemoveTypeFilter(remove_strings, remove_option="all")
    filters = HedFilters('test_filters', [filter1])
    for hed_string in var_manager.hed_strings:
        print(f"Before {str(hed_string)}")
        filter1.remove_tags(hed_string)
        filters.apply_ops(hed_string)
        print(f"After: {str(hed_string)}")
