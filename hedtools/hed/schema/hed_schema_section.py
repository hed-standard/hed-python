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
    def __init__(self, section_key, case_sensitive=True):
        # {lower_case_name: HedSchemaEntry}
        self.all_names = {}
        self._section_key = section_key
        self.case_sensitive = case_sensitive

        # Points to the entries in attributes
        self.valid_attributes = {}
        self._attribute_cache = {}

        self._section_entry = entries_by_section.get(section_key)

    def _add_to_dict(self, name):
        name_key = name
        if not self.case_sensitive:
            name_key = name.lower()

        # todo: could add this check back and improve.
        #  This detects two FULLY identical tags, including all terms and parents.
        # if name_key in self.all_names:
        #     print(f"NotImplemented: {name_key} found twice in schema.")
        new_entry = self._section_entry(name, self)
        self.all_names[name_key] = new_entry

        return new_entry

    def get_entries_with_attribute(self, attribute_name, return_name_only=False):
        """
            Returns an iterator of all entries with the given attribute

            If this is called outside of schema validation, you may wish to cache this result or update
            this function to have a cache.

        Parameters
        ----------
        attribute_name: str
            The name of the attribute(generally a HedKey entry)

        Returns
        -------
        [HedSchemaEntry] or [str]
        """
        if attribute_name not in self._attribute_cache:
            new_val = [tag_entry for tag_entry in self.values() if tag_entry.has_attribute(attribute_name)]
            self._attribute_cache[attribute_name] = new_val

        cache_val = self._attribute_cache[attribute_name]
        if return_name_only:
            return [tag_entry.long_name for tag_entry in cache_val]
        return cache_val

    # ===============================================
    # Simple wrapper functions to make this class primarily function as a dict
    # ===============================================
    def __iter__(self):
        return iter(self.all_names)

    def items(self):
        return self.all_names.items()

    def values(self):
        return self.all_names.values()

    def keys(self):
        return self.all_names.keys()

    def __getitem__(self, key):
        if not self.case_sensitive:
            key = key.lower()
        return self.all_names[key]

    def get(self, key):
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
        return True

    def __bool__(self):
        return bool(self.all_names)
