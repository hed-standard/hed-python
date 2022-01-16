import json
from hed.models.sidecar import Sidecar
from hed.schema.hed_schema_file import load_schema


class HedGroupSummary():

    def __init__(self, hed_group, hed_schema, name=None, keep_all_values=False):
        self.name = name
        self.hed_group = hed_group
        self.tag_dict = {}
        self._set_tag_dictionary(hed_schema, keep_all_values)

    def _set_tag_dictionary(self, hed_schema, keep_all_values):
        tag_list = self.hed_group.get_all_tags()
        for tag in tag_list:
            tag.convert_to_canonical_forms(hed_schema)
            key = tag.short_base_tag
            if not keep_all_values:
                self.tag_dict[key] = [tag]
            else:
                value = self.tag_dict.get(key, [])
                if not value or tag.extension_or_value_portion:
                    value.append(tag)
                self.tag_dict[key] = value

    def get_description(self):
        if 'Description' not in self.tag_dict:
            return ''
        str_desc = ''
        for item in self.tag_dict['Description']:
            str_desc += item.extension_or_value_portion + ' '
        return str_desc

    def is_top_level(self, short_base_tag):
        if short_base_tag not in self.tag_dict:
            return False
        value = self.tag_dict[short_base_tag]
        for child in value.get_direct_children:
            print(child)
        print("To here")

    def to_json(self, with_values=False, as_json=True):
        json_dict = {"Name": self.name, "Tags": list(self.tag_dict)}
        if with_values:
            tag_values = {}
            for key, values in self.tag_dict.items():
                value_list = []
                for tag in values:
                    if tag.extension_or_value_portion:
                        value_list.append(tag.extension_or_value_portion)
                if not value_list:
                    continue
                elif len(value_list) == 1:
                    tag_values[key] = value_list[0]
                else:
                    tag_values[key] = value_list
            if tag_values:
                json_dict["Tags with values:"] = tag_values
        if as_json:
            return json.dumps(json_dict)
        else:
            return json.dumps(json_dict, indent=4, sort_keys=True)

    def __str__(self):
        return f"{self.name}: {self.get_description()} Tags: {str(list(self.tag_dict.keys()))}"


if __name__ == '__main__':
    the_path = '../../tests/data/bids/task-FacePerception_events.json'
    sidecar = Sidecar(the_path)
    hed_schema = load_schema(
            hed_url_path='https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
    def_dicts = [column_entry.def_dict for column_entry in sidecar]
    group_list = []
    for def_dict in def_dicts:
        this_dict = def_dict._defs
        for def_name, def_entry in this_dict.items():
            x = HedGroupSummary(def_entry.contents, hed_schema, name=def_entry.name, keep_all_values=True)
            group_list.append(x)
            print("String representation:")
            print(f"{str(x)}")
            print("Dumping Json:")
            print(f"{x.to_json(with_values=True, as_json=False)}")
    print("whew")
