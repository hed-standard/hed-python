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
        pass

    def set_attribute_value(self, attribute_name, attribute_value):
        """ Add attribute and set its value.

        Parameters:
            attribute_name (str): The name of the schema entry attribute.
            attribute_value (bool or str):  The value of the attribute.

        Notes:
            - If this an invalid attribute name, it will be also added as an unknown attribute.

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
        """ Return True if this entry has the attribute.

        Parameters:
            attribute_name (str): The attribute to check for.
            return_value (bool):  If True return the actual attribute value rather than just indicate presence.

        Returns:
            bool or str:  If return_value is false, a boolean is returned rather than the actual value.

        Notes:
            - A return value of True does not indicate whether or not this attribute is valid

        """
        if return_value:
            return self.attributes.get(attribute_name, None)
        else:
            return attribute_name in self.attributes

    def attribute_has_property(self, attribute_name, property_name):
        """ Return True if attribute has property.

        Parameters:
            attribute_name (str): Attribute name to check for property_name.
            property_name (str): The property value to return.

        Returns:
            bool: Returns True if this entry has the property.

        """
        attr_entry = self._section.valid_attributes.get(attribute_name)
        if attr_entry and attr_entry.has_attribute(property_name):
            return True

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
        return hash((self.name, self._section._section_key))

    def __str__(self):
        return self.name


class UnitClassEntry(HedSchemaEntry):
    """ A single unit class entry in the HedSchema. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._units = []
        self.unit_class_units = []
        self.derivative_units = []
        self.unit_class_entry = None

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
        self.unit_class_units = {unit_entry.name: unit_entry for unit_entry in self._units}
        for unit_name, unit_entry in self.unit_class_units.items():
            new_derivative_units = [unit_name]
            if not unit_entry.has_attribute(HedKey.UnitSymbol):
                new_derivative_units.append(pluralize.plural(unit_name))

            for derived_unit in new_derivative_units:
                derivative_units[derived_unit] = unit_entry
                for modifier in unit_entry.unit_modifiers:
                    derivative_units[modifier.name + derived_unit] = unit_entry
        self.derivative_units = derivative_units


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
        self.unit_modifiers = schema.get_modifiers_for_unit(self.name)


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

    @staticmethod
    def get_fake_tag_entry(tag, tags_to_identify):
        """ Create a tag entry if a given a tag has a match in a list of possible short tags.

        Parameters:
            tag (str): The short/mid/long form tag to identify.
            tags_to_identify (list): A list of lowercase short tags to identify.

        Returns:
            tuple:
                - HedTagEntry or None: The fake entry showing the short tag name as the found tag.
                - str: The remaining text after the located short tag, which may be empty.

        Notes:
             - The match is done left to right.

        """
        split_names = tag.split("/")
        index = 0
        for name in split_names:
            if name.lower() in tags_to_identify:
                fake_entry = HedTagEntry(name=tag[:index + len(name)], section=None)
                fake_entry.long_tag_name = fake_entry.name
                fake_entry.short_tag_name = name
                return fake_entry, tag[index + len(name):]

            index += len(name) + 1

        return None, ""

    def any_parent_has_attribute(self, attribute):
        """ Check if tag (or parents) has the attribute.

        Parameters:
            attribute (str): The name of the attribute to check for.

        Returns:
            bool: True if the tag has the given attribute. False, if otherwise.

        Notes:
            - This is mostly used to check extension allowed.  Could be cached.

        """
        iter_entry = self
        while iter_entry is not None:
            if iter_entry.has_attribute(attribute):
                return True
            iter_entry = iter_entry._parent_tag
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
