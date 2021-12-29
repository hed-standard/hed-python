from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.hed_schema_constants import HedKey

import inflect

pluralize = inflect.engine()
pluralize.defnoun("hertz", "hertz")


class HedSchemaEntry:
    """
        A single entry in the HedSchema, containing its attributes/properties/etc.
    """
    def __init__(self, long_name, section):
        self.long_name = long_name
        # key: property/attribute name, value = property value.  Will often be a bool
        self.attributes = {}
        self.description = None
        self._section = section

        # This section is largely unused.  It will only be filled in when we try to add an attribute
        # that isn't valid in this section.
        self._unknown_attributes = None

    def finalize_entry(self, schema):
        """
            Called once after schema load to set up the internal state of this entry.

        Parameters
        ----------
        schema: HedSchema
            The schema rules come from.
        Returns
        -------
        """
        pass

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
            The property name we're looking for in attribute_name
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
        return True


class UnitClassEntry(HedSchemaEntry):
    """
        A single unit class entry in the HedSchema, containing it's units, etc.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_class_units = []
        self.derivative_units = []

    def finalize_entry(self, schema):
        """
            Called once after schema load to set up the internal state of this entry.

        Parameters
        ----------
        schema: HedSchema
            The schema rules come from.
        Returns
        -------
        """
        derivative_units = {}
        self.unit_class_units = schema.get_units_for_unit_class(self.long_name)
        for unit_name, unit_entry in self.unit_class_units.items():
            new_derivative_units = [unit_name]
            if not unit_entry.has_attribute(HedKey.UnitSymbol):
                new_derivative_units.append(pluralize.plural(unit_name))

            for derived_unit in new_derivative_units:
                derivative_units[derived_unit] = unit_entry
                for modifier in unit_entry.unit_modifiers:
                    derivative_units[modifier.long_name + derived_unit] = unit_entry
        self.derivative_units = derivative_units


class UnitEntry(HedSchemaEntry):
    """
        A single unit entry in the HedSchema, containing its unit modifiers etc.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_class_name = None
        self.unit_modifiers = []

    def finalize_entry(self, schema):
        """
            Called once after schema load to set up the internal state of this entry.

        Parameters
        ----------
        schema: HedSchema
            The schema rules come from.
        Returns
        -------
        """
        self.unit_modifiers = schema.get_modifiers_for_unit(self.long_name)


class HedTagEntry(HedSchemaEntry):
    """
        A single tag entry in the HedSchema, containing its parent tag, unit classes, value classes, etc.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_classes = {}
        self.value_classes = {}
        self._parent_tag = None

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
            iter_entry = iter_entry._parent_tag
        return False

    def base_tag_has_attribute(self, tag_attribute):
        """Checks to see if the base tag has a specific attribute.  This mostly is relevant for takes value tags.

        Parameters
        ----------
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        base_entry = self
        if self.has_attribute(HedKey.TakesValue):
            base_entry = base_entry._parent_tag

        return base_entry.has_attribute(tag_attribute)

    def finalize_entry(self, schema):
        """
            Called once after schema load to set up the internal state of this entry.

        Parameters
        ----------
        schema: HedSchema
            The schema rules come from.
        Returns
        -------
        """
        parent_name, _, child_name = self.long_name.rpartition("/")
        parent_tag = None
        if parent_name:
            parent_tag = schema._get_entry_for_tag(parent_name)
        self._parent_tag = parent_tag

        # We only allow unit or value classes on # nodes, it should be flagged as a warning otherwise.
        if child_name == "#":
            if HedKey.UnitClass in self.attributes:
                self.unit_classes = {}
                for unit_class_name in self.attributes[HedKey.UnitClass].split(","):
                    entry = schema._get_entry_for_tag(unit_class_name, HedSectionKey.UnitClasses)
                    if entry:
                        self.unit_classes[unit_class_name] = entry

            if HedKey.ValueClass in self.attributes:
                self.value_classes = {}
                for value_class_name in self.attributes[HedKey.ValueClass].split(","):
                    entry = schema._get_entry_for_tag(value_class_name, HedSectionKey.ValueClasses)
                    if entry:
                        self.value_classes[value_class_name] = entry
