"""
This module contains the HedSchema class which encapsulates all HED tags, tag attributes, unit classes, and
unit class attributes in a dictionary.

The dictionary is a dictionary of dictionaries. The dictionary names are the list in HedKey from hed_schema_constants.
"""
from hed.schema.hed_schema_constants import HedKey, ATTRIBUTE_PROPERTIES
from hed.util import file_util, error_reporter
from hed.schema.schema2xml import HedSchema2XML
from hed.schema.schema2wiki import HedSchema2Wiki
from hed.schema import schema_compliance
from hed.util.error_types import ValidationErrors


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

    def get_as_mediawiki_string(self):
        """
        Return the schema to a mediawiki string

        Returns
        -------
        filename: str
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
        filename: str
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

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        if self._filename is None:
            self._filename = value

    def check_compliance(self, also_check_for_warnings=True, display_filename=None,
                         error_handler=None):
        """
            Checks for hed3 compliance of this schema.

        Parameters
        ----------
        also_check_for_warnings : bool, default True
            If True, also checks for formatting issues like invalid characters, capitalization, etc.
        display_filename: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        issue_list : [{}]
            A list of all warnings and errors found in the file.
        """
        return schema_compliance.check_compliance(self, also_check_for_warnings, display_filename, error_handler)

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

    def get_all_tags(self, return_short_form=False):
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
                and key_name not in self.dictionaries[HedKey.UnitModifierProperty]]

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
            if key not in self.dictionaries:
                # Potentially raise or return an error here.
                continue
            if check_name in self.dictionaries[key]:
                value = self.dictionaries[key][check_name]
                # A tag attribute is True if the tag name and dictionary value are the same, ignoring capitalization
                if value is True or value and check_name.lower() == value.lower():
                    attributes[key] = True
                else:
                    if value is None:
                        value = False
                    attributes[key] = value

        return attributes

    def get_all_forms_of_tag(self, short_tag_to_check):
        """
        Given a short tag, return all the longer versions of it.

        This is primarily used to match definition tags without converting them to long first.

        Note: In hed2 schema the tags may be unrelated if multiple copies of the term exist, and only the long
              forms will be returned.

        eg in hed3: "definition" will return
                ["definition", "informational/definition", "attribute/informational/definition"]

        Parameters
        ----------
        short_tag_to_check : str
            The short version of a hed tag we are interested in.

        Returns
        -------
        tag_versions: [str]
            A list of all short, intermediate, and long versions of the passed in short tag.
        """
        try:
            tag_entry = self.short_tag_mapping[short_tag_to_check.lower()]
        except (KeyError, TypeError):
            return []

        if self.is_hed3_compatible:
            split_tags = tag_entry.lower().split("/")
            final_tag = ""
            all_forms = []
            for tag in reversed(split_tags):
                final_tag = tag + "/" + final_tag
                all_forms.append(final_tag)
        else:
            if isinstance(tag_entry, list):
                all_forms = [tag.lower() for tag in tag_entry]
            else:
                all_forms = [tag_entry.lower()]

        return all_forms

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
    def has_unit_modifiers(self):
        return HedKey.SIUnitModifier in self.dictionaries

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

    def tag_has_attribute(self, tag, tag_attribute):
        """Checks to see if the tag has a specific attribute.

        Parameters
        ----------
        tag: str
            A tag.
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        if self.dictionaries[tag_attribute].get(tag.lower()):
            return True
        return False

    def finalize_dictionaries(self):
        self._propagate_extension_allowed()
        self._populate_short_tag_dict()

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

    def __eq__(self, other):
        if self.dictionaries != other.dictionaries:
            # Comment the following back in for easy debugging of schema that should be equal.
            # dict_keys = set(list(self.dictionaries.keys()) + list(other.dictionaries.keys()))
            # for dict_key in dict_keys:
            #     if dict_key not in self.dictionaries:
            #         print(f"{dict_key} dict not in self")
            #         continue
            #     if dict_key not in other.dictionaries:
            #         print(f"{dict_key} dict not in other")
            #         continue
            #     dict1 = self.dictionaries[dict_key]
            #     dict2 = other.dictionaries[dict_key]
            #     if dict1 != dict2:
            #         print(f"DICT {dict_key} NOT EQUAL")
            #         key_union = set(list(dict1.keys()) + list(dict2.keys()))
            #         for key in key_union:
            #             if key not in dict1:
            #                 print(f"{key} not in dict1")
            #                 continue
            #             if key not in dict2:
            #                 print(f"{key} not in dict2")
            #                 continue
            #             if dict1[key] != dict2[key]:
            #                 print(f"{key} doesn't match.  '{dict1[key]}' vs '{dict2[key]}'")
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
        dictionaries[HedKey.Attributes] = {}

        dictionaries[HedKey.UnknownAttributes] = {}

        dictionaries[HedKey.Descriptions] = {}

        for attribute_property_name in ATTRIBUTE_PROPERTIES:
            dictionaries[attribute_property_name] = {}

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

    def _convert_to_canonical_tag(self, hed_tag, error_handler=None):
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
        hed_tag: str or HedTag
            A single hed tag(long or short)
        Returns
        -------
        long_tag: str
            The converted long tag
        short_tag_index: int
            The position the short tag starts at in long_tag
        errors: list
            a list of errors while converting
        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()

        clean_tag = hed_tag.lower()
        split_tags = clean_tag.split("/")

        index_end = 0
        found_unknown_extension = False
        found_index_end = 0
        found_index_start = 0
        found_long_org_tag = None
        # Iterate over tags left to right keeping track of current index
        for tag in split_tags:
            tag_len = len(tag)
            # Skip slashes
            if index_end != 0:
                index_end += 1
            index_start = index_end
            index_end += tag_len

            # If we already found an unknown tag, it's implicitly an extension.  No known tags can follow it.
            if not found_unknown_extension:
                if tag not in self.short_tag_mapping:
                    found_unknown_extension = True
                    if not found_long_org_tag:
                        error = error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                           hed_tag, index=index_start, index_end=index_end)
                        return str(hed_tag), None, error
                    continue

                long_org_tags = self.short_tag_mapping[tag]
                long_org_tag = None
                if isinstance(long_org_tags, str):
                    tag_string = long_org_tags.lower()

                    main_hed_portion = clean_tag[:index_end]

                    # Verify the tag has the correct path above it.
                    if tag_string.endswith(main_hed_portion):
                        long_org_tag = long_org_tags
                else:
                    for org_tag_string in long_org_tags:
                        tag_string = org_tag_string.lower()

                        main_hed_portion = clean_tag[:index_end]

                        if tag_string.endswith(main_hed_portion):
                            long_org_tag = org_tag_string
                            break
                if not long_org_tag:
                    error = error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, tag=hed_tag,
                                                       index=index_start, index_end=index_end,
                                                       expected_parent_tag=long_org_tags)
                    return str(hed_tag), None, error

                # In hed2 compatible, make sure this is a long form of a tag or throw an invalid base tag error.
                if not self.is_hed3_compatible:
                    if not clean_tag.startswith(long_org_tag.lower()):
                        error = error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                           hed_tag, index=index_start, index_end=index_end)
                        return str(hed_tag), None, error

                found_index_start = index_start
                found_index_end = index_end
                found_long_org_tag = long_org_tag
            else:
                # These means we found a known tag in the remainder/extension section, which is an error
                if tag in self.short_tag_mapping:
                    error = error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, hed_tag,
                                                       index=index_start, index_end=index_end,
                                                       expected_parent_tag=self.short_tag_mapping[tag])
                    return str(hed_tag), None, error

        # Finally don't actually adjust the tag if it's hed2 style.
        if not self.is_hed3_compatible:
            return str(hed_tag), None, []

        remainder = str(hed_tag)[found_index_end:]

        long_tag_string = found_long_org_tag + remainder

        # calculate short_tag index into long tag.
        found_index_start += (len(long_tag_string) - len(str(hed_tag)))
        return long_tag_string, found_index_start, []

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
        attribute_dict = {
            HedKey.Attributes: ATTRIBUTE_PROPERTIES,
            HedKey.AllTags: self.get_tag_attribute_names(),
            HedKey.UnitClasses: self.dictionaries[HedKey.UnitClassProperty],
            HedKey.Units: self.dictionaries[HedKey.UnitProperty],
            HedKey.UnitModifiers: self.dictionaries[HedKey.UnitModifierProperty]
        }

        return attribute_dict[key_class]

    # Semi private functions for adding new tags and classes(used by loaders)
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
            if new_value is True or new_value == "true":
                new_value = tag_name
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
        if desc:
            if key_class == HedKey.AllTags:
                tag_name = tag_name.lower()
            self.dictionaries[HedKey.Descriptions][f"{key_class}_{tag_name}"] = desc

    def _add_attribute_name_to_dict(self, attribute_name):
        if attribute_name in self.dictionaries[HedKey.Attributes]:
            raise ValueError(f"Duplicate attribute {attribute_name} found in attributes section.")
        self.dictionaries[HedKey.Attributes][attribute_name] = attribute_name
        self.dictionaries[attribute_name] = {}

    def add_hed2_attributes(self, only_add_if_none_present=True):
        """
        This adds the default attributes for old hed2 schema without an attribute section

        Parameters
        ----------
        only_add_if_none_present : bool
            If True(default), will only add attributes if there is currently none.
            If False, will add any missing attributes.
        """
        if only_add_if_none_present and self.dictionaries[HedKey.Attributes]:
            return

        from hed.schema import hed_2g_attributes
        for attribute_name, (attribute_props, attribute_desc) in hed_2g_attributes.attributes.items():
            if attribute_name not in self.dictionaries[HedKey.Attributes]:
                self._add_attribute_name_to_dict(attribute_name)
                self._add_description_to_dict(attribute_name, attribute_desc, HedKey.Attributes)

                for attribute_property_name in attribute_props:
                    self._add_attribute_to_dict(attribute_name, attribute_property_name, True, HedKey.Attributes)
