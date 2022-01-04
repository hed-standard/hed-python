from hed.tools.hed_group_summary import HedGroupSummary

class HedDefSummary(HedGroupSummary):

    def __init__(self, def_entry, hed_schema):

        super().__init__(def_entry.contents, hed_schema, name=def_entry.name, keep_all_values=True)
        self.def_entry = def_entry


class HedDatasetSummary():

    def __init__(self, def_dict, hed_schema):
        self.dict_sum = 0


