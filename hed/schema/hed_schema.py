
from hed.schema.hed_schema_constants import HedKey, HedSectionKey
from hed.schema.schema_io import schema_util
from hed.schema.schema_io.schema2xml import HedSchema2XML
from hed.schema.schema_io.schema2wiki import HedSchema2Wiki

from hed.schema import schema_validation_util
from hed.schema.hed_schema_section import HedSchemaSection, HedSchemaTagSection
from hed.errors import ErrorHandler
from hed.errors.error_types import ValidationErrors


class HedSchema:
    """ A HED schema suitable for processing. """

    def __init__(self):
        """ Constructor for the HedSchema class.

            A HedSchema can be used for validation, checking tag attributes, parsing tags, etc.
        """
        self._has_duplicate_tags = False
        self.header_attributes = {}
        self._filename = None
        self.prologue = ""
        self.epilogue = ""

        self._is_hed3_schema = None
        # This is the specified library name_prefix - tags will be {schema_prefix}:{tag_name}
        self._schema_prefix = ""

        self._sections = self._create_empty_sections()

    # ===============================================
    # Basic schema properties
    # ===============================================
    @property
    def filename(self):
        """ The filename if one is known.

        Returns:
            str: The filename of this schema.
        """
        return self._filename

    @filename.setter
    def filename(self, value):
        """ Set the filename, if one has not already been set.

        Parameters:
            value (str): The source filename for this file
        """
        if self._filename is None:
            self._filename = value

    @property
    def version(self):
        """ The HED version of this schema.

        Returns:
            str: The version of this schema.

        """
        return self.header_attributes['version']

    def get_formatted_version(self, as_string=True):
        """ The HED version string including prefix and library name if any of this schema.

        Returns:
            str: The complete version of this schema including library name and prefix.

        """
        library = self.header_attributes.get('library', '')
        if library:
            library = library + '_'
        return self._schema_prefix + library + self.header_attributes.get('version', '')

    @property
    def library(self):
        """ The name of this library schema if one exists.

        Returns:
            str or None: Library name if any.

        """
        return self.header_attributes.get('library')

    def schema_for_prefix(self, prefix):
        """ Return HedSchema object for this prefix.

        Parameters:
            prefix (str): The schema library name prefix.

        Returns:
            HedSchema: The HED schema object for this schema.

        Notes:
            -This is mostly a placeholder for HedSchemaGroup and may be refactored out later.

        """
        if self._schema_prefix != prefix:
            return None
        return self

    @property
    def valid_prefixes(self):
        """ Return a list of all prefixes this schema will accept

        Returns:
            list:   A list of valid tag prefixes for this schema.

        Notes:
            - The return value is always length 1 if using a HedSchema.
        """
        return [self._schema_prefix]

    # ===============================================
    # Creation and saving functions
    # ===============================================
    def get_as_mediawiki_string(self):
        """ Return the schema to a mediawiki string.

        Returns:
            str:  The schema as a string in mediawiki format.

        """
        schema2wiki = HedSchema2Wiki()
        output_strings = schema2wiki.process_schema(self)
        return '\n'.join(output_strings)

    def get_as_xml_string(self):
        """ Return the schema to an XML string.

        Returns:
            str: Return the schema as an XML string.

        """
        schema2xml = HedSchema2XML()
        xml_tree = schema2xml.process_schema(self)
        return schema_util._xml_element_2_str(xml_tree)

    def save_as_xml(self):
        """ Save as XML to a temporary file.

        Returns:
            str: The name of the newly created schema file.

        """
        schema2xml = HedSchema2XML()
        xml_tree = schema2xml.process_schema(self)
        local_xml_file = schema_util.write_xml_tree_2_xml_file(xml_tree, ".xml")
        return local_xml_file

    def save_as_mediawiki(self):
        """ Save as mediawiki to a temporary file.

        Returns:
            str:    The newly created schema filename.

        """
        schema2wiki = HedSchema2Wiki()
        output_strings = schema2wiki.process_schema(self)
        local_wiki_file = schema_util.write_strings_to_file(output_strings, ".mediawiki")
        return local_wiki_file

    def set_schema_prefix(self, schema_prefix):
        """ Set library prefix associated for this schema.

        Parameters:
            schema_prefix (str): Should be empty, or end with a colon.(Colon will be automated added if missing).

        """
        if schema_prefix and schema_prefix[-1] != ":":
            schema_prefix += ":"

        self._schema_prefix = schema_prefix

    def check_compliance(self, check_for_warnings=True, name=None, error_handler=None):
        """ Check for HED3 compliance of this schema.

        Parameters:
            check_for_warnings (bool): If True, also checks for formatting issues
            name (str): If present, use this as the filename for context
            error_handler (ErrorHandler or None): Used to report errors.

        Returns:
            list: A list of all warnings and errors found in the file. Each issue is a dictionary.

        Notes:
            - Formatting issues include invalid characters and capitalization.
            - The name parameter is useful when handling temporary files.
            - A default error handler is created if none passed in.

        """
        from hed.schema import schema_compliance
        return schema_compliance.check_compliance(self, check_for_warnings, name, error_handler)

    def find_duplicate_tags(self):
        """ Find all tags that are not unique.

        Returns:
            dict: A dictionary of all duplicate short tags

        Notes:
            - The returned dictionary has the short-form tags as keys and lists
            of long tags sharing the short form as the values.

        """
        return self.all_tags.duplicate_names

    def __getitem__(self, section_key):
        return self._sections[section_key]

    @property
    def has_duplicate_tags(self):
        """ Return True if this is a valid hed3.

        Returns:
            bool:  True if this is a valid hed3 schema with no duplicate short tags.

        """
        return self._has_duplicate_tags

    @property
    def all_tags(self):
        """ Return the tag schema section.

        Returns:
            HedSchemaSection: The tag section.

        """
        return self._sections[HedSectionKey.AllTags]

    @property
    def unit_classes(self):
        """ Return the unit classes schema section.

        Returns:
            HedSchemaSection: The unit classes section.

        """
        return self._sections[HedSectionKey.UnitClasses]

    @property
    def unit_modifiers(self):
        """ Return the modifiers classes schema section

        Returns:
            HedSchemaSection: The unit modifiers section.

        """
        return self._sections[HedSectionKey.UnitModifiers]

    @property
    def value_classes(self):
        """ Return the value classes schema section.

        Returns:
            HedSchemaSection: The value classes section.

        """
        return self._sections[HedSectionKey.ValueClasses]

    @property
    def is_hed3_schema(self):
        """ Return true if this is at least version HED3.

        Returns:
            bool: True if this is a hed3 schema.

        Notes:
            - This is considered true if the version number is >= 8.0 or it has a library name.

        """
        if self._is_hed3_schema is not None:
            return self._is_hed3_schema

        return self.library or schema_validation_util.is_hed3_version_number(self.version)

    def __eq__(self, other):
        """ Return True if these schema match exactly.

        Parameters:
            other (HedSchema): The schema to be compared.

        Returns:
            bool: True if other exactly matches this schema.

        Notes:
            - Matches must include attributes, tag names, etc.

        """
        if other is None:
            return False
        if self.header_attributes != other.header_attributes:
            return False
        if self._has_duplicate_tags != other._has_duplicate_tags:
            return False
        if self.prologue != other.prologue:
            return False
        if self.epilogue != other.epilogue:
            return False
        if self._sections != other._sections:
            # This block is useful for debugging when modifying the schema class itself.
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
            #                     s = f"{key} unmatched: '{str(dict1[key].long_name)}' vs '{str(dict2[key].long_name)}'"
            #                     print(s)
            return False
        if self._schema_prefix != other._schema_prefix:
            return False
        return True

    def get_unit_class_units(self, unit_class_type):
        """ Get the list of unit class units this type will accept.

        Parameters:
            unit_class_type (str): The unit class type to check for.  e.g. "time".

        Returns:
            list: A list of each UnitEntry this type allows.

        Examples:
            Eg 'time' returns ['second', 's', 'day', 'minute', 'hour']

        """
        unit_class_entry = self.get_tag_entry(unit_class_type, HedSectionKey.UnitClasses)
        if unit_class_entry:
            return unit_class_entry.unit_class_units
        return []

    def get_tags_with_attribute(self, key, section_key=HedSectionKey.AllTags):
        """ Return tag entries with the given attribute.

        Parameters:
            key (str): A tag attribute.  Eg HedKey.ExtensionAllowed
            section_key (str): The HedSectionKey for the section to retrieve from.

        Returns:
            list: A list of all tags with this attribute.

        Notes:
            - The result is cached so will be fast after first call.

        """
        return self._sections[section_key].get_entries_with_attribute(key, return_name_only=True,
                                                                      schema_prefix=self._schema_prefix)

    def get_tag_entry(self, name, key_class=HedSectionKey.AllTags, schema_prefix=""):
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
                This will not handle extensions or similar.
                If this is a tag, it can have a schema prefix, but it's not required
            key_class (HedSectionKey or str):  The type of entry to return.
            schema_prefix (str): Only used on AllTags.  If incorrect, will return None.

        Returns:
            HedSchemaEntry: The schema entry for the given tag.

        """
        if key_class == HedSectionKey.AllTags:
            if schema_prefix != self._schema_prefix:
                return None
            if name.startswith(self._schema_prefix):
                name = name[len(self._schema_prefix):]

        return self._get_tag_entry(name, key_class)

    def _get_tag_entry(self, name, key_class=HedSectionKey.AllTags):
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
                This will not handle extensions or similar.
            key_class (HedSectionKey or str):  The type of entry to return.

        Returns:
            HedSchemaEntry: The schema entry for the given tag.

        """
        return self._sections[key_class].get(name)

    def find_tag_entry(self, tag, schema_prefix=""):
        """ Find the schema entry for a given source tag.

            Note: Will not identify tags if schema_prefix is set incorrectly

        Parameters:
            tag (str, HedTag):     Any form of tag to look up.  Can have an extension, value, etc.
            schema_prefix (str):  The schema prefix of the tag, if any.

        Returns:
            HedTagEntry: The located tag entry for this tag.
            str: The remainder of the tag that isn't part of the base tag.
            list: A list of errors while converting.

        Notes:
            Works left to right (which is mostly relevant for errors).

        """
        if schema_prefix != self._schema_prefix:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_LIBRARY_UNMATCHED, tag,
                                                          schema_prefix, self.valid_prefixes)
            return None, None, validation_issues
        return self._find_tag_entry(tag, schema_prefix)

    def _find_tag_entry(self, tag, schema_prefix=""):
        """ Find the schema entry for a given source tag.

        Parameters:
            tag (str, HedTag):     Any form of tag to look up.  Can have an extension, value, etc.
            schema_prefix (str):  The schema prefix of the tag, if any.

        Returns:
            HedTagEntry: The located tag entry for this tag.
            str: The remainder of the tag that isn't part of the base tag.
            list: A list of errors while converting.

        Notes:
            Works left to right (which is mostly relevant for errors).

        """
        clean_tag = str(tag)
        prefix = schema_prefix
        clean_tag = clean_tag[len(prefix):]
        prefix_tag_adj = len(prefix)
        working_tag = clean_tag.lower()

        # Most tags are in the schema directly, so test that first
        found_entry = self._get_tag_entry(working_tag)
        if found_entry:
            # this handles the one special case where the actual tag contains "/#" instead of something specific.
            if working_tag.endswith("/#"):
                remainder = working_tag[-2:]
            else:
                remainder = ""

            return found_entry, remainder, []

        current_slash_index = -1
        current_entry = None

        # Loop left to right, checking each word.  Once we find an invalid word, we stop.
        while True:
            next_index = working_tag.find("/", current_slash_index + 1)
            if next_index == -1:
                next_index = len(working_tag)
            parent_name = working_tag[:next_index]
            parent_entry = self._get_tag_entry(parent_name)

            if not parent_entry:
                # We haven't found any tag at all yet
                if current_entry is None:
                    error = ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                      tag,
                                                      index_in_tag=prefix_tag_adj,
                                                      index_in_tag_end=prefix_tag_adj + next_index)
                    return None, None, error
                # If this is not a takes value node, validate each term in the remainder.
                if not current_entry.takes_value_child_entry:
                    child_names = working_tag[current_slash_index + 1:].split("/")
                    word_start_index = current_slash_index + 1 + prefix_tag_adj
                    for name in child_names:
                        if self._get_tag_entry(name):
                            error = ErrorHandler.format_error(ValidationErrors.INVALID_PARENT_NODE,
                                                              tag,
                                                              index_in_tag=word_start_index,
                                                              index_in_tag_end=word_start_index + len(name),
                                                              expected_parent_tag=self.all_tags[name].name)
                            return None, None, error
                        word_start_index += len(name) + 1
                break

            current_entry = parent_entry
            current_slash_index = next_index
            if next_index == len(working_tag):
                break
            continue

        remainder = None
        if current_slash_index != -1:
            remainder = clean_tag[current_slash_index:]
        if remainder and current_entry.takes_value_child_entry:
            current_entry = current_entry.takes_value_child_entry
        found_entry = current_entry

        return found_entry, remainder, []

    # ===============================================
    # Semi-private creation finalizing functions
    # ===============================================
    def finalize_dictionaries(self):
        """ Call to finish loading. """
        self._is_hed3_schema = self.is_hed3_schema
        self._has_duplicate_tags = bool(self.all_tags.duplicate_names)
        self._update_all_entries()

    def _update_all_entries(self):
        """ Call finalize_entry on every schema entry(tag, unit, etc). """
        for section in self._sections.values():
            for entry in section.values():
                entry.finalize_entry(self)

    def _initialize_attributes(self, key_class):
        """ Set the valid attributes for a section.

        Parameters:
            key_class (str): The section key for the section to update.

        """
        self._sections[key_class].valid_attributes = self._get_attributes_for_section(key_class)

    # ===============================================
    # Getters used to write out schema primarily.
    # ===============================================
    def get_desc_iter(self):
        """ Return an iterator over all the descriptions.

        Yields:
            tuple:
                - str: The tag node name.
                - str: The description associated with the node.

        """
        for section in self._sections.values():
            for tag_entry in section.values():
                if tag_entry.description:
                    yield tag_entry.name, tag_entry.description

    def get_tag_description(self, tag_name, key_class=HedSectionKey.AllTags):
        """ Return the description associated with the tag.

        Parameters:
            tag_name (str): A hed tag name(or unit/unit modifier etc) with proper capitalization.
            key_class (str): A string indicating type of description (e.g. All tags, Units, Unit modifier).
                The default is HedSectionKey.AllTags.

        Returns:
            str:  A description of the specified tag.

        """
        tag_entry = self._get_tag_entry(tag_name, key_class)
        if tag_entry:
            return tag_entry.description

    def get_all_schema_tags(self, return_last_term=False):
        """ Get a list of all hed terms from the schema.

        Returns:
            list: A list of all terms(short tags) from the schema.

        Notes:
            Compatible with Hed2 or Hed3.

        """
        final_list = []
        for lower_tag, tag_entry in self.all_tags.items():
            if return_last_term:
                final_list.append(tag_entry.name.split('/')[-1])
            else:
                final_list.append(tag_entry.name)
        return final_list

    def get_unknown_attributes(self):
        """ Retrieve the current list of unknown attributes.

        Returns:
            dict: The keys are attribute names and the values are lists of tags with this attribute.

        Notes:
            This includes attributes found in the wrong section for example
                unitClass attribute found on a Tag.
            The return tag list is in long form.

        """
        unknown_attributes = {}
        for section in self._sections.values():
            for entry in section.values():
                if entry._unknown_attributes:
                    for attribute_name in entry._unknown_attributes:
                        unknown_attributes.setdefault(attribute_name, []).append(entry.name)

        return unknown_attributes

    def get_tag_attribute_names(self):
        """ Return a dict of all allowed tag attributes.

        Returns:
            dict: A dictionary whose keys are attribute names and values are HedSchemaEntry object.

        """
        return {tag_entry.name: tag_entry for tag_entry in self._sections[HedSectionKey.Attributes].values()
                if not tag_entry.has_attribute(HedKey.UnitClassProperty)
                and not tag_entry.has_attribute(HedKey.UnitProperty)
                and not tag_entry.has_attribute(HedKey.UnitModifierProperty)
                and not tag_entry.has_attribute(HedKey.ValueClassProperty)}

    def get_all_tag_attributes(self, tag_name, key_class=HedSectionKey.AllTags):
        """ Gather all attributes for a given tag name.

        Parameters:
            tag_name (str): The name of the tag to check.
            key_class (str): The type of attributes requested.  e.g. Tag, Units, Unit modifiers, or attributes.

        Returns:
            dict: A dictionary of attribute name and attribute value.

        Notes:
            If keys is None, gets all normal hed tag attributes.

        """
        tag_entry = self._get_tag_entry(tag_name, key_class)
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
        """ Return the valid modifiers for the given unit

        Parameters:
            unit (str): A known unit.

        Returns:
            list: List of HedSchemaEntry.

        Notes:
            This is a lower level one that doesn't rely on the Unit entries being fully setup.

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

    def _get_attributes_for_section(self, key_class):
        """ Return the valid attributes for this section.

        Parameters:
            key_class (str): The HedKey for this section.

        Returns:
            dict or HedSchemaSection: A dict of all the attributes and this section.

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
