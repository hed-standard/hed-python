from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.hed_schema_constants import HedKey

import inflect

pluralize = inflect.engine()
pluralize.defnoun("hertz", "hertz")


class HedSchemaEntry:
    """ A single node in a HedSchema.

        The structure contains all the node information including attributes and properties.

    """
    def __init__(self, name, section):
        """ Constructor for HedSchemaEntry.

        Parameters:
            name (str): The name of the entry.
            section (HedSchemaSection):  The section to which it belongs.

        """
        self.name = name
        # key: property/attribute name, value = property value.  Will often be a bool
        self.attributes = {}
        self.description = None
        self._section = section

        # This section is largely unused.  It will only be filled in when we try to add an attribute
        # that isn't valid in this section.
        self._unknown_attributes = None

    def finalize_entry(self, schema):
        """ Called once after loading to set internal state.

        Parameters:
            schema (HedSchema): The schema that holds the rules.

        """
        # Clear out any known attributes from the unknown section
        to_remove = []
        if self._unknown_attributes:
            for attribute in self._unknown_attributes:
                if attribute in self._section.valid_attributes:
                    to_remove.append(attribute)

            for item in to_remove:
                self._unknown_attributes.pop(item)

    def has_attribute(self, attribute, return_value=False):
        """ Checks for the existence of an attribute in this entry.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            bool or any: If return_value is False, returns True if the attribute exists and False otherwise.
            If return_value is True, returns the value of the attribute if it exists, else returns None.

        Notes:
            - The existence of an attribute does not guarantee its validity.
        """
        if return_value:
            return self.attributes.get(attribute, None)
        else:
            return attribute in self.attributes

    def attribute_has_property(self, attribute, property_name):
        """ Return True if attribute has property.

        Parameters:
            attribute (str): Attribute name to check for property_name.
            property_name (str): The property value to return.

        Returns:
            bool: Returns True if this entry has the property.

        """
        attr_entry = self._section.valid_attributes.get(attribute)
        if attr_entry and attr_entry.has_attribute(property_name):
            return True

    def _set_attribute_value(self, attribute, attribute_value):
        """ Add attribute and set its value.

        Parameters:
            attribute (str): The name of the schema entry attribute.
            attribute_value (bool or str):  The value of the attribute.

        Notes:
            - If this an invalid attribute name, it will be also added as an unknown attribute.

        """
        if not attribute_value:
            return

        # todo: remove this patch and redo the code
        # This check doesn't need to be done if the schema is valid.
        if attribute not in self._section.valid_attributes:
            # print(f"Unknown attribute {attribute}")
            if self._unknown_attributes is None:
                self._unknown_attributes = {}
            self._unknown_attributes[attribute] = attribute_value
        self.attributes[attribute] = attribute_value

    @property
    def section_key(self):
        return self._section.section_key

    def __eq__(self, other):
        if self.name != other.name:
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

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class UnitClassEntry(HedSchemaEntry):
    """ A single unit class entry in the HedSchema. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._units = []
        self.units = []
        self.derivative_units = []

    def add_unit(self, unit_entry):
        """ Add the given unit entry to this unit class.

        Parameters:
            unit_entry (HedSchemaEntry): Unit entry to add.

        """
        self._units.append(unit_entry)

    def finalize_entry(self, schema):
        """ Called once after schema load to set state.

        Parameters:
            schema (HedSchema): The object with the schema rules.

        """
        derivative_units = {}
        self.units = {unit_entry.name: unit_entry for unit_entry in self._units}
        for unit_name, unit_entry in self.units.items():
            new_derivative_units = [unit_name]
            if not unit_entry.has_attribute(HedKey.UnitSymbol):
                new_derivative_units.append(pluralize.plural(unit_name))

            for derived_unit in new_derivative_units:
                derivative_units[derived_unit] = unit_entry
                for modifier in unit_entry.unit_modifiers:
                    derivative_units[modifier.name + derived_unit] = unit_entry
        self.derivative_units = derivative_units

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if self.units != other.units:
            return False
        return True


class UnitEntry(HedSchemaEntry):
    """ A single unit entry with modifiers in the HedSchema. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_class_name = None
        self.unit_modifiers = []

    def finalize_entry(self, schema):
        """ Called once after loading to set internal state.

        Parameters:
            schema (HedSchema): The schema rules come from.

        """
        self.unit_modifiers = schema._get_modifiers_for_unit(self.name)


