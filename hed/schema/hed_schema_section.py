from hed.schema.hed_schema_entry import HedSchemaEntry, UnitClassEntry, UnitEntry, HedTagEntry
from hed.schema.hed_schema_constants import HedSectionKey


entries_by_section = {
    HedSectionKey.Properties: HedSchemaEntry,
    HedSectionKey.Attributes: HedSchemaEntry,
    HedSectionKey.UnitModifiers: HedSchemaEntry,
    HedSectionKey.Units: UnitEntry,
    HedSectionKey.UnitClasses: UnitClassEntry,
    HedSectionKey.ValueClasses: HedSchemaEntry,
    HedSectionKey.AllTags: HedTagEntry,
}


class HedSchemaSection:
    """Container with entries in one section of the schema. """

    def __init__(self, section_key, case_sensitive=True):
        """ Construct schema section.

        Parameters:
            section_key (str):  Name of the schema section.
            case_sensitive (bool): If True, names are case sensitive.

        """
        # {lower_case_name: HedSchemaEntry}
        self.all_names = {}
        self._section_key = section_key
        self.case_sensitive = case_sensitive

        # Points to the entries in attributes
        self.valid_attributes = {}
        self._attribute_cache = {}

        self._section_entry = entries_by_section.get(section_key)
        self.duplicate_names = {}
        self.all_entries = []

    def _add_to_dict(self, name):
        """ Add a name to the dictionary for this section. """
        name_key = name
        if not self.case_sensitive:
            name_key = name.lower()

        new_entry = self._section_entry(name, self)
        if name_key in self.all_names:
            if name_key not in self.duplicate_names:
                self.duplicate_names[name_key] = [self.all_names[name_key]]
            self.duplicate_names[name_key].append(new_entry)
        else:
            self.all_names[name_key] = new_entry

        self.all_entries.append(new_entry)
        return new_entry

    def get_entries_with_attribute(self, attribute_name, return_name_only=False, schema_prefix=""):
        """ Return entries or names with given attribute.

        Parameters:
            attribute_name (str): The name of the attribute(generally a HedKey entry).
            return_name_only (bool): If true, return the name as a string rather than the tag entry.
            schema_prefix (str): Prepends given prefix to each name if returning names.

        Returns:
            list: List of HedSchemaEntry or strings representing the names.

        """
        if attribute_name not in self._attribute_cache:
            new_val = [tag_entry for tag_entry in self.values() if tag_entry.has_attribute(attribute_name)]
            self._attribute_cache[attribute_name] = new_val

        cache_val = self._attribute_cache[attribute_name]
        if return_name_only:
            return [f"{schema_prefix}{tag_entry.name}" for tag_entry in cache_val]
        return cache_val

    # ===============================================
    # Simple wrapper functions to make this class primarily function as a dict
    # ===============================================
    def __iter__(self):
        return iter(self.all_names)

    def __len__(self):
        return len(self.all_names)

    def items(self):
        """ Return the items. """
        return self.all_names.items()

    def values(self):
        """ All names of the sections. """
        return self.all_names.values()

    def keys(self):
        """ The names of the keys. """
        return self.all_names.keys()

    def __getitem__(self, key):
        if not self.case_sensitive:
            key = key.lower()
        return self.all_names[key]

    def get(self, key):
        """ Return the name associated with key.

        Parameters:
            key (str): The name of the key.

        """
        if not self.case_sensitive:
            key = key.lower()
        return self.all_names.get(key)

    def __eq__(self, other):
        if self.all_names != other.all_names:
            return False
        if self._section_key != other._section_key:
            return False
        if self.case_sensitive != other.case_sensitive:
            return False
        if self.duplicate_names != other.duplicate_names:
            return False
        return True

    def __bool__(self):
        return bool(self.all_names)


class HedSchemaTagSection(HedSchemaSection):
    """ A section of the schema. """

    def __init__(self, *args, case_sensitive=False, **kwargs):
        super().__init__(*args, **kwargs, case_sensitive=case_sensitive)
        # This dict contains all forms of all tags.  The .all_names variable has ONLY the long forms.
        self.long_form_tags = {}

    def _add_to_dict(self, name):
        name_key = name
        tag_forms = []
        while name_key:
            tag_forms.append(name_key)
            slash_index = name_key.find("/")
            if slash_index == -1:
                name_key = None
            else:
                name_key = name_key[slash_index + 1:]

        # We can't add value tags by themselves
        if tag_forms[-1] == "#":
            tag_forms = tag_forms[:-1]
        new_entry = super()._add_to_dict(name)

        # remove the /# if present, but only from the entry, not from the lookups
        # This lets us easily use source_tag + remainder instead of having to strip off the /# later.
        short_name = tag_forms[-1]
        long_tag_name = name
        if long_tag_name.endswith("/#"):
            long_tag_name = long_tag_name[:-2]
            short_name = short_name[:-2]
        new_entry.long_tag_name = long_tag_name
        new_entry.short_tag_name = short_name

        for tag_key in tag_forms:
            self.long_form_tags[tag_key.lower()] = new_entry

        return new_entry

    def get(self, key):
        if not self.case_sensitive:
            key = key.lower()
        return self.long_form_tags.get(key)

    def __getitem__(self, key):
        if not self.case_sensitive:
            key = key.lower()
        return self.long_form_tags[key]

    def __contains__(self, key):
        if not self.case_sensitive:
            key = key.lower()
        return key in self.long_form_tags
