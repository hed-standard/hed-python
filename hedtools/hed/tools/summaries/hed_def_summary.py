from hed.tools.summaries.group_summary import HedGroupSummary
from hed.models.sidecar import Sidecar
from hed.models.def_dict import DefDict
from hed.schema.hed_schema_io import load_schema


class HedDefSummary():

    def __init__(self, def_dicts, hed_schema):
        self.def_summary = {}
        self.unique_tags = {}
        self.add_defs_to_summary(def_dicts, hed_schema)

    def add_defs_to_summary(self, def_dicts, hed_schema):
        if isinstance(def_dicts, DefDict):
            def_dicts = [def_dicts]
        for def_dict in def_dicts:
            this_dict = def_dict._defs
            for def_name, def_entry in this_dict.items():
                self.def_summary[def_name] = HedGroupSummary(def_entry.contents, hed_schema,
                                                             name=def_entry.name, keep_all_values=True)
            self._set_unique_tags()

    def _set_unique_tags(self):
        tag_dict = {}
        for key, item in self.def_summary.items():
            for tag in item.tag_dict:
                tag_dict[tag] = ''
        self.unique_tags = list(tag_dict.keys())

    def get_condition_variables(self):
        cond_variables = {}
        return cond_variables


if __name__ == '__main__':
    the_path = '../../tests/data/bids_old/task-FacePerception_events.json'
    sidecar = Sidecar(the_path)
    hed_schema = load_schema(
            hed_url_path='https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
    def_dict1 = [column_entry.def_dict for column_entry in sidecar]
    hed_defs = HedDefSummary(def_dict1, hed_schema)
    print("whew")
