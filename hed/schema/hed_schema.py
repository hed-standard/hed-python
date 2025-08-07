from __future__ import annotations

import json
from typing import Union

from pandas import DataFrame

from hed.schema.hed_schema_entry import HedSchemaEntry
from hed.schema.hed_schema_constants import (HedKey, HedSectionKey, HedKeyOld,
                                           VERSION_ATTRIBUTE, LIBRARY_ATTRIBUTE,
                                           WITH_STANDARD_ATTRIBUTE, UNMERGED_ATTRIBUTE)
from hed.schema.schema_io import schema_util, df_util
from hed.schema.schema_io.schema2xml import Schema2XML
from hed.schema.schema_io.schema2wiki import Schema2Wiki
from hed.schema.schema_io.schema2df import Schema2DF

from hed.schema.hed_schema_section import (HedSchemaSection, HedSchemaTagSection, HedSchemaUnitClassSection,
                                           HedSchemaUnitSection)
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
        self.header_attributes = {}
        self.filename = None
        self.prologue = ""
        self.epilogue = ""
        self.extras = {} # Used to store any additional data that might be needed for serialization (like OWL or other formats)

        # This is the specified library name_prefix - tags will be {schema_namespace}:{tag_name}
        self._namespace = ""

        self._sections = self._create_empty_sections()
        self.source_format = None  # The type of file this was loaded from(mediawiki, xml, or owl - None if mixed)

    # ===============================================
    # Basic schema properties
    # ===============================================
    @property
    def version_number(self) -> str:
        """ The HED version of this schema.

        Returns:
            str: The version of this schema.
        """
        return self.header_attributes['version']

    @property
    def version(self) -> str:
        """ The complete schema version, including prefix and library name(if applicable).

        Returns:
            str: The complete schema version including library name and namespace.
        """
        libraries = self.library.split(",")
        versions = self.version_number.split(",")
        namespace = self._namespace
        combined_versions = [f"{namespace}{version}" if not library else f"{namespace}{library}_{version}"
                             for library, version in zip(libraries, versions)]

        return ",".join(combined_versions)

    @property
    def library(self) -> str:
        """ The name of this library schema if one exists.

        Returns:
            str: Library name if any.
        """
        return self.header_attributes.get(LIBRARY_ATTRIBUTE, "")

    @property
    def schema_namespace(self) -> str:
        """ Returns the schema namespace prefix.

        Returns:
            str: The schema namespace prefix.
        """
        return self._namespace

    def can_save(self) -> bool:
        """ Returns if it's legal to save this schema.

        You cannot save schemas loaded as merged from multiple library schemas.

        Returns:
            bool: True if this can be saved.
        """
        return not self.library or "," not in self.library

    @property
    def with_standard(self) -> str:
        """ The version of the base schema this is extended from, if it exists.

        Returns:
            str: HED version or empty string.
        """
        return self.header_attributes.get(WITH_STANDARD_ATTRIBUTE, "")

    @property
    def merged(self) -> bool:
        """ Returns if this schema was loaded from a merged file.

        Returns:
            bool: True if file was loaded from a merged file.
        """
        return not self.header_attributes.get(UNMERGED_ATTRIBUTE, "")

    @property
    def tags(self) -> "HedSchemaTagSection":
        """ Return the tag schema section.

        Returns:
            HedSchemaTagSection: The tag section.
        """
        return self._sections[HedSectionKey.Tags]

    @property
    def unit_classes(self) -> "HedSchemaUnitClassSection":
        """ Return the unit classes schema section.

        Returns:
            HedSchemaUnitClassSection: The unit classes section.
        """
        return self._sections[HedSectionKey.UnitClasses]

    @property
    def units(self) -> "HedSchemaUnitSection":
        """ Return the unit schema section.

        Returns:
            HedSchemaUnitSection: The unit section.
        """
        return self._sections[HedSectionKey.Units]

    @property
    def unit_modifiers(self) -> "HedSchemaSection":
        """ Return the modifiers classes schema section.

        Returns:
            HedSchemaSection: The unit modifiers section.
        """
        return self._sections[HedSectionKey.UnitModifiers]

    @property
    def value_classes(self) -> "HedSchemaSection":
        """ Return the value classes schema section.

        Returns:
            HedSchemaSection: The value classes section.
        """
        return self._sections[HedSectionKey.ValueClasses]

    @property
    def attributes(self) -> "HedSchemaSection":
        """ Return the attributes schema section.

        Returns:
            HedSchemaSection: The attributes section.
        """
        return self._sections[HedSectionKey.Attributes]

    @property
    def properties(self) -> "HedSchemaSection":
        """ Return the properties schema section.

        Returns:
            HedSchemaSection: The properties section.
        """
        return self._sections[HedSectionKey.Properties]

    def get_schema_versions(self) -> list[str]:
        """ A list of HED version strings including namespace and library name if any of this schema.

        Returns:
            list[str]: The complete version of this schema including library name and namespace.
        """
        return [self.get_formatted_version()]

    def get_formatted_version(self) -> str:
        """ The HED version string including namespace and library name if any of this schema.

        Returns:
            str: A json formatted string of the complete version of this schema including library name and namespace.
        """
        return json.dumps(self.version)

    def get_save_header_attributes(self, save_merged: bool = False) -> dict:
        """ Returns the attributes that should be saved.

        Parameters:
            save_merged (bool): Whether to save as merged schema.

        Returns:
            dict: The header attributes dictionary.
        """
        sort_to_start = "!!!!!!!!!!!!!!"
        header_attributes = dict(sorted(self.header_attributes.items(),
                                        key=lambda x: sort_to_start if x[0] == VERSION_ATTRIBUTE else x[0],
                                        reverse=False))
        if save_merged:
            header_attributes.pop(UNMERGED_ATTRIBUTE, None)
        else:
            # make sure it's the last attribute(just to make sure it's in an order)
            header_attributes.pop(UNMERGED_ATTRIBUTE, None)
            header_attributes[UNMERGED_ATTRIBUTE] = "True"

        return header_attributes

    def schema_for_namespace(self, namespace: str) -> Union["HedSchema", None]:
        """ Return HedSchema object for this namespace.

        Parameters:
            namespace (str): The schema library name namespace.

        Returns:
            Union[HedSchema, None]: The HED schema object for this schema, or None if namespace doesn't match.
        """
        if self._namespace != namespace:
            return None
        return self

    @property
    def valid_prefixes(self) -> list[str]:
        """ Return a list of all prefixes this schema will accept

        Returns:
            list[str]:   A list of valid tag prefixes for this schema.

        Notes:
            - The return value is always length 1 if using a HedSchema.
        """
        return [self._namespace]

    def get_extras(self, extras_key) -> Union[DataFrame, None]:
        """ Get the extras corresponding to the given key

        Parameters:
            extras_key (str): The key to check for in the extras dictionary.

        Returns:
            Union[pd.DataFrame, None]: The DataFrame for this extras key, or None if it doesn't exist or is empty.
        """
        if not hasattr(self, 'extras') or not extras_key in self.extras:
            return None
        externals = self.extras[extras_key]
        if externals.empty:
            return None
        return externals

    # ===============================================
    # Creation and saving functions
    # ===============================================

    # todo: we may want to collapse these 6 functions into one like this
    # def serialize(self, filename=None, save_merged=False, file_format=whatever is default):
    #     pass

    def get_as_mediawiki_string(self, save_merged=False) -> str:
        """ Return the schema to a mediawiki string.

        Parameters:
            save_merged (bool): If True, this will save the schema as a merged schema if it is a "withStandard" schema.
                                If it is not a "withStandard" schema, this setting has no effect.

        Returns:
            str: The schema as a string in mediawiki format.

        """
        output_strings = Schema2Wiki().process_schema(self, save_merged)
        return '\n'.join(output_strings)

    def get_as_xml_string(self, save_merged=True) -> str:
        """ Return the schema to an XML string.

        Parameters:
            save_merged (bool): If True, this will save the schema as a merged schema if it is a "withStandard" schema.
                                If it is not a "withStandard" schema, this setting has no effect.

        Returns:
            str: The schema as an XML string.

        """
        xml_tree = Schema2XML().process_schema(self, save_merged)
        return schema_util.xml_element_2_str(xml_tree)

    def get_as_dataframes(self, save_merged=False) -> dict[DataFrame]:
        """ Get a dict of dataframes representing this file

        Parameters:
            save_merged (bool): If True, returns DFs as if merged with standard.

        Returns:
            dict[DataFrame]: A dict of dataframes you can load as a schema.
        """
        output_dfs = Schema2DF().process_schema(self, save_merged)
        return output_dfs

    def save_as_mediawiki(self, filename, save_merged=False):
        """ Save as mediawiki to a file.

        Parameters:
            filename (str): Save location.
            save_merged (bool): If True, this will save the schema as a merged schema if it is a "withStandard" schema.
                                If it is not a "withStandard" schema, this setting has no effect.

        Raises:
            OSError: File cannot be saved for some reason.
        """
        output_strings = Schema2Wiki().process_schema(self, save_merged)
        with open(filename, mode='w', encoding='utf-8') as opened_file:
            for string in output_strings:
                opened_file.write(string)
                opened_file.write('\n')

    def save_as_xml(self, filename, save_merged=True):
        """ Save as XML to a file.

        Parameters:
            filename (str): Save location.
            save_merged (bool): If true, this will save the schema as a merged schema if it is a "withStandard" schema.
                                If it is not a "withStandard" schema, this setting has no effect.

        Raises:
            OSError: File cannot be saved for some reason.
        """
        xml_tree = Schema2XML().process_schema(self, save_merged)
        with open(filename, mode='w', encoding='utf-8') as opened_file:
            xml_string = schema_util.xml_element_2_str(xml_tree)
            opened_file.write(xml_string)

    def save_as_dataframes(self, base_filename, save_merged=False):
        """ Save as dataframes to a folder of files.

            If base_filename has a .tsv suffix, save directly to the indicated location.
            If base_filename is a directory(does NOT have a .tsv suffix), save the contents into a directory named that.
            The subfiles are named the same.  e.g. HED8.3.0/HED8.3.0_Tag.tsv

        Parameters:
            base_filename (str): Save filename. A suffix will be added to most, e.g. _Tag
            save_merged (bool): If True, this will save the schema as a merged schema if it is a "withStandard" schema.
                                If it is not a "withStandard" schema, this setting has no effect.

        Raises:
            OSError: File cannot be saved for some reason.
        """
        output_dfs = Schema2DF().process_schema(self, save_merged)
        if hasattr(self, 'extras') and self.extras:
           output_dfs.update(self.extras)
        df_util.save_dataframes(base_filename, output_dfs)

    def set_schema_prefix(self, schema_namespace):
        """ Set library namespace associated for this schema.

        Parameters:
            schema_namespace (str): Should be empty, or end with a colon.(Colon will be automated added if missing).

        Raises:
            HedFileError: The prefix is invalid.
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
            # print(f"Header attributes not equal: '{self.get_save_header_attributes()}' vs '{other.get_save_header_attributes()}'")
            return False
        if self.has_duplicates() != other.has_duplicates():
            # print(f"Duplicates: '{self.has_duplicates()}' vs '{other.has_duplicates()}'")
            return False
        if self.prologue.strip() != other.prologue.strip():
            # print(f"PROLOGUE NOT EQUAL: '{self.prologue.strip()}' vs '{other.prologue.strip()}'")
            return False
        if self.epilogue.strip() != other.epilogue.strip():
            # print(f"EPILOGUE NOT EQUAL: '{self.epilogue.strip()}' vs '{other.epilogue.strip()}'")
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
            # print(f"NAMESPACE NOT EQUAL: '{self._namespace}' vs '{other._namespace}'")
            return False
        return True

    def __getitem__(self, section_key):
        return self._sections[section_key]

    def check_compliance(self, check_for_warnings=True, name=None, error_handler=None) -> list[dict]:
        """ Check for HED3 compliance of this schema.

        Parameters:
            check_for_warnings (bool): If True, checks for formatting issues like invalid characters, capitalization.
            name (str): If present, use as the filename for context, rather than using the actual filename.
                        Useful for temp filenames when supporting web services.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.

        Returns:
            list[dict]: A list of all warnings and errors found in the file. Each issue is a dictionary.
        """
        from hed.schema import schema_compliance
        return schema_compliance.check_compliance(self, check_for_warnings, name, error_handler)

    def get_tags_with_attribute(self, attribute, key_class=HedSectionKey.Tags) -> list["HedSchemaEntry"]:
        """ Return tag entries with the given attribute.

        Parameters:
            attribute (str): A tag attribute.  Eg HedKey.ExtensionAllowed
            key_class (HedSectionKey): The HedSectionKey for the section to retrieve from.

        Returns:
            list[HedSchemaEntry]: A list of all tags with this attribute.

        Notes:
            - The result is cached so will be fast after first call.
        """
        return self._sections[key_class].get_entries_with_attribute(attribute, return_name_only=True,
                                                                    schema_namespace=self._namespace)

    def get_tag_entry(self, name: str, key_class=HedSectionKey.Tags, schema_namespace: str = "") -> Union["HedSchemaEntry", None]:
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
                This will not handle extensions or similar.
                If this is a tag, it can have a schema namespace, but it's not required
            key_class (HedSectionKey or str):  The type of entry to return.
            schema_namespace (str): Only used on Tags.  If incorrect, will return None.

        Returns:
            Union[HedSchemaEntry, None]: The schema entry for the given tag, or None if not found.
        """
        if key_class == HedSectionKey.Tags:
            if schema_namespace != self._namespace:
                return None
            if name.startswith(self._namespace):
                name = name[len(self._namespace):]

        return self._get_tag_entry(name, key_class)

    def find_tag_entry(self, tag, schema_namespace="") -> tuple[Union["HedTagEntry", None], Union[str, None], list[dict]]:
        """ Find the schema entry for a given source tag.

        Parameters:
            tag (str, HedTag):     Any form of tag to look up.  Can have an extension, value, etc.
            schema_namespace (str):  The schema namespace of the tag, if any.

        Returns:
            tuple[Union["HedTagEntry", None], Union[str, None], list[dict]]:
            - The located tag entry for this tag.
            - The remainder of the tag that isn't part of the base tag.
            - A list of errors while converting.

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

    def _find_tag_entry(self, tag, schema_namespace="") -> tuple[Union["HedTagEntry", None], Union[str, None], list[dict]]:
        """ Find the schema entry for a given source tag.

        Parameters:
            tag (str, HedTag):     Any form of tag to look up.  Can have an extension, value, etc.
            schema_namespace (str):  The schema namespace of the tag, if any.

        Returns:
            tuple[Union["HedTagEntry", None], Union[str, None], list[dict]]:
            - The located tag entry for this tag.
            - The remainder of the tag that isn't part of the base tag.
            - A list of errors while converting.

        Notes:
            Works left to right (which is mostly relevant for errors).

        """
        clean_tag = str(tag)
        namespace = schema_namespace
        clean_tag = clean_tag[len(namespace):]
        working_tag = clean_tag.casefold()

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

        Raises:
            _TagIdentifyError: One of the extension terms already exists as a schema term.
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

    def has_duplicates(self):
        """Returns the first duplicate tag/unit/etc. if any section has a duplicate name"""
        for section in self._sections.values():
            has_duplicates = bool(section.duplicate_names)
            if has_duplicates:
                # Return first entry of dict
                return next(iter(section.duplicate_names))

        return False

    # ===============================================
    # Semi-private creation finalizing functions
    # ===============================================
    def finalize_dictionaries(self):
        """ Call to finish loading. """
        # Kludge - Reset this here so it recalculates while having all properties
        self._schema83 = None
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
    def get_tag_attribute_names_old(self) -> dict[str, HedSchemaEntry]:
        """ Return a dict of all allowed tag attributes.

        Returns:
            dict[str, HedSchemaEntry]: A dictionary whose keys are attribute names and values are HedSchemaEntry object.

        """
        return {tag_entry.name: tag_entry for tag_entry in self._sections[HedSectionKey.Attributes].values()
                if not tag_entry.has_attribute(HedKeyOld.UnitClassProperty)
                and not tag_entry.has_attribute(HedKeyOld.UnitProperty)
                and not tag_entry.has_attribute(HedKeyOld.UnitModifierProperty)
                and not tag_entry.has_attribute(HedKeyOld.ValueClassProperty)}

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
        dictionaries[HedSectionKey.Units] = HedSchemaUnitSection(HedSectionKey.Units)
        dictionaries[HedSectionKey.UnitClasses] = HedSchemaUnitClassSection(HedSectionKey.UnitClasses)
        dictionaries[HedSectionKey.ValueClasses] = HedSchemaSection(HedSectionKey.ValueClasses)
        dictionaries[HedSectionKey.Tags] = HedSchemaTagSection(HedSectionKey.Tags, case_sensitive=False)

        return dictionaries

    def _get_modifiers_for_unit(self, unit):
        """ Return the valid modifiers for the given unit

        Parameters:
            unit (str): A known unit.

        Returns:
           list[HedSchemaEntry]: The derived units for this unit.

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

    def _add_element_property_attributes(self, attribute_dict, attribute_name):
        attributes = {attribute: entry for attribute, entry in self._sections[HedSectionKey.Attributes].items()
                      if entry.has_attribute(attribute_name)}

        attribute_dict.update(attributes)

    def _get_attributes_for_section(self, key_class):
        """Return the valid attributes for this section.

        Parameters:
            key_class (HedSectionKey): The HedKey for this section.

        Returns:
            dict: A dict of all the attributes for this section.
        """
        element_prop_key = HedKey.ElementDomain if self.schema_83_props else HedKeyOld.ElementProperty

        # Common logic for Attributes and Properties
        if key_class in [HedSectionKey.Attributes, HedSectionKey.Properties]:
            prop_added_dict = {}
            if key_class == HedSectionKey.Attributes:
                prop_added_dict = {key: value for key, value in self._sections[HedSectionKey.Properties].items()}
            self._add_element_property_attributes(prop_added_dict, element_prop_key)
            return prop_added_dict

        if self.schema_83_props:
            attrib_classes = {
                HedSectionKey.UnitClasses: HedKey.UnitClassDomain,
                HedSectionKey.Units: HedKey.UnitDomain,
                HedSectionKey.UnitModifiers: HedKey.UnitModifierDomain,
                HedSectionKey.ValueClasses: HedKey.ValueClassDomain,
                HedSectionKey.Tags: HedKey.TagDomain
            }
        else:
            attrib_classes = {
                HedSectionKey.UnitClasses: HedKeyOld.UnitClassProperty,
                HedSectionKey.Units: HedKeyOld.UnitProperty,
                HedSectionKey.UnitModifiers: HedKeyOld.UnitModifierProperty,
                HedSectionKey.ValueClasses: HedKeyOld.ValueClassProperty
            }
            if key_class == HedSectionKey.Tags:
                return self.get_tag_attribute_names_old()

        # Retrieve attributes based on the determined class
        attrib_class = attrib_classes.get(key_class)
        if not attrib_class:
            return []

        attributes = {attribute: entry for attribute, entry in self._sections[HedSectionKey.Attributes].items()
                      if entry.has_attribute(attrib_class) or entry.has_attribute(element_prop_key)}
        return attributes

    # ===============================================
    # Semi private function used to create a schema in memory(usually from a source file)
    # ===============================================
    def _add_tag_to_dict(self, long_tag_name, new_entry, key_class):
        section = self._sections[key_class]
        return section._add_to_dict(long_tag_name, new_entry)

    def _create_tag_entry(self, long_tag_name, key_class):
        section = self._sections[key_class]
        return section._create_tag_entry(long_tag_name)

    class _TagIdentifyError(Exception):
        """Used internally to note when a tag cannot be identified."""
        def __init__(self, issue):
            self.issue = issue
