"""Allows output of HedSchema objects as .mediawiki format"""

from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io.ontology_util import get_library_name_and_id, remove_prefix, create_empty_dataframes
from hed.schema.schema_io.schema2base import Schema2Base
import pandas as pd
import hed.schema.hed_schema_df_constants as constants
from hed.schema.hed_schema_entry import HedTagEntry

section_key_to_df = {
    HedSectionKey.Tags: constants.TAG_KEY,
    HedSectionKey.Units: constants.UNIT_KEY,
    HedSectionKey.UnitClasses: constants.UNIT_CLASS_KEY,
    HedSectionKey.UnitModifiers: constants.UNIT_MODIFIER_KEY,
    HedSectionKey.ValueClasses: constants.VALUE_CLASS_KEY,
    HedSectionKey.Attributes: HedSectionKey.Attributes,
    HedSectionKey.Properties: HedSectionKey.Properties
}


class Schema2DF(Schema2Base):
    def __init__(self, get_as_ids=False):
        """ Constructor for schema to dataframe converter

        Parameters:
            get_as_ids(bool): If true, return the hedId rather than name in most places
                              This is mostly relevant for creating an ontology.
        """
        super().__init__()
        self._get_as_ids = get_as_ids
        self._tag_rows = []

    def _get_object_name_and_id(self, object_name, include_prefix=False):
        """ Get the adjusted name and ID for the given object type.

        Parameters:
            object_name(str): The name of the base hed object, e.g. HedHeader, HedUnit
            include_prefix(bool): If True, include the "hed:"
        Returns:
            object_name(str): The inherited object name, e.g. StandardHeader
            hed_id(str): The full formatted hed_id
        """
        prefix, obj_id = get_library_name_and_id(self._schema)
        name = f"{prefix}{remove_prefix(object_name, 'Hed')}"
        full_hed_id = self._get_object_id(object_name, obj_id, include_prefix)
        return name, full_hed_id

    def _get_object_id(self, object_name, base_id=0, include_prefix=False):
        prefix=""
        if include_prefix:
            prefix = "hed:"
        return f"{prefix}HED_{base_id + constants.struct_base_ids[object_name]:07d}"


    # =========================================
    # Required baseclass function
    # =========================================
    def _initialize_output(self):
        self.output = create_empty_dataframes()
        self._tag_rows = []

    def _create_and_add_object_row(self, base_object, attributes="", description=""):
        name, full_hed_id = self._get_object_name_and_id(base_object)
        new_row = {
            constants.hed_id: full_hed_id,
            constants.name: name,
            constants.attributes: attributes,
            constants.subclass_of: base_object,
            constants.description: description.replace("\n", "\\n"),
        }
        self.output[constants.STRUCT_KEY].loc[len(self.output[constants.STRUCT_KEY])] = new_row

    def _output_header(self, attributes, prologue):
        base_object = "HedHeader"
        attributes_string = self._get_attribs_string_from_schema(attributes, sep=", ")
        self._create_and_add_object_row(base_object, attributes_string)

        base_object = "HedPrologue"
        self._create_and_add_object_row(base_object, description=prologue)

    def _output_footer(self, epilogue):
        base_object = "HedEpilogue"
        self._create_and_add_object_row(base_object, description=epilogue)

    def _start_section(self, key_class):
        pass

    def _end_tag_section(self):
        self.output[constants.TAG_KEY] = pd.DataFrame(self._tag_rows, columns=constants.tag_columns, dtype=str)

    def _write_tag_entry(self, tag_entry, parent_node=None, level=0):
        tag_id = tag_entry.attributes.get(HedKey.HedID, "")
        new_row = {
            constants.hed_id: f"{tag_id}",
            constants.level: f"{level}",
            constants.name: tag_entry.short_tag_name if not tag_entry.has_attribute(HedKey.TakesValue) else tag_entry.short_tag_name + "-#",
            constants.subclass_of: self._get_subclass_of(tag_entry),
            constants.attributes: self._format_tag_attributes(tag_entry.attributes),
            constants.description: tag_entry.description,
            constants.equivalent_to: self._get_tag_equivalent_to(tag_entry),
        }
        # Todo: do other sections like this as well for efficiency
        self._tag_rows.append(new_row)

    def _write_entry(self, entry, parent_node, include_props=True):
        df_key = section_key_to_df.get(entry.section_key)
        if not df_key:
            return

        # Special case
        if df_key == HedSectionKey.Properties:
            return self._write_property_entry(entry)
        elif df_key == HedSectionKey.Attributes:
            return self._write_attribute_entry(entry, include_props=include_props)
        df = self.output[df_key]
        tag_id = entry.attributes.get(HedKey.HedID, "")
        new_row = {
            constants.hed_id: f"{tag_id}",
            constants.name: entry.name,
            constants.subclass_of: self._get_subclass_of(entry),
            constants.attributes: self._format_tag_attributes(entry.attributes),
            constants.description: entry.description,
            constants.equivalent_to: self._get_tag_equivalent_to(entry),
        }
        # Handle the special case of units, which have the extra unit class
        if hasattr(entry, "unit_class_entry"):
            class_entry_name = entry.unit_class_entry.name
            if self._get_as_ids:
                class_entry_name = f"{entry.unit_class_entry.attributes.get(constants.hed_id)}"
            new_row[constants.has_unit_class] = class_entry_name
        df.loc[len(df)] = new_row
        pass

    def _write_attribute_entry(self, entry, include_props):
        df_key = constants.OBJECT_KEY
        property_type = "ObjectProperty"
        if HedKey.AnnotationProperty in entry.attributes:
            df_key = constants.ANNOTATION_KEY
            property_type = "AnnotationProperty"
        elif (HedKey.NumericRange in entry.attributes
              or HedKey.StringRange in entry.attributes
              or HedKey.BoolRange in entry.attributes):
            df_key = constants.DATA_KEY
            property_type = "DataProperty"

        hed_id_mapping = {
            "HedTag": self._get_object_id("HedTag", include_prefix=True),
            "HedUnit": self._get_object_id("HedUnit", include_prefix=True),
            "HedUnitClass": self._get_object_id("HedUnitClass", include_prefix=True),
            "HedUnitModifier": self._get_object_id("HedUnitModifier", include_prefix=True),
            "HedValueClass": self._get_object_id("HedValueClass", include_prefix=True),
            "HedElement": self._get_object_id("HedElement", include_prefix=True),
            "string": "xsd:string",
            "boolean": "xsd:boolean",
            "float": "xsd:float"
        }

        domain_attributes = {
            HedKey.TagDomain: "HedTag",
            HedKey.UnitDomain: "HedUnit",
            HedKey.UnitClassDomain: "HedUnitClass",
            HedKey.UnitModifierDomain: "HedUnitModifier",
            HedKey.ValueClassDomain: "HedValueClass",
            HedKey.ElementDomain: "HedElement"
        }
        range_attributes = {
            HedKey.StringRange: "string",
            HedKey.TagRange: "HedTag",
            HedKey.NumericRange: "float",
            HedKey.BoolRange: "boolean",
            HedKey.UnitRange: "HedUnit",
            HedKey.UnitClassRange: "HedUnitClass",
            HedKey.ValueClassRange: "HedValueClass"
        }

        domain_keys = [key for key in entry.attributes if key in domain_attributes]
        range_keys = [key for key in entry.attributes if key in range_attributes]

        if self._get_as_ids:
            domain_string = " or ".join(hed_id_mapping[domain_attributes[key]] for key in domain_keys)
            range_string = " or ".join(hed_id_mapping[range_attributes[key]] for key in range_keys)
        else:
            domain_string = " or ".join(domain_attributes[key] for key in domain_keys)
            range_string = " or ".join(range_attributes[key] for key in range_keys)

        df = self.output[df_key]
        tag_id = entry.attributes.get(HedKey.HedID, "")
        new_row = {
            constants.hed_id: f"{tag_id}",
            constants.name: entry.name,
            constants.property_type: property_type,
            constants.property_domain: domain_string,
            constants.property_range: range_string,
            constants.properties: self._format_tag_attributes(entry.attributes) if include_props else "",
            constants.description: entry.description,
        }
        df.loc[len(df)] = new_row

    def _write_property_entry(self, entry):
        df_key = constants.ATTRIBUTE_PROPERTY_KEY
        property_type = "AnnotationProperty"
        df = self.output[df_key]
        tag_id = entry.attributes.get(HedKey.HedID, "")
        new_row = {
            constants.hed_id: f"{tag_id}",
            constants.name: entry.name,
            constants.property_type: property_type,
            constants.description: entry.description,
        }
        df.loc[len(df)] = new_row

    def _attribute_disallowed(self, attribute):
        if super()._attribute_disallowed(attribute):
            return True
        # strip out hedID in dataframe format
        return attribute in [HedKey.HedID, HedKey.AnnotationProperty]

    def _get_tag_equivalent_to(self, tag_entry):
        subclass = self._get_subclass_of(tag_entry)

        attribute_types = {
            "object": "some",
            "data": "value"
        }
        range_types = {
            HedKey.TagRange: HedSectionKey.Tags,
            HedKey.UnitRange: HedSectionKey.Units,
            HedKey.UnitClassRange: HedSectionKey.UnitClasses,
            HedKey.ValueClassRange: HedSectionKey.ValueClasses,
            HedKey.NumericRange: HedKey.NumericRange
        }
        attribute_strings = []
        for attribute, value in tag_entry.attributes.items():
            attribute_entry = self._schema.attributes.get(attribute)
            attribute_type = self._calculate_attribute_type(attribute_entry)
            if self._attribute_disallowed(attribute) or attribute_type == "annotation":
                continue
            if isinstance(value, str):
                values = value.split(",")
                values = [v.strip() for v in values]
                found_range = None
                for range_type in range_types:
                    if range_type in attribute_entry.attributes:
                        found_range = range_types[range_type]
                        break
                if self._get_as_ids and found_range and found_range != HedKey.NumericRange:
                    section = self._schema[found_range]
                    if any(section.get(v) is None for v in values):
                        raise ValueError(f"Cannot find schema entry for {values}")
                    for v in values:
                        test_id = section.get(v).attributes.get(HedKey.HedID)
                        if not test_id:
                            raise ValueError(f"Schema entry {v} has no hedId.")

                    values = [f"hed:{section.get(v).attributes[HedKey.HedID]}" for v in values]
                # If not a known type, add quotes.
                if not found_range:
                    values = [f'"{v}"' for v in values]
            else:
                if value is True:
                    value = 'true'
                values = [value]
            for v in values:
                if self._get_as_ids:
                    attribute = f"hed:{attribute_entry.attributes[HedKey.HedID]}"
                attribute_strings.append(f"({attribute} {attribute_types[attribute_type]} {v})")
        if hasattr(tag_entry, "unit_class_entry"):
            class_entry_name = tag_entry.unit_class_entry.name
            if self._get_as_ids:
                class_entry_name = f"hed:{tag_entry.unit_class_entry.attributes.get(constants.hed_id)}"

            if self._get_as_ids:
                attribute_strings.append(f"(hed:HED_0000103 some {class_entry_name})")
            else:
                attribute_strings.append(f"({constants.has_unit_class} some {class_entry_name})")
        if hasattr(tag_entry, "parent") and not tag_entry.parent:
            schema_name, schema_id = self._get_object_name_and_id("HedSchema", include_prefix=True)
            if self._get_as_ids:
                attribute_strings.append(f"(hed:HED_0000102 some {schema_id})")
            else:
                attribute_strings.append(f"(inHedSchema some {schema_name})")

        # If they match, we want to leave equivalent_to blank
        final_out = " and ".join([subclass] + attribute_strings)
        if final_out == subclass:
            return ""
        return final_out

    def _get_subclass_of(self, tag_entry):
        # Special case for HedTag
        if isinstance(tag_entry, HedTagEntry):
            if self._get_as_ids:
                parent_entry = tag_entry.parent
                if parent_entry:
                    return f"hed:{parent_entry.attributes[HedKey.HedID]}"

                # HedTag always returns as base object
                return "hed:HED_0000005"
            else:
                return tag_entry.parent.short_tag_name if tag_entry.parent else "HedTag"

        base_objects = {
            HedSectionKey.Units: f"HedUnit",
            HedSectionKey.UnitClasses: f"HedUnitClass",
            HedSectionKey.UnitModifiers: f"HedUnitModifier",
            HedSectionKey.ValueClasses: f"HedValueClass"
        }
        name, obj_id = self._get_object_name_and_id(base_objects[tag_entry.section_key], include_prefix=True)

        if self._get_as_ids:
            return obj_id
        return name

    @staticmethod
    def _calculate_attribute_type(attribute_entry):
        attributes = attribute_entry.attributes
        object_ranges = {HedKey.TagRange, HedKey.UnitRange, HedKey.UnitClassRange, HedKey.ValueClassRange}
        if HedKey.AnnotationProperty in attributes:
            return "annotation"
        elif any(attribute in object_ranges for attribute in attributes):
            return "object"
        return "data"
