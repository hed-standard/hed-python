"""
This module contains the HedSchema class, which contains all the tags and attributes from a given schema file.
"""
from hed.schema.hed_schema_constants import HedKey, HedSectionKey
from hed.util import file_util
from hed.schema.fileio.schema2xml import HedSchema2XML
from hed.schema.fileio.schema2wiki import HedSchema2Wiki

from hed.schema import schema_validation_util
from hed.schema.hed_schema_section import HedSchemaSection


class HedSchema:
    """
        Internal representation of a loaded hed schema xml or mediawiki file.
    """

    def __init__(self):
        """Constructor for the HedSchema class.

        Parameters
        ----------
        Returns
        -------
        HedSchema
            A HedSchema object.
        """
        self._has_duplicate_tags = False
        self.header_attributes = {}
        self._filename = None
        self.prologue = ""
        self.epilogue = ""

        self._is_hed3_schema = None
        # This is the specified library name_prefix - tags will be {library_prefix}:{tag_name}
        self._library_prefix = ""

        self._sections = self._create_empty_sections()
        self.short_tag_mapping = {}

    # ===============================================
    # Basic schema properties
    # ===============================================
    @property
    def filename(self):
        """
            Returns the filename if one is known.

        Returns
        -------
        filename: str
        """
        return self._filename

    @filename.setter
    def filename(self, value):
        """
            Set the filename, if one has not already been set.

        Parameters
        ----------
        value : str
            The source filename for this file
        """
        if self._filename is None:
            self._filename = value

    @property
    def version(self):
        """
            Return the HED version of this schema.

        Returns
        -------
        hed_version: str
        """
        return self.header_attributes['version']

    @property
    def library(self):
        """
            Returns the name of this library schema if one exists.

        Returns
        -------
        library_name: str or None
        """
        return self.header_attributes.get('library')

    def schema_for_prefix(self, prefix):
        """
            Return the specific HedSchema object for the given tag name_prefix.

            This is mostly a placeholder for HedSchemaGroup.  May be refactored out later.

        Parameters
        ----------
        prefix : str
            A schema library name_prefix to get the schema for.

        Returns
        -------
        schema: HedSchema
        """
        if self._library_prefix != prefix:
            return None
        return self

    @property
    def valid_prefixes(self):
        """
            Gets a list of all prefixes this schema will accept.  This is always length 1 if using a HedSchema.

        Returns
        -------
        valid_prefixes: [str]
            A list of valid tag prefixes for this schema.
        """
        return list(self._library_prefix)

    # ===============================================
    # Creation and saving functions
    # ===============================================
    def get_as_mediawiki_string(self):
        """
        Return the schema to a mediawiki string

        Returns
        -------
        schema: str
            The schema string
        """
        schema2wiki = HedSchema2Wiki()
        output_strings = schema2wiki.process_schema(self)
        return '\n'.join(output_strings)

    def get_as_xml_string(self, save_as_legacy_format=False):
        """
        Return the schema to an XML string

        Parameters
        ----------
        save_as_legacy_format : bool
            You should never use this.  Some information will not be saved if old format.

        Returns
        -------
        schema: str
            The schema string
        """
        schema2xml = HedSchema2XML(save_as_legacy_format=save_as_legacy_format)
        xml_tree = schema2xml.process_schema(self)
        return file_util._xml_element_2_str(xml_tree)

    def save_as_xml(self, save_as_legacy_format=False):
        """
        Save the schema to a temporary file, returning the filename.

        Parameters
        ----------
        save_as_legacy_format : bool
            You should never use this.  Some information will not be saved if old format.
        Returns
        -------
        filename: str
            The newly created schema filename
        """
        schema2xml = HedSchema2XML(save_as_legacy_format=save_as_legacy_format)
        xml_tree = schema2xml.process_schema(self)
        local_xml_file = file_util.write_xml_tree_2_xml_file(xml_tree, ".xml")
        return local_xml_file

    def save_as_mediawiki(self):
        """
        Save the schema to a temporary file, returning the filename.

        Parameters
        ----------
        Returns
        -------
        filename: str
            The newly created schema filename
        """
        schema2wiki = HedSchema2Wiki()
        output_strings = schema2wiki.process_schema(self)
        local_wiki_file = file_util.write_strings_to_file(output_strings, ".mediawiki")
        return local_wiki_file

    def set_library_prefix(self, library_prefix):
        """
        Updates the tags in this schema with the given name_prefix, removing any existing name_prefix.

        Parameters
        ----------
        library_prefix : str
            Should be empty, or end with a colon.(Colon will be automated added if missing)
        Returns
        -------
        None
        """
        if library_prefix and library_prefix[-1] != ":":
            library_prefix += ":"

        self._library_prefix = library_prefix

    # ===============================================
    # Schema validation functions
    # ===============================================
    def check_compliance(self, also_check_for_warnings=True, name=None,
                         error_handler=None):
        """
            Checks for hed3 compliance of this schema.

        Parameters
        ----------
        also_check_for_warnings : bool, default True
            If True, also checks for formatting issues like invalid characters, capitalization, etc.
        name: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        issue_list : [{}]
            A list of all warnings and errors found in the file.
        """
        from hed.schema import schema_compliance
        return schema_compliance.check_compliance(self, also_check_for_warnings, name, error_handler)

    def find_duplicate_tags(self):
        """Finds all tags that are not unique.

        Returns
        -------
        duplicate_tag_dict: {str: [str]}
            A dictionary of all duplicate short tags as keys, with the values being a list of
            long tags sharing that short tag
        """
        duplicate_dict = {}
        short_tag_dict = self.short_tag_mapping
        for tag_name in short_tag_dict:
            if isinstance(short_tag_dict[tag_name], list):
                duplicate_dict[tag_name] = short_tag_dict[tag_name]

        return duplicate_dict

    def dupe_tag_iter(self, return_detailed_info=False):
        """
        An iterator that goes over each line of the duplicate tags dict, including descriptive ones.

        Parameters
        ----------
        return_detailed_info : bool
            If true, also returns header lines listing the number of duplicate tags for each short tag.

        Yields
        -------
        text_line: str
            A list of long tags that have duplicates, with optional descriptive short tag lines.
        """
        duplicate_dict = self.find_duplicate_tags()
        prefix_string = ""
        if return_detailed_info:
            prefix_string = "\t"
        for tag_name in duplicate_dict:
            if return_detailed_info:
                yield f"Duplicate tag found {tag_name} - {len(duplicate_dict[tag_name])} versions:"
            for tag_entry in duplicate_dict[tag_name]:
                yield f"{prefix_string}{tag_entry}"

    # ===============================================
    # General schema properties/functions
    # ===============================================
    def __getitem__(self, section_key):
        return self._sections[section_key]

    @property
    def has_duplicate_tags(self):
        """
        Returns True if this is a valid hed3 schema with no duplicate short tags.

        Returns
        -------
        bool
            Returns True if this is a valid hed3 schema with no duplicate short tags.
        """
        return self._has_duplicate_tags

    @property
    def unit_classes(self):
        """
            Returns the unit classes schema section

        Returns
        -------
        section: HedSchemaSection
            The unit classes section
        """
        return self._sections[HedSectionKey.UnitClasses]

    @property
    def unit_modifiers(self):
        """
            Returns the modifiers classes schema section

        Returns
        -------
        section: HedSchemaSection
            The unit modifiers section
        """
        return self._sections[HedSectionKey.UnitModifiers]

    @property
    def value_classes(self):
        """
            Returns the value classes schema section

        Returns
        -------
        section: HedSchemaSection
            The value classes section
        """
        return self._sections[HedSectionKey.ValueClasses]

    @property
    def is_hed3_schema(self):
        """
            Returns true if this is a HED3 or greater versioned schema.

            This is considered true if the version number is >= 8.0 or it has a library name.

        Returns
        -------
        is_hed3: bool
            True if this is a hed3 schema.
        """
        if self._is_hed3_schema is not None:
            return self._is_hed3_schema

        return self.library or schema_validation_util.is_hed3_version_number(self.version)

    def __eq__(self, other):
        """
            Returns True if these schemas match exactly.  All attributes, tag names, etc.

        Parameters
        ----------
        other : HedSchema

        Returns
        -------

        """
        if self.header_attributes != other.header_attributes:
            return False
        if self._has_duplicate_tags != other._has_duplicate_tags:
            return False
        if self.prologue != other.prologue:
            return False
        if self.epilogue != other.epilogue:
            return False
        if self._sections != other._sections:
            # for section1, section2 in zip(self._sections.values(), other._sections.values()):
            #     if section1 != section2:
            #         dict1 = section1.all_names
            #         dict2 = section2.all_names
            #         if dict1 != dict2:
            #             print(f"DICT {section1._section_key} NOT EQUAL")
            #             key_union = set(list(dict1.keys()) + list(dict2.keys()))
            #             for key in key_union:
            #                 if key not in dict1:
            #                     print(f"{key} not in dict1")
            #                     continue
            #                 if key not in dict2:
            #                     print(f"{key} not in dict2")
            #                     continue
            #                 if dict1[key] != dict2[key]:
            #                     print(
            #                         f"{key} doesn't match.  '{str(dict1[key].long_name)}' vs '{str(dict2[key].long_name)}'")
            return False
        return True

    def get_unit_class_units(self, unit_class_type):
        """
            Get the list of unit class units this type will accept.

            Eg 'time' returns ['second', 's', 'day', 'minute', 'hour']

        Parameters
        ----------
        unit_class_type : str
            The unit class type to check for.  e.g. "time"

        Returns
        -------
        unit_class_units: [UnitEntry]
            A list of each unit this type allows.
        """
        unit_class_entry = self._get_entry_for_tag(unit_class_type, HedSectionKey.UnitClasses)
        if unit_class_entry:
            return unit_class_entry.unit_class_units
        return []

    def get_all_tags_with_attribute(self, key, section_key=HedSectionKey.AllTags):
        """
            Returns a list of all tags with the given attribute.

            Note: Result is cached so will be fast after first call.

        Parameters
        ----------
        key : str
            A tag attribute.  Eg HedKey.ExtensionAllowed
        section_key: str
            The HedSectionKey for teh section to retrieve from.

        Returns
        -------
        tag_list: [str]
            A list of all tags with this attribute
        """
        return self._sections[section_key].get_entries_with_attribute(key, return_name_only=True)

    # ===============================================
    # Semi-private creation finalizing functions
    # ===============================================
    def finalize_dictionaries(self):
        """
            Called to finish loading.  Also needs to be called if you've altered the schema in memory.

        Returns
        -------
        """
        self._is_hed3_schema = self.is_hed3_schema
        self._populate_short_tag_dict()
        self._update_all_entries()

    def _update_all_entries(self):
        for section in self._sections.values():
            for entry in section.values():
                entry.finalize_entry(self)

    def _initialize_attributes(self, key_class):
        """
        Sets the valid attributes for the given section based on the schema.

        Parameters
        ----------
        key_class : str
            The section key for the section to update.
        Returns
        -------

        """
        self._sections[key_class].valid_attributes = self._get_attributes_for_class(key_class)

    def add_hed2_attributes(self, only_add_if_none_present=True):
        """
        This adds the default attributes for old hed2 schema without an attribute section

        Parameters
        ----------
        only_add_if_none_present : bool
            If True(default), will only add attributes if there is currently none.
            If False, will add any missing attributes.
        """
        if HedKey.ValueClassProperty not in self._sections[HedSectionKey.Properties]:
            self._add_single_default_property(HedKey.ValueClassProperty)

        # Allowed character used to be a unit class property - just remove it entirely if this is the case.
        if HedKey.AllowedCharacter in self._sections[HedSectionKey.Attributes]:
            attribute_entry = self._sections[HedSectionKey.Attributes][HedKey.AllowedCharacter]
            if attribute_entry.has_attribute(HedKey.UnitClassProperty):
                del self._sections[HedSectionKey.Attributes].all_names[HedKey.AllowedCharacter]

        if only_add_if_none_present and bool(self._sections[HedSectionKey.Attributes]):
            return

        from hed.schema import hed_2g_attributes
        for attribute_name in hed_2g_attributes.attributes:
            self._add_single_default_attribute(attribute_name)

    def add_default_properties(self, only_add_if_none_present=True):
        """
            This adds the default properties for a hed3 schema.

            Parameters
            ----------
            only_add_if_none_present : bool
                If True(default), will only add properties if there is currently none.
                If False, will add any missing properties.
                """
        if only_add_if_none_present and bool(self._sections[HedSectionKey.Properties]):
            return

        from hed.schema import hed_2g_attributes
        for prop_name in hed_2g_attributes.properties:
            self._add_single_default_property(prop_name)

    def update_old_hed_schema(self):
        """
            Updates old hed schema with now required attributes - such as $ being a unit name_prefix.

        Returns
        -------

        """
        if HedKey.UnitPrefix not in self._sections[HedSectionKey.Attributes]:
            self._add_single_default_attribute(HedKey.UnitPrefix)

        if not self.get_all_tags_with_attribute(HedKey.UnitPrefix):
            tag_entry = self._get_entry_for_tag("$", HedSectionKey.Units)
            if tag_entry:
                tag_entry.set_attribute_value(HedKey.UnitPrefix, True)

    # ===============================================
    # Getters used to write out schemas primarily.
    # ===============================================
    def get_desc_iter(self):
        """
            Returns an iterator over all the descriptions found in all sections.

        Returns
        -------
        tag_name: str
        description: str
        """
        for section in self._sections.values():
            for tag_entry in section.values():
                if tag_entry.description:
                    yield tag_entry.long_name, tag_entry.description

    def get_tag_description(self, tag_name, key_class=HedSectionKey.AllTags):
        """
            If a description exists for the given name, returns it

        Parameters
        ----------
        tag_name : str
            A hed tag name(or unit/unit modifier etc) with proper capitalization.
        key_class: str, default HedSectionKey.AllTags
            A HedKey indicating what type of description you are asking for.  (All tags, Units, Unit modifier)

        Returns
        -------
        description: str or None
        """
        tag_entry = self._get_entry_for_tag(tag_name, key_class)
        if tag_entry:
            return tag_entry.description

    def get_all_schema_tags(self, return_short_form=False):
        """
        Gets a list of all hed terms from the schema, compatible with Hed2 or Hed3

        Returns
        -------
        term_list: [str]
            A list of all terms(short tags) from the schema.
        """
        final_list = []
        for lower_tag, tag_entry in self._sections[HedSectionKey.AllTags].items():
            if return_short_form:
                final_list.append(tag_entry.long_name.split('/')[-1])
            else:
                final_list.append(tag_entry.long_name)

        return final_list

    def get_all_unknown_attributes(self):
        """
            Retrieves the current list of unknown attributes found in the schema.  This includes attributes
            found in the wrong section.  Eg a unitClass attribute found on a Tag.

        Returns
        -------
        attr_dict: {str: [str]}
            {attribute_name: [long form tags/units/etc with it]}
        """
        unknown_attributes = {}
        for section in self._sections.values():
            for entry in section.values():
                if entry._unknown_attributes:
                    for attribute_name in entry._unknown_attributes:
                        unknown_attributes.setdefault(attribute_name, []).append(entry.long_name)

        return unknown_attributes

    def get_tag_attribute_names(self):
        """
            Returns a dict of all the attributes allowed to be used on tags.

        Returns
        -------
        tag_entries: {str: HedSchemaEntry}
        """
        return {tag_entry.long_name: tag_entry for tag_entry in self._sections[HedSectionKey.Attributes].values()
                if not tag_entry.has_attribute(HedKey.UnitClassProperty)
                and not tag_entry.has_attribute(HedKey.UnitProperty)
                and not tag_entry.has_attribute(HedKey.UnitModifierProperty)
                and not tag_entry.has_attribute(HedKey.ValueClassProperty)}

    def get_all_tag_attributes(self, tag_name, key_class=HedSectionKey.AllTags):
        """
            Gathers all attributes for a given tag name.  If keys is none, gets all normal hed tag attributes.

        Parameters
        ----------
        tag_name : str
            The name of the tag to check
        key_class: str
            The type of attributes we are asking for.  e.g. Tag, Units, Unit modifiers, or attributes.

        Returns
        -------
        tag_values: {str: str}
            {key_name : attribute_value}
        """
        tag_entry = self._get_entry_for_tag(tag_name, key_class)
        attributes = {}
        if tag_entry:
            attributes = tag_entry.attributes

        return attributes

    # ===============================================
    # Private utility functions
    # ===============================================
    @staticmethod
    def _create_empty_sections():
        dictionaries = {}
        # Add main sections
        dictionaries[HedSectionKey.Properties] = HedSchemaSection(HedSectionKey.Properties)
        dictionaries[HedSectionKey.Attributes] = HedSchemaSection(HedSectionKey.Attributes)
        dictionaries[HedSectionKey.UnitModifiers] = HedSchemaSection(HedSectionKey.UnitModifiers)
        dictionaries[HedSectionKey.Units] = HedSchemaSection(HedSectionKey.Units)
        dictionaries[HedSectionKey.UnitClasses] = HedSchemaSection(HedSectionKey.UnitClasses)
        dictionaries[HedSectionKey.ValueClasses] = HedSchemaSection(HedSectionKey.ValueClasses)
        dictionaries[HedSectionKey.AllTags] = HedSchemaSection(HedSectionKey.AllTags, case_sensitive=False)

        return dictionaries

    def _populate_short_tag_dict(self):
        """
        Create a mapping from the short version of a tag to the long version and
        determines if this is a hed3 compatible schema.

        Returns
        -------
        """
        self._has_duplicate_tags = False
        base_tag_dict = self._sections[HedSectionKey.AllTags]
        new_short_tag_dict = {}
        for tag, tag_entry in base_tag_dict.items():
            unformatted_tag = tag_entry.long_name
            split_tags = unformatted_tag.split("/")
            short_tag = split_tags[-1]
            if short_tag == "#":
                # if it's a takes value tag, we should also include the parent.
                short_tag = split_tags[-2] + "/#"
            short_clean_tag = short_tag.lower()
            new_tag_entry = unformatted_tag
            if short_clean_tag not in new_short_tag_dict:
                new_short_tag_dict[short_clean_tag] = new_tag_entry
            else:
                self._has_duplicate_tags = True
                if not isinstance(new_short_tag_dict[short_clean_tag], list):
                    new_short_tag_dict[short_clean_tag] = [new_short_tag_dict[short_clean_tag]]
                new_short_tag_dict[short_clean_tag].append(new_tag_entry)
        self.short_tag_mapping = new_short_tag_dict

    def get_modifiers_for_unit(self, unit):
        """
            Returns the valid modifiers for the given unit

            This is a lower level one that doesn't rely on the Unit entries being fully setup.

        Parameters
        ----------
        unit: str
            A known unit

        Returns
        -------
        modifier_list: [HedSchemaEntry]

        """
        unit_entry = self._get_entry_for_tag(unit, HedSectionKey.Units)
        if unit_entry is None:
            return []
        is_si_unit = unit_entry.has_attribute(HedKey.SIUnit)
        is_unit_symbol = unit_entry.has_attribute(HedKey.UnitSymbol)
        if not is_si_unit:
            return []
        if is_unit_symbol:
            modifier_attribute_name = HedKey.SIUnitSymbolModifier
        else:
            modifier_attribute_name = HedKey.SIUnitModifier
        valid_modifiers = self.unit_modifiers.get_entries_with_attribute(modifier_attribute_name)
        return valid_modifiers

    def get_units_for_unit_class(self, unit_class):
        """
            Gets all the unit entries for the given unit class name

            This is a lower level one that doesn't rely on the UnitClass entries being fully setup.

        Parameters
        ----------
        unit_class: str
            A known unit class

        Returns
        -------
        unit_dict: {str: UnitEntry}
            A dict of all units the given unit class accepts.
        """
        return {unit_entry.long_name: unit_entry for unit_entry in self._sections[HedSectionKey.Units].values()
                if unit_entry.unit_class_name == unit_class}

    def _get_attributes_for_class(self, key_class):
        """
        Returns the valid attributes for this section

        Parameters
        ----------
        key_class : str
            The HedKey for this section.

        Returns
        -------
        attributes: {str:entry} or HedSchemaSection
            A dict of all the attributes for this section.  May be a HedSchemaSection and not actually a dict.
        """
        if key_class == HedSectionKey.AllTags:
            return self.get_tag_attribute_names()
        elif key_class == HedSectionKey.Attributes:
            return self._sections[HedSectionKey.Properties]
        else:
            attrib_classes = {
                HedSectionKey.UnitClasses: HedKey.UnitClassProperty,
                HedSectionKey.Units: HedKey.UnitProperty,
                HedSectionKey.UnitModifiers: HedKey.UnitModifierProperty,
                HedSectionKey.ValueClasses: HedKey.ValueClassProperty
            }
            attrib_class = attrib_classes.get(key_class, None)
            if attrib_class is None:
                return []

            attributes = {attribute: entry for attribute, entry in self._sections[HedSectionKey.Attributes].items()
                          if entry.has_attribute(attrib_class)}
            return attributes

    # ===============================================
    # Semi private functions used to create a schema in memory(usually from a source file)
    # ===============================================
    def _get_entry_for_tag(self, long_tag_name, key_class=HedSectionKey.AllTags):
        """
            Returns the schema entry for this tag, if one exists.

        Parameters
        ----------
        long_tag_name :
        key_class :

        Returns
        -------
        tag_entry: HedSchemaEntry
            The schema entry for the given tag.
        """
        if self._library_prefix and key_class == HedSectionKey.AllTags:
            long_tag_name = long_tag_name.lower()
            if long_tag_name.startswith(self._library_prefix):
                long_tag_name = long_tag_name[len(self._library_prefix):]

        return self._sections[key_class].get(long_tag_name)

    def _add_tag_to_dict(self, long_tag_name, key_class):
        section = self._sections[key_class]
        if not section:
            self._initialize_attributes(key_class)
        return section._add_to_dict(long_tag_name)

    def _add_unit_class(self, unit_class):
        self._add_tag_to_dict(unit_class, HedSectionKey.UnitClasses)

    def _add_unit_class_unit(self, unit_class, unit_class_unit):
        unit_class_unit_entry = self._add_tag_to_dict(unit_class_unit, HedSectionKey.Units)
        unit_class_unit_entry.unit_class_name = unit_class
        return unit_class_unit_entry

    def _add_single_default_attribute(self, attribute_name):
        from hed.schema import hed_2g_attributes
        attribute_props, attribute_desc = hed_2g_attributes.attributes[attribute_name]
        if attribute_name not in self._sections[HedSectionKey.Attributes]:
            self._add_tag_to_dict(attribute_name, HedSectionKey.Attributes)
        tag_entry = self._get_entry_for_tag(attribute_name, HedSectionKey.Attributes)
        if attribute_desc:
            tag_entry.description = attribute_desc

        for attribute_property_name in attribute_props:
            tag_entry.set_attribute_value(attribute_property_name, True)

    def _add_single_default_property(self, prop_name):
        from hed.schema import hed_2g_attributes
        prop_desc = hed_2g_attributes.properties[prop_name]
        self._add_tag_to_dict(prop_name, HedSectionKey.Properties)
        tag_entry = self._get_entry_for_tag(prop_name, HedSectionKey.Properties)
        if prop_desc:
            tag_entry.description = prop_desc
