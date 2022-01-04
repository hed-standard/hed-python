import os
import json
from bids_file import BidsFile
from hed.models.events_input import EventsInput


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
                self.tag_dict[key] = tag.extension_or_value_portion
            else:
                value = self.tag_dict.get(key, [])
                if tag.extension_or_value_portion:
                    value.append(tag.extension_or_value_portion)
                self.tag_dict[key] = value

    def get_json(self, with_values=False, as_json=True):
        json_dict = {"Name": self.name, "Tags": list(self.tag_dict)}
        if with_values:
            tag_values = {}
            for key, values in self.tag_dict.items():
                if not values:
                    continue
                else:
                    tag_values[key] = values
            json_dict["Tags with values:"] = tag_values
        if as_json:
            return json.dumps(json_dict)
        else:
            return json.dumps(json_dict, indent=4, sort_keys=True)
