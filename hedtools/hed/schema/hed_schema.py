"""
This module contains the HedSchema class, which contains all the tags and attributes from a given schema file.
"""
from hed.schema.hed_schema_constants import HedKey, HedSectionKey
from hed.util import file_util
from hed.schema.io.schema2xml import HedSchema2XML
from hed.schema.io.schema2wiki import HedSchema2Wiki

from hed.schema import schema_validation_util
from hed.schema.hed_schema_section import HedSchemaSection, HedSchemaTagSection
from hed.errors import ErrorHandler
from hed.errors.error_types import ValidationErrors


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

    def get_as_xml_string(self):
        """
        Return the schema to an XML string

        Parameters
        ----------
        Returns
        -------
        schema: str
            The schema string
        """
        schema2xml = HedSchema2XML()
        xml_tree = schema2xml.process_schema(self)
        return file_util._xml_element_2_str(xml_tree)

    def save_as_xml(self):
        """
        Save the schema to a temporary file, returning the filename.

        Parameters
        ----------
        Returns
        -------
        filename: str
            The newly created schema filename
        """
        schema2xml = HedSchema2XML()
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
        return self.all_tags.duplicate_names

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
    def all_tags(self):
        """
            Returns the tag schema section

        Returns
        -------
        section: HedSchemaSection
            The tag section
        """
        return self._sections[HedSectionKey.AllTags]

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
        unit_class_entry = self.get_tag_entry(unit_class_type, HedSectionKey.UnitClasses)
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

    def get_tag_entry(self, name, key_class=HedSectionKey.AllTags, library_prefix=""):
        """
            Returns the schema entry for this tag, if one exists.

        Parameters
        ----------
        name : str
            Any form of basic tag(or other section entry) to look up.  This will not handle extensions or similar.
        key_class : HedSectionKey or str

        library_prefix: str
            Unused(only used for HedSchemaGroup currently)
        Returns
        -------
        tag_entry: HedSchemaEntry
            The schema entry for the given tag.
        """
        if self._library_prefix and key_class == HedSectionKey.AllTags:
            name = name.lower()
            if name.startswith(self._library_prefix):
                name = name[len(self._library_prefix):]

        return self._sections[key_class].get(name)

    def find_tag_entry(self, tag, library_prefix=""):
        """
        This takes a source tag and finds the schema entry for it.

        Works right to left.(mostly relevant for errors)

        Parameters
        ----------
        tag : str or HedTag
            Any form of tag to look up.  Can have an extension, value, etc.
        library_prefix: str
            The prefix the library, if any.

        Returns
        -------
        tag_entry: HedTagEntry
            The located tag entry for this tag.
        remainder: str
            The remainder of the tag that isn't part of the base tag.
        errors: list
            a list of errors while converting
        """
        clean_tag = str(tag)
        prefix = library_prefix
        clean_tag = clean_tag[len(prefix):]
        prefix_tag_adj = len(prefix)
        working_tag = clean_tag.lower()
        found_entry = None
        remainder = ""

        # this handles the one special case where the actual tag contains "/#" instead of something specific.
        if working_tag.endswith("/#"):
            working_tag = working_tag[:-2]
            remainder = "/#"
        while True:
            tag_entry = self.get_tag_entry(working_tag)
            parent_name, _, child_name = working_tag.rpartition("/")
            if tag_entry is None:
                if self.get_tag_entry(child_name):
                    error = ErrorHandler.format_error(ValidationErrors.INVALID_PARENT_NODE,
                                                      tag,
                                                      index_in_tag=len(parent_name) + 1 + prefix_tag_adj,
                                                      index_in_tag_end=len(parent_name) + 1 + len(
                                                          child_name) + prefix_tag_adj,
                                                      expected_parent_tag=self.all_tags[child_name].name)
                    return None, None, error
                if not parent_name:
                    error = ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                      tag,
                                                      index_in_tag=len(parent_name) + prefix_tag_adj,
                                                      index_in_tag_end=len(parent_name) + len(
                                                          child_name) + prefix_tag_adj)
                    return None, None, error
                working_tag = parent_name
                remainder = clean_tag[len(working_tag):][:len(child_name) + 1] + remainder
                continue

            if remainder and tag_entry.takes_value_child_entry:
                tag_entry = tag_entry.takes_value_child_entry
            found_entry = tag_entry
            break

        return found_entry, remainder, []

    # ===============================================
    # Semi-private creation finalizing functions
    # ===============================================
    def finalize_dictionaries(self):
        """
            Called to finish loading.

        Returns
        -------
        """
        self._is_hed3_schema = self.is_hed3_schema
        self._has_duplicate_tags = bool(self.all_tags.duplicate_names)
        self._update_all_entries()

    def _update_all_entries(self):
        """
            Calls finalize_entry on every schema entry(tag, unit, etc)

        Returns
        -------

        """
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
                    yield tag_entry.name, tag_entry.description

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
        tag_entry = self.get_tag_entry(tag_name, key_class)
        if tag_entry:
            return tag_entry.description

    def get_all_schema_tags(self, return_last_term=False):
        """
        Gets a list of all hed terms from the schema, compatible with Hed2 or Hed3

        Returns
        -------
        term_list: [str]
            A list of all terms(short tags) from the schema.
        """
        final_list = []
        for lower_tag, tag_entry in self.all_tags.items():
            if return_last_term:
                final_list.append(tag_entry.name.split('/')[-1])
            else:
                final_list.append(tag_entry.name)
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
                        unknown_attributes.setdefault(attribute_name, []).append(entry.name)

        return unknown_attributes

    def get_tag_attribute_names(self):
        """
            Returns a dict of all the attributes allowed to be used on tags.

        Returns
        -------
        tag_entries: {str: HedSchemaEntry}
        """
        return {tag_entry.name: tag_entry for tag_entry in self._sections[HedSectionKey.Attributes].values()
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
        tag_entry = self.get_tag_entry(tag_name, key_class)
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
        dictionaries[HedSectionKey.AllTags] = HedSchemaTagSection(HedSectionKey.AllTags, case_sensitive=False)

        return dictionaries

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
        unit_entry = self.get_tag_entry(unit, HedSectionKey.Units)
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
    # Semi private function used to create a schema in memory(usually from a source file)
    # ===============================================
    def _add_tag_to_dict(self, long_tag_name, key_class):
        section = self._sections[key_class]
        if not section:
            self._initialize_attributes(key_class)
        return section._add_to_dict(long_tag_name)
