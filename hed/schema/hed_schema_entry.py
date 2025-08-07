from __future__ import annotations
from typing import Union, Any
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

    def has_attribute(self, attribute, return_value=False) -> Union[bool, Any]:
        """ Checks for the existence of an attribute in this entry.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            Union[bool, any]: If return_value is False, returns True if the attribute exists and False otherwise.
            If return_value is True, returns the value of the attribute if it exists, else returns None.

        Notes:
            - The existence of an attribute does not guarantee its validity.
        """
        if return_value:
            return self.attributes.get(attribute, None)
        else:
            return attribute in self.attributes

    def attribute_has_property(self, attribute, property_name) -> bool:
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
        return False

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
        if not self._compare_attributes_no_order(self.attributes, other.attributes):
            return False
        if self.description != other.description:
            return False
        return True

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    @staticmethod
    def _compare_attributes_no_order(left, right):
        if left != right:
            left = {name: (set(value.split(",")) if isinstance(value, str) else value)
                    for (name, value) in left.items()}
            right = {name: (set(value.split(",")) if isinstance(value, str) else value)
                     for (name, value) in right.items()}

        return left == right


class UnitClassEntry(HedSchemaEntry):
    """ A single unit class entry in the HedSchema. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._units = []
        self.units = []
        self.derivative_units = {}

    @property
    def children(self):
        """ Alias to get the units for this class

        Returns:
            unit_list(list): The unit list for this class
        """
        return self.units

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
        self.units = {unit_entry.name: unit_entry for unit_entry in self._units}
        for unit_entry in self.units.values():
            unit_entry.unit_class_entry = self
        derivative_units = {}
        for unit_entry in self.units.values():
            derivative_units.update({key: unit_entry for key in unit_entry.derivative_units.keys()})

        self.derivative_units = derivative_units

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if self.units != other.units:
            return False
        return True

    def get_derivative_unit_entry(self, units):
        """ Gets the (derivative) unit entry if it exists

        Parameters:
            units (str): The unit name to check, can be plural or include a modifier.

        Returns:
            Union[UnitEntry, None]: The unit entry if it exists.

        """
        possible_match = self.derivative_units.get(units)
        # If we have a match that's a unit symbol, we're done, return it.
        if possible_match and possible_match.has_attribute(HedKey.UnitSymbol):
            return possible_match

        possible_match = self.derivative_units.get(units.casefold())
        # Unit symbols must match including case, a match of a unit symbol now is something like M becoming m.
        if possible_match and possible_match.has_attribute(HedKey.UnitSymbol):
            possible_match = None

        return possible_match


class UnitEntry(HedSchemaEntry):
    """ A single unit entry with modifiers in the HedSchema. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_modifiers = []
        self.derivative_units = {}
        self.unit_class_entry = None

    def finalize_entry(self, schema):
        """ Called once after loading to set internal state.

        Parameters:
            schema (HedSchema): The schema rules come from.

        """
        self.unit_modifiers = schema._get_modifiers_for_unit(self.name)
        derivative_units = {}
        if self.has_attribute(HedKey.UnitSymbol):
            base_plural_units = {self.name}
        else:
            base_plural_units = {self.name.lower()}
            base_plural_units.add(pluralize.plural(self.name.lower()))

        for derived_unit in base_plural_units:
            derivative_units[derived_unit] = self._get_conversion_factor(None)
            for modifier in self.unit_modifiers:
                derivative_units[modifier.name + derived_unit] = self._get_conversion_factor(modifier_entry=modifier)
        self.derivative_units = derivative_units

    def _get_conversion_factor(self, modifier_entry):
        base_factor = modifier_factor = 1.0
        try:
            base_factor = float(self.attributes.get(HedKey.ConversionFactor, "1.0").replace("^", "e"))
            if modifier_entry:
                modifier_factor = float(modifier_entry.attributes.get(HedKey.ConversionFactor, "1.0").replace("^", "e"))
        except (ValueError, AttributeError):
            pass  # Just default to 1.0
        return base_factor * modifier_factor

    def get_conversion_factor(self, unit_name):
        """Returns the conversion factor from combining this unit with the specified modifier

        Parameters:
            unit_name (str or None): the full name of the unit with modifier

        Returns:
            Union[float, None]: Returns the conversion factor or None
        """
        if HedKey.ConversionFactor in self.attributes:
            return float(self.derivative_units.get(unit_name))


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
        # During setup, it's better to have attributes shadow inherited before getting its own copy later.
        self.inherited_attributes = self.attributes
        # Descendent tags below this one
        self.children = {}

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if not self._compare_attributes_no_order(self.inherited_attributes, other.inherited_attributes):
            return False
        return True

    def has_attribute(self, attribute, return_value=False):
        """ Returns th existence or value of an attribute in this entry.

            This also checks parent tags for inheritable attributes like ExtensionAllowed.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            Union[bool, any]: If return_value is False, returns True if the attribute exists and False otherwise.
            If return_value is True, returns the value of the attribute if it exists, else returns None.

        Notes:
            - The existence of an attribute does not guarantee its validity.
        """
        val = self.inherited_attributes.get(attribute)
        if not return_value:
            val = val is not None
        return val

    def _check_inherited_attribute_internal(self, attribute):
        """Gather up all instances of an attribute from this entry and any parent entries"""
        attribute_values = []

        iter_entry = self
        while iter_entry is not None:
            if iter_entry.takes_value_child_entry:
                break
            if attribute in iter_entry.attributes:
                attribute_values.append(iter_entry.attributes[attribute])
            iter_entry = iter_entry._parent_tag

        return attribute_values

    def _check_inherited_attribute(self, attribute, return_value=False):
        """
        Checks for the existence of an attribute in this entry and its parents.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            Union[bool, any]: Depending on the flag return_value,
            returns either the presence of the attribute, or its value.

        Notes:
            - The existence of an attribute does not guarantee its validity.
            - For string attributes, the values are joined with a comma as a delimiter from all ancestors.
            - For other attributes, only the value closest to the leaf is returned
        """
        attribute_values = self._check_inherited_attribute_internal(attribute)

        if return_value:
            if not attribute_values:
                return None
            try:
                return ",".join(attribute_values)
            except TypeError:
                return attribute_values[0]  # Return the lowest level attribute if we don't want the union
        return bool(attribute_values)

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

    def _finalize_classes(self, schema, attribute_key, section_key):
        result = {}
        if attribute_key in self.attributes:
            for attribute_name in self.attributes[attribute_key].split(","):
                entry = schema._get_tag_entry(attribute_name, section_key)
                if entry:
                    result[attribute_name] = entry
        return result

    def _finalize_takes_value_tag(self, schema):
        if self.name.endswith("/#"):
            self.unit_classes = self._finalize_classes(schema, HedKey.UnitClass, HedSectionKey.UnitClasses)
            self.value_classes = self._finalize_classes(schema, HedKey.ValueClass, HedSectionKey.ValueClasses)

    def _finalize_inherited_attributes(self):
        # Replace the list with a copy we can modify.
        self.inherited_attributes = self.attributes.copy()
        for attribute in self._section.inheritable_attributes:
            if self._check_inherited_attribute(attribute):
                self.inherited_attributes[attribute] = self._check_inherited_attribute(attribute, True)

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
        if self._parent_tag:
            self._parent_tag.children[self.short_tag_name] = self
        self.takes_value_child_entry = schema._get_tag_entry(self.name + "/#")
        self.tag_terms = tuple(self.long_tag_name.casefold().split("/"))

        self._finalize_inherited_attributes()
        self._finalize_takes_value_tag(schema)