class HedTagEntry(HedSchemaEntry):
    """ A single tag entry in the HedSchema. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_classes = {}
        self.value_classes = {}
        # These always have any /# stripped off the end, so they can easily be used with normal code.
        self.long_tag_name = None
        self.short_tag_name = None
        self.takes_value_child_entry = None  # this is a child takes value tag, if one exists
        self._parent_tag = None
        self.tag_terms = tuple()
        self._inheritable_attributes = []
        self.inherited_attributes = {}

    def has_attribute(self, attribute, return_value=False):
        """ Returns th existence or value of an attribute in this entry.

            This also checks parent tags for inheritable attributes like ExtensionAllowed.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            bool or any: If return_value is False, returns True if the attribute exists and False otherwise.
            If return_value is True, returns the value of the attribute if it exists, else returns None.

        Notes:
            - The existence of an attribute does not guarantee its validity.
        """
        if attribute in self._inheritable_attributes:
            val = self.inherited_attributes.get(attribute)
            if not return_value:
                val = val is not None
            return val
        return super().has_attribute(attribute, return_value)

    def _check_inherited_attribute(self, attribute, return_value=False, return_union=False):
        """
        Checks for the existence of an attribute in this entry and its parents.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.
            return_union(bool): If true, return a union of all parent values

        Returns:
            bool or any: Depending on the flag return_value,
            returns either the presence of the attribute, or its value.

        Notes:
            - The existence of an attribute does not guarantee its validity.
            - For string attributes, the values are joined with a comma as a delimiter from all ancestors.
        """
        if return_value:
            attribute_values = []

        iter_entry = self
        while iter_entry is not None:
            if iter_entry.takes_value_child_entry:
                break
            if attribute in iter_entry.attributes:
                if return_value:
                    attribute_values.append(iter_entry.attributes[attribute])
                    if not return_union:
                        break
                else:
                    return True
            iter_entry = iter_entry._parent_tag

        if return_value:
            if not attribute_values:
                return None
            if return_union:
                return ",".join(attribute_values)
            else:
                return attribute_values[0]
        else:
            return False

    def base_tag_has_attribute(self, tag_attribute):
        """ Check if the base tag has a specific attribute.

        Parameters:
            tag_attribute (str): A tag attribute.

        Returns:
            bool: True if the tag has the specified attribute. False, if otherwise.

        Notes:
            This mostly is relevant for takes value tags.

        """
        base_entry = self
        if self.has_attribute(HedKey.TakesValue):
            base_entry = base_entry._parent_tag

        return base_entry.has_attribute(tag_attribute)

    @property
    def parent(self):
        """Get the parent entry of this tag"""
        return self._parent_tag

    @property
    def parent_name(self):
        """Gets the parent tag entry name"""
        if self._parent_tag:
            return self._parent_tag.name
        parent_name, _, child_name = self.name.rpartition("/")
        return parent_name

    def _finalize_takes_value_tag(self, schema):
        if self.name.endswith("/#"):
            if HedKey.UnitClass in self.attributes:
                self.unit_classes = {}
                for unit_class_name in self.attributes[HedKey.UnitClass].split(","):
                    entry = schema._get_tag_entry(unit_class_name, HedSectionKey.UnitClasses)
                    if entry:
                        self.unit_classes[unit_class_name] = entry

            if HedKey.ValueClass in self.attributes:
                self.value_classes = {}
                for value_class_name in self.attributes[HedKey.ValueClass].split(","):
                    entry = schema._get_tag_entry(value_class_name, HedSectionKey.ValueClasses)
                    if entry:
                        self.value_classes[value_class_name] = entry

    def _finalize_inherited_attributes(self):
        self._inheritable_attributes = self._section.inheritable_attributes
        self.inherited_attributes = {}
        for attribute in self._section.inheritable_attributes:
            if self._check_inherited_attribute(attribute):
                treat_as_string = not self.attribute_has_property(attribute, HedKey.BoolProperty)
                self.inherited_attributes[attribute] = self._check_inherited_attribute(attribute, True, treat_as_string)

    def finalize_entry(self, schema):
        """ Called once after schema loading to set state.

        Parameters:
            schema (HedSchema): The schema that the rules come from.

        """
        # Set the parent and child pointers.  Child is just for "takes value"
        parent_name, _, child_name = self.name.rpartition("/")
        parent_tag = None
        if parent_name:
            parent_tag = schema._get_tag_entry(parent_name)
        self._parent_tag = parent_tag
        self.takes_value_child_entry = schema._get_tag_entry(self.name + "/#")
        self.tag_terms = tuple(self.long_tag_name.lower().split("/"))

        self._finalize_inherited_attributes()
        self._finalize_takes_value_tag(schema)
