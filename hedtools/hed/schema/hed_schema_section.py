

class HedSchemaEntry:
    def __init__(self, long_name, section):
        self.long_name = long_name
        # key: property/attribute name, value = property value.  Will often be a bool
        self.attributes = {}
        self.description = None
        self.value = None
        self._section = section

        # This section is largely unused.  It will only be filled in when we try to add an attribute
        # that isn't valid in this section.
        self._unknown_attributes = None

    def set_attribute_value(self, attribute_name, attribute_value):
        """
            Add the given attribute to this entry and set its value

            If this is not a valid attribute name, it will be also added as an unknown attribute.

        Parameters
        ----------
        attribute_name : str
        attribute_value : bool or str

        Returns
        -------

        """
        if not attribute_value:
            return

        if attribute_name not in self._section.valid_attributes:
            # print(f"Unknown attribute {attribute_name}")
            if self._unknown_attributes is None:
                self._unknown_attributes = {}
            self._unknown_attributes[attribute_name] = attribute_value
        self.attributes[attribute_name] = attribute_value

    def has_attribute(self, attribute_name, return_value=False):
        """
        Returns if this entry has this attribute.  This does not guarantee it's a valid attribute for this entry.

        Parameters
        ----------
        attribute_name : str
            The attribute to check for
        return_value : bool
            Return the value of the attribute, rather than simply if it is present

        Returns
        -------

        """
        if return_value:
            return self.attributes.get(attribute_name, None)
        else:
            return attribute_name in self.attributes

    def attribute_has_property(self, attribute_name, property_name):
        """
            If this is a valid attribute for this section, retrieve if it has the given property

        Parameters
        ----------
        attribute_name : str
            Attribute name to check for property_name
        property_name : str
        Returns
        -------
        has_property: bool
            Returns if it has the property
        """
        attr_entry = self._section.valid_attributes.get(attribute_name)
        if attr_entry and attr_entry.has_attribute(property_name):
            return True

    def __eq__(self, other):
        if self.long_name != other.long_name:
            return False
        if self.attributes != other.attributes:
            # We only want to compare known attributes
            self_attr = {key: value for key, value in self.attributes.items()
                         if not self._unknown_attributes or key not in self._unknown_attributes}
            other_attr = {key: value for key, value in other.attributes.items()
                          if not other._unknown_attributes or key not in other._unknown_attributes}
            if self_attr != other_attr:
                return False
        if self.description != other.description:
            return False
        if self.value != other.value:
            return False
        return True


class HedSchemaSection:
    def __init__(self, section_key, case_sensitive=True):
        # {lower_case_name: HedSchemaEntry}
        self.all_names = {}
        self._section_key = section_key
        self.case_sensitive = case_sensitive

        # Points to the entries in attributes
        self.valid_attributes = {}

    def _add_to_dict(self, name):
        name_key = name
        if not self.case_sensitive:
            name_key = name.lower()

        # todo: could add this check back and improve.
        #  This detects two FULLY identical tags, including all terms and parents.
        # if name_key in self.all_names:
        #     print(f"NotImplemented: {name_key} found twice in schema.")
        new_entry = HedSchemaEntry(name, self)
        self.all_names[name_key] = new_entry

        return new_entry

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
