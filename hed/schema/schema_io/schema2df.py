"""Allows output of HedSchema objects as .mediawiki format"""

from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io.schema2base import Schema2Base
import pandas as pd
from hed.schema.hed_schema_df_constants import *


class Schema2DF(Schema2Base):
    # todo: add omn:EquivalentTo"
    struct_columns = ["hedId", "rdfs:label", "Attributes", "omn:SubClassOf", "dc:description"]
    tag_columns = ["hedId", "Level", "rdfs:label", "omn:SubClassOf", "Attributes", "dc:description"]
    def __init__(self):
        super().__init__()
        self.current_tag_string = ""
        self.current_tag_extra = ""
        self.output = {
            STRUCT_KEY: pd.DataFrame(columns=self.struct_columns, dtype=str),
            TAG_KEY: pd.DataFrame(columns=self.tag_columns, dtype=str)}

    # =========================================
    # Required baseclass function
    # =========================================
    def _output_header(self, attributes, prologue):
        attributes_string = self._get_attribs_string_from_schema(attributes, sep=", ")
        new_row = {
            "hedId": f"HED_0010010",
            "rdfs:label": "StandardHeader",
            "Attributes": attributes_string,
            "omn:SubClassOf": "HedHeader",
            "dc:description": "",
            # "omn:EquivalentTo": "",
        }
        self.output[STRUCT_KEY].loc[len(self.output[STRUCT_KEY])] = new_row

        new_row = {
            "hedId": f"HED_0010011",
            "rdfs:label": "StandardPrologue",
            "Attributes": "",
            "omn:SubClassOf": "HedPrologue",
            "dc:description": prologue.replace("\n", "\\n"),
            # "omn:EquivalentTo": "",
        }
        self.output[STRUCT_KEY].loc[len(self.output[STRUCT_KEY])] = new_row

    def _output_footer(self, epilogue):
        new_row = {
            "hedId": f"HED_0010012",
            "rdfs:label": "StandardEpilogue",
            "Attributes": "",
            "omn:SubClassOf": "HedEpilogue",
            "dc:description": epilogue.replace("\n", "\\n"),
            # "omn:EquivalentTo": "",
        }
        self.output[STRUCT_KEY].loc[len(self.output[STRUCT_KEY])] = new_row

    def _start_section(self, key_class):
        pass

    def _end_tag_section(self):
        pass

    def _write_tag_entry(self, tag_entry, parent_node=None, level=0):
        # ["hedID", "Level", "rdfs:label", "Parent", "Attributes", "dc:description", "omn:EquivalentTo"]
        tag_id = tag_entry.attributes.get(HedKey.HedID, "")
        new_row = {
            "hedId": tag_id,
            "Level": f"{level}",
            "rdfs:label": tag_entry.short_tag_name if not tag_entry.has_attribute(HedKey.TakesValue) else tag_entry.short_tag_name + "-#",
            "omn:SubClassOf": tag_entry.parent.short_tag_name if tag_entry.parent else "HedTag",
            "Attributes": self._format_tag_attributes(tag_entry.attributes),
            "dc:description": tag_entry.description,
            # "omn:EquivalentTo": "",
        }
        self.output[TAG_KEY].loc[len(self.output[TAG_KEY])] = new_row

    def _write_entry(self, entry, parent_node, include_props=True):
        # only tags page implemented so far
        pass

    def _attribute_disallowed(self, attribute):
        if super()._attribute_disallowed(attribute):
            return True
        # strip out hedID in dataframe format
        return attribute == HedKey.HedID
