class HedSchemaEntry:
    def __init__(self, long_name, section, parent_entry):
        self.long_name = long_name
        # key: property/attribute name, value = property value.  Will often be a bool
        self.attributes = {}
        self.description = None
        self._section = section

        # this is currently used exclusively for unit class units.
        self.value = None

        # This section is largely unused.  It will only be filled in when we try to add an attribute
        # that isn't valid in this section.
        self._unknown_attributes = None
        self._parent_entry = parent_entry

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

    def any_parent_has_attribute(self, attribute):
        """Checks to see if the tag (or any of its parents) have the given attribute.

        Parameters
        ----------
        attribute: str
            The name of the attribute to check for.
        Returns
        -------
        tag_has_attribute: bool
            True if the tag has the given attribute. False, if otherwise.
        """
        iter_entry = self
        while iter_entry is not None:
            if iter_entry.has_attribute(attribute):
                return True
            iter_entry = iter_entry._parent_entry
        return False

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
        return True