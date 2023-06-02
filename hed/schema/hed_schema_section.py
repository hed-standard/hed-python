from hed.schema.hed_schema_entry import HedSchemaEntry, UnitClassEntry, UnitEntry, HedTagEntry
from hed.schema.hed_schema_constants import HedSectionKey, HedKey


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
            section_key (HedSectionKey):  Name of the schema section.
            case_sensitive (bool): If True, names are case-sensitive.

        """
        # {lower_case_name: HedSchemaEntry}
        self.all_names = {}
        self._section_key = section_key
        self.case_sensitive = case_sensitive

        # Points to the entries in attributes
        self.valid_attributes = {}
        self._attribute_cache = {}

        self._section_entry = entries_by_section.get(section_key)
        self._duplicate_names = {}

        self.all_entries = []

    @property
    def section_key(self):
        return self._section_key

    @property
    def duplicate_names(self):
        return self._duplicate_names

    def _create_tag_entry(self, name):
        new_entry = self._section_entry(name, self)
        return new_entry

    def _check_if_duplicate(self, name_key, new_entry):
        return_entry = new_entry
        if name_key in self.all_names:
            if name_key not in self._duplicate_names:
                self._duplicate_names[name_key] = [self.all_names[name_key]]
            self._duplicate_names[name_key].append(new_entry)
        else:
            self.all_names[name_key] = new_entry

        return return_entry

    def _add_to_dict(self, name, new_entry, parent_index=None):
        """ Add a name to the dictionary for this section. """
        name_key = name
        if not self.case_sensitive:
            name_key = name.lower()

        return_entry = self._check_if_duplicate(name_key, new_entry)

        if parent_index is None:
            parent_index = len(self.all_entries)
        self.all_entries.insert(parent_index, new_entry)
        return return_entry

    def get_entries_with_attribute(self, attribute_name, return_name_only=False, schema_namespace=""):
        """ Return entries or names with given attribute.

        Parameters:
            attribute_name (str): The name of the attribute(generally a HedKey entry).
            return_name_only (bool): If true, return the name as a string rather than the tag entry.
            schema_namespace (str): Prepends given namespace to each name if returning names.

        Returns:
            list: List of HedSchemaEntry or strings representing the names.

        """
        if attribute_name not in self._attribute_cache:
            new_val = [tag_entry for tag_entry in self.values() if tag_entry.has_attribute(attribute_name)]
            self._attribute_cache[attribute_name] = new_val

        cache_val = self._attribute_cache[attribute_name]
        if return_name_only:
            return [f"{schema_namespace}{tag_entry.name}" for tag_entry in cache_val]
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


class HedSchemaUnitClassSection(HedSchemaSection):
    def _check_if_duplicate(self, name_key, new_entry):
        if name_key in self and len(new_entry.attributes) == 1\
                    and HedKey.InLibrary in new_entry.attributes:
            return self.all_names[name_key]
        return super()._check_if_duplicate(name_key, new_entry)


class HedSchemaTagSection(HedSchemaSection):
    """ A section of the schema. """

    def __init__(self, *args, case_sensitive=False, **kwargs):
        super().__init__(*args, **kwargs, case_sensitive=case_sensitive)
        # This dict contains all forms of all tags.  The .all_names variable has ONLY the long forms.
        self.long_form_tags = {}

    @staticmethod
    def _get_tag_forms(name):
        name_key = name
        tag_forms = []
        while name_key:
            tag_forms.append(name_key)
            slash_index = name_key.find("/")
            if slash_index == -1:
                break
            else:
                name_key = name_key[slash_index + 1:]

        # We can't add value tags by themselves
        if tag_forms[-1] == "#":
            tag_forms = tag_forms[:-1]

        return name_key, tag_forms

    def _create_tag_entry(self, name):
        new_entry = super()._create_tag_entry(name)

        _, tag_forms = self._get_tag_forms(name)
        # remove the /# if present, but only from the entry, not from the lookups
        # This lets us easily use source_tag + remainder instead of having to strip off the /# later.
        short_name = tag_forms[-1]
        long_tag_name = name
        if long_tag_name.endswith("/#"):
            long_tag_name = long_tag_name[:-2]
            short_name = short_name[:-2]
        new_entry.long_tag_name = long_tag_name
        new_entry.short_tag_name = short_name

        return new_entry

    def _check_if_duplicate(self, name, new_entry):
        name_key, tag_forms = self._get_tag_forms(name)
        if name_key in self:
            if name_key not in self._duplicate_names:
                self._duplicate_names[name_key] = [self.get(name_key)]
            self._duplicate_names[name_key].append(new_entry)
        else:
            self.all_names[name] = new_entry
            for tag_key in tag_forms:
                name_key = tag_key.lower()
                self.long_form_tags[name_key] = new_entry

        return new_entry

    def _add_to_dict(self, name, new_entry, parent_index=None):
        if new_entry.has_attribute(HedKey.InLibrary):
            parent_name = new_entry.parent_name
            if parent_name.lower() in self:
                # Make sure we insert the new entry after all previous relevant ones, as order isn't assured
                # for rooted tags
                parent_entry = self.get(parent_name.lower())
                parent_index = self.all_entries.index(parent_entry)
                for i in range(parent_index, len(self.all_entries)):
                    if self.all_entries[i].name.startswith(parent_entry.name):
                        parent_index = i + 1
                        continue
                    break

        return super()._add_to_dict(name, new_entry, parent_index)

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
