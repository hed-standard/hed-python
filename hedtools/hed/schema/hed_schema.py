"""
This module contains the HedSchema class which encapsulates all HED tags, tag attributes, unit classes, and
unit class attributes in a dictionary.

The dictionary is a dictionary of dictionaries. The dictionary names are the list in HedKey from hed_schema_constants.
"""
from hed.schema.hed_schema_constants import HedKey
from hed.schema import hed_schema_constants as constants
from hed.util import file_util
from hed.schema.schema2xml import HedSchema2XML
from hed.schema.schema2wiki import HedSchema2Wiki
from hed.schema import schema_compliance


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
        self.schema_attributes = {}
        self._filename = None
        self.dictionaries = self.create_empty_dictionaries()
        self.prologue = ""
        self.epilogue = ""

    def set_attributes(self, schema_attributes):
        self.schema_attributes = schema_attributes

    def set_dictionaries(self, dictionaries):
        self.dictionaries = dictionaries
        self._propagate_extension_allowed()
        self._populate_short_tag_dict()
        self._add_hed3_compatible_tags()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        if self._filename is None:
            self._filename = value

    def save_as_xml(self):
        schema2xml = HedSchema2XML()
        xml_tree = schema2xml.process_schema(self)
        local_xml_file = file_util.write_xml_tree_2_xml_file(xml_tree, ".xml")
        return local_xml_file

    def save_as_mediawiki(self):
        schema2wiki = HedSchema2Wiki()
        output_strings = schema2wiki.process_schema(self)
        local_wiki_file = file_util.write_strings_to_file(output_strings, ".mediawiki")
        return local_wiki_file

    def __eq__(self, other):
        if self.schema_attributes != other.schema_attributes:
            return False
        if self.schema_attributes != other.schema_attributes:
            return False
        if self.no_duplicate_tags != other.no_duplicate_tags:
            return False
        if self.prologue != other.prologue:
            return False
        if self.epilogue != other.epilogue:
            return False
        return True

    @staticmethod
    def create_empty_dictionaries():
        """
        Initializes a dictionary with the minimum so the tools won't crash
        """
        dictionaries = {}
        for tag in constants.ALL_TAG_DICTIONARY_KEYS:
            dictionaries[tag] = {}
        dictionaries[HedKey.Descriptions] = {}
        return dictionaries

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

    def get_tag_description(self, tag_name, tag_class=HedKey.AllTags):
        """
            If a description exists for the given name, returns it

        Parameters
        ----------
        tag_name : str
            A hed tag name(or unit/unit modifier etc) with proper capitalization.
        tag_class: str, default HedKey.AllTags
            A HedKey indicating what type of description you are asking for.  (All tags, Units, Unit modifier)

        Returns
        -------
        description: str or None
        """
        if tag_class == HedKey.AllTags:
            tag_class = ""
        return self.dictionaries[HedKey.Descriptions].get(tag_class + tag_name, None)

    def get_all_tags(self, return_short_form=False):
        """
        Gets a single copy of all hed terms from the schema, for hed2 or hed3 compatible.

        Returns
        -------
        term_list: [str]
            A list of all terms(short tags) from the schema.
        """
        final_list = []
        if not self.has_duplicate_tags():
            for lower_tag, org_tag in self.short_tag_mapping.items():
                if return_short_form:
                    final_list.append(org_tag.split('/')[-1])
                else:
                    final_list.append(org_tag)
        # Fallback for hed2 style schema validation
        else:
            for lower_tag, org_tag in self.dictionaries[HedKey.AllTags].items():
                if return_short_form:
                    final_list.append(org_tag.split('/')[-1])
                else:
                    final_list.append(org_tag)
        return final_list

    def get_all_tag_attributes(self, tag_name, keys=None):
        """
            Gathers all attributes for a given tag name.  If keys is none, gets all normal hed tag attributes.

        Parameters
        ----------
        tag_name : str
            The name of the tag to check
        keys : [str]
            A list of HedKey tags.

        Returns
        -------
        tag_values: {str: str}
            {key_name : attribute_value}
        """
        if keys is None:
            keys = constants.TAG_ATTRIBUTE_KEYS
        attributes = {}
        for key in keys:
            check_name = tag_name
            if key in constants.TAG_ATTRIBUTE_KEYS:
                check_name = tag_name.lower()
            if check_name in self.dictionaries[key]:
                value = self.dictionaries[key][check_name]
                # A tag attribute is considered True if the tag name and dictionary value are the same, ignoring capitalization
                if value and check_name.lower() == value.lower():
                    attributes[key] = True
                else:
                    if value is None:
                        value = False
                    attributes[key] = value

        return attributes

    def get_all_forms_of_tag(self, short_tag_to_check):
        """
        Given a short tag, return all the longer versions of it.  Always returns empty list if not a valid HED3G schema.

        eg: "definition" will return
                ["definition", "informational/definition", "attribute/informational/definition"]

        Parameters
        ----------
        short_tag_to_check : str
            The short version of a hed tag we are interested in.

        Returns
        -------
        tag_versions: [str]
            A list of all short, intermediate, and long versions of the passed in short tag.
            Returns empty list if no versions found.
        """
        try:
            tag_entry = self.short_tag_mapping[short_tag_to_check.lower()]
        except (KeyError, TypeError):
            return []

        split_tags = tag_entry.lower().split("/")
        final_tag = ""
        all_forms = []
        for tag in reversed(split_tags):
            final_tag = tag + "/" + final_tag
            all_forms.append(final_tag)

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
        return HedKey.Units in self.dictionaries

    @property
    def has_unit_modifiers(self):
        return HedKey.SIUnitModifier in self.dictionaries

    @property
    def short_tag_mapping(self):
        """
        This returns the short->long tag dictionary if we have a hed3 compatible schema.

        Returns
        -------
        short_tag_dict: {}
            Returns the short tag mapping dictionary, or None if this is not a hed3 compatible schema.
        """
        if self.no_duplicate_tags:
            return self.dictionaries[HedKey.ShortTags]
        return None

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

    def _propagate_extension_allowed(self):
        """
        Populates the ExtensionAllowedPropagated based on the ExtensionAllowed one.

        Returns
        -------

        """
        allowed_extensions = self.dictionaries[HedKey.ExtensionAllowed]
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

    def _add_hed3_compatible_tags(self):
        """
        Updates the normal tag dictionaries with all the intermediate forms if this is a hed3 compatible schema."

        Returns
        -------
        """
        if self.no_duplicate_tags:
            for dict_key in constants.ALL_TAG_DICTIONARY_KEYS:
                tag_dictionary = self.dictionaries[dict_key]
                new_entries = {}
                for full_tag, value in tag_dictionary.items():
                    split_tags = full_tag.split("/")
                    final_tag = ""
                    for tag in reversed(split_tags):
                        final_tag = tag + "/" + final_tag
                        # We need to include the #, but make sure we don't create a tag with just # alone.
                        if tag == "#":
                            continue
                        # Remove extra trailing slash.
                        new_entries[final_tag[:-1]] = value
                tag_dictionary.update(new_entries)
