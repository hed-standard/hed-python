"""
This module contains the HedSchema class which encapsulates all HED tags, tag attributes, unit classes, and
unit class attributes in a dictionary.

The dictionary is a dictionary of dictionaries. The dictionary names are the list in HedKey from hed_schema_constants.
"""
from hed.schema.hed_schema_constants import HedKey
from hed.util import file_util
from hed.errors import error_reporter
from hed.schema.schema2xml import HedSchema2XML
from hed.schema.schema2wiki import HedSchema2Wiki
from hed.schema import schema_compliance
from hed.errors.error_types import ValidationErrors
from hed.schema import schema_validation_util

import inflect
pluralize = inflect.engine()
pluralize.defnoun("hertz", "hertz")


class HedSchema:
    def __init__(self):
        """Constructor for the HedSchema class.

        Parameters
        ----------
        Returns
        -------
        HedSchema
            A HedSchema object.
        """
        self.no_duplicate_tags = True
        self.header_attributes = {}
        self._filename = None
        self.dictionaries = self._create_empty_dictionaries()
        self.prologue = ""
        self.epilogue = ""

        self.issues = []
        self._is_hed3_schema = None
        # This is the specified library prefix - tags will be {library_prefix}:{tag_name}
        self._library_prefix = ""

    # ===============================================
    # Basic schema properties
    # ===============================================
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        if self._filename is None:
            self._filename = value

    @property
    def version(self):
        return self.header_attributes['version']

    @property
    def library(self):
        return self.header_attributes.get('library')
    
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
        Return the schema to an xml string

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
        schema2wiki = HedSchema2Wiki()
        output_strings = schema2wiki.process_schema(self)
        local_wiki_file = file_util.write_strings_to_file(output_strings, ".mediawiki")
        return local_wiki_file

    def set_library_prefix(self, library_prefix):
        """
        Updates the tags in this schema with the given prefix, removing any existing prefix.

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

        len_prefix = len(self._library_prefix)
        new_tag_dicts = {}
        dicts_to_update = self.get_tag_attribute_names()
        bool_attribute_names = [dict_name for dict_name in dicts_to_update
                                if dict_name in self.dictionaries[HedKey.BoolProperty]]
        dicts_to_update += [HedKey.AllTags, HedKey.ExtensionAllowedPropagated]
        bool_attribute_names += [HedKey.AllTags, HedKey.ExtensionAllowedPropagated]
        for dict_name in dicts_to_update:
            tag_dict = self.dictionaries[dict_name]
            new_dict = {}
            for tag_key_name, tag_key_value in tag_dict.items():
                tag_key_name = library_prefix.lower() + tag_key_name[len_prefix:]
                if dict_name in bool_attribute_names:
                    tag_key_value = library_prefix + tag_key_value[len_prefix:]
                new_dict[tag_key_name] = tag_key_value
            new_tag_dicts[dict_name] = new_dict

        for dict_name, new_dict in new_tag_dicts.items():
            self.dictionaries[dict_name] = new_dict

        # Update description dictionary
        tag_desc_prefix = f"{HedKey.AllTags}_"
        len_prefix += len(tag_desc_prefix)
        new_desc_dict = {}
        for desc_name, desc in self.dictionaries[HedKey.Descriptions].items():
            if desc_name.startswith(tag_desc_prefix):
                desc_name = tag_desc_prefix + library_prefix.lower() + desc_name[len_prefix:]
            new_desc_dict[desc_name] = desc
        self.dictionaries[HedKey.Descriptions] = new_desc_dict

        self._library_prefix = library_prefix
        self.finalize_dictionaries()

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
        short_tag_dict = self.dictionaries[HedKey.ShortTags]
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
    @property
    def has_duplicate_tags(self):
        """
        Returns True if this is a valid hed3 schema with no duplicate short tags.

        Returns
        -------
        bool
            Returns True if this is a valid hed3 schema with no duplicate short tags.
        """
        return not self.no_duplicate_tags

    @property
    def has_unit_classes(self):
        return HedKey.UnitClasses in self.dictionaries

    @property
    def is_hed3_compatible(self):
        return self.no_duplicate_tags

    @property
    def is_hed3_schema(self):
        if self._is_hed3_schema is not None:
            return self._is_hed3_schema

        return self.library or schema_validation_util.is_hed3_version_number(self.version)

    @property
    def has_unit_modifiers(self):
        return HedKey.SIUnitModifier in self.dictionaries

    @property
    def has_value_classes(self):
        return bool(self.dictionaries[HedKey.ValueClasses])

    def __eq__(self, other):
        # Comment the following back in for easy debugging of schema that should be equal.
        dict_keys = set(list(self.dictionaries.keys()) + list(other.dictionaries.keys()))
        for dict_key in dict_keys:
            if dict_key not in self.dictionaries:
                print(f"{dict_key} dict not in self")
                continue
            if dict_key not in other.dictionaries:
                print(f"{dict_key} dict not in other")
                continue
            dict1 = self.dictionaries[dict_key]
            dict2 = other.dictionaries[dict_key]
            if dict1 != dict2:
                print(f"DICT {dict_key} NOT EQUAL")
                key_union = set(list(dict1.keys()) + list(dict2.keys()))
                for key in key_union:
                    if key not in dict1:
                        print(f"{key} not in dict1")
                        continue
                    if key not in dict2:
                        print(f"{key} not in dict2")
                        continue
                    if dict1[key] != dict2[key]:
                        print(f"{key} doesn't match.  '{dict1[key]}' vs '{dict2[key]}'")
        if self.dictionaries != other.dictionaries:
            return False
        if self.header_attributes != other.header_attributes:
            return False
        if self.no_duplicate_tags != other.no_duplicate_tags:
            return False
        if self.prologue != other.prologue:
            return False
        if self.epilogue != other.epilogue:
            return False
        return True

    def calculate_canonical_forms(self, original_tag, error_handler=None):
        """
        This takes a hed tag(short or long form) and converts it to the long form
        Works left to right.(mostly relevant for errors)
        Note: This only does minimal validation

        eg 'Event'                    - Returns ('Event', None)
           'Sensory event'            - Returns ('Event/Sensory event', None)
        Takes Value:
           'Environmental sound/Unique Value'
                                      - Returns ('Item/Sound/Environmental Sound/Unique Value', None)
        Extension Allowed:
            'Experiment control/demo_extension'
                                      - Returns ('Event/Experiment Control/demo_extension/', None)
            'Experiment control/demo_extension/second_part'
                                      - Returns ('Event/Experiment Control/demo_extension/second_part', None)


        Parameters
        ----------
        original_tag: HedTag
            A single hed tag(long or short)
        error_handler: ErrorHandler
            The error handler to use for context.  Will create a default one if not passed.
        Returns
        -------
        long_tag: str
            The converted long tag
        short_tag_index: int
            The position the short tag starts at in long_tag
        extension_index: int
            The position the extension or value starts at in the long_tag
        errors: list
            a list of errors while converting
        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()

        clean_tag = original_tag.tag.lower()
        prefix = original_tag.library_prefix
        clean_tag = clean_tag[len(prefix):]
        prefix_tag_adj = len(prefix)
        split_tags = clean_tag.split("/")
        found_unknown_extension = False
        found_index_end = 0
        found_index_start = 0
        found_long_org_tag = None
        index_in_tag_end = 0
        # Iterate over tags left to right keeping track of current index
        for tag in split_tags:
            tag_len = len(tag)
            # Skip slashes
            if index_in_tag_end != 0:
                index_in_tag_end += 1
            index_start = index_in_tag_end
            index_in_tag_end += tag_len

            # If we already found an unknown tag, it's implicitly an extension.  No known tags can follow it.
            if not found_unknown_extension:
                if tag not in self.short_tag_mapping:
                    found_unknown_extension = True
                    if not found_long_org_tag:
                        error = error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                           original_tag, index_in_tag=index_start + prefix_tag_adj,
                                                           index_in_tag_end=index_in_tag_end + prefix_tag_adj)
                        return str(original_tag), None, None, error
                    continue

                long_org_tags = self.short_tag_mapping[tag]
                long_org_tag = None
                if isinstance(long_org_tags, str):
                    tag_string = long_org_tags.lower()

                    main_hed_portion = clean_tag[:index_in_tag_end]
                    # Verify the tag has the correct path above it.
                    if tag_string.endswith(main_hed_portion):
                        long_org_tag = long_org_tags
                else:
                    for org_tag_string in long_org_tags:
                        tag_string = org_tag_string.lower()

                        main_hed_portion = clean_tag[:index_in_tag_end]

                        if tag_string.endswith(main_hed_portion):
                            long_org_tag = org_tag_string
                            break
                if not long_org_tag:
                    error = error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, tag=original_tag,
                                                       index_in_tag=index_start + prefix_tag_adj,
                                                       index_in_tag_end=index_in_tag_end + prefix_tag_adj,
                                                       expected_parent_tag=long_org_tags)
                    return str(original_tag), None, None, error

                # In hed2 compatible, make sure this is a long form of a tag or throw an invalid base tag error.
                if not self.is_hed3_compatible:
                    if not clean_tag.startswith(long_org_tag.lower()):
                        error = error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                           original_tag, index_in_tag=index_start + prefix_tag_adj,
                                                           index_in_tag_end=index_in_tag_end + prefix_tag_adj)
                        return str(original_tag), None, None, error

                found_index_start = index_start
                found_index_end = index_in_tag_end
                found_long_org_tag = long_org_tag
            else:
                # These means we found a known tag in the remainder/extension section, which is an error
                if tag in self.short_tag_mapping:
                    error = error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, original_tag,
                                                       index_in_tag=index_start + prefix_tag_adj,
                                                       index_in_tag_end=index_in_tag_end + prefix_tag_adj,
                                                       expected_parent_tag=self.short_tag_mapping[tag])
                    return str(original_tag), None, None, error

        full_tag_string = str(original_tag)
        # skip over the tag prefix if present
        full_tag_string = full_tag_string[len(prefix):]
        # Finally don't actually adjust the tag if it's hed2 style.
        if not self.is_hed3_compatible:
            return full_tag_string, None, found_index_end, []

        remainder = full_tag_string[found_index_end:]
        long_tag_string = found_long_org_tag + remainder

        # calculate short_tag index into long tag.
        found_index_start += (len(long_tag_string) - len(full_tag_string))
        remainder_start_index = found_index_end + (len(long_tag_string) - len(full_tag_string))
        return prefix + long_tag_string, found_index_start + prefix_tag_adj, remainder_start_index + prefix_tag_adj, {}

    # ===============================================
    # Basic tag attributes
    # ===============================================
    def is_extension_allowed_tag(self, original_tag):
        """Checks to see if the tag has the 'extensionAllowed' attribute. It will strip the tag until there are no more
        slashes to check if its ancestors have the attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        tag_takes_extension: bool
            True if the tag has the 'extensionAllowed' attribute. False, if otherwise.
        """
        base_tag = original_tag.base_tag.lower()
        return self.tag_has_attribute(base_tag, HedKey.ExtensionAllowedPropagated)

    def is_takes_value_tag(self, original_tag):
        """Checks to see if the tag has the 'takesValue' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'takesValue' attribute. False, if otherwise.

        """
        return self._value_tag_has_attribute(original_tag, HedKey.TakesValue)

    def is_unit_class_tag(self, original_tag):
        """Checks to see if the tag has the 'unitClass' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'unitClass' attribute. False, if otherwise.

        """
        return self._value_tag_has_attribute(original_tag, HedKey.UnitClass)

    def is_value_class_tag(self, original_tag):
        """Checks to see if the tag has the 'valueClass' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'valueClass' attribute. False, if otherwise.

        """
        return self._value_tag_has_attribute(original_tag, HedKey.ValueClass)

    def is_basic_tag(self, original_tag):
        return self.dictionaries[HedKey.AllTags].get(original_tag.lower())

    def base_tag_has_attribute(self, original_tag, tag_attribute):
        """Checks to see if the tag has a specific attribute.

        Parameters
        ----------
        original_tag: HedTag
            A tag.
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        if self.dictionaries[tag_attribute].get(original_tag.base_tag.lower()):
            return True
        return False

    def tag_has_attribute(self, original_tag, tag_attribute):
        """Checks to see if the tag has a specific attribute.

        Parameters
        ----------
        original_tag: HedTag
            A tag.
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        if self.dictionaries[tag_attribute].get(original_tag.lower()):
            return True
        return False

    # ===============================================
    # More complex tag attributes/combinations of tags etc.
    # ===============================================
    def get_tag_unit_classes(self, original_tag):
        """Gets the unit classes associated with a particular tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        []
            A list containing the unit classes associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit classes associated with it.

        """
        unit_classes = self._value_tag_has_attribute(original_tag, HedKey.UnitClass, return_value=True)
        if unit_classes:
            unit_classes = unit_classes.split(',')
        else:
            unit_classes = []
        return unit_classes

    def get_tag_value_class(self, original_tag):
        return self._value_tag_has_attribute(original_tag, HedKey.ValueClass, return_value=True)

    def get_unit_class_default_unit(self, original_tag):
        """Gets the default unit class unit that is associated with the specified tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        str
            The default unit class unit associated with the specific tag. If the tag doesn't have a unit class then an
            empty string is returned.

        """
        default_unit = ''
        unit_classes = self.get_tag_unit_classes(original_tag)
        if unit_classes:
            first_unit_class = unit_classes[0]
            default_unit = self.dictionaries[HedKey.DefaultUnits][first_unit_class]

        return default_unit

    def get_tag_unit_class_units(self, original_tag):
        """Gets the unit class units associated with a particular tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag to get units for
        Returns
        -------
        []
            A list containing the unit class units associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit class units associated with it.

        """
        units = []
        unit_classes = self.get_tag_unit_classes(original_tag)
        for unit_class in unit_classes:
            unit = self.dictionaries[HedKey.UnitClasses].get(unit_class)
            if unit:
                units += unit
        return units

    def get_stripped_unit_value(self, original_tag):
        """
        Returns the extension portion of the tag if it exists, without the units.

        eg 'Duration/3 ms' will return '3'

        Parameters
        ----------
        original_tag : HedTag
            The hed tag you want the units portion for.

        Returns
        -------
        stripped_unit_value: str
            The extension portion with the units removed.
        """
        tag_unit_classes = self.get_tag_unit_classes(original_tag)
        original_tag_unit_value = original_tag.extension_or_value_portion
        formatted_tag_unit_value = original_tag_unit_value.lower()

        for unit_class_type in tag_unit_classes:
            unit_class_units = self.get_unit_class_units(unit_class_type)
            stripped_value = self._get_tag_units_portion(original_tag_unit_value, formatted_tag_unit_value,
                                                         unit_class_units)
            if stripped_value:
                return stripped_value

        return formatted_tag_unit_value

    def get_all_with_attribute(self, key):
        return self.dictionaries[key]

    def get_unit_class_units(self, unit_class_type):
        unit_class_units = self.dictionaries[HedKey.UnitClasses].get(unit_class_type)
        return unit_class_units

    # ===============================================
    # Semi-private creation finalizing functions
    # ===============================================
    def finalize_dictionaries(self):
        self._is_hed3_schema = self.is_hed3_schema
        self._propagate_extension_allowed()
        self._populate_short_tag_dict()

    def add_hed2_attributes(self, only_add_if_none_present=True):
        """
        This adds the default attributes for old hed2 schema without an attribute section

        Parameters
        ----------
        only_add_if_none_present : bool
            If True(default), will only add attributes if there is currently none.
            If False, will add any missing attributes.
        """
        if HedKey.ValueClassProperty not in self.dictionaries:
            self._add_single_default_property(HedKey.ValueClassProperty)

        # !BFK! for handling old files.  If allowed character is a unit class property, ignore it entirely.
        if HedKey.AllowedCharacter in self.dictionaries[HedKey.UnitClassProperty]:
            del self.dictionaries[HedKey.AllowedCharacter]
            del self.dictionaries[HedKey.UnitClassProperty][HedKey.AllowedCharacter]
            del self.dictionaries[HedKey.Attributes][HedKey.AllowedCharacter]
            self._add_description_to_dict(HedKey.AllowedCharacter, None, key_class=HedKey.Attributes)

        if only_add_if_none_present and self.dictionaries[HedKey.Attributes]:
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
        if only_add_if_none_present and self.dictionaries[HedKey.Properties]:
            return

        from hed.schema import hed_2g_attributes
        for prop_name in hed_2g_attributes.properties:
            self._add_single_default_property(prop_name)

    def update_old_hed_schema(self):
        if HedKey.UnitPrefix not in self.dictionaries:
            self._add_single_default_attribute(HedKey.UnitPrefix)

        if self.dictionaries[HedKey.UnitPrefix]:
            return

        self.dictionaries[HedKey.UnitPrefix]['$'] = "$"

    # ===============================================
    # Getters used to write out schemas primarily.
    # ===============================================
    def get_desc_dict(self):
        """
            Helper to return HedKey.Descriptions dictionary

        Returns
        -------
        descriptions_dict: {str:str}
        """
        return self.dictionaries[HedKey.Descriptions]

    def get_tag_description(self, tag_name, key_class=HedKey.AllTags):
        """
            If a description exists for the given name, returns it

        Parameters
        ----------
        tag_name : str
            A hed tag name(or unit/unit modifier etc) with proper capitalization.
        key_class: str, default HedKey.AllTags
            A HedKey indicating what type of description you are asking for.  (All tags, Units, Unit modifier)

        Returns
        -------
        description: str or None
        """
        if key_class == HedKey.AllTags:
            tag_name = tag_name.lower()
        return self.dictionaries[HedKey.Descriptions].get(f"{key_class}_{tag_name}", None)

    def get_all_schema_tags(self, return_short_form=False):
        """
        Gets a list of all hed terms from the schema, compatible with Hed2 or Hed3

        Returns
        -------
        term_list: [str]
            A list of all terms(short tags) from the schema.
        """
        final_list = []
        for lower_tag, org_tag in self.dictionaries[HedKey.AllTags].items():
            if return_short_form:
                final_list.append(org_tag.split('/')[-1])
            else:
                final_list.append(org_tag)
        return final_list

    def get_tag_attribute_names(self):
        return [key_name for key_name in self.dictionaries[HedKey.Attributes]
                if key_name not in self.dictionaries[HedKey.UnitClassProperty]
                and key_name not in self.dictionaries[HedKey.UnitProperty]
                and key_name not in self.dictionaries[HedKey.UnitModifierProperty]
                and key_name not in self.dictionaries[HedKey.ValueClassProperty]]

    def get_all_tag_attributes(self, tag_name, key_class=HedKey.AllTags, keys=None):
        """
            Gathers all attributes for a given tag name.  If keys is none, gets all normal hed tag attributes.

        Parameters
        ----------
        tag_name : str
            The name of the tag to check
        key_class: str
            The type of attributes we are asking for.  eg Tag, Units, Unit modifiers, or attributes.
        keys : [str]
            If this is filled in, use these exact keys and ignore the key_class parameter.

        Returns
        -------
        tag_values: {str: str}
            {key_name : attribute_value}
        """
        if keys is None:
            keys = self._get_attributes_for_class(key_class)
            if keys is None:
                raise KeyError("Invalid key_class property type")
        attributes = {}
        for key in keys:
            check_name = tag_name
            if key in self.get_tag_attribute_names():
                check_name = tag_name.lower()
            source_dicts = self.dictionaries
            if key_class == HedKey.AllTags:
                source_dicts = self.dictionaries
            if key not in source_dicts:
                # Potentially raise or return an error here.
                continue
            if check_name in source_dicts[key]:
                value = source_dicts[key][check_name]
                # A tag attribute is True if the tag name and dictionary value are the same, ignoring capitalization
                if value is True or value and check_name.lower() == value.lower():
                    attributes[key] = True
                else:
                    if value is None:
                        value = False
                    attributes[key] = value

        return attributes

    # ===============================================
    # Private utility functions
    # ===============================================
    @staticmethod
    def _create_empty_dictionaries():
        """
        Initializes a dictionary with the minimum so the tools won't crash
        """
        dictionaries = {}

        # Add main sections
        dictionaries[HedKey.AllTags] = {}
        dictionaries[HedKey.UnitClasses] = {}
        dictionaries[HedKey.Units] = {}
        dictionaries[HedKey.UnitModifiers] = {}
        dictionaries[HedKey.ValueClasses] = {}
        dictionaries[HedKey.Attributes] = {}
        dictionaries[HedKey.Properties] = {}

        dictionaries[HedKey.UnknownAttributes] = {}
        dictionaries[HedKey.Descriptions] = {}

        return dictionaries

    def _propagate_extension_allowed(self):
        """
        Populates the ExtensionAllowedPropagated based on the ExtensionAllowed one.

        Returns
        -------

        """
        allowed_extensions = self.dictionaries[HedKey.ExtensionAllowed]
        self.dictionaries[HedKey.ExtensionAllowedPropagated] = {}
        for long_tag in self.dictionaries[HedKey.AllTags].values():
            lower_tag = long_tag.lower()
            if lower_tag in allowed_extensions:
                self.dictionaries[HedKey.ExtensionAllowedPropagated][lower_tag] = long_tag
                continue

            if self.tag_has_attribute(lower_tag, HedKey.TakesValue):
                continue

            current_index = -1
            found_slash = lower_tag.find("/", current_index + 1)
            while found_slash != -1:
                current_index = found_slash
                check_tag = lower_tag[:current_index]
                if check_tag in allowed_extensions:
                    self.dictionaries[HedKey.ExtensionAllowedPropagated][lower_tag] = long_tag
                    break
                found_slash = lower_tag.find("/", current_index + 1)

    @property
    def short_tag_mapping(self):
        """
        This returns the short->long tag dictionary.


        Returns
        -------
        short_tag_dict: {str:str} or {str:str or list}
            Returns the short tag mapping dictionary.  If this is hed2 and has duplicates, the values of the dict
            may contain lists in addition to strings.
        """
        return self.dictionaries[HedKey.ShortTags]

    def _populate_short_tag_dict(self):
        """
        Create a mapping from the short version of a tag to the long version and
        determines if this is a hed3 compatible schema.

        Returns
        -------
        """
        self.no_duplicate_tags = True
        base_tag_dict = self.dictionaries[HedKey.AllTags]
        new_short_tag_dict = {}
        for tag, unformatted_tag in base_tag_dict.items():
            if self._library_prefix and unformatted_tag.startswith(self._library_prefix):
                unformatted_tag = unformatted_tag[len(self._library_prefix):]
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
                self.no_duplicate_tags = False
                if not isinstance(new_short_tag_dict[short_clean_tag], list):
                    new_short_tag_dict[short_clean_tag] = [new_short_tag_dict[short_clean_tag]]
                new_short_tag_dict[short_clean_tag].append(new_tag_entry)
        self.dictionaries[HedKey.ShortTags] = new_short_tag_dict

    def _value_tag_has_attribute(self, original_tag, key=HedKey.ExtensionAllowedPropagated,
                                 return_value=False):
        """
            Will return if original tag has the specified attribute, or False if original tag is not a takes value tag.

        Parameters
        ----------
        original_tag : HedTag

        key : str
            A HedKey value to check for
        return_value : bool
            If true, returns the value of the attribute, rather than True/False

        Returns
        -------
        attribute_name_or_value: bool or str
            Returns the name or value of the specified attribute
        """
        if not original_tag.extension_or_value_portion:
            return False

        if key not in self.dictionaries:
            return False
        value_class_tag = original_tag.base_tag.lower() + "/#"

        value = self.dictionaries[key].get(value_class_tag, False)
        if return_value:
            return value
        return bool(value)

    def _get_tag_units_portion(self, original_tag_unit_value, formatted_tag_unit_value,
                               tag_unit_class_units):
        """Checks to see if the specified string has a valid unit, and removes it if so.

        Parameters
        ----------
        original_tag_unit_value: str
            The unformatted value of the tag
        formatted_tag_unit_value: str
            The formatted value of the tag
        tag_unit_class_units: [str]
            A list of valid units for this tag
        Returns
        -------
        stripped_value: str
            A tag_unit_values with the valid unit removed, if one was present.
            Otherwise, returns original_tag_unit_value

        """
        tag_unit_class_units = sorted(tag_unit_class_units, key=len, reverse=True)
        for unit in tag_unit_class_units:
            derivative_units = self._get_valid_unit_plural(unit)
            for derivative_unit in derivative_units:
                if self.has_unit_modifiers and \
                        self.dictionaries[HedKey.UnitSymbol].get(unit):
                    found_unit, stripped_value = self._strip_off_units_if_valid(original_tag_unit_value,
                                                                                derivative_unit,
                                                                                True)
                else:
                    found_unit, stripped_value = self._strip_off_units_if_valid(formatted_tag_unit_value,
                                                                                derivative_unit,
                                                                                False)

                if found_unit:
                    return stripped_value

        return None

    def _strip_off_units_if_valid(self, unit_value, unit, is_unit_symbol):
        """Validates and strips units from a value.

        Parameters
        ----------
        unit_value: str
            The value to validate.
        unit: str
            The unit to strip.
        is_unit_symbol: bool
            Whether the unit is a symbol.
        Returns
        -------
        tuple
            The found unit and the stripped value.
        """
        found_unit = False
        stripped_value = ''

        should_be_prefix = self.dictionaries[HedKey.UnitPrefix].get(unit, False)
        if should_be_prefix and str(unit_value).startswith(unit):
            found_unit = True
            stripped_value = str(unit_value)[len(unit):].strip()
        elif not should_be_prefix and str(unit_value).endswith(unit):
            found_unit = True
            stripped_value = str(unit_value)[0:-len(unit)].strip()

        if found_unit and self.has_unit_modifiers:
            if is_unit_symbol:
                modifier_key = HedKey.SIUnitSymbolModifier
            else:
                modifier_key = HedKey.SIUnitModifier

            for unit_modifier in self.dictionaries[modifier_key]:
                if stripped_value.startswith(unit_modifier):
                    stripped_value = stripped_value[len(unit_modifier):].strip()
                elif stripped_value.endswith(unit_modifier):
                    stripped_value = stripped_value[0:-len(unit_modifier)].strip()
        return found_unit, stripped_value

    def _get_valid_unit_plural(self, unit):
        """
        Parameters
        ----------
        unit: str
            unit to generate plural forms
        Returns
        -------
        [str]
            list of plural units
        """
        derivative_units = [unit]
        if self.has_unit_modifiers and \
                self.dictionaries[HedKey.UnitSymbol].get(unit) is None:
            derivative_units.append(pluralize.plural(unit))
        return derivative_units

    def _get_attributes_for_class(self, key_class):
        """
        Returns the valid attributes for this section

        Parameters
        ----------
        key_class : str
            The HedKey for this section.

        Returns
        -------
        attributes: [str] or {str:}
            A list of all the attributes for this section.  May return a dict where the keys are the attribute names.
        """
        if key_class == HedKey.AllTags:
            return self.get_tag_attribute_names()
        attrib_classes = {
            HedKey.Properties: None,
            HedKey.Attributes: HedKey.Properties,
            HedKey.UnitClasses: HedKey.UnitClassProperty,
            HedKey.Units: HedKey.UnitProperty,
            HedKey.UnitModifiers: HedKey.UnitModifierProperty,
            HedKey.ValueClasses: HedKey.ValueClassProperty
        }
        attrib_class = attrib_classes.get(key_class, None)
        if attrib_class is None:
            return []

        return self.dictionaries[attrib_class]

    # ===============================================
    # Semi private functions used to create a schema in memory(usually from a source file)
    # ===============================================
    def _add_tag_to_dict(self, long_tag_name, key_class=HedKey.AllTags, value=None):
        if value is None:
            value = long_tag_name
        if key_class == HedKey.AllTags:
            self.dictionaries[key_class][long_tag_name.lower()] = value
        else:
            self.dictionaries[key_class][long_tag_name] = value

    def _add_attribute_to_dict(self, tag_name, attribute_name, new_value, key_class):
        if not new_value:
            return

        if attribute_name in self.dictionaries[HedKey.BoolProperty]:
            # This case will only happen if someone has a slightly malformed schema where they use
            # "extensionAllowed=true" instead of just "extensionAllowed"
            # Todo: We should probably update this to internally store true/false for simplicity.
            if new_value is True or new_value == "true":
                new_value = tag_name
            # if new_value == "true":
            #     new_value = True
            elif new_value is False or new_value == "false":
                return

        # Tags are case insensitive.
        if key_class == HedKey.AllTags:
            tag_name = tag_name.lower()

        valid_attribute_classes = self._get_attributes_for_class(key_class)
        # This might have duplicates as it's unknown and could be in other sections.
        if attribute_name in self.dictionaries[HedKey.UnknownAttributes] \
                or attribute_name not in valid_attribute_classes:
            tag_name = key_class + "_" + tag_name
            attribute_name = "invalidAttribute_" + attribute_name
            if key_class == HedKey.AllTags:
                if attribute_name not in self.dictionaries:
                    self.dictionaries[attribute_name] = {}
                    self.dictionaries[HedKey.UnknownAttributes][attribute_name] = "true"
            else:
                if attribute_name not in self.dictionaries:
                    self.dictionaries[attribute_name] = {}
                    self.dictionaries[HedKey.UnknownAttributes][attribute_name] = "true"

        self.dictionaries[attribute_name][tag_name] = new_value

    def _add_unit_class_unit(self, unit_class, unit_class_unit):
        if unit_class not in self.dictionaries[HedKey.UnitClasses]:
            self.dictionaries[HedKey.UnitClasses][unit_class] = []
        if unit_class_unit is not None:
            self.dictionaries[HedKey.UnitClasses][unit_class].append(unit_class_unit)
        self.dictionaries[HedKey.Units][unit_class_unit] = unit_class_unit

    def _add_description_to_dict(self, tag_name, desc, key_class=HedKey.AllTags):
        if key_class == HedKey.AllTags:
            tag_name = tag_name.lower()
        desc_key = f"{key_class}_{tag_name}"
        if desc:
            self.dictionaries[HedKey.Descriptions][desc_key] = desc
        else:
            try:
                del self.dictionaries[HedKey.Descriptions][desc_key]
            except KeyError:
                pass

    def _add_attribute_name_to_dict(self, attribute_name):
        if attribute_name in self.dictionaries[HedKey.Attributes]:
            raise ValueError(f"Duplicate attribute {attribute_name} found in attributes section.")
        if attribute_name in self.dictionaries:
            raise ValueError(f"Attribute '{attribute_name}' is already reserved in dictionary and cannot be re-used.")
        self.dictionaries[HedKey.Attributes][attribute_name] = attribute_name
        self.dictionaries[attribute_name] = {}

    def _add_property_name_to_dict(self, prop_name, prop_desc):
        if prop_name in self.dictionaries[HedKey.Properties]:
            raise ValueError(f"Duplicate property {prop_name} found in properties section.")
        if prop_name in self.dictionaries:
            raise ValueError(f"Property '{prop_name}' is already in dictionary as reserved and cannot be re-used.")
        self.dictionaries[HedKey.Properties][prop_name] = prop_name
        self.dictionaries[prop_name] = {}
        self._add_description_to_dict(prop_name, prop_desc, HedKey.Properties)

    def _add_single_default_attribute(self, attribute_name):
        from hed.schema import hed_2g_attributes
        attribute_props, attribute_desc = hed_2g_attributes.attributes[attribute_name]
        if attribute_name not in self.dictionaries[HedKey.Attributes]:
            self._add_attribute_name_to_dict(attribute_name)
        self._add_description_to_dict(attribute_name, attribute_desc, HedKey.Attributes)

        for attribute_property_name in attribute_props:
            self._add_attribute_to_dict(attribute_name, attribute_property_name, True, HedKey.Attributes)

    def _add_single_default_property(self, prop_name):
        from hed.schema import hed_2g_attributes
        prop_desc = hed_2g_attributes.properties[prop_name]
        self._add_property_name_to_dict(prop_name, prop_desc)
