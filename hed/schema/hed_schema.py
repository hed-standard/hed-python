import json

from hed.schema.hed_schema_constants import HedKey, HedSectionKey
from hed.schema import hed_schema_constants as constants
from hed.schema.schema_io import schema_util
from hed.schema.schema_io.schema2xml import Schema2XML
from hed.schema.schema_io.schema2wiki import Schema2Wiki
from hed.schema.hed_schema_section import HedSchemaSection, HedSchemaTagSection, HedSchemaUnitClassSection
from hed.errors import ErrorHandler
from hed.errors.error_types import ValidationErrors
from hed.schema.hed_schema_base import HedSchemaBase
from hed.errors.exceptions import HedFileError, HedExceptions


class HedSchema(HedSchemaBase):
    """ A HED schema suitable for processing. """

    def __init__(self):
        """ Constructor for the HedSchema class.

            A HedSchema can be used for validation, checking tag attributes, parsing tags, etc.
        """
        super().__init__()
        self._has_duplicate_tags = False
        self.header_attributes = {}
        self.filename = None
        self.prologue = ""
        self.epilogue = ""

        # This is the specified library name_prefix - tags will be {schema_namespace}:{tag_name}
        self._namespace = ""

        self._sections = self._create_empty_sections()

    # ===============================================
    # Basic schema properties
    # ===============================================
    @property
    def version_number(self):
        """ The HED version of this schema.

        Returns:
            str: The version of this schema.

        """
        return self.header_attributes['version']

    @property
    def version(self):
        """The complete schema version, including prefix and library name(if applicable)"""
        library = self.library
        if library:
            library = library + '_'
        return self._namespace + library + self.version_number

    @property
    def library(self):
        """ The name of this library schema if one exists.

        Returns:
            str: Library name if any.

        """
        return self.header_attributes.get(constants.LIBRARY_ATTRIBUTE, "")

    @property
    def with_standard(self):
        """ The version of the base schema this is extended from, if it exists..

        Returns:
            str: HED version or ""

        """
        return self.header_attributes.get(constants.WITH_STANDARD_ATTRIBUTE, "")

    @property
    def merged(self):
        """ Returns if this schema was loaded from a merged file

        Returns:
            bool: True if file was loaded from a merged file


        """
        return not self.header_attributes.get(constants.UNMERGED_ATTRIBUTE, "")

    @property
    def tags(self):
        """ Return the tag schema section.

        Returns:
            HedSchemaTagSection: The tag section.
        """
        return self._sections[HedSectionKey.Tags]

    @property
    def unit_classes(self):
        """ Return the unit classes schema section.

        Returns:
            HedSchemaUnitClassSection: The unit classes section.
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
    def attributes(self):
        """ Return the attributes schema section.

        Returns:
            HedSchemaSection: The attributes section.
        """
        return self._sections[HedSectionKey.Attributes]

    @property
    def properties(self):
        """ Return the properties schema section.

        Returns:
            HedSchemaSection: The properties section.
        """
        return self._sections[HedSectionKey.Properties]

    def get_schema_versions(self):
        """ A list of HED version strings including namespace and library name if any of this schema.

        Returns:
            list: The complete version of this schema including library name and namespace.
        """
        return [self.get_formatted_version()]

    def get_formatted_version(self):
        """ The HED version string including namespace and library name if any of this schema.

        Returns:
            str: A json formatted string of the complete version of this schema including library name and namespace.
        """

        return json.dumps(self.version)

    def get_save_header_attributes(self, save_merged=False):
        """ returns the attributes that should be saved.

        """
        sort_to_start = "!!!!!!!!!!!!!!"
        header_attributes = dict(sorted(self.header_attributes.items(),
                                        key=lambda x: sort_to_start if x[0] == constants.VERSION_ATTRIBUTE else x[0],
                                        reverse=False))
        if save_merged:
            header_attributes.pop(constants.UNMERGED_ATTRIBUTE, None)
        else:
            # make sure it's the last attribute(just to make sure it's in an order)
            header_attributes.pop(constants.UNMERGED_ATTRIBUTE, None)
            header_attributes[constants.UNMERGED_ATTRIBUTE] = "True"

        return header_attributes

    def schema_for_namespace(self, namespace):
        """ Return HedSchema object for this namespace.

        Parameters:
            namespace (str): The schema library name namespace.

        Returns:
            HedSchema: The HED schema object for this schema.
        """
        if self._namespace != namespace:
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
        return [self._namespace]

    # ===============================================
    # Creation and saving functions
    # ===============================================
    def get_as_mediawiki_string(self, save_merged=False):
        """ Return the schema to a mediawiki string.

        Parameters:
            save_merged (bool): If true, this will save the schema as a merged schema if it is a "withStandard" schema.
                                If it is not a "withStandard" schema, this setting has no effect.

        Returns:
            str:  The schema as a string in mediawiki format.

        """
        output_strings = Schema2Wiki.process_schema(self, save_merged)
        return '\n'.join(output_strings)

    def get_as_xml_string(self, save_merged=True):
        """ Return the schema to an XML string.

        Parameters:
            save_merged (bool):
            If true, this will save the schema as a merged schema if it is a "withStandard" schema.
            If it is not a "withStandard" schema, this setting has no effect.
        Returns:
            str: Return the schema as an XML string.

        """
        xml_tree = Schema2XML.process_schema(self, save_merged)
        return schema_util._xml_element_2_str(xml_tree)

    def save_as_mediawiki(self, filename=None, save_merged=False):
        """ Save as mediawiki to a file.

        filename: str
            If present, move the resulting file to this location.
        save_merged: bool
            If true, this will save the schema as a merged schema if it is a "withStandard" schema.
            If it is not a "withStandard" schema, this setting has no effect.

        Returns:
            str:    The newly created schema filename.
        """
        output_strings = Schema2Wiki.process_schema(self, save_merged)
        local_wiki_file = schema_util.write_strings_to_file(output_strings, ".mediawiki")
        return schema_util.move_file(local_wiki_file, filename)

    def save_as_xml(self, filename=None, save_merged=True):
        """ Save as XML to a file.

        filename: str
            If present, move the resulting file to this location.
        save_merged: bool
            If true, this will save the schema as a merged schema if it is a "withStandard" schema.
            If it is not a "withStandard" schema, this setting has no effect.

        Returns:
            str: The name of the newly created schema file.
        """
        xml_tree = Schema2XML.process_schema(self, save_merged)
        local_xml_file = schema_util.write_xml_tree_2_xml_file(xml_tree, ".xml")
        return schema_util.move_file(local_xml_file, filename)

    def set_schema_prefix(self, schema_namespace):
        """ Set library namespace associated for this schema.

        Parameters:
            schema_namespace (str): Should be empty, or end with a colon.(Colon will be automated added if missing).

        :raises HedFileError:
            - The prefix is invalid
        """
        if schema_namespace and schema_namespace[-1] != ":":
            schema_namespace += ":"

        if schema_namespace and not schema_namespace[:-1].isalpha():
            raise HedFileError(HedExceptions.INVALID_LIBRARY_PREFIX,
                               "Schema namespace must contain only alpha characters",
                               self.filename)

        self._namespace = schema_namespace

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
        if self.get_save_header_attributes() != other.get_save_header_attributes():
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
            #                     s = f"{key} unmatched: '{str(dict1[key].name)}' vs '{str(dict2[key].name)}'"
            #                     print(s)
            return False
        if self._namespace != other._namespace:
            return False
        return True

    def __getitem__(self, section_key):
        return self._sections[section_key]

    def check_compliance(self, check_for_warnings=True, name=None, error_handler=None):
        """ Check for HED3 compliance of this schema.

        Parameters:
            check_for_warnings (bool): If True, checks for formatting issues like invalid characters, capitalization.
            name (str): If present, use as the filename for context, rather than using the actual filename.
                        Useful for temp filenames when supporting web services.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.

        Returns:
            list: A list of all warnings and errors found in the file. Each issue is a dictionary.
        """
        from hed.schema import schema_compliance
        return schema_compliance.check_compliance(self, check_for_warnings, name, error_handler)

    def get_tags_with_attribute(self, attribute, key_class=HedSectionKey.Tags):
        """ Return tag entries with the given attribute.

        Parameters:
            attribute (str): A tag attribute.  Eg HedKey.ExtensionAllowed
            key_class (HedSectionKey): The HedSectionKey for the section to retrieve from.

        Returns:
            list: A list of all tags with this attribute.

        Notes:
            - The result is cached so will be fast after first call.
        """
        return self._sections[key_class].get_entries_with_attribute(attribute, return_name_only=True,
                                                                    schema_namespace=self._namespace)

    def get_tag_entry(self, name, key_class=HedSectionKey.Tags, schema_namespace=""):
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
                This will not handle extensions or similar.
                If this is a tag, it can have a schema namespace, but it's not required
            key_class (HedSectionKey or str):  The type of entry to return.
            schema_namespace (str): Only used on Tags.  If incorrect, will return None.

        Returns:
            HedSchemaEntry: The schema entry for the given tag.
        """
        if key_class == HedSectionKey.Tags:
            if schema_namespace != self._namespace:
                return None
            if name.startswith(self._namespace):
                name = name[len(self._namespace):]

        return self._get_tag_entry(name, key_class)

    def find_tag_entry(self, tag, schema_namespace=""):
        """ Find the schema entry for a given source tag.

        Parameters:
            tag (str, HedTag): Any form of tag to look up.  Can have an extension, value, etc.
            schema_namespace (str): The schema namespace of the tag, if any.

        Returns:
            HedTagEntry: The located tag entry for this tag.
            str: The remainder of the tag that isn't part of the base tag.
            list: A list of errors while converting.

        Notes:
            Works left to right (which is mostly relevant for errors).
        """
        if schema_namespace != self._namespace:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_LIBRARY_UNMATCHED, tag,
                                                          schema_namespace, self.valid_prefixes)
            return None, None, validation_issues
        return self._find_tag_entry(tag, schema_namespace)

    # ===============================================
    # Private utility functions for getting/finding tags
    # ===============================================
    def _get_tag_entry(self, name, key_class=HedSectionKey.Tags):
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
                This will not handle extensions or similar.
            key_class (HedSectionKey or str):  The type of entry to return.

        Returns:
            HedSchemaEntry: The schema entry for the given tag.

        """
        return self._sections[key_class].get(name)

    def _find_tag_entry(self, tag, schema_namespace=""):
        """ Find the schema entry for a given source tag.

        Parameters:
            tag (str, HedTag):     Any form of tag to look up.  Can have an extension, value, etc.
            schema_namespace (str):  The schema namespace of the tag, if any.

        Returns:
            HedTagEntry: The located tag entry for this tag.
            str: The remainder of the tag that isn't part of the base tag.
            list: A list of errors while converting.

        Notes:
            Works left to right (which is mostly relevant for errors).

        """
        clean_tag = str(tag)
        namespace = schema_namespace
        clean_tag = clean_tag[len(namespace):]
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

        prefix_tag_adj = len(namespace)

        try:
            found_entry, current_slash_index = self._find_tag_subfunction(tag, working_tag, prefix_tag_adj)
        except self._TagIdentifyError as e:
            issue = e.issue
            return None, None, issue

        remainder = None
        if current_slash_index != -1:
            remainder = clean_tag[current_slash_index:]
        if remainder and found_entry.takes_value_child_entry:
            found_entry = found_entry.takes_value_child_entry

        return found_entry, remainder, []

    def _find_tag_subfunction(self, tag, working_tag, prefix_tag_adj):
        """Finds the base tag and remainder from the left, raising exception on issues"""
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
                    raise self._TagIdentifyError(error)
                # If this is not a takes value node, validate each term in the remainder.
                if not current_entry.takes_value_child_entry:
                    # This will raise _TagIdentifyError on any issues
                    self._validate_remaining_terms(tag, working_tag, prefix_tag_adj, current_slash_index)
                break

            current_entry = parent_entry
            current_slash_index = next_index
            if next_index == len(working_tag):
                break

        return current_entry, current_slash_index

    def _validate_remaining_terms(self, tag, working_tag, prefix_tag_adj, current_slash_index):
        """ Validates the terms past current_slash_index.
        
        :raises _TagIdentifyError:
            - One of the extension terms already exists as a schema term.
        """
        child_names = working_tag[current_slash_index + 1:].split("/")
        word_start_index = current_slash_index + 1 + prefix_tag_adj
        for name in child_names:
            if self._get_tag_entry(name):
                error = ErrorHandler.format_error(ValidationErrors.INVALID_PARENT_NODE,
                                                  tag,
                                                  index_in_tag=word_start_index,
                                                  index_in_tag_end=word_start_index + len(name),
                                                  expected_parent_tag=self.tags[name].name)
                raise self._TagIdentifyError(error)
            word_start_index += len(name) + 1

    # ===============================================
    # Semi-private creation finalizing functions
    # ===============================================
    def finalize_dictionaries(self):
        """ Call to finish loading. """
        self._has_duplicate_tags = bool(self.tags.duplicate_names)
        self._update_all_entries()

    def _update_all_entries(self):
        """ Call finalize_entry on every schema entry(tag, unit, etc). """
        for key_class, section in self._sections.items():
            self._initialize_attributes(key_class)
            section._finalize_section(self)

    def _initialize_attributes(self, key_class):
        """ Set the valid attributes for a section.

        Parameters:
            key_class (HedSectionKey): The section key for the section to update.

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

    def get_tag_description(self, tag_name, key_class=HedSectionKey.Tags):
        """ Return the description associated with the tag.

        Parameters:
            tag_name (str): A hed tag name(or unit/unit modifier etc) with proper capitalization.
            key_class (str): A string indicating type of description (e.g. All tags, Units, Unit modifier).
                The default is HedSectionKey.Tags.

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
        for lower_tag, tag_entry in self.tags.items():
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
            - This includes attributes found in the wrong section for example unitClass attribute found on a Tag.
            - The return tag list is in long form.

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

    def get_all_tag_attributes(self, tag_name, key_class=HedSectionKey.Tags):
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
        dictionaries[HedSectionKey.UnitClasses] = HedSchemaUnitClassSection(HedSectionKey.UnitClasses)
        dictionaries[HedSectionKey.ValueClasses] = HedSchemaSection(HedSectionKey.ValueClasses)
        dictionaries[HedSectionKey.Tags] = HedSchemaTagSection(HedSectionKey.Tags, case_sensitive=False)

        return dictionaries

    def _get_modifiers_for_unit(self, unit):
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

    def _add_element_property_attributes(self, attribute_dict):
        attributes = {attribute: entry for attribute, entry in self._sections[HedSectionKey.Attributes].items()
                      if entry.has_attribute(HedKey.ElementProperty)}

        attribute_dict.update(attributes)

    def _get_attributes_for_section(self, key_class):
        """ Return the valid attributes for this section.

        Parameters:
            key_class (HedSectionKey): The HedKey for this section.

        Returns:
            dict or HedSchemaSection: A dict of all the attributes and this section.

        """
        if key_class == HedSectionKey.Tags:
            return self.get_tag_attribute_names()
        elif key_class == HedSectionKey.Attributes:
            prop_added_dict = {key: value for key, value in self._sections[HedSectionKey.Properties].items()}
            self._add_element_property_attributes(prop_added_dict)
            return prop_added_dict
        elif key_class == HedSectionKey.Properties:
            prop_added_dict = {}
            self._add_element_property_attributes(prop_added_dict)
            return prop_added_dict
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
                          if entry.has_attribute(attrib_class) or entry.has_attribute(HedKey.ElementProperty)}
            return attributes

    # ===============================================
    # Semi private function used to create a schema in memory(usually from a source file)
    # ===============================================
    def _add_tag_to_dict(self, long_tag_name, new_entry, key_class):
        # Add the InLibrary attribute to any library schemas as they are loaded
        # These are later removed when they are saved out, if saving unmerged
        if self.library and (not self.with_standard or (not self.merged and self.with_standard)):
            # only add it if not already present - This is a rare case
            if not new_entry.has_attribute(HedKey.InLibrary):
                new_entry._set_attribute_value(HedKey.InLibrary, self.library)

        section = self._sections[key_class]
        return section._add_to_dict(long_tag_name, new_entry)

    def _create_tag_entry(self, long_tag_name, key_class):
        section = self._sections[key_class]
        return section._create_tag_entry(long_tag_name)

    class _TagIdentifyError(Exception):
        """Used internally to note when a tag cannot be identified."""
        def __init__(self, issue):
            self.issue = issue
